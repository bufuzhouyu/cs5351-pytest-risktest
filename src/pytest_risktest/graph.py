"""Static import graph used to compute the *conservative* part of the impact set.

Dynamic traces (see :mod:`pytest_risktest.monitor`) only know what a test
executed in the *previous* run.  A change can therefore introduce a dependency
that was never observed.  The static import graph closes that gap: it answers
"which files cannot be correct anymore if file *f* changed?" without running
anything, at the price of precision.

The two views are combined by :mod:`pytest_risktest.selector`.
"""

from __future__ import annotations

import ast
import os
from pathlib import Path
from typing import Dict, Iterable, Iterator, Optional, Set

from .monitor import EXCLUDED_DIR_NAMES


def normalize_rel(path: Path | str, root: Path) -> str:
    """Return a POSIX-style path relative to ``root`` (the tool's canonical key)."""
    p = Path(path)
    if p.is_absolute():
        return p.relative_to(root).as_posix()
    return Path(os.path.relpath(p, root)).as_posix() if p.is_absolute() else p.as_posix()


def iter_python_files(root: Path, excluded: Iterable[str] = EXCLUDED_DIR_NAMES) -> Iterator[Path]:
    excluded_set = set(excluded)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d
            for d in dirnames
            if d not in excluded_set and not d.startswith(".")
        ]
        for name in filenames:
            if name.endswith(".py"):
                yield Path(dirpath) / name


def is_test_file(rel_path: str) -> bool:
    name = Path(rel_path).name
    parts = rel_path.split("/")
    return (
        (name.startswith("test_") and name.endswith(".py"))
        or name.endswith("_test.py")
        or "tests" in parts[:-1]
    )


def module_index(root: Path) -> Dict[str, str]:
    """Map dotted module names to relative POSIX paths for a project tree."""
    index: Dict[str, str] = {}
    for path in iter_python_files(root):
        rel = path.relative_to(root).as_posix()
        parts = rel.split("/")[:-1]
        stem = path.stem
        dotted_parts = parts if stem == "__init__" else [*parts, stem]
        dotted = ".".join(part for part in dotted_parts if part and part.isidentifier())
        if dotted:
            index.setdefault(dotted, rel)
    return index


def _resolve_module(
    index: Dict[str, str], dotted: str, root: Path, level: int, current_rel: str
) -> Optional[str]:
    """Resolve an import to a project file, tolerating ``from a.b.c import d``."""
    if level:
        # Relative import: anchor on the importing module's package.
        package_parts = current_rel.split("/")[:-1]
        base_parts = package_parts[: len(package_parts) - level + 1] if level > 1 else package_parts
        prefix = ".".join(base_parts)
        dotted = f"{prefix}.{dotted}" if dotted and prefix else (dotted or prefix)
    if not dotted:
        return None
    candidate = dotted
    while candidate:
        if candidate in index:
            return index[candidate]
        if "." not in candidate:
            break
        candidate = candidate.rsplit(".", 1)[0]
    return None


def static_imports(root: Path, index: Optional[Dict[str, str]] = None) -> Dict[str, Set[str]]:
    """Return ``relative path -> set of relative paths it imports`` for one tree."""
    root = root.resolve()
    index = module_index(root) if index is None else index
    result: Dict[str, Set[str]] = {}
    for path in iter_python_files(root):
        rel = path.relative_to(root).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"), filename=str(path))
        except SyntaxError:
            result[rel] = set()
            continue
        dependencies: Set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    target = _resolve_module(index, alias.name, root, 0, rel)
                    if target and target != rel:
                        dependencies.add(target)
            elif isinstance(node, ast.ImportFrom):
                base = node.module or ""
                if base:
                    target = _resolve_module(index, base, root, node.level, rel)
                    if target and target != rel:
                        dependencies.add(target)
                for alias in node.names:
                    # ``from pkg.mod import name`` may import a submodule rather
                    # than a symbol, and ``from . import name`` is a package-relative
                    # submodule import.  Resolving both keeps the graph conservative.
                    dotted = f"{base}.{alias.name}" if base else alias.name
                    target = _resolve_module(index, dotted, root, node.level, rel)
                    if target and target != rel:
                        dependencies.add(target)
        result[rel] = dependencies
    return result


class ImportGraph:
    """Reverse-dependency closure over the static import graph."""

    def __init__(self, imports: Dict[str, Set[str]]) -> None:
        self._imports: Dict[str, Set[str]] = {k: set(v) for k, v in imports.items()}
        reverse: Dict[str, Set[str]] = {}
        for source, targets in self._imports.items():
            for target in targets:
                reverse.setdefault(target, set()).add(source)
        self._reverse = reverse

    @classmethod
    def from_root(cls, root: Path) -> "ImportGraph":
        return cls(static_imports(root))

    @property
    def imports(self) -> Dict[str, Set[str]]:
        return self._imports

    @property
    def reverse(self) -> Dict[str, Set[str]]:
        return self._reverse

    def importers_of(self, rel_path: str) -> Set[str]:
        return set(self._reverse.get(rel_path, set()))

    def affected_by(self, changed: Iterable[str], depth: Optional[int]) -> Set[str]:
        """Files (transitively) importing any changed file.

        ``depth=0`` disables the static expansion, ``depth=None`` means "until
        fixpoint".  Note that ``changed`` files themselves are excluded: the
        caller handles direct impact through the dynamic traces.
        """
        if depth == 0:
            return set()
        frontier = set(changed)
        seen: Set[str] = set()
        level = 0
        while frontier and (depth is None or level < depth):
            level += 1
            next_frontier: Set[str] = set()
            for path in frontier:
                for importer in self._reverse.get(path, ()):
                    if importer not in seen and importer not in changed:
                        seen.add(importer)
                        next_frontier.add(importer)
            frontier = next_frontier
        return seen
