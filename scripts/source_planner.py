#!/usr/bin/env python3
"""Deterministic first-pass source routing for Statistikassistenten.

This module does not fetch data. It produces a source plan that must still pass
source-specific metadata gates before any data is used. The rules are designed
to be conservative: ambiguity is surfaced instead of being silently guessed.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable


class SourcePlannerError(ValueError):
    pass


@dataclass(frozen=True)
class Signal:
    source: str
    weight: int
    reason: str


SOURCE_ADAPTER = {
    "scb": "scripts/scb_adapter.py",
    "eurostat": "scripts/eurostat_adapter.py",
    "comext": "scripts/comext_adapter.py",
    "bra": "scripts/bra_adapter.py",
    "kolada": "scripts/kolada_adapter.py",
    "socialstyrelsen": "scripts/socialstyrelsen_adapter.py",
    "folkhalsodata": "scripts/folkhalsodata_adapter.py",
    "arbetsformedlingen": "scripts/arbetsformedlingen_adapter.py",
    "riksbank": "scripts/riksbank_adapter.py",
    "energimyndigheten": "scripts/energimyndigheten_adapter.py",
    "forsakringskassan": "scripts/forsakringskassan_adapter.py",
    "jordbruksverket": "scripts/jordbruksverket_adapter.py",
    "skolverket": "scripts/skolverket_adapter.py",
    "smhi": "scripts/smhi_adapter.py",
    "worldbank": "scripts/worldbank_adapter.py",
    "oecd": "scripts/oecd_adapter.py",
    "who": "scripts/who_adapter.py",
    "bis": "scripts/bis_adapter.py",
    "ecb": "scripts/ecb_adapter.py",
}

# Deliberately narrow, high-signal concepts. Broader language is handled by
# fallback rules or surfaced as ambiguity rather than overconfident routing.
BRA_TERMS = {
    "anmälda brott", "anmälda brotten", "brottsanmälningar", "brottskod",
    "misshandel", "bilstöld", "bilstölder", "inbrott", "narkotikabrott",
    "rån", "stöld", "stölder"
}
COMEXT_TERMS = {
    "import", "export", "utrikeshandel", "handelsvärde", "varukod",
    "cn-kod", "cn kod", "partnerland", "varuexport", "varuimport"
}
EUROSTAT_TERMS = {
    "eu", "eurostat", "eu-länder", "eu-länderna", "europeiska unionen",
    "jämför länder", "jämför medlemsländer", "eu27"
}
SCB_TERMS = {
    "befolkning", "invånare", "folkmängd", "arbetslöshet", "sysselsättning",
    "bnp", "kpi", "inflation", "inkomst", "kommun", "län", "sverige",
    "företag", "födda", "döda"
}

KOLADA_TERMS = {
    "kolada", "nyckeltal", "kommunens kostnad", "kostnad per elev", "äldreomsorg",
    "hemtjänst", "lss", "kommunal verksamhet", "kommunjämförelse", "regionnyckeltal"
}
SOCIALSTYRELSEN_TERMS = {
    "socialstyrelsen", "dödsorsak", "dödsorsaker", "läkemedel", "patientregistret",
    "slutenvård", "öppenvård", "ekonomiskt bistånd", "socialtjänst", "cancer", "förlossning"
}
FOLKHALSODATA_TERMS = {
    "folkhälsa", "folkhälsodata", "folkhälsomyndigheten", "vaccination", "vaccinationer",
    "smittsam", "smittsamma", "antibiotika", "levnadsvanor", "riskkonsumtion", "psykiskt välbefinnande"
}
ARBETSMARKNAD_TERMS = {
    "platsannonser", "platsannons", "lediga jobb", "jobbannonser", "efterfrågade kompetenser",
    "efterfrågade yrken", "arbetsförmedlingen", "jobsearch"
}
RIKSBANK_TERMS = {
    "riksbanken", "styrränta", "referensränta", "växelkurs", "valutakurs", "swea",
    "swestr", "kronkurs", "sek mot", "ränta och valut"
}
ENERGI_TERMS = {
    "energimyndigheten", "energistatistik", "energianvändning", "energibalans",
    "elproduktion", "fjärrvärme", "biogas", "solcellsanlägg", "kraftslag"
}
FORSakringskassan_TERMS = {
    "försäkringskassan", "sjukpenning", "sjukfall", "sjukersättning",
    "aktivitetsersättning", "föräldrapenning", "vab", "assistansersättning",
    "omvårdnadsbidrag", "graviditetspenning"
}
JORDBRUK_TERMS = {
    "jordbruksverket", "jordbruksstatistik", "skörd", "gröda", "jordbruksmark",
    "lantbruksdjur", "animalieproduktion", "trädgårdsodling", "vattenbruk",
    "livsmedelskonsumtion"
}
SKOLVERKET_TERMS = {
    "skolverket", "skolenhet", "skolenheter", "skolregister", "gymnasieprogram",
    "komvux", "planerade utbildningar", "utbildningstillfällen", "skolstatistik"
}
SMHI_TERMS = {
    "smhi", "meteorolog", "väderstation", "väderobservation", "nederbörd",
    "lufttemperatur", "vindhastighet", "molnmängd", "klimatobservation"
}
WORLDBANK_TERMS = {
    "världsbanken", "world bank", "fattigdom", "extrem fattigdom",
    "utvecklingsindikator", "world development indicators", "globalt bnp",
    "global befolkning", "länder i världen"
}
OECD_TERMS = {
    "oecd", "oecd-länder", "oecd-länderna", "oecd-genomsnitt",
    "produktivitet i oecd", "skattetryck i oecd"
}
WHO_TERMS = {
    "who", "världshälsoorganisationen", "global hälsa", "global hälsostatistik",
    "barnadödlighet", "mödradödlighet", "förväntad livslängd globalt"
}
BIS_TERMS = {
    "bis", "bank for international settlements", "internationella regleringsbanken",
    "hushållens skuldsättning internationellt", "reala bostadspriser",
    "effektiv växelkurs", "internationell bankstatistik"
}
ECB_TERMS = {
    "ecb", "europeiska centralbanken", "euroområdet", "euro area",
    "ecb ränta", "ecb-ränta", "monetära aggregat euro"
}

PER_CAPITA_TERMS = {
    "per 100 000", "per 100000", "per capita", "per invånare", "per tusen"
}


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _contains_any(text: str, terms: Iterable[str]) -> bool:
    return any(term in text for term in terms)


def _signals(question: str) -> list[Signal]:
    q = _norm(question)
    out: list[Signal] = []
    if _contains_any(q, BRA_TERMS):
        out.append(Signal("bra", 6, "Frågan innehåller ett tydligt brottsstatistiskt begrepp."))
    if _contains_any(q, COMEXT_TERMS):
        out.append(Signal("comext", 6, "Frågan gäller import/export eller detaljerad varuhandel."))
    if _contains_any(q, EUROSTAT_TERMS):
        out.append(Signal("eurostat", 4, "Frågan efterfrågar EU- eller landsjämförelse."))
    if _contains_any(q, KOLADA_TERMS):
        out.append(Signal("kolada", 7, "Frågan gäller kommun-/regionnyckeltal eller kommunal verksamhet som Kolada samlar."))
    if _contains_any(q, SOCIALSTYRELSEN_TERMS) and not _contains_any(q, COMEXT_TERMS):
        out.append(Signal("socialstyrelsen", 7, "Frågan gäller hälso-, vård- eller socialtjänststatistik från Socialstyrelsen."))
    if _contains_any(q, FOLKHALSODATA_TERMS):
        out.append(Signal("folkhalsodata", 7, "Frågan gäller folkhälsoindikatorer eller Folkhälsomyndighetens statistik."))
    if _contains_any(q, ARBETSMARKNAD_TERMS):
        out.append(Signal("arbetsformedlingen", 7, "Frågan gäller platsannonser eller aktuell efterfrågan på yrken/kompetenser."))
    if _contains_any(q, RIKSBANK_TERMS):
        out.append(Signal("riksbank", 7, "Frågan gäller Riksbankens räntor, växelkurser eller finansiella tidsserier."))
    if _contains_any(q, ENERGI_TERMS):
        out.append(Signal("energimyndigheten", 7, "Frågan gäller energistatistik som Energimyndigheten publicerar."))
    if _contains_any(q, FORSakringskassan_TERMS):
        out.append(Signal("forsakringskassan", 7, "Frågan gäller socialförsäkringsstatistik från Försäkringskassan."))
    if _contains_any(q, JORDBRUK_TERMS):
        out.append(Signal("jordbruksverket", 7, "Frågan gäller jordbruk, skörd, djur eller livsmedelsstatistik från Jordbruksverket."))
    if _contains_any(q, SKOLVERKET_TERMS):
        out.append(Signal("skolverket", 7, "Frågan gäller skolenheter, utbildningar eller Skolverkets statistik."))
    if _contains_any(q, SMHI_TERMS):
        out.append(Signal("smhi", 7, "Frågan gäller meteorologiska observationer eller klimatdata från SMHI."))
    if _contains_any(q, WORLDBANK_TERMS):
        out.append(Signal("worldbank", 7, "Frågan gäller globala utvecklingsindikatorer eller World Bank-data."))
    if _contains_any(q, OECD_TERMS):
        out.append(Signal("oecd", 7, "Frågan gäller harmoniserad statistik för OECD-länder."))
    if _contains_any(q, WHO_TERMS):
        out.append(Signal("who", 7, "Frågan gäller global hälsostatistik från WHO."))
    if _contains_any(q, BIS_TERMS):
        out.append(Signal("bis", 7, "Frågan gäller internationell bank-, kredit-, bostadspris- eller finansstatistik från BIS."))
    if _contains_any(q, ECB_TERMS):
        out.append(Signal("ecb", 7, "Frågan gäller euroområdets monetära eller finansiella statistik från ECB."))
    if _contains_any(q, SCB_TERMS):
        out.append(Signal("scb", 3, "Frågan innehåller svensk samhällsstatistik eller svensk geografi."))
    return out


def _needs_population_denominator(question: str, sources: list[str]) -> bool:
    q = _norm(question)
    return "bra" in sources and _contains_any(q, PER_CAPITA_TERMS)


def _trade_conflict(question: str, sources: list[str]) -> tuple[list[str], list[str]]:
    """Resolve generic Eurostat vs Comext overlap for detailed trade.

    Comext owns detailed goods trade. Generic Eurostat is retained only when a
    second, non-trade EU statistic is explicitly requested in the same question.
    """
    q = _norm(question)
    conflicts: list[str] = []
    result = list(sources)
    if "comext" in result and "eurostat" in result:
        non_trade_eu = any(term in q for term in ("befolkning", "bnp", "arbetslös", "sysselsätt", "inflation"))
        if not non_trade_eu:
            result.remove("eurostat")
            conflicts.append("Detaljerad varuhandel routas till Comext i stället för generella Eurostat-adaptern.")
    return result, conflicts


def plan_sources(question: str) -> dict:
    if not isinstance(question, str) or not question.strip():
        raise SourcePlannerError("question must not be empty")

    signals = _signals(question)
    scores: dict[str, int] = {}
    reasons: dict[str, list[str]] = {}
    for signal in signals:
        scores[signal.source] = scores.get(signal.source, 0) + signal.weight
        reasons.setdefault(signal.source, []).append(signal.reason)

    ambiguities: list[str] = []
    conflicts: list[str] = []

    if not scores:
        return {
            "question": question.strip(),
            "status": "needs_clarification",
            "sources": ["scb"],
            "steps": [{
                "id": "clarify-source",
                "source": "scb",
                "purpose": "Klargör vilket statistikområde och vilken källa frågan avser innan metadata söks.",
                "adapter": SOURCE_ADAPTER["scb"],
            }],
            "decision": {
                "reason": "Frågan saknar tillräckligt tydliga domänsignaler för säkert källval.",
                "confidence": "low",
                "ambiguities": ["Statistikområde eller avsedd datakälla kan inte avgöras säkert."],
                "conflicts": []
            },
            "clarification_question": "Vilket statistikområde vill du undersöka, till exempel befolkning, brott, EU-jämförelse eller handel?"
        }

    # Select all high-signal domains, plus SCB when it contributes a denominator
    # or a separate Swedish statistic. Weak SCB geography signals alone must not
    # steal questions from Brå/Comext.
    max_score = max(scores.values())
    selected = [source for source, score in scores.items() if score >= max_score - 1]

    q = _norm(question)
    if "bra" in selected and "scb" in scores:
        # Keep SCB only when the question explicitly needs another statistic or denominator.
        extra_scb = _contains_any(q, PER_CAPITA_TERMS) or any(term in q for term in ("befolkning", "invånare", "arbetslös", "inkomst", "bnp"))
        if extra_scb and "scb" not in selected:
            selected.append("scb")
    if "comext" in selected and "scb" in scores:
        # Swedish geography words are not enough to require SCB for a trade query.
        extra_scb = any(term in q for term in ("befolkning", "bnp", "arbetslös", "inflation", "företag"))
        if extra_scb and "scb" not in selected:
            selected.append("scb")

    selected, trade_conflicts = _trade_conflict(question, selected)
    conflicts.extend(trade_conflicts)
    if "comext" in selected and "eurostat" in scores and "eurostat" not in selected:
        conflicts.append("EU-signal finns, men detaljerad varuhandel routas till Comext i stället för generella Eurostat-adaptern.")

    if _needs_population_denominator(question, selected) and "scb" not in selected:
        selected.append("scb")
        reasons.setdefault("scb", []).append("SCB behövs som befolkningsnämnare för ett per-capita-mått.")

    # If both SCB and Eurostat are plausible for a generic internationally
    # comparable concept and the user did not specify geography, ask rather than guess.
    has_eu = "eurostat" in selected
    has_scb = "scb" in selected
    explicit_sweden = any(term in q for term in ("sverige", "svensk", "kommun", "län"))
    explicit_eu = _contains_any(q, EUROSTAT_TERMS)
    if has_eu and has_scb and not explicit_sweden and not explicit_eu:
        ambiguities.append("Både svensk och europeisk statistik kan vara relevant, men geografin är inte tydlig.")

    order = ("bra", "kolada", "socialstyrelsen", "folkhalsodata", "arbetsformedlingen", "riksbank", "energimyndigheten", "forsakringskassan", "jordbruksverket", "skolverket", "smhi", "worldbank", "oecd", "who", "bis", "ecb", "comext", "scb", "eurostat")
    selected = sorted(set(selected), key=lambda s: order.index(s))
    steps = []
    for idx, source in enumerate(selected, start=1):
        purpose = {
            "scb": "Sök och verifiera svensk officiell statistik via SCB innan datauttag.",
            "eurostat": "Sök och verifiera generell EU-statistik via Eurostat SDMX.",
            "comext": "Sök och verifiera detaljerad varuhandel via Eurostat/Comext.",
            "bra": "Sök och verifiera Brå-statistik över anmälda brott via officiell tjänst eller fil.",
            "kolada": "Sök och verifiera kommun-/regionnyckeltal via Kolada API v3, inklusive metadata och ursprunglig källa.",
            "socialstyrelsen": "Sök och verifiera vård-/socialtjänststatistik via Socialstyrelsens Statistikdatabas API.",
            "folkhalsodata": "Sök och verifiera folkhälsoindikatorer via Folkhälsodata/PxWeb API.",
            "arbetsformedlingen": "Sök verifierade platsannonser via Arbetsförmedlingens publika JobSearch API och skilj efterfrågedata från arbetslöshetsstatistik.",
            "riksbank": "Sök och verifiera räntor, växelkurser och andra Riksbanksserier via SWEA API.",
            "energimyndigheten": "Sök och verifiera energistatistik via Energimyndighetens PxWeb-statistikdatabas.",
            "forsakringskassan": "Sök och verifiera socialförsäkringsstatistik via Försäkringskassans öppna metadata och distributioner.",
            "jordbruksverket": "Sök och verifiera jordbruks- och livsmedelsstatistik via Jordbruksverkets PxWeb-statistikdatabas.",
            "skolverket": "Sök och verifiera skolenheter, utbildningar och statistik via Skolverkets öppna API:er.",
            "smhi": "Sök och verifiera meteorologiska observationer via SMHI:s öppna MetObs API.",
            "worldbank": "Sök och verifiera globala indikatorer via World Bank Indicators API v2.",
            "oecd": "Sök och verifiera harmoniserade OECD-data via OECD Data Explorer SDMX.",
            "who": "Sök och verifiera global hälsostatistik via WHO World Health Data Hub och aktuell officiell export.",
            "bis": "Sök och verifiera internationell finans- och bankstatistik via BIS SDMX API.",
            "ecb": "Sök och verifiera euroområdets monetära och finansiella statistik via ECB Data Portal SDMX.",
        }[source]
        step = {
            "id": f"source-{idx}-{source}",
            "source": source,
            "purpose": purpose,
            "adapter": SOURCE_ADAPTER[source],
        }
        steps.append(step)

    if len(selected) > 1:
        dependencies = [step["id"] for step in steps]
        steps.append({
            "id": "combine-results",
            "source": selected[0],
            "purpose": "Kombinera först efter att METHOD-GATE verifierat förenliga definitioner, geografi, period och enheter.",
            "adapter": "schemas/statistical-result.schema.json",
            "depends_on": dependencies,
        })

    status = "needs_clarification" if ambiguities else "ready"
    confidence = "high" if max_score >= 6 and not ambiguities else "medium" if not ambiguities else "low"
    reason_parts = []
    for source in selected:
        reason_parts.extend(reasons.get(source, []))
    reason = " ".join(dict.fromkeys(reason_parts)) or "Källorna valdes från domänsignaler i frågan."

    plan = {
        "question": question.strip(),
        "status": status,
        "sources": selected,
        "steps": steps,
        "decision": {
            "reason": reason,
            "confidence": confidence,
            "ambiguities": ambiguities,
            "conflicts": conflicts,
        },
    }
    if status == "needs_clarification":
        plan["clarification_question"] = "Vill du ha svensk statistik från SCB, en EU-jämförelse från Eurostat, eller båda?"
    return plan
