"""Generate the benchmark subjects.

The assignment requires a *baseline -> change -> measure* evaluation, so the
subjects are generated (not hand-written once) to make the experiment
reproducible from a seed:

``python benchmark/generate_subjects.py --subjects 6 --features 8 --seed 20260101``

Each subject is a small but layered Python project: core helpers, a store, three
services that depend on them, and one test module per unit.  This shape matters:
a change in ``app/core/mathx.py`` propagates to several test modules through the
import graph, which is exactly the situation where the different selection
policies are expected to disagree.

On top of that core, ``--features N`` adds ``N`` generated feature modules with
their own test modules.  They make the suite large enough for wall-clock effects
to be visible (see ``benchmark/README.md`` for why the per-test *work factor*
exists and how it is controlled).
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
SUBJECTS_DIR = HERE / "subjects"

MATHX = '''"""Numeric helpers used across the services."""

TAX_RATE = {tax}
CURRENCY_SCALE = {scale}


def add(a, b):
    return a + b


def mul(a, b):
    return a * b


def clamp(value, low, high):
    if value < low:
        return low
    if value > high:
        return high
    return value


def with_tax(amount):
    return round(amount * (1 + TAX_RATE), 2)
'''

TEXTX = '''"""String helpers."""

SEPARATOR = "{separator}"


def normalize(text):
    return SEPARATOR.join(text.split())


def slugify(text):
    return normalize(text).lower().replace(" ", "-")


def titleize(text):
    return " ".join(word.capitalize() for word in normalize(text).split())
'''

MEMORY = '''"""Tiny in-memory store used by the catalog service."""


class MemoryStore:
    def __init__(self):
        self._items = {{}}

    def insert(self, key, value):
        self._items[key] = value
        return value

    def get(self, key, default=None):
        return self._items.get(key, default)

    def size(self):
        return len(self._items)

    def keys(self):
        return sorted(self._items)
'''

VALIDATE = '''"""Validation helpers."""

from app.core.mathx import clamp


def is_positive(value):
    return value > 0


def bounded_quantity(value, limit={limit}):
    if not is_positive(value):
        raise ValueError("quantity must be positive")
    return int(clamp(value, 1, limit))


def validate_line(item):
    quantity = item.get("quantity", 0)
    if not is_positive(quantity):
        return False
    return item.get("price", 0) >= 0
'''

BILLING = '''"""Billing service."""

from app.core.mathx import add, with_tax
from app.utils.validate import validate_line

DISCOUNT = {discount}


def subtotal(items):
    total = 0
    for item in items:
        if not validate_line(item):
            continue
        total = add(total, item["price"] * item["quantity"])
    return total


def discounted_total(items):
    total = subtotal(items)
    if total > 100:
        total = total * (1 - DISCOUNT)
    return round(total, 2)


def total_with_tax(items):
    return with_tax(discounted_total(items))
'''

CATALOG = '''"""Catalog service built on the text helpers and the memory store."""

from app.core.textx import slugify, titleize
from app.store.memory import MemoryStore


class Catalog:
    def __init__(self):
        self.store = MemoryStore()

    def register(self, name, price):
        key = slugify(name)
        return self.store.insert(key, {{"name": titleize(name), "price": price}})

    def price_of(self, name):
        entry = self.store.get(slugify(name))
        return entry["price"] if entry else 0

    def count(self):
        return self.store.size()
'''

REPORTS = '''"""Reporting service aggregating billing and the catalog."""

from app.services.billing import subtotal


def cheap_items(items, limit={limit}):
    return [item for item in items if item.get("price", 0) <= limit]


def summary(items):
    total = subtotal(items)
    return {{"count": len(items), "total": round(total, 2), "cheap": len(cheap_items(items))}}


def biggest(items):
    if not items:
        return None
    return max(items, key=lambda item: item["price"])
'''

TEST_MATHX = """from app.core.mathx import add, clamp, mul, with_tax


def test_add():
    assert add(2, 3) == 5


def test_mul():
    assert mul(4, 5) == 20


def test_clamp():
    assert clamp(11, 0, 10) == 10
    assert clamp(-1, 0, 10) == 0
    assert clamp(5, 0, 10) == 5


def test_with_tax():
    assert with_tax(100) == round(100 * 1.07, 2)
"""

SUPPORT = '''"""Shared test helpers.

