# SPDX-FileCopyrightText: Copyright (c) 2023 Dana Runge
#
# SPDX-License-Identifier: MIT
"""
`dmx_transmitter.dmx_transmitter`
=================================

Main class for sending DMX512 lighting data out of a GPIO pin.

* Author: Dana Runge

Implementation Notes
--------------------

**Hardware:**

* `Any RP2040 CircuitPython board. I used the Adafruit KB2040
  <https://www.adafruit.com/product/5302>`_ (Product ID: <5302>)

* An isolated RS485 line driver. I used a Digilent PmodRS485.
"""

import array
import rp2pio

from .payload_USITT_DMX512_A import Payload_USITT_DMX512_A
from .machine_code import MachineCode


__author__ = "Dana Runge"
__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/mydana/CircuitPython_DMX_Transmitter"


class DMXTransmitter:
    """Configure an RP2040 PIO state machine to drive the DMX512 protocol.

        Up to three (3) universes are supported for each state machine.

    **Required parameter:**

    :param ~microcontroller.Pin first_out_pin: the first pin for the
        first new DMX universe.

    **Optional parameters:**

    :param ~microcontroller.Pin first_timing_pin: a sideset pin available for
        each state machine. This pin can potentially be used for sending
        RDM frames, or for connecting to an oscilloscope for debugging.

    :param int timing_pins: How many timing pins to implement.

        - 0 - No timing pins
        - 1 - Transmitter enable, active high.
        - 2 - Transmitter enable, MARK AFTER BREAK, active high.
        - -1 - Transmitter enable, active low.
        - -2 - Transmitter enable, MARK AFTER BREAK, active low.
    """

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        first_out_pin,
        first_timing_pin=None,
        timing_pins=0,
        payload_class=Payload_USITT_DMX512_A,
        exclusive_pin_use=True,
        **kwargs,
    ) -> None:
        """Bind a list-like object to a PIO state machine to send DMX."""
        timing_pins = int(timing_pins)
        if abs(timing_pins) > len(MachineCode.assembled) // 2:
            raise ValueError("Too many timing pins.")
        self.payload = payload_class(**kwargs)
        self.state_machine = rp2pio.StateMachine(
            MachineCode.assembled[timing_pins],
            sideset_pin_count=max(1, abs(timing_pins)),
            sideset_enable=False,
            frequency=1_000_000,
            pull_threshold=16,
            auto_pull=True,
            initial_out_pin_state=-1,
            out_pin_count=1,
            first_out_pin=first_out_pin,
            first_sideset_pin=first_timing_pin if timing_pins else None,
            exclusive_pin_use=exclusive_pin_use,
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
        return self.payload.__getitem__(index)

    def __setitem__(self, index, val) -> None:
        self.payload.__setitem__(index, val)
