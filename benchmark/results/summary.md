# Benchmark summary

- mutation runs: 48
- targets: pytest-risktest (self-hosted), subject_01, subject_02, subject_03
- policies: balanced, fast, safe

## Selection quality per policy

| policy | runs | skip_rate | recall | misses | apfd_tool | apfd_baseline | time_saved | work_saved |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| balanced | 16 | 0.746 | 1.000 | 0 | 0.925 | 0.521 | 0.197 | 0.694 |
| fast | 16 | 0.852 | 1.000 | 0 | 0.925 | 0.521 | 0.252 | 0.853 |
| safe | 16 | 0.731 | 1.000 | 0 | 0.925 | 0.521 | 0.185 | 0.675 |

`recall` is reported as the worst case over all runs: it is the safety metric,
so the minimum matters rather than the mean.

## Generated vs self-hosted targets

| target kind | policy | runs | skip_rate | recall | misses | apfd_tool | work_saved |
| --- | --- | --- | --- | --- | --- | --- | --- |
| generated | balanced | 12 | 0.794 | 1.000 | 0 | 0.931 | 0.708 |
| generated | fast | 12 | 0.860 | 1.000 | 0 | 0.931 | 0.816 |
| generated | safe | 12 | 0.773 | 1.000 | 0 | 0.931 | 0.682 |
| self-hosted | balanced | 4 | 0.604 | 1.000 | 0 | 0.907 | 0.655 |
| self-hosted | fast | 4 | 0.830 | 1.000 | 0 | 0.907 | 0.963 |
| self-hosted | safe | 4 | 0.604 | 1.000 | 0 | 0.907 | 0.653 |

## Observation overhead

| target | kind | total_tests | untraced_s | traced_file_s | traced_line_s | overhead_file_pct | overhead_line_pct |
| --- | --- | --- | --- | --- | --- | --- | --- |
| subject_01 | generated | 88 | 0.994 | 1.111 | 12.913 | 11.740 | 1199.180 |
| subject_02 | generated | 88 | 0.966 | 1.090 | 13.453 | 12.870 | 1293.100 |
| subject_03 | generated | 88 | 1.060 | 1.129 | 13.335 | 6.470 | 1158.090 |
| pytest-risktest (self-hosted) | self-hosted | 103 | 1.447 | 1.857 | 1.959 | 28.280 | 35.320 |

## Per-mutation detail

