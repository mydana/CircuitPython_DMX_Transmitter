EXAMPLES
========

Interactive use
---------------

.. code-block:: Python

   Adafruit CircuitPython 8.2.4 on 2023-08-22; Adafruit KB2040 with rp2040
   >>> import board
   >>> from dmx_transmitter import dmx_transmitter
   >>> DMX_PIN = board.D0
   >>> dmx = dmx_transmitter.DMXTransmitter(first_out_pin=DMX_PIN)
   >>> dmx.run()
   >>> dmx[0] = 255
   >>> dmx[1] = 255
   >>> 


blink.py
--------

.. code-block:: Python

    # SPDX-FileCopyrightText: Copyright (c) 2023 Dana Runge
    #
    # SPDX-License-Identifier: Unlicense
    "Blink a DMX-equipped light."

    import time
    import board

    from dmx_transmitter import dmx_transmitter

    # Wire DMX_PIN to an isolated RS485 line driver.

    DMX_PIN = board.D0

    dmx = dmx_transmitter.DMXTransmitter(first_out_pin=DMX_PIN)

    # Blinking lights
    while True:
        dmx.clear()  # Turn off the light(s)
        dmx.show()
        time.sleep(1)
        dmx[0:3] = 255  # Turn lights on full. DMX channels: 1, 2, 3,
        dmx.show()
        time.sleep(1)

    # Note: The dmx index numbers are one (1) less than the DMX channel
    #       number. This is by design.


fireworks.py
------------

.. code-block:: Python

   # SPDX-FileCopyrightText: Copyright (c) 2023 Dana Runge
   #
   # SPDX-License-Identifier: Unlicense
   "Implement a 'fireworks' effect."
   import time
   import random
   import board

   from dmx_transmitter import dmx_transmitter

   # Wire first_out_pin to the line driver.

   FIRST_PIN = board.D0

   dmx = dmx_transmitter.DMXTransmitter(first_out_pin=FIRST_PIN)

   # Configuration
   # Note: The dmx index numbers are one (1) less than the DMX channel
   #       number. This is by design.
   rockets = (1, 2, 3, 9, 10, 11)  # Slot numbers we want to show.
   main_dimmers = (
       0,
       8,
   )  # Slot numbers for the main dimmers

   # Setup
   tick = 0
   for slot in main_dimmers:
       dmx[slot] = 0xFF
   waxing = random.choice(rockets)
   waning = None

   # Fireworks!
   while True:
       time.sleep(0.1)
       tick = tick + 1
       if tick > 8:
           tick = 0
           waning = waxing
           waxing = random.choice([r for r in rockets if r != waxing])
       waxing_dim = pow(2, tick) - 1
       waning_dim = pow(2, 8 - tick) - 1
       if waxing is not None:
           dmx[waxing] = waxing_dim
       if waning is not None:
           dmx[waning] = waning_dim
       dmx.show()
