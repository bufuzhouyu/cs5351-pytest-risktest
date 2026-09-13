# Untraced code paths (boundary experiment)

The product (`app/cli.py`) only ever runs in a child process, so the
instrumented interpreter never records it as a dependency of the tests.
A mutation that breaks both tests is therefore invisible to a purely
dynamic selection.

| phase | tests | selected | executed | real failures | detected | missed |
| --- | --- | --- | --- | --- | --- | --- |
| no declaration (dynamic tracing only) | 2 | 1 | 1 | 2 | 1 | 1 |
| @pytest.mark.risktest_always | 2 | 2 | 2 | 2 | 2 | 0 |

`risktest_always` is honoured independently of the policy and of the stop
rule, which is why the documentation requires process-boundary tests to
declare themselves.
