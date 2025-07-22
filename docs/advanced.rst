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

Optimize performance
====================
Reduce the number of slots
--------------------------

By default each Universe supports 512 slots. This number can be reduced in the
constructor. This reduces the load on resources as such::

  Each slot consumes 4 bytes of memory.

  Each slot consumes some of the microcontroller processing time.

  Each slot consumes 40 microseconds of time for each DMX512 packet.

Be aware that the DMX512 standard requires a minimum packet duration of
1204 microseconds, although your equipment probably doesn't care. See
the 'interval' property documentation, or more information about DMX Timing,
below.

Turn off double-buffering
-------------------------

By default the library double-buffers the DMX512 data, that means there are
two copies of the intermediate data structure, and that one is used for
editing the DMX512 slot data values, and the other one is used to show the
slot data values on the state machine, and play the data down the wire to
the lights. This is indicated by having the 'auto_write' property as False.
In this state, any changes will not visible until on the lights until the
'show' method is called. When that happens, the two buffers swap roles, the
one that was editing slot data will now show it, and vice-versa.

This swap takes time. There is a delay for the existing buffer to finish
playing down the wire before the other buffer can start, and there is also a
delay to copy slot values from one buffer to another.

If the 'auto_write' property is set True, then the library uses one buffer for
both editing and playing the data down the wire. This is significantly faster
because neither the delay nor the copy operation is needed. In this state
the 'show' method is ignored.

Double-buffering also consumes memory. There are two copies of the DMX512 data.
If the 'buffers' parameter in DXMTransmitter can be set to 1. If this done,
the library is forced to 'auto_write' to True, and double-buffering becomes
impossible.

The DMXTransmitter 'buffers' parameter can be set to more than 2 (the default)
more buffers are constructed, but the DMXPayload class won't use them.

How to implement multiple DMX512 Universes
==========================================
Implement multiple DMXTransmitter objects, one for each DMX512 Universe

In theory the designer can implement 8 DMX512 Universes for each RP2040,
and implement 12 DMX512 Universes for each RP2350, but a realistic
number may be significantly less.

This library uses an RP2040/RP2350 subsystem called the Programmable
Input/Output. (PIO) Each PIO hosts machine code memory that implements a
wire protocol, and four state machines that execute that machine code. These
state machines are in-turn connected to the microcontroller GPIO pins, with
one DMX512 universe for each 

If the applications' machine code is small enough, multiple different
applications can be shared within a PIO. However, this library's machine code
uses almost all of the available machine code, so that it's unlikely that an
another application can share the same PIO.


 Each PIO hosts machine code that defines a wire protcol,
and four state machines that executes the machine code. These state machines
are connected to microcontoller GPIO pins. In this library, each state machine
is connected to one 'dmx_output_pin', then subsequently to a line driver,
and ultimately to the controlled lights. (Timing pins, described below, also
connect to one state machine.)

What's important is that each PIO has one machine code memory that is shared
among all the state machines in that PIO. The code from this library
consumes almost all the available machine code memory, this practically means
that that a PIO used for this library cannot be re-used for another application.




This means that if one state machine is used for one DMX512 Universe, then four
state machines and therefore four DMX512 Universes are available. Further,
if five DMX512 Unverses are implemented, then state machines for eight DMX512
Universes are available.

Be aware, however, that other RP2040/RP2350 applications may also use PIOs, but
if the applications' machine code is small enough, the applications may be
shared together in one PIO. (This appears to happen with the RP2040. In a
preliminary test, I was able to load this library on a Adafruit Macropad even
though the Macropad uses a PIO for both driving the NeoPixels as well as the
rotary encoder.)

Also, be aware that this library itself implements five variants of the state
machine code. These are determined by the DMXTransmitter 'timing_pin_control'
class constructor parameter. If implemeting more than one Universe, a good
practice will be to use the same value for 'timing_pin_control' for each
Universe. If not, a RuntimeError indicating that no available state machines
may be raised.

Finally, the designer needs to consider the microcontroller performance, while
I've seen an RP2040 implement 8 universes in the benchmark tests that are
available in the source code, but I'm skeptical that a practical application
will have sufficient performance.

DMX TIMING
==========
Background
----------
DMX512 is an asychronous serial protocol. The first asynchronous serial
communication protocol was Morse code, and the telegraohy terms, "mark", "space"
and "break" used today still used today. A "mark" indicates that current is
flowing. A "space" means that current is not flowing, and a "break" means that
current has not be flowing for a longer time. In the days of the telegraph the
the difference between a "space" and a "break" might be measured in minutes,
whereas in DMX512 the difference is measured in microseconds.

Asynchronous means that the line may stay idle betwen messages, and may stay idle
between words as well. The line stays in the "mark" during idle periods. Both
protocols, Morse code and DMX512 also use breaks to indicate when a messsage is
coming. This is unusual for modern asynchronous serial protocols, most protocols
format data packets using headers in the data stream instead of a hardware break.
This incompatibility is why one cannot use a computer terminal to send DMX512
data.

After the break, called "SPACE FOR BREAK" in the specification, DMX512 sends up
to 513 bytes of data. The first byte indicates the data type. This called the
"NULL START" code in the specification. A null (a zero) indicates that the data
packet is dimmer (and other lighting accessory) values, as opposed to diagnostics
or other ancillary data.

