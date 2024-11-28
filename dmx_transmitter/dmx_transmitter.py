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

    :param ~microcontroller.Pin first_out_pin: the first pin for the
        first new DMX universe.

    **Optional parameters:**

    :param ~microcontroller.Pin first_timing_pin: a sideset pin available for
        each state machine. This pin can potentially be used for sending
        RDM frames, or for connecting to an oscilloscope for debugging.

    :param list timing_pins: a list of :class:`TimingPin` class methods that
        control how many, and which TimingPin functionalities to implement.

    """

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        first_out_pin,
        first_timing_pin=None,
        exclusive_pin_use=True,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.state_machine = rp2pio.StateMachine(
            machine_code[0],
            **pio_kwargs(0),
            frequency=1_000_000,
            pull_threshold=16,
            auto_pull=True,
            initial_out_pin_state=1,
            out_pin_count=1,
            first_out_pin=first_out_pin,
            first_sideset_pin=first_timing_pin,
            exclusive_pin_use=exclusive_pin_use,
        )
        self.state_machine.background_write(once=None, loop=self.get_show_buffer())

    def show(self):
        "TODO: This method will be re-implimented after this work is done."
        pass
