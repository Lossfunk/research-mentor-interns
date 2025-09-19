# Citation System Documentation

The Academic Research Mentor now includes a comprehensive citation system that provides proper grounding and traceability for all research outputs across tools.

## Overview

The citation system consists of:
- **Unified Citation Model**: Consistent data structure across all tools
- **Citation Validation**: Quality checks and completeness scoring
- **Citation Aggregation**: Deduplication and merging across sources
- **Citation Formatting**: Consistent display and output formatting

## Core Components

### Citation Data Model

```python
from academic_research_mentor.citations import Citation

citation = Citation(
    id="unique_id",
    title="Paper Title",
    url="https://example.com/paper",
    source="arxiv",
    authors=["Author One", "Author Two"],
    year=2023,
    venue="Conference Name",
    doi="10.1000/example",
    snippet="Brief excerpt...",
    relevance_score=0.95
)
```

### Citation Formatter

```python
from academic_research_mentor.citations import CitationFormatter

formatter = CitationFormatter(style="academic")
formatted = formatter.format_inline(citation)
# Output: "Author One, Author Two (2023). Paper Title. Conference Name. https://example.com/paper"
```

### Citation Validator

```python
from academic_research_mentor.citations import CitationValidator

validator = CitationValidator()
result = validator.validate_citation(citation)
# Returns: {"valid": True, "score": 85, "issues": [], "completeness": 90}
```

### Citation Aggregator

```python
from academic_research_mentor.citations import CitationAggregator

aggregator = CitationAggregator()
citations = aggregator.add_citations(citation_list, source="arxiv")
stats = aggregator.get_citation_stats(citations)
```

## Tool Integration

### Guidelines Tool

The guidelines tool now includes:
- **Structured Citations**: All evidence items converted to Citation objects
- **Citation Quality Metrics**: Validation scores and completeness ratings
- **Cross-References**: Links between related evidence items

```python
result = guidelines_tool.execute({"query": "research methodology"})
# result["citations"] contains structured citations
# result["citation_quality"] contains validation metrics
```

### arXiv Tools

Both legacy and O3 search tools now emit:
- **Structured Citations**: Paper metadata converted to Citation objects
- **Source Attribution**: Clear identification of arXiv papers
- **URL Strategy**: Consistent citation URLs for grounding

```python
result = arxiv_tool.execute({"query": "machine learning"})
# result["citations"] contains structured paper citations
```

### Literature Synthesis

The synthesis tool now tracks:
- **Citation Provenance**: Full traceability of citation sources
- **Citation Aggregation**: Merged citations from multiple sources
- **Citation Statistics**: Comprehensive metrics about citation quality

```python
result = synthesize_literature(topics, arxiv_results, openreview_results)
# result["citations"] contains aggregated citations
# result["citation_stats"] contains quality metrics
```

## Citation Quality Metrics

### Validation Scoring

Citations are scored based on:
- **Required Fields**: Title, URL, authors, year (70% of score)
- **Optional Fields**: Venue, DOI, snippet (30% of score)
- **Quality Checks**: URL validity, year range, completeness

### Completeness Rating

Each citation receives a completeness score (0-100) based on:
- Title presence and length
- Valid URL
- Author information
- Publication year
- Venue information
- DOI availability
- Meaningful snippet

## Usage Examples

### Basic Citation Creation

```python
from academic_research_mentor.citations import Citation, CitationFormatter

# Create a citation
citation = Citation(
    id="paper_001",
    title="Deep Learning for Research",
    url="https://arxiv.org/abs/2023.12345",
    source="arxiv",
    authors=["Jane Smith", "John Doe"],
    year=2023,
    venue="arXiv",
    snippet="This paper presents novel approaches to..."
)

# Format for display
formatter = CitationFormatter()
print(formatter.format_inline(citation))
```

### Tool Integration

```python
from academic_research_mentor.tools.guidelines.tool import GuidelinesTool

# Initialize tool
tool = GuidelinesTool()
tool.initialize()

# Execute query with citation support
result = tool.execute({
    "query": "research methodology",
    "topic": "academic research"
})

# Access citations
if "citations" in result:
    citations = result["citations"]["citations"]
    quality = result["citation_quality"]
    print(f"Found {len(citations)} citations with quality score {quality['score']}")
```

### Citation Validation

```python
from academic_research_mentor.citations import CitationValidator

validator = CitationValidator()

# Validate single citation
result = validator.validate_citation(citation)
if result["valid"]:
    print(f"Citation is valid with score {result['score']}")
else:
    print(f"Issues: {result['issues']}")

# Validate collection
results = validator.validate_citations(citation_list)
print(f"Valid: {results['valid_count']}/{results['total_count']}")
```

## Best Practices

### For Tool Developers

1. **Always Include Citations**: Convert tool outputs to Citation objects
2. **Validate Quality**: Use CitationValidator to ensure citation integrity
3. **Provide Metadata**: Include source attribution and provenance
4. **Handle Errors**: Gracefully handle missing or invalid citation data

### For Citation Quality

1. **Complete Information**: Include title, URL, authors, and year
2. **Valid URLs**: Ensure URLs are accessible and properly formatted
3. **Meaningful Snippets**: Provide relevant excerpts for context
4. **Source Attribution**: Clearly identify the source of each citation

## Migration Guide

### Existing Tools

To add citation support to existing tools:

1. Import citation utilities:
```python
from academic_research_mentor.citations import Citation, CitationFormatter
```

2. Convert outputs to Citation objects:
```python
citations = []
for item in results:
    citation = Citation(
        id=f"item_{hash(item['url'])}",
        title=item.get("title", ""),
        url=item.get("url", ""),
        source="your_source",
        # ... other fields
    )
    citations.append(citation)
```

3. Add citations to output:
```python
if citations:
    formatter = CitationFormatter()
    result["citations"] = formatter.to_output_block(citations)
```

### Metadata Updates

Update tool metadata to include citation capabilities:

```python
def get_metadata(self):
    meta = super().get_metadata()
    meta["citations"] = {
        "supports_citations": True,
        "citation_format": "structured",
        "citation_validation": True,
        "citation_aggregation": True
    }
    return meta
```

## Testing

The citation system includes comprehensive tests:

```bash
# Run all citation tests
pytest tests/test_citation_framework.py -v

# Run specific test categories
pytest tests/test_citation_framework.py::TestCitation -v
pytest tests/test_citation_framework.py::TestCitationValidator -v
pytest tests/test_citation_framework.py::TestCitationIntegration -v
```

## Future Enhancements

Planned improvements include:
- **Citation Styles**: Support for APA, MLA, Chicago formats
- **Citation Networks**: Graph-based citation relationships
- **Citation Metrics**: Impact and influence scoring
- **Citation Export**: Export to various bibliography formats
- **Citation Search**: Search and filter capabilities

## Troubleshooting

### Common Issues

1. **Missing Citations**: Ensure tools are properly converting outputs to Citation objects
2. **Validation Failures**: Check that required fields are present and valid
3. **Formatting Issues**: Verify CitationFormatter is properly initialized
4. **Deduplication Problems**: Check URL and title similarity thresholds

### Debug Mode

Enable debug logging for citation operations:

```python
import logging
logging.getLogger("academic_research_mentor.citations").setLevel(logging.DEBUG)
```

This will provide detailed information about citation processing, validation, and formatting operations.
