ADVANCED USAGE
==============

The story so far::

    In the beginning the Universe was created.  This has made a lot of people very
    angry and been widely regarded as a bad move.
        -- Douglas Adams, "The Restaurant at the End of the Universe"

User population
---------------
* Wants to allocate fewer slots per universe.
* Wants to control the DMX timing.
* Wants to put the line driver into a high impedance state.
* Wants to hook up an oscilloscope.

How it works
------------
This library consists of the DMXTransmitter class and a payload class.

The DMXTransmitter class handles the care and feeding of a state
machine's hardware. Initialization, start, stop, and deinitialize,
and upload of new lighting parameters to the state machine are all
operations handled by objects of this class.

This class also constructs a 'payload' object that contains the lighting
parameters for sending to the state machine. Also, this class has convenience
methods that forward control of the lighting values to the payload object.
In fact, the operations described in the 'Python Object Indexing Tutorial' in
the Basic Use section are all ones that are forwarded to the payload class.

DMX TIMING
==========
By default, this library implements the USITT DMX512-A standard timings.
All timings are the minimum, except for SPACE FOR BREAK which is at the
recommended timing.

Unfortunately, not all equipment in the field is compatible with the standard.

By default the DMXTransmitter constructs a payload object, which by default is
Payload_USITT_DMX512_A. This object has properties that allows the adjustment
of the DMX timing. For example:

.. code-block:: Python

   >>> dmx.payload.space_for_break
   172
   >>> dmx.payload.space_for_break = 88
   >>> dmx.payload.space_for_break
   88
   >>>

Remember that either the 'run' method or the 'show' method has to be
called to send the new timing to the state machine.

All available timing parameters are available in the API Reference section
see the Payload_USITT_DMX512_A class subsection.

Warning: The parameters can be set such that the DMX frame's timing no longer
meets DMX512 standards. Check the documentation on the interval method in
the API Reference for more information.


TIMING PINS
-----------

The RP2040 PIO has a 'side set' pin capability. This is a set of pins that can
be sent as part the assembly code that runs the state machine. This library
has the capability to set side set pins. The DMXTransmitter constructor
has 'timing_pins' and 'first_timing_pin' parameters. See the API Reference.

These pins could be used for driving an oscilloscope, for example. Tell us
about any esoteric uses you find for these.
