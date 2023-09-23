BASICS
======

User population
---------------
"I can program a light show in Python? Cool!"

* Doesn't care how it works, as long as it does.
* One universe.
* Has memory to spare.
* Not satisfied just watching the blinking light, wants to program it.

Getting started
---------------
1. Buy an Adafruit microcontroller board built on the RP2040 chip.
   The DMX Transmitter needs one PIO (the RP2040 has two) and one GPIO pin.
2. Read the "Primary Guide" for the selected board on the Adafruit website.
   This guide helps you getting started on CircuitPython programming.
3. Install this library. Follow the Circup instructions in the main page,
   or put the dmx_transmitter folder and contained files into the
   CircuitPython lib folder.
4. Read, and follow along the 'Python Object Indexing Tutorial', below.

Python Object Indexing Tutorial
-------------------------------
This brief tutorial shows how a DMXTransmitter object is indexed. It's very
similar to a Python list, but there are a few differences. If you are new to
Python I recommend comparing and contrasting how the DMXTransmitter object
behaves from how a Python list behaves.

Fire up a microcontroller if you want to follow along, no wiring nor lights
are needed for this tutorial.

Set up the tutorial: A KB2040 is not required, any rp2040 board will work.
DMX_PIN is shown as board.D0 to conform with the example wiring schematic
you may use any available microcontroller pin you wish.

.. code-block:: Python

   Adafruit CircuitPython 8.2.4 on 2023-08-22; Adafruit KB2040 with rp2040
   >>> import board
   >>> from dmx_transmitter import dmx_transmitter
   >>> DMX_PIN = board.D0
   >>> dmx = dmx_transmitter.DMXTransmitter(first_out_pin=DMX_PIN)
   >>> dmx.run()
   >>>

Unlike Python lists, the DMXTransmitter object is already initialized to 0:

.. code-block:: Python

   >>> dmx[0]
   0
   >>>

By default, there are exactly 512 slots available: This is configurable in the
constructor.

.. code-block:: Python

   >>> len(dmx)
   512
   >>>

Notice that indexes range from 0 through 511: This contrasts from the DMX
standard, where slot numbers run from 1 through 512. There is an off-by-one
error when comparing DMXTransmitter object indexes and DMX addresses. This
is deliberate. This library follows Python semantics rather than DMX semantics
because Circuit Python is designed for teaching Python.

.. code-block:: Python

   >>> dmx[511]
   0
   >>> dmx[512]
   IndexError: Index too large
   >>>

Negative indexing is supported: Like Python lists, negative indexes start from
the end of the list,

.. code-block:: Python

   >>> dmx[-1] = 42
   >>> dmx[511]
   42
   >>>

Slicing is supported:

.. code-block:: Python

   >>> dmx[0:8]
   [0, 0, 0, 0, 0, 0, 0, 0]
   >>>

Slice assignment is allowed if the source and destination slices are the same
length:

.. code-block:: Python

   >>> dmx[0:5] = range(5)
   >>> dmx[0:8]
   [0, 1, 2, 3, 4, 0, 0, 0]
   >>>

Slice assignment is allowed if the source is a scalar integer: Such assignment
fills the slice with the scalar.

.. code-block:: Python

   >>> dmx[0:8]
   [0, 1, 2, 3, 4, 0, 0, 0]
   >>> dmx[0:3] = 42
   >>> dmx[0:8]
   [42, 42, 42, 3, 4, 0, 0, 0]
   >>>

Slice assignment with a different source length and destination length would
change the DMXTransmitter object length, and that is not allowed:

.. code-block:: Python

   >>> dmx[0:8] = range(5)
   ...
   ValueError: Can only assign a slice of the same size. (8)
   >>>

Values are exclusively integers between 0 through 255:

.. code-block:: Python

   >>> dmx[0:256] = range(256)
   >>>

Values can be expressed as any Python integer (in the range of 0-255). For
example, binary, octal, and hexadecimal values are all valid:

.. code-block:: Python

   >>> dmx[0] = 0b00001111
   >>> dmx[1] = 0o134
   >>> dmx[2] = 0xFF
   >>>


LIGHTING
========

Purchase an RS485 line driver and a female XLR connector::

         ┌─────┐            ╔═════════════════╗
    ╔════╡USB-C╞════╗       ║                 ║
    ║    └─────┘    ║    ┌──╫(6) VCC          ║       ╔══════════════╗
    ║            3V ╫────┤  ║    __         Y ╫───────╫─< (3) Data + ║
    ║               ║    ├──╫(1) RE           ║  ┌────╫─< (2) Data - ║
    ║               ║    │  ║               Z ╫──┘ ┌──╫─< (1) Common ║
    ║               ║    └──╫(4) DE           ║    │  ╚══════════════╝
    ║         TX/DO ╫───┐   ║               A ╫ NC │   XLR Connector
    ║               ║   └───╫(2) TXD          ║    │   Female
    ║               ║       ║               B ╫ NC │
    ║               ║    NC ╫(3) RXD          ║    │
    ║           GND ╫──┐    ║          ISOGND ╫────┴────┐
    ║               ║  └────╫(5) GND          ║      ┌──┴───┐
    ║               ║       ║                 ║      │Earth │
    ╚═══════════════╝       ╚═════════════════╝      │Ground│
     Microcontroller         RS485 Line Driver       └──────┘
     Adafruit KB2040         Digilent PmodR485

    Significant DMX wiring requirements are necessarily out of scope
    in this document. Consult a qualified local expert.


DMX Personality
---------------
Every DMX light model may have a different DMX personality, that is, a
different purpose for each available channel. A your light's manual
should show the "DMX personality" for your light model.

This example table is the DMX personality of the lights used in the
code examples. Adjust the code examples for your light's personality.

Code Examples DMX Personality::

    +-------------+--------+--------------------------+
    | DMX Channel | Python | Purpose                  |
    +=============+========+==========================+
    | Channel 1   | dmx[0] | Main dimmer              |
    | Channel 2   | dmx[1] | Red dimmer               |
    | Channel 3   | dmx[2] | Green dimmer             |
    | Channel 4   | dmx[3] | Blue dimmer              |
    | Channel 5   | dmx[4] | Strobe from slow to fast |
    | Channel 6   | dmx[5] | Color macros             |
    | Channel 7   | dmx[6] | Speed adjustment         |
    +=============+========+==========================+

* Observe that the Python 'dmx' object keys are one less than the
  corresponding DMX channel.

* Note that the terms 'channel', 'address', and 'slot', are practically
  synonymous with each other.

API Basics
----------
This manual shows an extensive API REFERENCE that illustrates the extensive
capabilities of this library. Basic uses will not use the bulk of it.

These are the most-used methods:

clear
   Clear the DMXTransmitter object, set all slot values to 0.

.. code-block:: Python

   >>> dmx.clear()
   >>>

show
   Take a snapshot of the DMXTransmitter object and send it down the wire,
   and thereby controlling the attached lights. Subsequent changes don't
   appear until the 'show' method is called again.

.. code-block:: Python

   >>> dmx.show()
   >>>

run
   Continuously send data down the wire, thereby controlling the attached
   lights. Subsequent changes will appear as soon as made.

.. code-block:: Python

   >>> dmx.run()
   >>>

deinit
   Turn off the state machine and release its resources.

.. deinit text copyright (c) 2021 Scott Shawcroft for Adafruit Industries

.. code-block:: Python

   >>> dmx.deinit()
   >>>

Blinkenlights
-------------
Check out the examples.
