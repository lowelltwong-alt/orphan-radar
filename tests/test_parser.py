from orphan_radar.parse.links import extract_wiki_links, normalize_link_target
from orphan_radar.parse.sanitize import strip_code
from orphan_radar.parse.tags import extract_tags, parse_frontmatter
from orphan_radar.parse.tokens import jaccard


def test_parser_extracts_standard_and_wiki_links():
    content = 'See [[Agent Reliability|agents]] and [[Testing Strategy#timeouts]] and [KG](Knowledge Graph Maintenance.md).'
    assert extract_wiki_links(content) == {'Agent Reliability', 'Testing Strategy'}
    assert normalize_link_target('Folder/Note.md#Heading|Alias') == 'Folder/Note'


def test_tags_and_frontmatter():
    content = '---\ntags: [ai, testing]\ntitle: X\n---\n# X\nBody #agent'
    metadata, body = parse_frontmatter(content)
    assert metadata['title'] == 'X'
    assert extract_tags(body, metadata) >= {'ai', 'testing', 'agent'}


def test_jaccard_formula_correct():
    assert jaccard({'a', 'b'}, {'b', 'c'}) == 1 / 3


def test_links_and_tags_not_harvested_from_code():
    body = (
        'Prose links to [[Agent Reliability]] and #reliability.\n\n'
        '```python\n'
        '# not a tag -> #notarealtag\n'
        'x = "[[Should Not Be A Link]]"\n'
        '```\n\n'
        'Inline `[[Also Not A Link]]` and `#alsonotatag`.\n'
        'Trailing real [[Testing Strategy]] and #realtag.\n'
    )
    prose = strip_code(body)
    assert extract_wiki_links(prose) == {'Agent Reliability', 'Testing Strategy'}
    assert extract_tags(prose) == {'reliability', 'realtag'}
    # Sanitizer must not damage code-free prose.
    plain = 'Just [[A]] and #b with no code.'
    assert strip_code(plain) == plain
