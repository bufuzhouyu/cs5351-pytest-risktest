---
name: Bug report
about: Something the tool does wrong
title: "bug: "
labels: ["bug"]
---

**Symptom**

**Reproduce**

```
python -m pytest ... -p pytest_risktest.plugin --risktest ...
```

**Expected / actual**

**Impact**

* can the bug hide a failing test?  yes/no
* can the bug break a user's run?  yes/no

**Diagnostics**

* `.risktest/last-run.json` (selection, reasons, outcomes)
* `risktest status`
* interpreter version (`python -V`) — the monitor needs CPython 3.12+

