from __future__ import annotations

import csv
import io
from typing import Any, Dict, List


STATUS_LABELS = {
    "observed": "observerad",
    "provisional": "preliminär",
    "estimated": "uppskattad",
    "break_in_series": "tidsseriebrott",
    "confidential": "sekretess",
    "missing": "saknas",
}


def _display_value(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def _trend_analysis(rows: List[Dict[str, Any]]) -> List[str]:
    numeric = [r for r in rows if isinstance(r.get("value"), (int, float))]
    if len(numeric) < 2:
        return []
    first, last = numeric[0], numeric[-1]
    fv, lv = float(first["value"]), float(last["value"])
    if lv > fv:
        direction = "ökade"
    elif lv < fv:
        direction = "minskade"
    else:
        direction = "var oförändrat"
    text = f"Mellan första och sista jämförbara observationen {direction} värdet från {_display_value(fv)} till {_display_value(lv)}."
    result = [text]
    if len(numeric) >= 3:
        values = [float(r["value"]) for r in numeric]
        deltas = [b - a for a, b in zip(values, values[1:])]
        if any(d > 0 for d in deltas) and any(d < 0 for d in deltas):
            result.append("Utvecklingen var inte entydig under hela perioden; serien innehåller både upp- och nedgångar.")
    return result


def from_statistical_result(result: Dict[str, Any], answer: str | None = None) -> Dict[str, Any]:
    measure_map = {m["id"]: m for m in result.get("measures", [])}
    rows = []
    for obs in result.get("observations", []):
        measure = measure_map.get(obs.get("measure"), {})
        rows.append({
            "dimensions": {str(k): str(v) for k, v in obs.get("dimensions", {}).items()},
            "value": obs.get("value"),
            "unit": str(measure.get("unit", "")),
            "status": str(obs.get("status", "observed")),
            "origin": "source",
        })
    source = result["provenance"]["source"]
    method = result.get("method", {})
    notes = list(method.get("comparability_notes", [])) + list(method.get("breaks_in_series", []))
    if any(r["status"] == "provisional" for r in rows):
        notes.append("Resultatet innehåller preliminära observationer.")
    title = result.get("dataset", {}).get("title", "Statistikresultat")
    default_answer = f"Resultatet innehåller {len(rows)} verifierade observationer."
    return {
        "title": title,
        "answer": answer or default_answer,
        "rows": rows,
        "analysis": _trend_analysis(rows),
        "method_notes": list(dict.fromkeys(notes)),
        "sources": [{
            "organization": source.get("organization", result.get("dataset", {}).get("publisher", "")),
            "dataset": source.get("dataset_title", title),
            "period": _period(rows),
            "geography": _geography(rows),
            "measure": ", ".join(m.get("label", m.get("id", "")) for m in result.get("measures", [])),
            **({"url": source["url"]} if source.get("url") else {}),
        }],
    }


def from_calculation_result(calc: Dict[str, Any], title: str, answer: str, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
    rows = [{
        "dimensions": {str(k): str(v) for k, v in obs.get("dimensions", {}).items()},
        "value": obs.get("value"),
        "unit": calc["calculation"]["unit"],
        "status": obs.get("status", "observed"),
        "origin": "calculated",
    } for obs in calc.get("observations", [])]
    return {
        "title": title,
        "answer": answer,
        "rows": rows,
        "analysis": _trend_analysis(rows),
        "method_notes": list(calc.get("method", {}).get("notes", [])),
        "sources": sources,
    }


def _period(rows: List[Dict[str, Any]]) -> str:
    vals = [r["dimensions"].get("time") for r in rows if r["dimensions"].get("time")]
    if not vals:
        return ""
    uniq = list(dict.fromkeys(vals))
    return uniq[0] if len(uniq) == 1 else f"{uniq[0]}–{uniq[-1]}"


def _geography(rows: List[Dict[str, Any]]) -> str:
    vals = []
    for r in rows:
        v = r["dimensions"].get("geography") or r["dimensions"].get("geo")
        if v:
            vals.append(v)
    uniq = list(dict.fromkeys(vals))
    return ", ".join(uniq)


def to_markdown(p: Dict[str, Any]) -> str:
    lines = [f"# {p['title']}", "", p["answer"]]
    if p["rows"]:
        dim_keys = []
        for row in p["rows"]:
            for key in row["dimensions"]:
                if key not in dim_keys:
                    dim_keys.append(key)
        headers = dim_keys + ["värde", "enhet", "status", "ursprung"]
        lines += ["", "## Data", "", "| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
        for row in p["rows"]:
            vals = [row["dimensions"].get(k, "") for k in dim_keys]
            vals += [_display_value(row["value"]), row["unit"], STATUS_LABELS.get(row["status"], row["status"]), row["origin"]]
            lines.append("| " + " | ".join(str(v).replace("|", "\\|") for v in vals) + " |")
    if p["analysis"]:
        lines += ["", "## Analys", ""] + [f"- {x}" for x in p["analysis"]]
    if p["method_notes"]:
        lines += ["", "## Metodnotering", ""] + [f"- {x}" for x in p["method_notes"]]
    lines += ["", "## Källor", ""]
    for s in p["sources"]:
        parts = [s["organization"], s["dataset"]]
        for key in ("period", "geography", "measure"):
            if s.get(key):
                parts.append(s[key])
        line = " — ".join(parts)
        if s.get("url"):
            line += f" — {s['url']}"
        lines.append(f"- {line}")
    return "\n".join(lines) + "\n"


def to_csv(p: Dict[str, Any]) -> str:
    dim_keys = []
    for row in p["rows"]:
        for key in row["dimensions"]:
            if key not in dim_keys:
                dim_keys.append(key)
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(dim_keys + ["value", "unit", "status", "origin"])
    for row in p["rows"]:
        writer.writerow([row["dimensions"].get(k, "") for k in dim_keys] + [row["value"] if row["value"] is not None else "", row["unit"], row["status"], row["origin"]])
    return out.getvalue()
