HARDWARE HACKERS
================

User population
----------------

"Can I figure out how to deploy RDM on this?"

* Wants to hook up an oscilloscope.
* Wants to put the line driver into a high impedance state.
* Wants to transmit RDM frames.
* Wants to transmit other START CODE frames.
* Wants to pore through the assembly code.
* Wants to convert the 'bit_interlace' function into C.
* Wants to convert the 'bit_deinterlace' function into C.

TIMING PINS
-----------

The RP2040 PIO has a 'side set' pin capability. This is a set of pins that can
be sent as part the assembly code that runs the state machine. This library
has the capability to set side set pins. The DMXTransmitter constructor
has 'timing_pins' and 'first_timing_pin' parameters. See the API Reference.

These pins could be used for driving an oscilloscope, for example. Tell us
about any esoteric uses you find for these.


EXTENDING THE LIBRARY
=====================

The dmx_transmitter library has hooks making it easy for another developer
to extend capabilities.

OTHER START CODES
-----------------

The Payload_USITT_DMX512_A class can be subclassed. Other START CODES defined
in the standard may be implemented by overloading the :meth:`_init_start_code`
method. The 'clone_from' parameter of the constructor will generate a new
payload with the new START CODE.

The :meth:`run` and :meth:`start` parameters implement a 'once' parameter
that allows the new payload be sent down the wire.

RDM AND HIGH IMPEDANCE
----------------------

The TimingPin methods :meth:`TRANSMITTING` and :meth:`NOT_TRANSMITING`
will enable a timing pin on the state machine that can be used for a
transmit enable pin on the RS485 line driver.

A subclass of the Payload_USITT_DMX512_A class can be constructed to set
the mark_after_frame longer than the minimum. Without this, the TRANSMITTING
pin will not go LOW.

Finally use the :meth:`stop` in the DMXTransmitter to orchestrate the data
stream stopping at the right time when the transmitter the TRANSMITTING pin
goes LOW and the state machine stalls waiting for data.

Succeed, and the RS485 bus will go into a high-impedance when desired.

It's possible. Good luck.

assembly_code.py
----------------

assembly_code.py / assembly_code.mpy do NOT need to be installed.

The assembly_code.py script/library is the assembly
code that programs the state machine. Both the DMXTransmitter class and the
Payload_USITT_DMX_A classes have frozen parameters that are opaque lists of
numbers. The assembly_code.py script is where they were created, just in case
poring through assembly code is your idea of fun.
