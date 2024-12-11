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

* Any RP2040 CircuitPython board. I used the Adafruit KB2040
  <https://www.adafruit.com/product/5302>`_ (Product ID: <5302>)

* An RP2350 CircuitPython board may work as well. It has not been tested yet.

* An isolated RS485 line driver. I used a Digilent PmodRS485.
"""


import rp2pio

from .machine_code import machine_code, pio_kwargs
from .dmx_payload import DMXPayload

__author__ = "Dana Runge"
__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/mydana/CircuitPython_DMX_Transmitter"


class DMXTransmitter(DMXPayload):
    """Configure an RP2040/RP2350 PIO state machine to drive the DMX512 protocol.

    :param ~microcontroller.Pin dmx_out_pin: the DMX universe. Needs a RS485
        line driver to work correctly. Check documentation.

    **Optional parameters:**

    :param bool auto_write: If True, output all changes immediately.
        If False, use the show method to output changes.

    :param int slots: How many DMX512 slots to implement (1 thru 512)

    :param ~microcontroller.Pin|Nine timing_out_pin: see Advanced Usage documention.

    :param bool|int timing_out_control: see Advanced Usage documention.

    :param exclusive_pin_use: Used for debugging.
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        dmx_out_pin,
        slots=512,
        auto_write=False,
        timing_out_pin=None,
        timing_out_control=False,
        exclusive_pin_use=True,
    ) -> None:
        super().__init__(slots=slots, buffers=2)
        try:
            self.auto_write = auto_write
        except ValueError:
            # Ignore error if one buffer.
            pass
        # Figure out which code to use.
        if timing_out_pin:
            if timing_out_control is None or timing_out_control == 0:
                self.code_index = 0
                if timing_out_pin is not None:
                    raise ValueError(
                        "timing_out_pin cannot be set if timing_out_control is set"
                    )
            else:
                if timing_out_control is False or timing_out_control == 1:
                    self.code_index = 1
                elif timing_out_control is True or timing_out_control == -1:
                    self.code_index = -1
                elif timing_out_control == 2:
                    self.code_index = 2
                elif timing_out_control == -2:
                    self.code_index = -2
                else:
                    raise ValueError(
                        "timing_out_control must be None, False, True, -2, -1, 0, 1, or 2"
                    )
                if timing_out_pin is None:
                    raise ValueError(
                        "timing_out_control must be set if timing_out_pin is"
                    )

        else:
            self.code_index = 0
        #
        # State machine parameters.
        self.dmx_out_pin = dmx_out_pin
        self.first_sideset_pin = timing_out_pin
        self.exclusive_pin_use = exclusive_pin_use
        #
        # Launch the state machine.
        self.reinit()

    def reinit(self):
        "Re-connect and state machine to the pin, and start the state machine."
        self.state_machine = rp2pio.StateMachine(
            machine_code[self.code_index],
            **pio_kwargs(abs(self.code_index)),
            frequency=1_000_000,
            pull_threshold=16,
            auto_pull=True,
            initial_out_pin_state=1,
            out_pin_count=1,
            first_out_pin=self.dmx_out_pin,
            first_sideset_pin=self.first_sideset_pin,
            exclusive_pin_use=self.exclusive_pin_use,
        )
        self._send_init(self.state_machine.background_write)

    def show(self, once=None) -> None:
        """If auto_write is False, send changes down the wire.

        If auto_write is True, ignored.

        'once' is an advanced parameter for sending Alternate START Codes,
        and if you don't know what that means, don't worry about it.
        """
        if once is None:
            self._send_show_buffer(self.state_machine.background_write)
        else:
            self._send_show_buffer(
                lambda once=once, loop=None: self.state_machine.background_write(
                    once=once, loop=loop
                )
            )

    def stop(self) -> None:
        """Stop sending data down the wire.

        Advanced use: Disable the line driver, if configured.
        """
        self.state_machine.background_write()
        self._send_stop_buffer(callback=self.state_machine.background_write)

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
