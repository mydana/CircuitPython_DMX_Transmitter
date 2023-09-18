# SPDX-FileCopyrightText: Copyright (c) 2023 Dana Runge
#
# SPDX-License-Identifier: Unlicense
"Blink a DMX-equipped light."

import time
import board

from dmx_transmitter import dmx_transmitter

# Wire DMX_PIN to an isolated RS485 line driver.

DMX_PIN = board.D0

dmx = dmx_transmitter.DMXTransmitter(first_out_pin=DMX_PIN)

# Blinking lights
while True:
    dmx.clear()  # Turn off the light(s)
    dmx.show()
    time.sleep(1)
    dmx[0:3] = 255  # Turn lights on full. DMX channels: 1, 2, 3,
    dmx.show()
    time.sleep(1)
