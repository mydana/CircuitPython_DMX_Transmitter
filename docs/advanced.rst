ADVANCED USAGE
==============

RESOURCES
---------

The DMXTransmitter constructor accepts a 'slots' parameter, an integer from
1 to 512 that indicates how many slots can be delivered via each pin
(universe). This parameter is passed on to class defined in the
'payload_class' parameter, default Payload_USITT_DMX512_A. The payload_class
then constructs a payload that accepts the defined number of 'slots'.

The DMXTransmitter constructor also allows a 'universes' parameter, an integer
1 to 3 that indicates how many pins (universes) that will be handled by each
state machine. If more universes are configured, the DMXTransmitter object
will have a length twice or thrice the number of 'slots' configured. The state
machine will transmit all universes simultaneously.

Each DMXTransmitter object can also be cloned. The cloned objects will be
implemented with the same number of universes (and pins) as the parent object.
But, the slot count may be configured differently. Cloned objects do not
transmit simultaneously as the parent objects.

Clones will use the same PIO until all state machines are in use. Then if the
other PIO is available the state machines from the other PIO will be used.

**Theoretical Resources available:**

3 universes * 8 state machines = 24 universes.

512 slots * 24 universes = 12,288 slots.

The actual limit is probably signifcantly less.


DMX TIMING
----------

The DMXTransmitter constructor has a default 'payload_class' parameter. By
default it's Payload_USITT_DMX512_A. When constructed, a 'payload' attribute
exists in the DMXTransmitter object. This payload has several properties
that allow the viewing and adjustment DMX parameters.

Warning: The parameters can be set such that the DMX frame's timing no longer
meets DMX512 standards.

The :meth:`interval` read-only property shows the total interval for each
DMX frame.


SHARING DMX TIMING
------------------

The Payload_USITT_DMX512_A can be subclassed to create a new class that has
different default timing than the USITT-DMX512-A standard. For example, if
a manufacturer's equipment works better with different timings, a subclass
can be written. This may be as easy as overloading the
:meth:`_init_timing_defaults` method.

Please share any such class by contributing it to this library.


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