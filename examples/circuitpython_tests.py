# SPDX-FileCopyrightText: Copyright (c) 2023 Dana Runge
#
# SPDX-License-Identifier: Unlicense
"Verify that we can load up 8 state machines on the RP2040."

import time
import board
from dmx_transmitter import dmx_transmitter


def test_construct():
    pin_number = 0
    transmitters = []
    try:
        while True:
            print(f"Testing D{pin_number}")
            dmx_pin = getattr(board, f"D{pin_number}")
            transmitters.append(dmx_transmitter.DMXTransmitter(first_out_pin=dmx_pin))
            pin_number = pin_number + 1
    except AttributeError:
        for state_machine in transmitters:
            state_machine.deinit()
        print(
            f"Poor test: This board only has {pin_number} sequential D pins. Needs 8."
        )
    except RuntimeError:
        for state_machine in transmitters:
            state_machine.deinit()
        print(f"Construction produced {pin_number} state machines. There should be 8.")


test_construct()

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
