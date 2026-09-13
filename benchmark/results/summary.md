# Benchmark summary

- mutation runs: 36
- targets: pytest-risktest (self-hosted), subject_01, subject_02, subject_03
- policies: balanced, fast, safe

## Selection quality per policy

| policy | runs | skip_rate | recall | misses | apfd_tool | apfd_baseline | time_saved | work_saved |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| balanced | 12 | 0.714 | 1.000 | 0 | 0.925 | 0.659 | 0.124 | 0.656 |
| fast | 12 | 0.854 | 1.000 | 0 | 0.925 | 0.659 | 0.180 | 0.851 |
| safe | 12 | 0.693 | 1.000 | 0 | 0.925 | 0.659 | 0.105 | 0.634 |

`recall` is reported as the worst case over all runs: it is the safety metric,
so the minimum matters rather than the mean.

## Generated vs self-hosted targets

| target kind | policy | runs | skip_rate | recall | misses | apfd_tool | work_saved |
| --- | --- | --- | --- | --- | --- | --- | --- |
| generated | balanced | 9 | 0.755 | 1.000 | 0 | 0.926 | 0.673 |
| generated | fast | 9 | 0.843 | 1.000 | 0 | 0.926 | 0.807 |
| generated | safe | 9 | 0.727 | 1.000 | 0 | 0.926 | 0.648 |
| self-hosted | balanced | 3 | 0.591 | 1.000 | 0 | 0.922 | 0.608 |
| self-hosted | fast | 3 | 0.886 | 1.000 | 0 | 0.922 | 0.981 |
| self-hosted | safe | 3 | 0.591 | 1.000 | 0 | 0.922 | 0.593 |

## Observation overhead

| target | kind | total_tests | untraced_s | traced_file_s | traced_line_s | overhead_file_pct | overhead_line_pct |
| --- | --- | --- | --- | --- | --- | --- | --- |
| subject_01 | generated | 88 | 1.486 | 1.359 | 9.043 | -8.530 | 508.420 |
| subject_02 | generated | 88 | 1.407 | 1.402 | 8.883 | -0.300 | 531.520 |
| subject_03 | generated | 88 | 1.362 | 1.470 | 8.864 | 7.920 | 550.700 |
| pytest-risktest (self-hosted) | self-hosted | 79 | 1.875 | 2.189 | 2.365 | 16.730 | 26.150 |

## Per-mutation detail

