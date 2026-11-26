# Line-tracing strategies (NFR-1 design option)

Best of 5 runs per configuration.

| workload | strategy | iterations | seconds | overhead_pct |
| --- | --- | --- | --- | --- |
| hot-loop | none | 200000 | 0.012 | 0.000 |
| hot-loop | file | 200000 | 0.011 | -2.290 |
| hot-loop | line-local | 200000 | 0.742 | 6276.200 |
| hot-loop | line-global | 200000 | 0.749 | 6339.360 |
| library-bound | none | 400 | 0.011 | 0.000 |
| library-bound | file | 400 | 0.013 | 17.480 |
| library-bound | line-local | 400 | 0.015 | 29.860 |
| library-bound | line-global | 400 | 0.025 | 120.360 |
