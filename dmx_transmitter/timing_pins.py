# SPDX-FileCopyrightText: Copyright (c) 2023 Dana Runge
#
# SPDX-License-Identifier: MIT
"""
`dmx_transmitter.timing_pins`
=============================

A framework to allow hardware hackers to choose timing pins (aka side set pins)
to activate on the state machines.

All other users can ignore this class.

* Author: Dana Runge
"""

import array

__author__ = "Dana Runge"
__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/mydana/CircuitPython_DMX_Transmitter"


def TRANSMITTING(side):  # pylint: disable=invalid-name
    """Send HIGH if data is being transmitted.

    Transmission may be gracefully by sending a non-zero mark_after_frame
    and ending the stream right after.
    """
    return bool(0b001 & side)


def NOT_TRANSMITTING(side):  # pylint: disable=invalid-name
    "Opposite of transmitting."
    return not bool(0b001 & side)


def MAB(side):  # pylint: disable=invalid-name
    "Send HIGH when MARK AFTER BREAK is being sent."
    return bool(0b010 & side)


def NOT_MAB(side):  # pylint: disable=invalid-name
    "Opposite of MAB"
    return not bool(0b010 & side)


def BREAK(side):  # pylint: disable=invalid-name
    "Send HIGH when SPACE for BREAK is being sent."
    return bool(0b100 & side)


def NOT_BREAK(side):  # pylint: disable=invalid-name
    "Opposite of BREAK"
    return not bool(0b100 & side)


class TimingPin:  # pylint: disable=too-few-public-methods
    """The catalog of timing pins available.

    Pass a list of up to three (3) these functions into the timing_pins
    parameter in the DMXTransmitter constructor. As such:

        timing_pins = [BREAK, NOT_TRANSMITTING]

    ALL pins values only reflect the progress in the program counter. If
    the state machine stalls unexpededly, the pin values will also stall.
    """

    def __init__(self, *pins, program):
        # __init__ is NOT used by the user.

        # How many pins are already in use.
        taken = (
            5  # 5 bits for delay
            + 8  # 8 bits of opcode parameters
            # Unless we use some bits for sideset:
            - program.pio_kwargs["sideset_pin_count"]
            - program.pio_kwargs["sideset_enable"]
        )

        # Which bits do we leave alone?
        mask = (
            0xE000  # This is the opcode
            | 2 ** (taken) - 1  # These are delay & opcode parameters
            | (0x1000 if program.pio_kwargs["sideset_enable"] else 0)
        )

        if len(pins) > program.pio_kwargs["sideset_pin_count"]:
            raise ValueError(
                f"No more than {program.pio_kwargs['sideset_pin_count']} pins."
            )

        self.assembled = array.array(
            "H",
            (
                (
                    # Assemble the replacement sideset bits.
                    sum(
                        # Go through the sideset pins from opcode.
                        2**bit
                        for bit, fun in enumerate(pins)
                        # 0x1FFF removes the 3 most significat bits
                        # these are the operation code.
                        # Then >> taken, removes the delay, opcode parameters
                        # Leaving only the allocated sideset.
                        if fun((opcode & 0x1FFF) >> taken)
                    )
                    << taken  # And move back into the right bits.
                )
                | (opcode & mask)
                for opcode in program.assembled
            ),
        )

        self.pio_kwargs = dict(
            program.pio_kwargs,
            sideset_pin_count=program.pio_kwargs["sideset_pin_count"] - len(pins),
            initial_sideset_pin_state=bin(
                sum(2**bit for bit, fun in enumerate(pins) if fun(0))
            ),
        )