``busy`` gives every test a small, deterministic amount of real CPU work
(~15 ms).  Without it a 24-test suite would be entirely dominated by interpreter
and pytest start-up, and no selection strategy could show a wall-clock effect.
The work factor is a *controlled knob*; the benchmark reports both wall-clock
savings and execution-time-only savings so the choice cannot flatter the tool.
"""

ITERATIONS = {iterations}


def busy(iterations=ITERATIONS):
    total = 0
    for index in range(iterations):
        total += (index * index) % 7
    return total
'''

FEATURE = '''"""Generated feature module {index} (owned by the feature_{index:02d} unit)."""

from app.core.mathx import add, mul

WEIGHT = {weight}


def compute(values):
    total = 0
    for value in values:
        total = add(total, mul(value, WEIGHT))
    return total


def normalize_total(values):
    return round(compute(values) / max(len(values), 1), 3)


def top(values, count=3):
    return sorted(values, reverse=True)[:count]


def spread(values):
    if not values:
        return 0
    return max(values) - min(values)
'''

FEATURE_TEST = '''from tests.support import busy

from app.features.feature_{index:02d} import WEIGHT, compute, normalize_total, spread, top


def test_compute():
    busy()
    assert compute([1, 2, 3]) == {expected_compute}


def test_compute_empty():
    busy()
    assert compute([]) == 0


def test_normalize_total():
    busy()
    assert normalize_total([{values}]) == {expected_normalize}


def test_top_returns_descending_prefix():
    busy()
    assert top([1, 5, 3, 4, 2]) == [5, 4, 3]


def test_spread():
    busy()
    assert spread([2, 9, 4]) == 7


def test_spread_of_empty():
    busy()
    assert spread([]) == 0


def test_weight_is_positive():
    busy()
    assert WEIGHT > 0


def test_compute_is_linear():
    busy()
    assert compute([2, 4]) == compute([4, 2])
'''

TEST_TEXTX = """from app.core.textx import normalize, slugify, titleize


def test_normalize():
    assert normalize("  a   b ") == "a b"


def test_slugify():
    assert slugify("Hello World") == "hello-world"


def test_titleize():
    assert titleize("hello wide world") == "Hello Wide World"
"""

TEST_MEMORY = """from app.store.memory import MemoryStore


def test_insert_and_get():
    store = MemoryStore()
    store.insert("a", 1)
    assert store.get("a") == 1


def test_default_value():
    assert MemoryStore().get("missing", 0) == 0


def test_size_and_keys():
    store = MemoryStore()
    store.insert("b", 2)
    store.insert("a", 1)
    assert store.size() == 2
    assert store.keys() == ["a", "b"]
"""

TEST_VALIDATE = """import pytest

from app.utils.validate import bounded_quantity, is_positive, validate_line


def test_is_positive():
    assert is_positive(1) is True


def test_bounded_quantity_clamps():
    assert bounded_quantity(50, 10) == 10


def test_bounded_quantity_rejects_non_positive():
    with pytest.raises(ValueError):
        bounded_quantity(0)


def test_validate_line():
    assert validate_line({"quantity": 2, "price": 3}) is True
    assert validate_line({"quantity": 0, "price": 3}) is False
"""

TEST_BILLING = """from app.services.billing import discounted_total, subtotal, total_with_tax


def test_subtotal_skips_invalid_lines():
    items = [{"price": 10, "quantity": 2}, {"price": 5, "quantity": 0}]
    assert subtotal(items) == 20


def test_subtotal_adds_lines():
    items = [{"price": 3, "quantity": 3}, {"price": 2, "quantity": 1}]
    assert subtotal(items) == 11


def test_discount_applies_above_threshold():
    items = [{"price": 60, "quantity": 2}]
    assert discounted_total(items) == round(120 * 0.95, 2)


def test_total_with_tax():
    items = [{"price": 10, "quantity": 1}]
    assert total_with_tax(items) == round(10 * 1.07, 2)
"""

TEST_CATALOG = """from app.services.catalog import Catalog


def test_register_and_price():
    catalog = Catalog()
    catalog.register("Blue Mug", 9)
    assert catalog.price_of("blue mug") == 9


def test_count():
    catalog = Catalog()
    catalog.register("a", 1)
    catalog.register("b", 2)
    assert catalog.count() == 2
"""

TEST_REPORTS = """from app.services.reports import biggest, cheap_items, summary