| mutation | operator | file | policy | selected | total | skip_rate | failures | recall | misses | apfd_tool | work_saved |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| subject_01-m0 | change-constant | app/features/feature_01.py:19 | fast | 8 | 88 | 0.909 | 1 | 1.000 | 0 | 0.926 | 0.852 |
| subject_01-m0 | change-constant | app/features/feature_01.py:19 | balanced | 8 | 88 | 0.909 | 1 | 1.000 | 0 | 0.926 | 0.847 |
| subject_01-m0 | change-constant | app/features/feature_01.py:19 | safe | 8 | 88 | 0.909 | 1 | 1.000 | 0 | 0.926 | 0.841 |
| subject_01-m1 | negate-condition | app/features/feature_03.py:24 | fast | 8 | 88 | 0.909 | 2 | 1.000 | 0 | 0.943 | 0.861 |
| subject_01-m1 | negate-condition | app/features/feature_03.py:24 | balanced | 8 | 88 | 0.909 | 2 | 1.000 | 0 | 0.943 | 0.852 |
| subject_01-m1 | negate-condition | app/features/feature_03.py:24 | safe | 8 | 88 | 0.909 | 2 | 1.000 | 0 | 0.943 | 0.844 |
| subject_01-m2 | change-constant | app/core/mathx.py:3 | fast | 34 | 88 | 0.614 | 2 | 1.000 | 0 | 0.801 | 0.497 |
| subject_01-m2 | change-constant | app/core/mathx.py:3 | balanced | 69 | 88 | 0.216 | 2 | 1.000 | 0 | 0.801 | -0.121 |
| subject_01-m2 | change-constant | app/core/mathx.py:3 | safe | 80 | 88 | 0.091 | 2 | 1.000 | 0 | 0.801 | -0.231 |
| subject_01-m3 | change-constant | app/features/feature_02.py:5 | fast | 8 | 88 | 0.909 | 2 | 1.000 | 0 | 0.977 | 0.864 |
| subject_01-m3 | change-constant | app/features/feature_02.py:5 | balanced | 8 | 88 | 0.909 | 2 | 1.000 | 0 | 0.977 | 0.856 |
| subject_01-m3 | change-constant | app/features/feature_02.py:5 | safe | 8 | 88 | 0.909 | 2 | 1.000 | 0 | 0.977 | 0.851 |
| subject_02-m0 | flip-boolean-return | app/features/feature_08.py:26 | fast | 8 | 88 | 0.909 | 1 | 1.000 | 0 | 0.949 | 0.846 |
| subject_02-m0 | flip-boolean-return | app/features/feature_08.py:26 | balanced | 8 | 88 | 0.909 | 1 | 1.000 | 0 | 0.949 | 0.840 |
| subject_02-m0 | flip-boolean-return | app/features/feature_08.py:26 | safe | 8 | 88 | 0.909 | 1 | 1.000 | 0 | 0.949 | 0.853 |
| subject_02-m1 | flip-boolean-return | app/features/feature_07.py:16 | fast | 8 | 88 | 0.909 | 1 | 1.000 | 0 | 0.960 | 0.857 |
| subject_02-m1 | flip-boolean-return | app/features/feature_07.py:16 | balanced | 8 | 88 | 0.909 | 1 | 1.000 | 0 | 0.960 | 0.843 |
| subject_02-m1 | flip-boolean-return | app/features/feature_07.py:16 | safe | 8 | 88 | 0.909 | 1 | 1.000 | 0 | 0.960 | 0.841 |
| subject_02-m2 | change-constant | app/core/mathx.py:3 | fast | 34 | 88 | 0.614 | 2 | 1.000 | 0 | 0.801 | 0.511 |
| subject_02-m2 | change-constant | app/core/mathx.py:3 | balanced | 69 | 88 | 0.216 | 2 | 1.000 | 0 | 0.801 | -0.101 |
| subject_02-m2 | change-constant | app/core/mathx.py:3 | safe | 80 | 88 | 0.091 | 2 | 1.000 | 0 | 0.801 | -0.240 |
| subject_02-m3 | flip-boolean-return | app/features/feature_03.py:16 | fast | 8 | 88 | 0.909 | 1 | 1.000 | 0 | 0.960 | 0.866 |
| subject_02-m3 | flip-boolean-return | app/features/feature_03.py:16 | balanced | 8 | 88 | 0.909 | 1 | 1.000 | 0 | 0.960 | 0.869 |
| subject_02-m3 | flip-boolean-return | app/features/feature_03.py:16 | safe | 8 | 88 | 0.909 | 1 | 1.000 | 0 | 0.960 | 0.861 |
| subject_03-m0 | flip-boolean-return | app/features/feature_07.py:26 | fast | 8 | 88 | 0.909 | 1 | 1.000 | 0 | 0.949 | 0.861 |
| subject_03-m0 | flip-boolean-return | app/features/feature_07.py:26 | balanced | 8 | 88 | 0.909 | 1 | 1.000 | 0 | 0.949 | 0.845 |
| subject_03-m0 | flip-boolean-return | app/features/feature_07.py:26 | safe | 8 | 88 | 0.909 | 1 | 1.000 | 0 | 0.949 | 0.838 |
| subject_03-m1 | flip-boolean-return | app/features/feature_06.py:26 | fast | 8 | 88 | 0.909 | 1 | 1.000 | 0 | 0.949 | 0.860 |
| subject_03-m1 | flip-boolean-return | app/features/feature_06.py:26 | balanced | 8 | 88 | 0.909 | 1 | 1.000 | 0 | 0.949 | 0.840 |
| subject_03-m1 | flip-boolean-return | app/features/feature_06.py:26 | safe | 8 | 88 | 0.909 | 1 | 1.000 | 0 | 0.949 | 0.810 |
| subject_03-m2 | flip-boolean-return | app/services/reports.py:17 | fast | 8 | 88 | 0.909 | 1 | 1.000 | 0 | 0.983 | 0.962 |
| subject_03-m2 | flip-boolean-return | app/services/reports.py:17 | balanced | 8 | 88 | 0.909 | 1 | 1.000 | 0 | 0.983 | 0.959 |
| subject_03-m2 | flip-boolean-return | app/services/reports.py:17 | safe | 8 | 88 | 0.909 | 1 | 1.000 | 0 | 0.983 | 0.961 |
| subject_03-m3 | flip-boolean-return | app/core/textx.py:7 | fast | 8 | 88 | 0.909 | 5 | 1.000 | 0 | 0.972 | 0.959 |
| subject_03-m3 | flip-boolean-return | app/core/textx.py:7 | balanced | 8 | 88 | 0.909 | 5 | 1.000 | 0 | 0.972 | 0.962 |
| subject_03-m3 | flip-boolean-return | app/core/textx.py:7 | safe | 8 | 88 | 0.909 | 5 | 1.000 | 0 | 0.972 | 0.957 |
| pytest-risktest (self-hosted)-m0 | flip-boolean-return | src/pytest_risktest/metrics.py:68 | fast | 20 | 103 | 0.806 | 2 | 1.000 | 0 | 0.864 | 0.961 |
| pytest-risktest (self-hosted)-m0 | flip-boolean-return | src/pytest_risktest/metrics.py:68 | balanced | 20 | 103 | 0.806 | 2 | 1.000 | 0 | 0.864 | 0.964 |
| pytest-risktest (self-hosted)-m0 | flip-boolean-return | src/pytest_risktest/metrics.py:68 | safe | 20 | 103 | 0.806 | 2 | 1.000 | 0 | 0.864 | 0.953 |
| pytest-risktest (self-hosted)-m1 | negate-condition | src/pytest_risktest/metrics.py:66 | fast | 20 | 103 | 0.806 | 2 | 1.000 | 0 | 0.864 | 0.965 |
| pytest-risktest (self-hosted)-m1 | negate-condition | src/pytest_risktest/metrics.py:66 | balanced | 20 | 103 | 0.806 | 2 | 1.000 | 0 | 0.864 | 0.966 |
| pytest-risktest (self-hosted)-m1 | negate-condition | src/pytest_risktest/metrics.py:66 | safe | 20 | 103 | 0.806 | 2 | 1.000 | 0 | 0.864 | 0.964 |
| pytest-risktest (self-hosted)-m2 | replace-operator | src/pytest_risktest/metrics.py:35 | fast | 20 | 103 | 0.806 | 6 | 1.000 | 0 | 0.945 | 0.958 |
| pytest-risktest (self-hosted)-m2 | replace-operator | src/pytest_risktest/metrics.py:35 | balanced | 20 | 103 | 0.806 | 6 | 1.000 | 0 | 0.945 | 0.963 |
| pytest-risktest (self-hosted)-m2 | replace-operator | src/pytest_risktest/metrics.py:35 | safe | 20 | 103 | 0.806 | 6 | 1.000 | 0 | 0.945 | 0.962 |
| pytest-risktest (self-hosted)-m3 | replace-operator | src/pytest_risktest/report.py:59 | fast | 10 | 103 | 0.903 | 3 | 1.000 | 0 | 0.953 | 0.967 |
| pytest-risktest (self-hosted)-m3 | replace-operator | src/pytest_risktest/report.py:59 | balanced | 103 | 103 | 0.000 | 3 | 1.000 | 0 | 0.953 | -0.271 |
| pytest-risktest (self-hosted)-m3 | replace-operator | src/pytest_risktest/report.py:59 | safe | 103 | 103 | 0.000 | 3 | 1.000 | 0 | 0.953 | -0.267 |

