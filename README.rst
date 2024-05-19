Introduction
============


.. image:: https://readthedocs.org/projects/circuitpython-dmx-transmitter/badge/?version=latest
    :target: https://circuitpython-dmx-transmitter.readthedocs.io/
    :alt: Documentation Status

.. image:: https://img.shields.io/discord/327254708534116352.svg
    :target: https://adafru.it/discord
    :alt: Discord


.. image:: https://github.com/mydana/CircuitPython_DMX_Transmitter/workflows/Build%20CI/badge.svg
    :target: https://github.com/mydana/CircuitPython_DMX_Transmitter/actions
    :alt: Build Status


.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black
    :alt: Code Style: Black

DMX512 lighting protocol transmitter on the RP2040

Usage Example
=============

.. code-block:: Python

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


Schematic
=========

Example::

>          ┌─────┐            ╔═════════════════╗
>     ╔════╡USB-C╞════╗       ║                 ║
>     ║    └─────┘    ║    ┌──╫(6) VCC          ║       ╔══════════════╗  
>     ║            3V ╫────┤  ║    __         Y ╫───────╫─< (3) Data + ║
>     ║               ║    ├──╫(1) RE           ║  ┌────╫─< (2) Data - ║
>     ║               ║    │  ║               Z ╫──┘ ┌──╫─< (1) Common ║
>     ║               ║    └──╫(4) DE           ║    │  ╚══════════════╝
>     ║         TX/DO ╫───┐   ║               A ╫ NC │   XLR Connector
>     ║               ║   └───╫(2) TXD          ║    │   Female
>     ║               ║       ║               B ╫ NC │
>     ║               ║    NC ╫(3) RXD          ║    │
>     ║           GND ╫──┐    ║          ISOGND ╫────┴────┐
>     ║               ║  └────╫(5) GND          ║      ┌──┴───┐
>     ║               ║       ║                 ║      │Earth │
>     ╚═══════════════╝       ╚═════════════════╝      │Ground│
>      Microcontroller         RS485 Line Driver       └──────┘
>      Adafruit KB2040         Digilent PmodR485

    Significant DMX wiring requirements are necessarily out of scope
    in this document. Consult a qualified local expert.

REQUIREMENTS
============
**Hardware:**

* `Any RP2040 CircuitPython board. I used the Adafruit KB2040
  <https://www.adafruit.com/product/5302>`_ (Product ID: <5302>)

* An isolated RS485 line driver. I used a Digilent PmodRS485.

**Software and Dependencies:**

* `Adafruit CircuitPython <https://github.com/adafruit/circuitpython>`_

* This library, dmx_transmitter, especially these files::

  * dmx_transmitter.mpy
  * payload_USITT_DMX512_A.mpy


Please ensure all dependencies are available on the CircuitPython filesystem.
This is easily achieved by downloading
`the Adafruit library and driver bundle <https://circuitpython.org/libraries>`_
or individual libraries can be installed using
`circup <https://github.com/adafruit/circup>`_.

Installing to a Connected CircuitPython Device with Circup
==========================================================

Make sure that you have ``circup`` installed in your Python environment.
Install it with the following command if necessary:

.. code-block:: shell

    pip3 install circup

With ``circup`` installed and your CircuitPython device connected use the
following command to install:

.. code-block:: shell

    circup install dmx_transmitter

Or the following command to update an existing version:

.. code-block:: shell

    circup update

Documentation
=============
API documentation for this library can be found on `Read the Docs <https://circuitpython-dmx-transmitter.readthedocs.io/>`_.

For information on building library documentation, please check out
`this guide <https://learn.adafruit.com/creating-and-sharing-a-circuitpython-library/sharing-our-docs-on-readthedocs#sphinx-5-1>`_.

Contributing
============

Contributions are welcome! Please read our `Code of Conduct
<https://github.com/mydana/CircuitPython_DMX_Transmitter/blob/HEAD/CODE_OF_CONDUCT.md>`_
before contributing to help this project stay welcoming.