| mutation | operator | file | policy | selected | total | skip_rate | failures | recall | misses | apfd_tool | work_saved |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| subject_01-m0 | flip-boolean-return | app/features/feature_02.py:12 | fast | 8 | 88 | 0.909 | 3 | 1.000 | 0 | 0.979 | 0.884 |
| subject_01-m0 | flip-boolean-return | app/features/feature_02.py:12 | balanced | 8 | 88 | 0.909 | 3 | 1.000 | 0 | 0.979 | 0.868 |
| subject_01-m0 | flip-boolean-return | app/features/feature_02.py:12 | safe | 8 | 88 | 0.909 | 3 | 1.000 | 0 | 0.979 | 0.847 |
| subject_01-m1 | replace-operator | app/services/billing.py:21 | fast | 8 | 88 | 0.909 | 1 | 1.000 | 0 | 0.994 | 0.950 |
| subject_01-m1 | replace-operator | app/services/billing.py:21 | balanced | 8 | 88 | 0.909 | 1 | 1.000 | 0 | 0.994 | 0.965 |
| subject_01-m1 | replace-operator | app/services/billing.py:21 | safe | 8 | 88 | 0.909 | 1 | 1.000 | 0 | 0.994 | 0.958 |
| subject_01-m2 | flip-boolean-return | app/services/catalog.py:17 | fast | 8 | 88 | 0.909 | 1 | 1.000 | 0 | 0.983 | 0.926 |
| subject_01-m2 | flip-boolean-return | app/services/catalog.py:17 | balanced | 8 | 88 | 0.909 | 1 | 1.000 | 0 | 0.983 | 0.930 |
| subject_01-m2 | flip-boolean-return | app/services/catalog.py:17 | safe | 8 | 88 | 0.909 | 1 | 1.000 | 0 | 0.983 | 0.935 |
| subject_02-m0 | change-constant | app/features/feature_01.py:19 | fast | 8 | 88 | 0.909 | 1 | 1.000 | 0 | 0.926 | 0.872 |
| subject_02-m0 | change-constant | app/features/feature_01.py:19 | balanced | 8 | 88 | 0.909 | 1 | 1.000 | 0 | 0.926 | 0.863 |
| subject_02-m0 | change-constant | app/features/feature_01.py:19 | safe | 8 | 88 | 0.909 | 1 | 1.000 | 0 | 0.926 | 0.835 |
| subject_02-m1 | negate-condition | app/features/feature_03.py:24 | fast | 8 | 88 | 0.909 | 2 | 1.000 | 0 | 0.943 | 0.881 |
| subject_02-m1 | negate-condition | app/features/feature_03.py:24 | balanced | 8 | 88 | 0.909 | 2 | 1.000 | 0 | 0.943 | 0.859 |
| subject_02-m1 | negate-condition | app/features/feature_03.py:24 | safe | 8 | 88 | 0.909 | 2 | 1.000 | 0 | 0.943 | 0.854 |
| subject_02-m2 | change-constant | app/core/mathx.py:3 | fast | 34 | 88 | 0.614 | 2 | 1.000 | 0 | 0.801 | 0.547 |
| subject_02-m2 | change-constant | app/core/mathx.py:3 | balanced | 69 | 88 | 0.216 | 2 | 1.000 | 0 | 0.801 | -0.163 |
| subject_02-m2 | change-constant | app/core/mathx.py:3 | safe | 80 | 88 | 0.091 | 2 | 1.000 | 0 | 0.801 | -0.180 |
| subject_03-m0 | flip-boolean-return | app/features/feature_08.py:26 | fast | 8 | 88 | 0.909 | 1 | 1.000 | 0 | 0.949 | 0.844 |
| subject_03-m0 | flip-boolean-return | app/features/feature_08.py:26 | balanced | 8 | 88 | 0.909 | 1 | 1.000 | 0 | 0.949 | 0.853 |
| subject_03-m0 | flip-boolean-return | app/features/feature_08.py:26 | safe | 8 | 88 | 0.909 | 1 | 1.000 | 0 | 0.949 | 0.836 |
| subject_03-m1 | flip-boolean-return | app/features/feature_07.py:16 | fast | 8 | 88 | 0.909 | 1 | 1.000 | 0 | 0.960 | 0.870 |
| subject_03-m1 | flip-boolean-return | app/features/feature_07.py:16 | balanced | 8 | 88 | 0.909 | 1 | 1.000 | 0 | 0.960 | 0.822 |
| subject_03-m1 | flip-boolean-return | app/features/feature_07.py:16 | safe | 8 | 88 | 0.909 | 1 | 1.000 | 0 | 0.960 | 0.867 |
| subject_03-m2 | change-constant | app/core/mathx.py:3 | fast | 34 | 88 | 0.614 | 2 | 1.000 | 0 | 0.801 | 0.488 |
| subject_03-m2 | change-constant | app/core/mathx.py:3 | balanced | 69 | 88 | 0.216 | 2 | 1.000 | 0 | 0.801 | 0.056 |
| subject_03-m2 | change-constant | app/core/mathx.py:3 | safe | 80 | 88 | 0.091 | 2 | 1.000 | 0 | 0.801 | -0.122 |
| pytest-risktest (self-hosted)-m0 | negate-condition | src/pytest_risktest/metrics.py:92 | fast | 9 | 79 | 0.886 | 1 | 1.000 | 0 | 0.905 | 0.990 |
| pytest-risktest (self-hosted)-m0 | negate-condition | src/pytest_risktest/metrics.py:92 | balanced | 9 | 79 | 0.886 | 1 | 1.000 | 0 | 0.905 | 0.991 |
| pytest-risktest (self-hosted)-m0 | negate-condition | src/pytest_risktest/metrics.py:92 | safe | 9 | 79 | 0.886 | 1 | 1.000 | 0 | 0.905 | 0.991 |
| pytest-risktest (self-hosted)-m1 | negate-condition | src/pytest_risktest/metrics.py:60 | fast | 9 | 79 | 0.886 | 1 | 1.000 | 0 | 0.918 | 0.991 |
| pytest-risktest (self-hosted)-m1 | negate-condition | src/pytest_risktest/metrics.py:60 | balanced | 9 | 79 | 0.886 | 1 | 1.000 | 0 | 0.918 | 0.990 |
| pytest-risktest (self-hosted)-m1 | negate-condition | src/pytest_risktest/metrics.py:60 | safe | 9 | 79 | 0.886 | 1 | 1.000 | 0 | 0.918 | 0.991 |
| pytest-risktest (self-hosted)-m2 | change-constant | src/pytest_risktest/report.py:22 | fast | 9 | 79 | 0.886 | 1 | 1.000 | 0 | 0.943 | 0.962 |
| pytest-risktest (self-hosted)-m2 | change-constant | src/pytest_risktest/report.py:22 | balanced | 79 | 79 | 0.000 | 1 | 1.000 | 0 | 0.943 | -0.156 |
| pytest-risktest (self-hosted)-m2 | change-constant | src/pytest_risktest/report.py:22 | safe | 79 | 79 | 0.000 | 1 | 1.000 | 0 | 0.943 | -0.202 |

