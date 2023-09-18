# SPDX-FileCopyrightText: Copyright (c) 2023 Dana Runge
#
# SPDX-License-Identifier: MIT
"""

"""

import array
import rp2pio

from .Payload_USITT_DMX512_A import Payload_USITT_DMX512_A

__author__ = "Dana Runge"
__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/mydana/CircuitPython_DMX_Transmitter"


class DMXTransmitter:
    """Configure an RP2040 PIO state machine to drive the DMX512 protocol.

        Up to three (3) universes are supported for each state machine.

    **Required parameter:**

    :param ~microcontroller.Pin first_out_pin: the first pin for the
        first new DMX universe. If multiple universes are used, additional
        pins are needed for each additional universe. These pins will be
        automatically appear at the subsequent GPIO pin number(s).

    **Optional parameters:**

    :param int universes: how many output pins. (count)
        Two universes use the same amount of memory as three.
        Minimum: 1. Default: 1. Maximum: 3.

    :param ~microcontroller.Pin first_timing_pin: a sideset pin available for
        each state machine. This pin can potentially be used for sending
        RDM frames, or for connecting to an oscilloscope for debugging.

    :param list timing_pins: a list of :class:`TimingPin` class methods that
        control how many, and which TimingPin functionalities to implement.

    If this state machine is cloned, :meth:`clone` both pin counts
    will be needed in the cloned state machine.
    """

    def __init__(
        self,
        first_out_pin,
        universes=1,
        first_timing_pin=None,
        timing_pins=(),
        payload_class=Payload_USITT_DMX512_A,
        clone_from=None,
        **kwargs,
    ) -> None:
        # Bind a list-like object to a PIO state machine to send DMX.
        if clone_from is None:
            #
            # Initiate the assembled machine code
            #   and coded-in parameters: universes, and timing_pins
            self.universes = int(universes)
            self.payload = payload_class(universes=self.universes, **kwargs)
            self.program = TimingPin(
                *timing_pins,
                program=MachineCode(
                    universes=self.universes,
                ),
            )
        else:
            #
            # Copy of the code and coded-in parameters
            self.universes = clone_from.universes
            self.payload = payload_class(clone_from=clone_from.payload, **kwargs)
            self.program = clone_from.program
        #
        # Setup the runtime environment.
        # State machine
        self.state_machine = rp2pio.StateMachine(
            array.array("H", (i & 0xE3FF for i in self.program.assembled)),
            # **self.program.sm_kwargs,
            frequency=1_000_000,
            pull_threshold=16 if self.universes == 1 else 32,
            auto_pull=True,
            initial_out_pin_state=2**self.universes - 1,
            out_pin_count=self.universes,
            first_out_pin=first_out_pin,
            first_sideset_pin=first_timing_pin,
        )

    def clone(self, first_out_pin, first_timing_pin=None, **kwargs):
        """Create a new DMX512tx bonded to a new state machine.

        This gives 1 to 3 more universes for each state machine,
        for a maximum of 24 universes.

        Supports the same parameters as in the constructor except,
        'universes', and 'timing_pins' which will be implemented identically
        as the parent object.

        All other parameters default to being copies of the parent object's
        parameters.

        If there is still another state machine available in this PIO,
        uses a state machine in that PIO. (There are 4 state machines in
        each PIO.) Once this PIO is full, will attempt to create a state
        machine in the other PIO if it is not in use for another application.

        :param ~microcontroller.Pin first_out_pin: the first pin for the
            first new DMX universe. If multiple universes are used, additional
            pins are needed for each additional universe. These pins will be
            automatically appear at the subsequent GPIO pin number(s).

        :param ~microcontroller.Pin timing_pin: a optional pin used for
            debugging or supporting RDM.
        """
        return type(self)(
            first_out_pin, first_timing_pin=first_timing_pin, clone_from=self, **kwargs
        )

    def run(self, once=None) -> None:
        """Link DMX payload to the state machine and out the wire.

        Changes are not buffered, but are sent immediately.
        """
        self.state_machine.background_write()
        self.state_machine.background_write(once=once, loop=self.payload.array)

    def show(self, once=None) -> None:
        """Buffer DMX payload to the state machine and out the wire.

        Changes are not seen until 'show' is called again.
        """
        self.state_machine.background_write()
        self.state_machine.background_write(once=once, loop=self.payload.array_copy())

    def stop(self) -> None:
        """Stop sending data down the wire.
        Go into a high impedance state, if enabled.
        """
        self.state_machine.background_write()
        self.state_machine.background_write(
            once=self.payload.array_stop(), loop=self.payload.array_empty()
        )

    def deinit(self) -> None:
        """Turn off the state machine and release its resources."""
        # Docstring copyright (c) 2021 Scott Shawcroft for Adafruit Industries
        return self.state_machine.deinit()

    def __enter__(self):
        """No-op used by Context Managers.
        Provided by context manager helper."""
        # Docstring copyright (c) 2021 Scott Shawcroft for Adafruit Industries
        return self

    def __exit__(self, *args) -> None:
        """Automatically deinitializes the hardware when exiting a context. See
        :ref:`lifetime-and-contextmanagers` for more info."""
        # Docstring copyright (c) 2021 Scott Shawcroft for Adafruit Industries
        return self.state_machine.__exit__(*args)

    def clear(self):
        "Set all slot values to 0."
        return self.payload.clear()

    def __len__(self):
        return len(self.payload)

    def __getitem__(self, index) -> int:
        return self.payload[index]

    def __setitem__(self, index, val) -> None:
        self.payload[index] = val