def test_cheap_items():
    items = [{"price": 5, "quantity": 1}, {"price": 50, "quantity": 1}]
    assert cheap_items(items, 10) == [{"price": 5, "quantity": 1}]


def test_summary():
    items = [{"price": 20, "quantity": 2}]
    assert summary(items)["total"] == 40


def test_biggest():
    items = [{"price": 5, "quantity": 1}, {"price": 9, "quantity": 1}]
    assert biggest(items)["price"] == 9


def test_biggest_of_empty_list():
    assert biggest([]) is None
"""


def build_subject(root: Path, seed: int, features: int = 8, iterations: int = 45000) -> None:
    rng = random.Random(seed)
    tax = round(rng.uniform(0.05, 0.2), 2)
    files = {
        "app/__init__.py": '"""Benchmark subject."""\n',
        "app/core/__init__.py": "",
        "app/store/__init__.py": "",
        "app/services/__init__.py": "",
        "app/utils/__init__.py": "",
        "app/core/mathx.py": MATHX.format(tax=tax, scale=100),
        "app/core/textx.py": TEXTX.format(separator=" "),
        "app/store/memory.py": MEMORY.format(),
        "app/utils/validate.py": VALIDATE.format(limit=100),
        "app/services/billing.py": BILLING.format(discount=0.05),
        "app/services/catalog.py": CATALOG.format(),
        "app/services/reports.py": REPORTS.format(limit=10),
        "app/features/__init__.py": "",
        "tests/support.py": SUPPORT.format(iterations=iterations),
        "tests/__init__.py": "",
        "tests/test_mathx.py": TEST_MATHX.replace("1.07", str(round(1 + tax, 2))),
        "tests/test_textx.py": TEST_TEXTX,
        "tests/test_memory.py": TEST_MEMORY,
        "tests/test_validate.py": TEST_VALIDATE,
        "tests/test_billing.py": TEST_BILLING.replace("1.07", str(round(1 + tax, 2))),
        "tests/test_catalog.py": TEST_CATALOG,
        "tests/test_reports.py": TEST_REPORTS,
        "pyproject.toml": "[project]\nname = 'subject'\nversion = '0.0.0'\n",
        # A ``pytest.ini`` pins the rootdir to the subject directory: without it
        # pytest walks up to the parent project's configuration and the tool
        # would compute relative paths against the wrong root.
        "pytest.ini": "[pytest]\ntestpaths = tests\n",
    }
    for index in range(1, features + 1):
        weight = rng.randint(2, 5)
        values = [rng.randint(1, 9) for _ in range(3)]
        expected_compute = (1 + 2 + 3) * weight
        expected_normalize = round(weight * sum(values) / len(values), 3)
        files[f"app/features/feature_{index:02d}.py"] = FEATURE.format(
            index=index, weight=weight
        )
        files[f"tests/test_feature_{index:02d}.py"] = FEATURE_TEST.format(
            index=index,
            values=", ".join(str(value) for value in values),
            expected_compute=expected_compute,
            expected_normalize=expected_normalize,
        )
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def generate(
    count: int,
    seed: int,
    base: Path = SUBJECTS_DIR,
    clean: bool = False,
    features: int = 8,
    iterations: int = 45000,
) -> list[Path]:
    created = []
    for index in range(1, count + 1):
        name = f"subject_{index:02d}"
        root = base / name
        if clean and root.exists():
            import shutil

            shutil.rmtree(root)
        build_subject(root, seed + index, features=features, iterations=iterations)
        (root / "subject.json").write_text(
            json.dumps({"name": name, "seed": seed + index}, indent=2), encoding="utf-8"
        )
        created.append(root)
    return created


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subjects", type=int, default=6)
    parser.add_argument("--features", type=int, default=8, help="generated feature modules per subject")
    parser.add_argument(
        "--iterations", type=int, default=45000, help="per-test CPU work factor (~15 ms per test)"
    )
    parser.add_argument("--seed", type=int, default=20260101)
    parser.add_argument("--output", default=str(SUBJECTS_DIR))
    parser.add_argument("--clean", action="store_true", help="delete existing subjects first")
    args = parser.parse_args(argv)
    created = generate(
        args.subjects,
        args.seed,
        Path(args.output),
        clean=args.clean,
        features=args.features,
        iterations=args.iterations,
    )
    for root in created:
        print(f"generated {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
