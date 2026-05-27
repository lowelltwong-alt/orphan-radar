# Architecture

Orphan Radar is built as a read-only source pipeline plus output-only artifact generation.

```text
source folder
  -> immutable scan + hashes
  -> parser
  -> link graph
  -> TF-IDF matrix
  -> hybrid graph
  -> communities
  -> orphan classification
  -> community routing
  -> candidate ranking
  -> bridge detection
  -> review queue
  -> output writer
  -> post-run source hash assertion
```

## Authority boundary

The system proposes candidate connections. It does not promote graph truth, rewrite notes, or apply links.

## Mutation boundary

All source reads go through `SourceStore`. All generated files go through `OutputWriter`, which refuses to write inside the source directory by default. The pipeline hashes source files before and after execution and raises an error if any source file changed.
