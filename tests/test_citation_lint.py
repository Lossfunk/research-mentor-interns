from __future__ import annotations

from academic_research_mentor.citations.lint import lint_response


def test_lint_flags_missing_legend_and_numeric():
    text = "Accuracy improved to 94.2% [P1]\nBut latency is 120ms."
    result = lint_response(text)
    assert "legend_missing" in result["issues"]
    assert "number_without_citation" in result["issues"]


def test_lint_ok_when_cited_and_has_legend():
    text = "Accuracy improved to 94.2% [P1]\n\nSources — A: attachments; P: papers"
    result = lint_response(text)
    assert result["issues"] == []
