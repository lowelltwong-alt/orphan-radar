from __future__ import annotations

from pathlib import Path


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


class OutputWriter:
    def __init__(self, source_dir: Path, output_dir: Path, allow_inside_source: bool = False):
        self.source_dir = source_dir.resolve()
        self.output_dir = output_dir.resolve()
        self.allow_inside_source = allow_inside_source

        if not allow_inside_source and _is_relative_to(self.output_dir, self.source_dir):
            raise RuntimeError('Refusing to write output inside source directory by default.')

    def path(self, relative_path: str) -> Path:
        target = (self.output_dir / relative_path).resolve()
        if not self.allow_inside_source and _is_relative_to(target, self.source_dir):
            raise RuntimeError('Refusing to write inside source directory.')
        return target

    def write_text(self, relative_path: str, content: str) -> Path:
        target = self.path(relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding='utf-8')
        return target