Each byte is organzed into 11 bits of serial data, with each bit presented for
4 microseconds. The fist bit, the start bit, is a "space" indicating that a
word of data is forthcoming. The next 8 bits consist of a byte of data, least
significant bit first. Finally at least 2 bits for the stop bits, where the line
remains in "mark" state for at least 8 microseconds. The timing from the start
bit to the end bit is critical, but after that the line may remain idle for some
time, in a "mark" state, or the next byte of data may be sent.

This ability for the line to remain idle after the stop bits allows for some
adjustment of the DMX512 timing. Likewise, the standard allows for variable
timing of the break that starts each packet.

Adjustment
----------
By default, this library implements the minimum timings allowed by the standard,
except for SPACE FOR BREAK, which is set to the recommended duration of 172
microseconds.

All of the timings are implemented as properties of the DMXPayload class, and
are also visible in the DMXTransmitter class. The documenation for each property
tells you the default, the minimum allowed, the maximum allowed, and if not
already at the default, the duration recommended by the standard. All values
are in microseconds.

.. code-block:: Python

   >>> dmx.space_for_break
   172
   >>> dmx.space_for_break = 88
   >>> dmx.space_for_break
   88
   >>>

Minimum DMX512 packet duration
------------------------------
Be aware that the DMX512 standard requires a minimum packet duration of
1204 microseconds, although your equipment probably doesn't care.

There is a read-only property available, 'interval' that shows the calculated
DMX512 packet duration. The only way to adjust the duration is to change the
DMX512 timing properties, or to increase the number of slots up to 512.

Timing pins
===========
The state machines have a feature called sideset pins. Roughly, these are bits
that may be added to the machine code, and as each instruction is executed, the
bit values are sent out to additional pins. This library implements up to two
sideset pins:

* Transmitter enable, and
* Oscilloscope sync

Transmitter enable
------------------

If the timing_out_control parameter is set to True or 1, one timing pin is
implemented it is the transmitter enable pin. This pin can be connected to
the line driver circuit enable input. This feature can be used to switch
the DMX Universe from one transmitter to another. The stop method will stop
the state machine, and disable the connected line driver.

This is advanced feature only for an advanced DMX hacker.

If the timing_out_control parameter is set to False or -1, the same timing
pin is implemented, but the logic is complemented.

This pin is set by the timing_out_pin parameter.

Oscilloscope sync
-----------------

If the timing_out_control parameter is set to 2, then two timing pins are
implemented, the first pin is the same transmitter pin, as descibed above.
The second pin is an oscilloscope sync pin. This pin is asserted during
MARK AFTER BREAK.  The intent is to use a digital oscilloscope to verify that
the timing is what it says it is.

If the timing_out_control parameter is set to -2, then the same two timing
pins are implemented, but the logic of both pins is complemented.

The two pins need to be consecutive. The first pin is the Transmitter enable,
and is specified by the timing_out_pin parameter. The second pin is not
specified by the library, instead the hardware automatically uses the next
pin in sequence.

If the timing_out_control parameter is not set, then no timing pins are
implemented.

Warning when implementing multiple DMX512 Universes
---------------------------------------------------
Be aware of a technical limitation. If you intend to implement timing pins and
implement multiple DMX512 Universes, all Universes handled by the same PIO need
to have the same value for the timing_out_control parameter. See above.

This limitation can cause unexpeced RuntimeError problems when debugging.

How this library works
======================
This library consists of three modules:

* dmx_transmitter.py aka dmx_transmitter.mpy
* dmx_payload.py aka dmx_payload.mpy
* machine_code.py aka machine_code.mpy

Together these allow an RP2040 (and presumably an RP2350) microcontroller's
Programmable I/O (PIO) peripheral to output a DMX512 serial data stream.

dmx_transmitter/machine_code.py is a machine-generated python library that contains
three objects:

1. A class that contains variations of the assembled machine code that runs the
PIO.

2. A function that synthesizes the pio_kwargs that Adafruit's assembler would
output.

3. A class that contains timing constants for various phases of the DMX waveform.

In order to write PIO assembly code, a developer needs to be mindful of both
the logic and the timing. This is difficult. To make it easier this developer
used a spreadsheet program to use a pivot table to keep track of timings while
focusing on the desired logic. While this program was not originally written
in LibreOffice calc, it was copied to that application for sharing on GitHub,
and can be found in the source code in the assembly_code folder.

Since the timing was already available in the spreadsheet, this developer created
a tool, reformat_pioasm, to assemble the machine code using Adafruit's assembler,
and output the objects mentioned above in the dmx_transmitter/machine_code.mpy
file.

Finally, this tool also allows the developer to defer TODO


* The ultimate source is in assembly_code/assembly_code.fods this file is the
  assembly code in a LibreOffice document.
* The next file, assembly_code/assembly_code.tsv is a text-separated file
  exported from the LibreOffice document.
* A script assembly_code/reformat_pioasm.py that uses Adafruit's assemble to
  assemble it, and writes the output into dmx_transmitter/machine_code.
* The makefile contains all the commands to build the machine code.









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
----------------------------------
Please open a ticket on GitHub and start a conversation with me about this.
It's probably doable, but I'm interested in discussing the coding strategy
before proposing a pull request. I'm also just curious about your use case.
