GLOSSARY
========
* Address, channel, slot - the index number of a value sent via the DMX
  protocol.

* Assembly code - machine code in a (somewhat) human-readable form.
  Unlike higher-level languages, each one operation in assembly code
  corresponds with one machine code operation, and therefore one operation by
  the state machine hardware.

* Asynchronous - Data sent without a specific inter-byte timing. Each DMX byte
  is framed with a stop bit (4 microseconds), then 8 bits of data
  (8 * 4 microseconds) and two stop bits (2 * 4 microseconds). The timing of
  each byte is defined (11 * 4 microseconds) but the idle time beteen bytes
  is not defined.

* Bit - the fundamental unit of binary data, 1 or 0, high or low, mark or space. 
  Each DMX bit is 4 microseconds long.

* Break - a term from telegraphy, and also used for asyncronous serial
  communication. It indicates the line is off for an extended time, and
  corresponds to a logic low. A break indicates a new DMX frame is starting.

* Byte - a unit of data consisting of 8 bits, DMX has one byte per slot, and
  is represented as an integer between 0 through 255. Each byte is sent down
  the wire preceding a start bit, then 8 bits of data then two stop bits.

* Channel, address, slot - the index number of a value sent via the DMX
  protocol.

* DMX512 - Digital Multiplex with 512 slots.
  A standard digital theatrical lighting protocol. It's also used for
  architectural lighting, and other non-lighting devices.

* Line driver - hardware that converts electrical levels from logic levels to
  RS485 levels. For a DMX network an isolated line driver is advised. This is
  to isolate the DMX wiring from the microcontroller and any connected
  computer, the DMX network may still need to be grounded.
  See local experts for advise about proper wiring and grounding.

* Machine code - the actual opcodes (operation codes) that the state
  machine executes.

* Mark - a term from telegraphy, and also used for asyncronous serial
  communication. It indicates the line is on, and corresponds to a logic high.

* PIO - Programmable I/O hardware
  A subsystem of the RP2040 microcontroller. There are two PIO in each RP2040.
  Each implement four state machines, program memory, clocks, and registers to
  be configured for different hardware protocols.

* RDM - Remote Device Management.
  A protocol for sending bi-directional communication from a light or other
  device and the controller.
  This library doesn't support RDM as-is, but it is designed to be subclassed
  for RDM frame writing.

* RS485 - the asynchronous serial protocol that DMX is built on.

* Slot, address, channel - the index number of a value sent via the DMX
  protocol.

* Space - a term from telegraphy, and also used for asyncronous serial
  communication. It indicates the line is off for a short time, and
  corresponds to a logic low.

* Start bit - a low bit (space) that ends a mark, and indicates that a byte of
  data will follow. all DMX start bits are 4 microseconds long, and are
  implemeted in the machine code.

* State machine - the hardware that formats the DMX data into serial data for
  sending down the wire.

* Stop bit - a high bit (mark) that ends a byte of data. DMX stop bits are
  4 microseconds long, but DMX has two stop bits, therefore 8 microseconds are
  allocated for the stop bits. Given that the stop bits follow a variable
  idle time (possibly 0) the transition from the end of the stop bits and the
  start of the idle period is not visible in an oscilloscope trace.

  In this library, any timing parameter that defines an idle after stop bits,
  includes the duration of the stop bits as well as any idle time.

* Universe (DMX) - the set of addresses and values sent down one cable. Also
  could refer to the cable, lights, and other hardware connected to that
  cable.
