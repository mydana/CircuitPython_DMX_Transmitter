BASICS
======

DMX PERSONALITY
---------------
Every DMX light model may have a different DMX personality, that is, a
different purpose for each available channel. A your light's manual
should show the "DMX personality" for your light model.

This example table is the DMX personality of the lights used in the
code examples. Adjust the code examples for your light model.

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


PYTHON OBJECT INDEXING TUTORIAL
-------------------------------
This brief tutorial shows how a DMXTransmitter object is indexed. It's very
similar to a Python list, but there are a few differences. Fire up a
microcontroller if you want to follow-along, no wiring nor lights are needed
for this tutorial.

Set up the tutorial: A KB2040 is not required, any rp2040 board will work.

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
   KeyError('Index too large',)
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


MOST IMPORTANT METHODS
----------------------

Clear the DMXTransmitter object, set all slot values to 0.

    :meth:`clear()`

Take a snapshot of the DMXTransmitter object and send it down the wire.

   :meth:`show()`

Continuously send data down the wire.
   
   :meth:`run()`

Turn off the state machine and release its resources.

   .. Doc text copyright (c) 2021 Scott Shawcroft for Adafruit Industries

   :meth:`deinit()`
