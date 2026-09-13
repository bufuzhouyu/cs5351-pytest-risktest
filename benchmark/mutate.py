"""Deterministic, semantics-changing source mutations.

Instead of a heavy mutation-testing framework the benchmark uses five small,
auditable operators that are known to change behaviour of the generated
subjects.  Every mutation records the exact file, line and patch so a reviewer
can reproduce (or reject) a benchmark result.
"""

from __future__ import annotations

import ast
import random
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional, Tuple

SKIP_PARTS = {"__pycache__", "tests", "subject.json", ".risktest"}


@dataclass(frozen=True)
class Mutation:
    path: str
    line: int
    operator: str
    before: str
    after: str

    def describe(self) -> str:
        return f"{self.path}:{self.line} {self.operator}"


def _replace_operator(line: str, rng: random.Random) -> Optional[str]:
    table = {
        "+": "-",
        "-": "+",
        "*": "+",
        ">": ">=",
        "<": "<=",
        "==": "!=",
        "!=": "==",
    }
    # Longest operators first so that ">=" is not split into ">" + "=".
    for token in (">=", "<=", "==", "!=", "+", "-", "*", ">", "<"):
        if token in line and token in table:
            index = line.index(token)
            return line[:index] + table[token] + line[index + len(token) :]
    return None


def _change_constant(line: str, rng: random.Random) -> Optional[str]:
    matches = list(re.finditer(r"\b(\d+)\b", line))
    if not matches:
        return None
    match = rng.choice(matches)
    value = int(match.group(1))
    new_value = value + 1 if rng.random() < 0.5 else max(0, value - 1)
    return line[: match.start()] + str(new_value) + line[match.end() :]


def _negate_condition(line: str, rng: random.Random) -> Optional[str]:
    stripped = line.strip()
    if not stripped.startswith("if ") or not stripped.endswith(":"):
        return None
    indent = line[: len(line) - len(line.lstrip())]
    return f"{indent}if not ({stripped[3:-1].strip()}):\n"


def _flip_boolean_return(line: str, rng: random.Random) -> Optional[str]:
    stripped = line.strip()
    if not stripped.startswith("return "):
        return None
    expr = stripped[len("return ") :].strip()
    if not expr or expr.endswith(":"):
        return None
    indent = line[: len(line) - len(line.lstrip())]
    if expr in ("True", "False"):
        return f"{indent}return {'False' if expr == 'True' else 'True'}\n"
    return f"{indent}return NotImplemented if ({expr}) is None else None\n"


OPERATORS: List[Tuple[str, Callable[[str, random.Random], Optional[str]]]] = [
    ("replace-operator", _replace_operator),
    ("change-constant", _change_constant),
    ("negate-condition", _negate_condition),
    ("flip-boolean-return", _flip_boolean_return),
]


def source_files(subject: Path) -> List[Path]:
    files = []
    for path in sorted((subject / "app").rglob("*.py")):
        if path.name == "__init__.py":
            continue
        files.append(path)
    return files


def apply_mutation(
    subject: Path,
    seed: int,
    prefer: Optional[str] = None,
    files: Optional[List[str]] = None,
) -> Optional[Mutation]:
    """Apply one mutation to ``subject`` and return a description of it."""
    rng = random.Random(seed)
    if files:
        candidates = [subject / relative for relative in files if (subject / relative).exists()]
    else:
        candidates = source_files(subject)
    if not candidates:
        return None
    rng.shuffle(candidates)
    for path in candidates:
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines(keepends=True)
        order = list(range(len(lines)))
        rng.shuffle(order)
        for index in order:
            line = lines[index]
            if line.lstrip().startswith(("#", '"""', '"""')) or not line.strip():
                continue
            operators = list(OPERATORS)
            if prefer:
                operators.sort(key=lambda item: item[0] != prefer)
            for name, operator in operators:
                mutated = operator(line, rng)
                if mutated is None or mutated == line:
                    continue
                candidate_lines = list(lines)
                candidate_lines[index] = mutated
                candidate_text = "".join(candidate_lines)
                try:
                    ast.parse(candidate_text)
                except SyntaxError:
                    continue
                path.write_text(candidate_text, encoding="utf-8")
                return Mutation(
                    path=path.relative_to(subject).as_posix(),
                    line=index + 1,
                    operator=name,
                    before=line.rstrip("\n"),
                    after=mutated.rstrip("\n"),
                )
    return None


def revert(subject: Path, mutation: Mutation) -> None:
    """Undo a mutation recorded by :func:`apply_mutation`."""
    path = subject / mutation.path
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    index = mutation.line - 1
    lines[index] = mutation.before + "\n"
    path.write_text("".join(lines), encoding="utf-8")