class TimingPin:
    """The catalog of timing pins available.

    Pass a list of up to three (3) these functions into the timing_pins
    parameter in the DMXTransmitter constructor. As such:

        timing_pins = [BREAK, NOT_TRANSMITTING]

    ALL pins values only reflect the progress in the program counter. If
    the state machine stalls unexpededly, the pin values will also stall.
    """

    @staticmethod
    def TRANSMITTING(side):
        """Send HIGH if data is being transmitted.

        Transmission may be gracefully by sending a non-zero mark_after_frame
        and ending the stream right after.
        """
        return bool(0b001 & side)

    @staticmethod
    def NOT_TRANSMITTING(side):
        "Opposite of transmitting."
        return not bool(0b001 & side)

    @staticmethod
    def MAB(side):
        "Send HIGH when MARK AFTER BREAK is being sent."
        return bool(0b010 & side)

    @staticmethod
    def NOT_MAB(side):
        "Opposite of MAB"
        return not bool(0b010 & side)

    @staticmethod
    def BREAK(side):
        "Send HIGH when SPACE for BREAK is being sent."
        return bool(0b100 & side)

    @staticmethod
    def NOT_BREAK(side):
        "Opposite of BREAK"
        return not bool(0b100 & side)

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
                "No more than {0} pins.".format(program.pio_kwargs["sideset_pin_count"])
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


class MachineCode:
    "Frozen machine code. From lib/dmx_transmitter/assembly_code."

    def __init__(self, universes):
        self.pio_kwargs = {"sideset_enable": False, "sideset_pin_count": 3}
        self.assembled = array.array(
            "H",
            (
                # 1 universes:
                (
                    # fmt: off
                    0x6430, 0x0441, 0xB403, 0x7430, 0x1444, 0x7430, 0xAC0B, 0x0C47,
                    0x6C50, 0x8CE0, 0xA603, 0xE427, 0x6501, 0xA442, 0x044C, 0xA40B,
                    0x6428, 0x0451, 0x0489, 0x84E0, 0xA603, 0xE427, 0x6501, 0xA442,
                    0x0456, 0xA40B, 0x6428, 0x0420, 0x045C, 0x80A0,
                    # fmt: on
                ),
                # 2 universes:
                (
                    # fmt: off
                    0x6420, 0x0441, 0xB403, 0x7420, 0x1444, 0x7420, 0xAC0B, 0x0C47,
                    0x6C40, 0x8CE0, 0xA603, 0xE427, 0x6502, 0x6461, 0x044C, 0xA40B,
                    0x6428, 0x0451, 0x0489, 0x84E0, 0xA603, 0xE427, 0x6502, 0x6461,
                    0x0456, 0xA40B, 0x6428, 0x0420, 0x045C, 0x80A0,
                    # fmt: on
                ),
                # 3 universes:
                (
                    # fmt: off
                    0x6420, 0x0441, 0xB403, 0x7420, 0x1444, 0x7420, 0xAC0B, 0x0C47,
                    0x6C40, 0x8CE0, 0xA603, 0xE427, 0x6503, 0xA442, 0x044C, 0xA40B,
                    0x6428, 0x0451, 0x0489, 0x84E0, 0xA603, 0xE427, 0x6503, 0xA442,
                    0x0456, 0xA40B, 0x6428, 0x0420, 0x045C, 0x80A0,
                    # fmt: on
                ),
            )[universes - 1],
        )
