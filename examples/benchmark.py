# SPDX-FileCopyrightText: 2020 Jeff Epler for Adafruit Industries
# SPDX-FileCopyrightText: 2020 Zoltán Vörös for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2024 Dana Runge
#
# SPDX-License-Identifier: MIT
"Run the benchmarks on the dmx_transmitter"

import time
import sys
import board  # type: ignore

from dmx_transmitter import dmx_transmitter

version_str = (
    f"{sys.implementation.name} {'.'.join(str(v) for v in sys.implementation.version)}"
)
print("-----------------------------------------------------")
print("---                                               ---")
print("---   CircuitPython_DMX_Transmitter Benchmarks:   ---")
print(f"---   {version_str + ' '*(44 - len(version_str))}---")
print("---                                               ---")
print("-----------------------------------------------------")
print()

SMALL_DMX = 16  # 16 slots
LARGE_DMX = 512  # 512 slots

PINS = (
    board.D0,
    board.D1,
    board.D2,
    board.D3,
    board.D4,
    board.D5,
    board.D6,
    board.D7,
    board.D8,
    board.D9,
    board.D10,
    board.D11,
    board.D12,
)

TEST_CASES = (
    ("16:False", {"slots": 16, "auto_write": False}),
    ("512:False", {"slots": 512, "auto_write": False}),
    ("16:True", {"slots": 16, "auto_write": True}),
    ("512:True", {"slots": 512, "auto_write": True}),
    ("32:False", {"slots": 32, "auto_write": False}),
    ("256:False", {"slots": 256, "auto_write": False}),
    ("32:True", {"slots": 32, "auto_write": True}),
    ("256:True", {"slots": 256, "auto_write": True}),
    ("64:False", {"slots": 64, "auto_write": False}),
    ("128:False", {"slots": 128, "auto_write": False}),
    ("64:True", {"slots": 64, "auto_write": True}),
    ("128:True", {"slots": 128, "auto_write": True}),
)


def timeit(s, f):
    """A Simple Benchmark from Adafruit Learning System"""
    # https://learn.adafruit.com/ulab-crunch-numbers-fast-with-circuitpython/a-simple-benchmark
    t0 = time.monotonic_ns()
    n = f()
    t1 = time.monotonic_ns()
    r = (t1 - t0) * 1e-6 / n
    print("%s:%f:%d" % (s, r, n))


#
# Set up the state machines for testing
#

instantiated_cases = []

for inx, pin in enumerate(PINS):
    test_case, attributes = TEST_CASES[inx % len(TEST_CASES)]
    try:
        instantiated_cases.append(
            (
                test_case,
                dmx_transmitter.DMXTransmitter(dmx_out_pin=pin, **attributes),
            )
        )
    except RuntimeError:
        print("Number of State Machines instantiated:")
        print(f"    {inx} State Machines instantiated.")
        print("    (Should be 8 for the RP2040 and 12 for the RP2350.)")
        print()
        break


def set_values(dmx):
    for _ in range(1000):
        dmx[0] = 100
    return 1000


def get_values(dmx):
    for _ in range(1000):
        dmx[0]  # pylint: disable=pointless-statement
    return 1000


def clear_all(dmx):
    for _ in range(100):
        dmx.clear()
    return 100


def fill_all(dmx):
    for _ in range(100):
        dmx.fill(255)
    return 100


def show(dmx):
    for _ in range(100):
        dmx.show()
    return 500


print("Slots:auto_write:Operation:Timing:Average over Cycles")
for case_name, state_machine in instantiated_cases:
    # pylint: disable=cell-var-from-loop
    timeit(f"{case_name}:Read a value to DMX", lambda: get_values(state_machine))
    timeit(f"{case_name}:Write a value to DMX", lambda: set_values(state_machine))
    timeit(f"{case_name}:Clear DMX", lambda: clear_all(state_machine))
    timeit(f"{case_name}:Fill DMX", lambda: fill_all(state_machine))
    timeit(f"{case_name}:Show", lambda: show(state_machine))
