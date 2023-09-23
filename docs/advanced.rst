ADVANCED USAGE
==============

The story so far::

    In the beginning the Universe was created.  This has made a lot of people very
    angry and been widely regarded as a bad move.
        -- Douglas Adams, "The Restaurant at the End of the Universe"

User population
---------------
* Wants to squeeze out every byte out of the available memory.
* Wants to allocate fewer slots per universe.
* Wants multiple universes. (Theoretical limit: 24 universes.)
* Wants to control the DMX timing.
* Wants to use a pre-built DMX timing.
* Wants to create a pre-built timing to share.

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

Sharing the DMX Timing
----------------------
Say through extensive experimenting you'd dialed in the perfect DMX timing
for an obscure piece of equipment, and you'd like to save and/or share it?

You want a subclass of Payload_USITT_DMX512_A. For example:

.. code-block:: Python

   import Payload_USITT_DMX512_A

   class PayloadMyDMXTiming(Payload_USITT_DMX512_A):
       """My documentation.
       """
       def _init_timing_defaults(self) -> None:
           "Set up my DMX timings."
           # fmt: off
           self.mark_after_frame = False
           self.mark_after_frame_default = 8  # last slot mark, for stopping
           # Set mark_after_frame before setting mark_before_break.
           self.mark_before_break = 8
           self.space_for_break = 88  # Was 172
           self.mark_after_break = 12
           self.mark_after_start_code = 8
           self.mark_between_slots = 8
           # fmt: on

Put that code into a file called 'PayloadMyDMXTiming.py' into the
lib/dmx_transmitter folder. Then activate in your code as such:

.. code-block:: Python

    import PayloadMyDMXTiming

    dmx = DMxTransmitter(payload_class=PayloadMyDMXTiming, first_out_pin=...

Please choose a more descriptive name, but please start the subclass with Payload,
and please name the file after the class, and please write a good desription
in the documentation strings. Doing that, please contribute it to this library.

RESOURCES
=========

Slots
-----
The slots parameter on the USITT_DMX512_A constructor, and also forwarded
from the DMXTransmitter constructor, configures how many slots of data
are available for each universe. The maximum is 512, as is the default.

Universes
---------
Each state machine can drive up to three universes by setting the universes
parameter in the DMXTransmitter constructor. (Default 1) Each state machine
requires a GPIO output pin for each universe. The GPIO pins need to be in
consecutive order. For example first_out_pin is GPIO2, and universes is 3,
then the universes will be connected to pins GPIO2, GPIO3, and GPIO4.

Indexing length
---------------
In the Basic Usage section 'Python Object Indexing Tutorial' it mentions that
the object's length is fixed to 512, but that it can be adjusted in the
constructor. The length is the product of the number of slots time the
number of universes. The slots are in slot-major order. In other words,
the indexing order runs through all the slots of universe 0 before
starting with universe 1.

Cloning
-------
A DMXTransmitter object can be cloned. A cloned object needs a new set of
GPIO pins (depending on how many univereses in the parent). The clone is a
new state machine, and a new payload object. As such it can be stopped
and started separately from the parent. It can also have a different number
of slots than the parent. It cannot have a different number of univereses,
because clones share the same running machine code.

Up to four clones can be built on one PIO (1 original constructed, and 3 cloned).
If more clones are attempted, these will succeed only if the other PIO is
not in use by amother application. If available up to eight clones may be
built total (1 original constructed, 3 one PIO and 4 other PIO).

Yes, in theory, this library can drive 24 DMX Universes, but i doubt it.
There may be other limits. I don't have the resources to find out.
