# Test report

- Branch: `sprint-3/m2-daijiale`
- Command: `$env:PYTHONPATH="src"; python -m pytest tests -q`
- Result: `121 passed in 8.89s` (baseline before this task: `99 passed`)
- New tests: `tests/test_selector_extra.py` — 22 collected cases in 19 test
  functions (one test is parametrised over the four selection policies)
- Coverage (optional): `62%` statement coverage over `src/pytest_risktest`
  (`coverage run --source=src/pytest_risktest -m pytest tests -q`). `cli.py`
  and `plugin.py` report `0%` under this method because they are exercised
  through subprocesses by `test_cli.py` and `test_plugin_integration.py`;
  excluding those two files the measured total is `89.6%`.
- Bugs found: none. No production code in `src/` was modified by this task.

## What the new tests pin down

| Area | Contract covered |
| --- | --- |
| Policies | `fast` has depth 0, `balanced` depth 1, `safe` is the full closure; `depth_label` renders `0` / `1` / `closure`; unknown policy names raise `ValueError` |
| APFD | rewards an early detection, returns `NaN` without failures, and scores an unexecuted failure below one found last |
| Recall | counts a missed failure and returns `1.0` when nothing failed |
| Skip rate | `0.0` for an empty universe, `0.5` for a half selection |
| Time saved / overhead | return the documented fraction and guard a zero baseline with `NaN` |
| Summary statistics | `n` / `mean` / `median` / `min` / `max`, dropping `NaN` values and handling empty input |
| Ordering | `original` keeps the plan order, `risk` sorts by descending score, `shuffle` is reproducible for a fixed seed and keeps the selection intact |

## How to reproduce

```powershell
$env:PYTHONPATH="src"
python -m pytest tests -q                       # 121 passed
python -m pytest tests/test_selector_extra.py -q  # 22 passed
```
