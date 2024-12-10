ADVANCED USAGE
==============

The story so far::

    In the beginning the Universe was created.  This has made a lot of people very
    angry and been widely regarded as a bad move.
        -- Douglas Adams, "The Restaurant at the End of the Universe"

User population
---------------

* Wants to squeeze out as much performance as possible.
* Wants to implement multiple DMX512 Universes.
* Wants to know the technical details of this library.
* Wants to control the DMX timing.
* Wants to pre-set alternative DMX timing.
* Wants to implement Alternate START Codes.
* Wants to implement half-duplex communication.
* Wants to hook up an oscilloscope.

How to squeeze more performance
-------------------------------
Reduce the number of slots.

Each slot consumes 4 bytes of memory, consumes time manipulating the data, and
40 microseconds for each DMX packet. While the DMX512 standard requires a
minimum packet time of 1204 microseconds, your equipment probably doesn't care.
See the interval property interval in the API Reference for more information.

This library runs the output at the fastest speed allowed by the standard, except
for the SPACE_FOR_BREAK timing, which is set to the recommended timing. The
property space_for_break can be lowered from 172 microseconds to 88 microseconds
without breaking the standard. The library allows it to be lowered further, but that
violates the standard.

Each byte also implements 2 stop bits, 8 microseconds. Much equipment can be run
faster, with only 1 stop bit, 4 microseconds implemented. This library also allows
that, but doing so is also a violation of the standard.

How to implement multiple DMX512 universes
------------------------------------------
Implement multiple DMXTransmitter objects.

The RP2040 features 2 PIOs, and the RP2030 features 3 PIOs. Each PIO has four
state machines that share the same machine code. These state machines feature
sideset pins. These are implemented as 'timing pins' in this library. A PIO
can implement zero, one, or two timing pins, and if implemented, can implement
normal or inverted logic, for five possible combinations. But, given that the
time pin combinations are codes in the machine code, all state machines
in a PIO are required to implement the same configuration of timing pins.

The CircuitPython PIO library that this library is built on intelligently
assigns state machines to group state machines to those who are executing the
same machine code, but the RP2040 can only implement two combinations of timing
pins (the RP2350, three). If a RuntimeError is thrown, check the combinations
of timing pins, especially during debugging.

How it works
------------
This library consists of three modules:

* dmx_transmitter
* dmx_payload
* machine_code

together these allow a RP2040 (and a presumably RP2350) microcontroller's Programmable
I/O (PIO) peripheral to output a DMX512 serial data stream.

dmx_transmitter/machine_code is a machine-generated python library that contains three objects:

1. A class that contains variations of the assembled machine code that runs the PIO.

2. A function that synthesizes the pio_kwargs that the assembler would output.

3. A class that contains timing constants for various phases of the DMX waveform.

While machine_code is machine-generated, the source code is available in source
the package, in the assembly_code folder.

* The ultimate source is in assembly_code/assembly_code.fods this file is the
  assembly code in a LibreOffice document.
* The next file, assembly_code/assembly_code.txt.csv is a text-separated file
  exported the LibreOffice document.
* A script assembly_code/reformat_pioasm formats, assembles it, and writes the
  output into dmx_transmitter/machine_code.
* The makefile contains all the commands to run this pipeline, and others.

This pipeline was implemented to tie timing information with the assembly code in
a way that's easy for the developer to work on the logic and the timing. It also
postpones the sideset pin count decision to the end user, while removing
the requirement for the end user to install adafruit_pioasm.

dmx_transmitter/dmx_payload contains one class, DMXPayload, that contains two
buffers containing a data structure needed for sending data to the machine code.
This data structure contains data, timing, and slot count data, but it's
formatted in an unobvious way that is suitable for the machine code. The class
fixes that by implementing properties and methods that are friendly for a
Python developer, and implementing methods helpful for the dmx_transmitter
object.

