---
tags: [timeouts, testing, agents]
---
# Orphan - Long Running Tests

AI coding agents waste time when long-running tests are launched with short timeout defaults.

A repository should remember which commands need extended timeout windows and use that memory to avoid repeated execution failures.
