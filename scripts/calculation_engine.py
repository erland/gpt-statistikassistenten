"""Deterministic calculation layer for normalized Statistikassistenten results.

The functions in this module only operate on the canonical statistical-result
shape.  They never infer missing periods, geographies, units or denominators.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


class CalculationError(ValueError):
    """Raised when a requested calculation is not methodologically valid."""


_STATUS_PRIORITY = {
    "observed": 0,
    "provisional": 1,
    "estimated": 2,
    "break_in_series": 3,
    "confidential": 4,
    "missing": 5,
}


def _measure(result: Mapping[str, Any], measure_id: str) -> Mapping[str, Any]:
    for measure in result.get("measures", []):
        if measure.get("id") == measure_id:
            return measure
    raise CalculationError(f"Okänt mått: {measure_id}")


def _observations(result: Mapping[str, Any], measure_id: str) -> List[Mapping[str, Any]]:
    rows = [o for o in result.get("observations", []) if o.get("measure") == measure_id]
    if not rows:
        raise CalculationError(f"Inga observationer för måttet {measure_id}")
    return rows


def _dimension_kind_map(result: Mapping[str, Any]) -> Dict[str, str]:
    return {d["id"]: d["kind"] for d in result.get("dimensions", [])}


def _time_dimension(result: Mapping[str, Any]) -> str:
    ids = [d["id"] for d in result.get("dimensions", []) if d.get("kind") == "time"]
    if len(ids) != 1:
        raise CalculationError("Beräkningen kräver exakt en explicit tidsdimension")
    return ids[0]


def _geo_dimensions(result: Mapping[str, Any]) -> List[str]:
    return [d["id"] for d in result.get("dimensions", []) if d.get("kind") == "geography"]


def _status(*statuses: str) -> str:
    return max(statuses, key=lambda s: _STATUS_PRIORITY.get(s, 99))


def _numeric(obs: Mapping[str, Any]) -> float:
    value = obs.get("value")
    if value is None or obs.get("status") in {"missing", "confidential"}:
        raise CalculationError("Saknat eller sekretesskyddat värde kan inte användas i beräkning")
    return float(value)


def _identity(dimensions: Mapping[str, str], *, exclude: Iterable[str] = ()) -> Tuple[Tuple[str, str], ...]:
    excluded = set(exclude)
    return tuple(sorted((k, v) for k, v in dimensions.items() if k not in excluded))


def _assert_same_frequency(a: Mapping[str, Any], b: Mapping[str, Any]) -> None:
    fa = a.get("dataset", {}).get("frequency", "unknown")
    fb = b.get("dataset", {}).get("frequency", "unknown")
    if fa != "unknown" and fb != "unknown" and fa != fb:
        raise CalculationError(f"Oförenlig tidsfrekvens: {fa} vs {fb}")


def _assert_same_geography(a: Mapping[str, Any], b: Mapping[str, Any]) -> None:
    ga = _geo_dimensions(a)
    gb = _geo_dimensions(b)
    if len(ga) != 1 or len(gb) != 1:
        raise CalculationError("Kombinerade mått kräver en explicit geografidimension i vardera källan")


def _base_contract(kind: str, unit: str, formula: str, notes: Optional[List[str]] = None) -> Dict[str, Any]:
    return {
        "calculation": {
            "type": kind,
            "unit": unit,
            "formula": formula,
        },
        "observations": [],
        "method": {
            "checks": ["numeric_values", "explicit_dimensions", "unit_verified"],
            "notes": notes or [],
        },
    }


def absolute_change(
    result: Mapping[str, Any],
    measure_id: str,
    start_period: str,
    end_period: str,
) -> Dict[str, Any]:
    measure = _measure(result, measure_id)
    time_dim = _time_dimension(result)
    rows = _observations(result, measure_id)
    grouped: Dict[Tuple[Tuple[str, str], ...], Dict[str, Mapping[str, Any]]] = {}
    for obs in rows:
        dims = obs["dimensions"]
        grouped.setdefault(_identity(dims, exclude=[time_dim]), {})[dims.get(time_dim)] = obs

    out = _base_contract("absolute_change", measure["unit"], "end - start")
    out["calculation"].update({"start_period": start_period, "end_period": end_period})
    for key, periods in grouped.items():
        if start_period not in periods or end_period not in periods:
            raise CalculationError(f"Periodmatchning saknas för {dict(key)}: {start_period} och {end_period} krävs")
        start, end = periods[start_period], periods[end_period]
        dims = dict(key)
        dims[time_dim] = f"{start_period}→{end_period}"
        out["observations"].append({
            "dimensions": dims,
            "value": _numeric(end) - _numeric(start),
            "status": _status(start["status"], end["status"]),
            "inputs": [
                {"period": start_period, "value": start["value"], "status": start["status"]},
                {"period": end_period, "value": end["value"], "status": end["status"]},
            ],
        })
    return out


def percent_change(
    result: Mapping[str, Any],
    measure_id: str,
    start_period: str,
    end_period: str,
) -> Dict[str, Any]:
    raw = absolute_change(result, measure_id, start_period, end_period)
    out = _base_contract("percent_change", "%", "((end - start) / start) * 100")
    out["calculation"].update({"start_period": start_period, "end_period": end_period})
    for obs in raw["observations"]:
        start = float(obs["inputs"][0]["value"])
        end = float(obs["inputs"][1]["value"])
        if start == 0:
            raise CalculationError("Procentuell förändring kan inte beräknas från basvärdet 0")
        item = deepcopy(obs)
        item["value"] = ((end - start) / start) * 100.0
        out["observations"].append(item)
    return out


def index_series(
    result: Mapping[str, Any],
    measure_id: str,
    base_period: str,
    base_index: float = 100.0,
) -> Dict[str, Any]:
    _measure(result, measure_id)
    time_dim = _time_dimension(result)
    rows = _observations(result, measure_id)
    grouped: Dict[Tuple[Tuple[str, str], ...], List[Mapping[str, Any]]] = {}
    for obs in rows:
        grouped.setdefault(_identity(obs["dimensions"], exclude=[time_dim]), []).append(obs)

    out = _base_contract("index", "index", f"(value / base_value) * {base_index:g}")
    out["calculation"].update({"base_period": base_period, "base_index": base_index})
    for key, observations in grouped.items():
        by_period = {o["dimensions"].get(time_dim): o for o in observations}
        if base_period not in by_period:
            raise CalculationError(f"Basperiod {base_period} saknas för {dict(key)}")
        base_obs = by_period[base_period]
        base_value = _numeric(base_obs)
        if base_value == 0:
            raise CalculationError("Index kan inte skapas med basvärdet 0")
        for obs in observations:
            item = {
                "dimensions": dict(obs["dimensions"]),
                "value": (_numeric(obs) / base_value) * base_index,
                "status": _status(base_obs["status"], obs["status"]),
                "inputs": [
                    {"period": base_period, "value": base_obs["value"], "status": base_obs["status"]},
                    {"period": obs["dimensions"].get(time_dim), "value": obs["value"], "status": obs["status"]},
                ],
            }
            out["observations"].append(item)
    return out


def _match_cross_source(
    a: Mapping[str, Any],
    a_measure_id: str,
    b: Mapping[str, Any],
    b_measure_id: str,
) -> List[Tuple[Mapping[str, Any], Mapping[str, Any], Dict[str, str]]]:
    _assert_same_frequency(a, b)
    _assert_same_geography(a, b)
    at = _time_dimension(a)
    bt = _time_dimension(b)
    ag = _geo_dimensions(a)[0]
    bg = _geo_dimensions(b)[0]

    def semantic_key(obs: Mapping[str, Any], t: str, g: str) -> Tuple[str, str]:
        dims = obs["dimensions"]
        if t not in dims or g not in dims:
            raise CalculationError("Observation saknar tid eller geografi")
        return dims[t], dims[g]

    a_rows = _observations(a, a_measure_id)
    b_rows = _observations(b, b_measure_id)
    b_index: Dict[Tuple[str, str], Mapping[str, Any]] = {}
    for obs in b_rows:
        key = semantic_key(obs, bt, bg)
        if key in b_index:
            raise CalculationError(f"Nämnarserien är inte entydig för period/geografi {key}")
        b_index[key] = obs

    pairs = []
    for obs in a_rows:
        key = semantic_key(obs, at, ag)
        if key not in b_index:
            raise CalculationError(f"Period/geografi saknas i kombinationsserien: {key}")
        # Preserve numerator dimensions but expose canonical time/geography values.
        dims = dict(obs["dimensions"])
        pairs.append((obs, b_index[key], dims))
    return pairs


def per_capita(
    numerator: Mapping[str, Any],
    numerator_measure_id: str,
    denominator: Mapping[str, Any],
    denominator_measure_id: str,
    *,
    scale: float = 100000.0,
) -> Dict[str, Any]:
    if scale <= 0:
        raise CalculationError("Per-capita-skalan måste vara positiv")
    num_measure = _measure(numerator, numerator_measure_id)
    den_measure = _measure(denominator, denominator_measure_id)
    if num_measure.get("statistic_type") != "count":
        raise CalculationError("Per-capita-täljaren måste vara ett antal")
    if den_measure.get("statistic_type") != "count":
        raise CalculationError("Per-capita-nämnaren måste vara ett antal personer/population")

    out = _base_contract("per_capita", f"per {scale:g}", f"(numerator / denominator) * {scale:g}")
    out["method"]["checks"].extend(["same_period", "same_geography", "positive_denominator"])
    for num, den, dims in _match_cross_source(numerator, numerator_measure_id, denominator, denominator_measure_id):
        n = _numeric(num)
        d = _numeric(den)
        if d <= 0:
            raise CalculationError("Per-capita-nämnaren måste vara större än 0")
        out["observations"].append({
            "dimensions": dims,
            "value": (n / d) * scale,
            "status": _status(num["status"], den["status"]),
            "inputs": [
                {"role": "numerator", "value": num["value"], "unit": num_measure["unit"], "status": num["status"]},
                {"role": "denominator", "value": den["value"], "unit": den_measure["unit"], "status": den["status"]},
            ],
        })
    return out


def share(
    numerator: Mapping[str, Any],
    numerator_measure_id: str,
    denominator: Mapping[str, Any],
    denominator_measure_id: str,
) -> Dict[str, Any]:
    num_measure = _measure(numerator, numerator_measure_id)
    den_measure = _measure(denominator, denominator_measure_id)
    if num_measure.get("unit") != den_measure.get("unit"):
        raise CalculationError(f"Andel kräver samma enhet: {num_measure.get('unit')} vs {den_measure.get('unit')}")
    out = _base_contract("share", "%", "(part / total) * 100")
    out["method"]["checks"].extend(["same_period", "same_geography", "same_unit", "positive_denominator"])
    for num, den, dims in _match_cross_source(numerator, numerator_measure_id, denominator, denominator_measure_id):
        n = _numeric(num)
        d = _numeric(den)
        if d <= 0:
            raise CalculationError("Andelsnämnaren måste vara större än 0")
        out["observations"].append({
            "dimensions": dims,
            "value": (n / d) * 100.0,
            "status": _status(num["status"], den["status"]),
            "inputs": [
                {"role": "part", "value": num["value"], "unit": num_measure["unit"], "status": num["status"]},
                {"role": "total", "value": den["value"], "unit": den_measure["unit"], "status": den["status"]},
            ],
        })
    return out