This class can be subclassed to update permanently update DMX512 timings, and can
be instantiated to create a stand-alone buffer that may be used to implement
DMX512 Alternate START Codes. These Alternate START Codes can implement DMX512
packets that contain other data types, such as text, and test packets. None of
these are supported in this library, but may be extended to implementing these
is desired.

dmx_transmitter/dmx_transmitter contains one class, DMXTransmitter, that handles
the care and feeding of the state machine. This is a superclass of DMXPayload,
so also inherits all the methods of that class.

DMX TIMING
==========
By default, this library implements the USITT DMX512-A standard timings.
All timings are the minimum, except for SPACE FOR BREAK which is at the
recommended timing of 172 microseconds.

Unfortunately, not all equipment in the field is compatible with the standard.

By default the DMXTransmitter constructs a payload object, which by default is
Payload_USITT_DMX512_A. This object has properties that allows the adjustment
of the DMX timing. For example:

.. code-block:: Python

   >>> dmx.space_for_break
   172
   >>> dmx.space_for_break = 500
   >>> dmx.space_for_break
   500
   >>>

Any timing adjustment are made on all buffers in the DMXPayload objecct.

All available timing parameters are available in the API Reference section
see the DMXPayload class subsection.

Warning: The parameters can be set such that the DMX frame's timing no longer
meets DMX512 standards. Check the documentation on the interval property in
the API Reference for more information.

Note: The DMX512 standard allows for very long packets, and this library allows
very long timing intervals up to 65 microseconds for some intervals, and in
excess of 250 miliseconds for each each slot's stop bits (normally 8). Although
the standard and the library allows very long delays, some equipment may not
accept these. Attempt to assign a negative integer to a timing parameter to get
a ValueError that indicates the accepted timing ranges for that parameter.

PRESET DMX TIMING
-----------------
Subclass DMXTransmitter or DMXPayload and implement a method called
init_timing_defaults. In that method set up these timing parameters:

* mark_after_frame_stop (default 50 microseconds)
* mark_before_break (default 8 microseconds)
* space_for_break (default 172 microseconds)
* mark_after_break (default 8 microseconds)
* mark_after_start_code (default 8 microseconds)
* mark_between_slots (default 8 microseconds)

IMPLEMENTING ALTERNATE START CODES
==================================
Please open a ticket on GitHub and get into a conversation with me about this.
It's probably doable, but I'm interested in discussing the coding strategy
before proposing a pull request.

IMPLEMENTING HALF-DUPLEX COMMUNICATION
======================================
The state machines implement a sideset capability, that is where pins can
be requested that indicate progress through the machine code. This program
supports two, one for half-duplex, and the other for an oscilloscope. These
are called timing pins.

For half-duplex communication, select a GPIO pin, assign it to the timing_out_pin
parameter. Connect the GPIO pin to the enable pin of the line driver. Set the
timing_out_control parameter to False, True, 1 or -1 depending on if the desired
logic should be inverted or not.

TODO - What is the logic???

The timing_out_control parameter can also be set to 2 or -2, but that will also
implement an oscilloscope timing pin, see below.

Note: How to coordinate among different transmitters is out-of-scope of this
library. Also, there are electrical concerns of active termination needed to
coordinate among different transmitters on the same DMX Universe. Good luck.

USE AN OSCILLOSCOPE
===================
The state machines implement a sideset capability, that is where pins can
be requested that indicate progress through the machine code. This program
supports two, one for half-duplex, and the other for an oscilloscope. These
are called timing pins.

For using an oscilloscope, select two adjacent GPIO pins, assign the lower
numbered to the timing_out_pin parameter. Ignore this one, it's used for half-
duplex as seen above. Attach the second GPIO pin to your oscilloscope's trigger
input. Set the timing_out_control parameter to 2 or -2 depending on if the logic
should be inverted or not.

TODO - What is the logic???

This pin will toggle state during the MARK AFTER BREAK period starts, and
again toggles after the MARK AFTER BREAK period ends, and the START Code (the
start of the data) begins.
