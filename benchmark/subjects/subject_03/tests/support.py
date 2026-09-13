"""Shared test helpers.

``busy`` gives every test a small, deterministic amount of real CPU work
(~15 ms).  Without it a 24-test suite would be entirely dominated by interpreter
and pytest start-up, and no selection strategy could show a wall-clock effect.
The work factor is a *controlled knob*; the benchmark reports both wall-clock
savings and execution-time-only savings so the choice cannot flatter the tool.
"""

ITERATIONS = 45000


def busy(iterations=ITERATIONS):
    total = 0
    for index in range(iterations):
        total += (index * index) % 7
    return total
