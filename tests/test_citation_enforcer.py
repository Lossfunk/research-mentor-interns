from __future__ import annotations

from academic_research_mentor.citations.enforcer import enforce_citation_schema


def test_enforcer_adds_legend_and_metadata():
    text = "Claim one [P1] and another [G1]."
    meta = [
        {"id": "P1", "title": "Paper", "venue": "ACL", "year": 2024, "strength": "strong"},
        {"id": "G1", "title": "Hamming", "venue": "Essay", "year": 1986, "strength": "strong"},
    ]

    out = enforce_citation_schema(text, source_metadata=meta)

    assert "Sources —" in out
    assert "(Paper | ACL | 2024" in out
    assert "(Hamming | Essay | 1986" in out


def test_enforcer_no_citations_no_change():
    original = "No cites here."
    out = enforce_citation_schema(original)
    assert out == original
