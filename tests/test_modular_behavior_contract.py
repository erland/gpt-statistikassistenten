"""Protect the canonical modular Skill split against loss of legacy behavior."""
from pathlib import Path
import re
import yaml

ROOT = Path(__file__).resolve().parents[1]
MAP = {
    "Identitet och syfte": "canonical/core.md",
    "Kärnregler": "canonical/core.md",
    "Arbetsflöde": "canonical/core.md",
    "Källval": "canonical/skills/statistikkallor/behavior.md",
    "METADATA-GATE": "canonical/skills/statistikkallor/behavior.md",
    "DATA-GATE": "canonical/skills/statistikkvalitet/behavior.md",
    "METHOD-GATE": "canonical/skills/statistikkvalitet/behavior.md",
    "PROVENANCE-GATE": "canonical/skills/statistikkvalitet/behavior.md",
    "QUALITY-GATE": "canonical/skills/statistikkvalitet/behavior.md",
    "Svar och export": "canonical/skills/statistikpresentation/behavior.md",
    "Custom GPT-runtime": "canonical/skills/statistikpresentation/behavior.md",
    "Begränsningar": "canonical/core.md",
}

def sections(text):
    matches = list(re.finditer(r"(?m)^## (.+?)\\s*$", text))
    result = {}
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        result[match.group(1)] = text[match.start():end].strip()
    return result

def test_every_original_behavior_section_is_preserved_verbatim():
    original = sections((ROOT / "assistant/instructions.md").read_text(encoding="utf-8"))
    assert set(original) == set(MAP), f"Unmapped legacy headings: {set(original) ^ set(MAP)}"
    for heading, target in MAP.items():
        modular = sections((ROOT / target).read_text(encoding="utf-8"))
        assert heading in modular, f"{heading} missing from {target}"
        assert modular[heading] == original[heading], f"Behavior drift in {heading}"

def test_modular_skill_routing_is_explicit_and_separate():
    profile = yaml.safe_load((ROOT / "gpt-project.yaml").read_text(encoding="utf-8"))
    assert profile["instructions"]["mode"] == "modular_skills"
    assert profile["instructions"]["core"] == "canonical/core.md"
    definitions = profile["skills"]["definitions"]
    expected = {"statistikkallor", "statistikkvalitet", "statistikpresentation"}
    assert {skill["id"] for skill in definitions} == expected
    assert {skill["source"] for skill in definitions} == {
        f"canonical/skills/{name}/behavior.md" for name in expected
    }
    for skill in definitions:
        assert (ROOT / skill["source"]).is_file()
        assert skill["description"].strip()
    core = (ROOT / "canonical/core.md").read_text(encoding="utf-8")
    for gate in ("METADATA-GATE", "DATA-GATE", "METHOD-GATE", "PROVENANCE-GATE", "QUALITY-GATE"):
        assert gate in core
