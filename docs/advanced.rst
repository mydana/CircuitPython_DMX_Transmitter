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

  Each slot consumes 40 microseconds from each DMX512 packet.

Be aware that the DMX512 standard requires a minimum packet duration of
1204 microseconds, although your equipment probably doesn't care. See
the 'interval' property documentation, or more information about DMX Timing,
below.

Switch from auto_write = False to auto_write = True
---------------------------------------------------

By default the library double-buffers the DMX512 data. Requiring the 'show'
method for pending changes to become visible. Each show operation swaps one
buffer for showing to another for editing. This swap consumes time, but also
the show buffer needs to be copied to the edit buffer, which takes more time.

If auto_write is set to True, only one buffer is used, and any changes go
directly to the one buffer that is also shown to the state machine.

auto_write may be changed in the constructor, but can also be changed by
setting the auto_write property.

How to implement multiple DMX512 Universes
==========================================
Implement multiple DMXTransmitter objects.

This library uses an RP2040/RP2350 subsystem called the Programmable
Input/Output. (PIO) Each PIO has machine code, and four available state machines.
The RP2040 contains two PIOs, and the RP2350 contains three PIOs. Note
that the PIO shares the same machine code for each state machine.

In theory the designer can implement one DMX512 Universe for each state machine,
therefore an RP2040 can implement 8 DMX512 Universes, and the RP2350 can
implement 12 DMX512 Universes. A realistic number may be significantly less.

First, the designer needs to consider the microcontroller performance, it
might be possible that an RP2350 can indeed drive 12 Universes for generally
static lighting, such as architectural lighting. However, although the benchmark
tests that I'd run on an RP2040 did instantiate 8 DMXTransmitter objects, I've
not tested them actually running lighting on any more that one Universe at one
time. If you do this test, let me know the results.

The shared machine code may also significantly reduce the number of PIOs
available. For example, the neopixel (R) library on the RP2040 consumes one PIO,
therefore if that library is instantiated, then the maximum number of Universes
drop to 4. This is true for any library that uses a PIO.

Another concern for shared machine code comes into play with the DMXTransmitter
class itself. Internally, the library implements 5 varients of machine code, one
for each combination of 5 possible timing_out_control values. Timing pins are
implemented as PIO sideset pins, and have to be accounted for in the code.
Therefore all state machines sharing a PIO need to have the same
timing_out_control values. Because of this, a consequence of changing the
timing_out_control of one state machine, and not changing it other state machines
may cause the code to fail with a RuntimeError with all state machines in use.

DMX TIMING
==========
By default, this library implements the USITT DMX512-A standard timings.
All timings are the minimum, except for SPACE FOR BREAK which is at the
recommended timing of 172 microseconds.

DMX512 is an asychronous serial protocol. Electronically the output is normally
high, and sends pulses of low of defined durations to send data to the
attached equipment. (Because DMX512 is a balanced protocol one wire is high when
the other is low and vice-versa. We'll only consider one wire.) A high state is
refered to a 'mark' state, and a low state is referred to a 'space' state. An
extended low state is referred to a 'break'. (These names came from Morse's
telegraph.)

The DMX512 transmitter repeatedly sends serial data in packets. Each packet
starts with a header, consisting of a mark before break, a break, and a mark
after break. Following the header, there is a start code, followed by slot data.
All header sections are adjustable.

The start code, and slot data are 8 bits of data, preceeded by one start bit (a
space), followed by two stop bits (each a mark), all of each are 4 microseconds
in duration. The start bit, and the data bits are not adjustable, but the stop
bits are. Stop bits may be "stretched" by adding additional time between each
byte of slot data and between the start code and the slot data.

These adjustments are implemented as properties of the
DMXPayload class, and are also visible in the DMXTransmitter class. The
documenation for each property tells you the default, the minimum allowed,
the maximum allowed, and if not already at the default, the recommended
timing from the DMX512 standard. All durations are in microseconds.

.. code-block:: Python

   >>> dmx.space_for_break
   172
   >>> dmx.space_for_break = 500
   >>> dmx.space_for_break
   500
   >>>

Setting the timing duration below the standard
----------------------------------------------
While the libary allows for setting durations less than the minimums, you might
want to do so to make the system more responsive. However, reducing the number
of slots, descibed above, will also make the system more responsive. Be aware,
setting timings below recommended minimums is not recommended, and may make your
DMX Universe unreliable.

If you do want to reduce the timing, reduce the space_for_break, because the
default duration is longer than what's required.

Minimum DMX512 packet duration
------------------------------
Be aware that the DMX512 standard requires a minimum packet duration of
1204 microseconds, although your equipment probably doesn't care.

There is a read-only property available, 'interval' that shows the calculated
DMX512 packet duration. The only way to adjust the duration is to change the
DMX512 timing properties, or to increase the number of slots up to 512.

Setting the timing duration above above the standard
----------------------------------------------------
Some, presumably older equipment is not exactly compatible with DMX512, some
additional padding is needed. There is an art to adjusting these timings, and
I welcome a Pull Request to elaborate what the best strategies are.

Be aware too, that the library allows for long padding durations,
260 microseconds (default 8 microseconds) between byte of slot data, and a
header length in excess of 150,000 microseconds (default 188 microseconds).
While the DMX512 standard allows these durations, some equipment may balk
at durations this long.

Timing pins
===========
The state machines have a feature called sideset pins. Roughly, these are bits
that may be added to the machine code, and as each instruction is executed, the
bit values are sent out to additional pins. This library implements up to two
sideset pins::

  Transmitter enable::

    If the timing_out_control parameter is set to True or 1, one timing pin is
    implemented it is the transmitter enable pin. This pin can be connected to
    the line driver circuit enable input. This feature can be used to switch
    the DMX Universe from one transmitter to another. The stop method will stop
    the state machine, and disable the connected line driver.

    This is advanced feature only for an advanced DMX hacker.

    If the timing_out_control parameter is set to False or -1, the same timing
    pin is implemented, but the logic is complemented.

    This pin is set by the timing_out_pin parameter.

  Oscilloscope sync::

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
Be aware that if you intend to implement timing pins and use multiple
DMX512 Universes, all Universes handled by the same PIO need to have
the same value for the timing_out_control parameter. This is because
the timing_out_control parameter chooses the version of the machine
code to run on the state machine, and all state machines on the same
PIO need to run the same machine code.

This limitation can cause unexpeced RuntimeError problems when debugging
multiple DMX512 Universes.

How this library works
======================
This library consists of three modules:

* dmx_transmitter
* dmx_payload
* machine_code

together these allow an RP2040 (and presumably an RP2350) microcontroller's
Programmable I/O (PIO) peripheral to output a DMX512 serial data stream.

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
