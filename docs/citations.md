# Citation Schema & Enforcement

## ID scheme
- `[A#]` attachments (PDF snippets)
- `[P#]` papers/literature (arXiv/unified research)
- `[G#]` guidelines (research_guidelines)
- `[W#]` web/news

## Formatting rules
- First mention includes micro-metadata: `Title | Venue/Domain | Year` and optional strength flag (`†strong` peer-reviewed/curated, `†weak` blog/forum).
- Cite per factual/quantitative claim (aim: 1 cite per 2–3 sentences).
- Reuse IDs when the same source supports multiple claims.
- Always add legend when any citation exists: `Sources — A: attachments; P: papers/arxiv/unified; G: research guidelines; W: web/news...`

## Enforcement
- `citations.enforcer.enforce_citation_schema` normalizes IDs, injects metadata when provided, and appends legend.
- Response path runs the enforcer so free-form model text is normalized before display.

## Linting
- `citations.lint.lint_response` flags:
  - `legend_missing` when citations exist but no legend.
  - `number_without_citation` when numbers appear without a nearby cite.

## Usage tips
- Prefer concise mode; switch to detailed only when user asks.
- If no supporting source exists, state it and suggest a follow-up tool call.
