# Line-tracing strategies (NFR-1 design option)

Best of 5 runs per configuration.

| workload | strategy | iterations | seconds | overhead_pct |
| --- | --- | --- | --- | --- |
| hot-loop | none | 150000 | 0.026 | 0.000 |
| hot-loop | file | 150000 | 0.026 | 3.040 |
| hot-loop | line-local | 150000 | 1.606 | 6169.820 |
| hot-loop | line-global | 150000 | 1.575 | 6046.200 |
| library-bound | none | 400 | 0.038 | 0.000 |
| library-bound | file | 400 | 0.039 | 3.570 |
| library-bound | line-local | 400 | 0.037 | -2.270 |
| library-bound | line-global | 400 | 0.074 | 97.200 |
