# SPDX-FileCopyrightText: Copyright (c) 2023 Dana Runge
#
# SPDX-License-Identifier: Unlicense
"Implement a 'fireworks' effect."
import time
import random
import board

from dmx_transmitter import dmx_transmitter

# Wire first_out_pin to the line driver.

FIRST_PIN = board.D0

dmx = dmx_transmitter.DMXTransmitter(first_out_pin=FIRST_PIN)

# Configuration
rockets = (1, 2, 3, 9, 10, 11)  # Slot numbers we want to show.
main_dimmers = (
    0,
    8,
)  # Slot numbers for the main dimmers

# Setup
tick = 0
for slot in main_dimmers:
    dmx[slot] = 0xFF
waxing = random.choice(rockets)
waning = None

# Fireworks!
while True:
    time.sleep(0.1)
    tick = tick + 1
    if tick > 8:
        tick = 0
        waning = waxing
        waxing = random.choice([r for r in rockets if r != waxing])
    waxing_dim = pow(2, tick) - 1
    waning_dim = pow(2, 8 - tick) - 1
    if waxing is not None:
        dmx[waxing] = waxing_dim
    if waning is not None:
        dmx[waning] = waning_dim
    dmx.show()
