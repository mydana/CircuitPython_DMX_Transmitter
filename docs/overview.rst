OVERVIEW
========

USER POPULATIONS
================

Basic users
-----------

"I can program a light show in Python? Cool!"

* Doesn't care how it works, as long as it does.
* One universe.
* Has memory to spare.
* Not satisfied just watching the blinking light, wants to program it.

Advanced users
--------------

"I need a 'DMX speed' control."

* Wants to squeeze out every byte out of the available memory.
* Wants to allocate fewer slots per universe.
* Wants multiple universes. (Theoretical limit: 24 universes.)
* Wants to control the DMX timing.
* Wants to use a pre-built DMX timing.
* Wants to create a pre-built timing to share.

Extra-advanced users
--------------------

"Can I figure out how to deploy RDM on this?"

* Wants to hook up an oscilloscope.
* Wants to put the line driver into a high impedance state.
* Wants to transmit RDM frames.
* Wants to transmit other START CODE frames.
* Wants to pore through the assembly code.

Circuit Python's developers
---------------------------

"That's a clever way to handle bit transposing."

* Wants to convert the 'bit_interlace' function into C.
* Wants to convert the 'bit_deinterlace' function into C.

HOW IT WORKS
============

The RP2040 chip
---------------

This library only works on microcontrollers built on the RP2040 chip.

The RP20240 chip contains two programmable I/O adaptors. (PIO) Each PIO has
four hardware state machines optimized for interfacing with serial protocols,
such as DMX512. 

DMXTransmitter class
--------------------

The DMXTransmitter class must be installed. All users use it.

The DMXTransmitter class handles the care and feeding of a state
machine's hardware parameters. Every user will want to use methods provided
to start and stop the state machine, and upload new lighting parameters to the
state machine. Advanced users can configure up to three outputs
(DMX universes) per state machine, configure up to three timing outputs, and/or
clone the state machine.

DMXTransmitter objects automatically include a payload attribute, typically, a
Payload_USITT_DMX512_A object or equivalent to handle the DMX lighting and
timing parameters. See, below.

Payload_USITT_DMX512_A class
----------------------------

The Payload_USITT_DMX512_A class or a subclass must be installed. But is only
used by advanced users.

The Payload_USITT_DMX512_A class is a data structure that carries a DMX frame,
that is, all the lighting parameters and timing parameters that advanced users
may care about. Users that don't need to adjust the DMX timing parameters need
not be concerned about this class.

For advanced users: The Payload_USITT_DMX512_A class takes its name from the
DMX standard that it implements. By default all DMX timing parameters are the
minimum, or the recommended timing parameter if the standard recommends a
longer timing. The DMX timing parameters can be temporarily adjusted by
accessing the payload object in the DMXTransmitter object. Or if the timing
parameters need to be adjusted, say to be compatible with some legacy DMX
equipment, the Payload_USITT_DMX512_A class can be easily subclassed to use
different timing parameters.

assembly_code.py
----------------

assembly_code.py / assembly_code.mpy do NOT need to be installed.

For extra advanced users: The assembly_code.py script/library is the assembly
code that programs the state machine. Both the DMXTransmitter class and the
Payload_USITT_DMX_A classes have frozen parameters that are opaque lists of
numbers. The assembly_code.py script is where they were created, just in case
poring through assembly code is your idea of fun.
