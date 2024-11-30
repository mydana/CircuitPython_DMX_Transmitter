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


import rp2pio

from .machine_code import machine_code, pio_kwargs
from .payload_USITT_DMX512_A import Payload_USITT_DMX512_A

__author__ = "Dana Runge"
__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/mydana/CircuitPython_DMX_Transmitter"


class DMXTransmitter(Payload_USITT_DMX512_A):
    """Configure an RP2040 PIO state machine to drive the DMX512 protocol.

    :param ~microcontroller.Pin dmx_out_pin: the first pin for the
        first new DMX universe.

    **Optional parameters:**

    :param bool auto_write: If True, output all changes immediately.
        If False, use the show method to output changes.

    :param int slots: How many DMX512 slots to implement (1 thru 512)

    :param ~microcontroller.Pin enable_out_pin: a pin for enabling the line
        driver.

    :param bool|int invert_enable: If True, invert the enable pin. If False,
        don't invert the enable pin. If -2 or 2, also implements a second
        enable_out_pin. (The next pin. If the enable_out_pin is D4, for example,
        then this second pin is D5.) This second pin pulses during MARK AFTER
        BREAK, which could be used to trigger an oscilloscope.

    :param exclusive_pin_use: Used for debugging.
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        dmx_out_pin,
        slots=512,
        auto_write=False,
        enable_out_pin=None,
        # TODO needs the code for inverting enable pin
        # TODO TEST: The enable_out_pin
        exclusive_pin_use=True,
    ) -> None:
        super().__init__(slots=slots, buffers=2)
        try:
            self.auto_write = auto_write
        except ValueError:
            # Ignore error if one buffer.
            pass
        #
        # State machine parameters.
        self.dmx_out_pin = dmx_out_pin
        self.first_sideset_pin = enable_out_pin
        self.exclusive_pin_use = exclusive_pin_use
        #
        # Launch the state machine.
        self.reinit()

    def reinit(self):
        "Re-connect the state machine"
        self.state_machine = rp2pio.StateMachine(
            machine_code[0],
            **pio_kwargs(0),
            frequency=1_000_000,
            pull_threshold=16,
            auto_pull=True,
            initial_out_pin_state=1,
            out_pin_count=1,
            first_out_pin=self.dmx_out_pin,
            first_sideset_pin=self.first_sideset_pin,
            exclusive_pin_use=self.exclusive_pin_use,
        )
        self.show()

    def show(self, once=None) -> None:
        """Buffer DMX payload to the state machine and out the wire.

        Changes are not seen until 'show' is called again.
        """
        self.state_machine.background_write(once=once, loop=self.get_show_buffer())

    def stop(self) -> None:
        """Stop sending data down the wire.
        Go into a high impedance state, if enabled.
        """
        # TODO implement
        self.state_machine.background_write()
        self.state_machine.background_write(
            once=self.payload.array_stop(), loop=self.payload.array_empty()
        )

    def deinit(self) -> None:
        """Turn off the state machine and release its resources."""
        # Docstring copyright (c) 2021 Scott Shawcroft for Adafruit Industries
        self.stop()
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
        self.stop()
        return self.state_machine.__exit__(*args)

    def write(self):
        """deprecated

        Use `show` instead.
        """
        self.show()
