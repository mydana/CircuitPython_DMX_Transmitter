# SPDX-FileCopyrightText: Copyright (c) 2023 Dana Runge
#
# SPDX-License-Identifier: MIT
"""
`dmx_transmitter.dmx_payload`
========================================

This module attempts to implement the data protocol standard for::

    American National Standard
    ANSI E1.11 –– 2008 (R2018)
    Entertainment Technology––-USITT DMX512-A
    Asynchronous Serial Digital Data
    Transmission Standard for Controlling
    Lighting Equipment and Accessories

    ANSI Document number: CP/2007-1013r3.1

aka DMX512 or DMX.

"""

import array

from .machine_code import IntervalTimings

__author__ = "Dana Runge"
__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/mydana/CircuitPython_DMX_Transmitter"

assert 4 == IntervalTimings.START, "Start bit SHALL be 4 µS"
assert 4 == IntervalTimings.DATA, "Data bit SHALL be 4 µS"
assert (
    IntervalTimings.ASTART == IntervalTimings.ATSTART
), "Clean transition to terminal slot."
assert 4 == IntervalTimings.TSTART, "Terminal start bit SHALL be 4 µS"
assert 4 == IntervalTimings.TDATA, "Terminal data bit SHALL be 4 µS"

# TODO CI fails

# TODO Oscilloscope validation.
# TODO timing logic sense.
# TODO verify the sideset pin configuration


class DMXPayload:  # pylint: disable=too-many-instance-attributes
    """Data Payload for the RP2040/RP2350 PIO state machine.

    The RP2040/RP2350 does not implement DMX512 directly, instead this library
    implements machine code in state machines in the Programmable I/O (PIO)
    peripheral. Unfortunately, that machine code cannot directly implement
    DMX512 either, instead that machine code consumes a data structure that
    combines data, timing, and quanity data usable by it.

    This class implements that data structure, and gives the user an interface
    that is friendly for Python programmers.

    Unlike DMX512 which is 1-based, this object is 0-based, just like Python
    lists. Therefore there is an inherent off-by-one error between DMX slot
    addresses and this object's indeces.

    This class is a superclass to the dmx_transmitter class, and implements much
    of the public interface. As such, it can also carry two copies of the data
    structure so that dmx_transmitter can implement double-buffering.

    For more advanced users, this class can be subclassed to create classes that
    implement alternative DMX timings, or Alternate START Codes.

    Caution: Several timing parameters include the stop bits. To meet the
    DMX standards include at least 8 microseconds in these parameters.

    * Author: Dana Runge

    """

    HEADER_SIZE = 4  # This many 16-bit words in the header.
    MIN_SLOTS = 1  # Offset of slot count in the header vs the user code.
    # This offset is a consequence of the machine code structure.
    MAX_SLOTS = 512  # This limit is defined in the DMX512 specification.
    START_CODE = 0x00  # This is the value that indicates this DMX512 packet
    # contains "dimmer" information. Consider this to be
    # the user data packet. This value is from the
    # DMX512 protocol specification.

    ## Buffer structure. This is the buffer that is sent the state machine.
    ##
    ## Header (16 bit words)
    ##      0 - mark_before_break (microseconds)
    ##      1 - space_for_break (microseconds)
    ##      2 - mark_after_break (microseconds)
    ##      3 - Number of slots, less MIN_SLOTS.
    ##
    ## Payload (8 bit bytes)
    ##   This section alternates between slot data and inter-slot
    ##   mark time. This time includes the required stop bit. (8 microseconds)
    ##          0  - The start code. This indicates the DMX512 packet data type.
    ##          1  - Mark time after the start code.
    ##          2  - The first data code. DMX512 slot #1 is here.
    ##          3  - Mark time after the first data code.
    ##     even 4+ - Remaining DMX512 slots.
    ##     odd  5+ - Mark time after the corresponding data code.
    ## penultimate - Last DMX512 slot.
    ##        last - mark_after_frame
    ##               Time before state machine shuts down.
    ##               If stop (shut down) is not commanded, then this value is 0.
    ##

    def __init__(
        self,
        slots=None,
        buffers=1,
    ):
        """
        construct a DMX payload state machine data structure.

        :param int slots: number of slots of DMX data available. (count)
            Consumes two bytes per slot per buffer.
            Minimum: 1. Default: 512. Maximum: 512.

        :param int buffers: how many data structures to implement.
            Minimum: 1. Default: 1
        """
        #
        # slots
        slots = int(slots) if slots is not None else self.MAX_SLOTS
        if slots < self.MIN_SLOTS:
            raise ValueError(
                f"'slots' is too low. Shall be {self.MIN_SLOTS} to {self.MAX_SLOTS}"
            )
        if slots > self.MAX_SLOTS:
            raise ValueError(
                f"'slots' is too high. Shall be {self.MIN_SLOTS} to {self.MAX_SLOTS}"
            )
        self.num_buffers = buffers
        self.edit_buffer = 0  # User-facing data.
        self.show_buffer = (
            1 if self.num_buffers > 1 else 0
        )  # Buffer for the state machine.

        #
        # Create buffers and memoryviews
        my_buffer_length = (
            self.HEADER_SIZE  # Size of the buffer
            + 1  # Space for the start code
            + slots  # How much user data
        )
        my_array = array.array(
            "H", (0 for _ in range(my_buffer_length * self.num_buffers))
        )
        self.buffers = tuple(
            memoryview(my_array)[b * my_buffer_length : (b + 1) * my_buffer_length]
            for b in range(self.num_buffers)
        )
        self.headers = tuple(b[0 : self.HEADER_SIZE] for b in self.buffers)
        self.payloads = tuple(b[self.HEADER_SIZE :].cast("B") for b in self.buffers)

        #
        # Initialize the newly-created array
        for header in self.headers:
            header[3] = slots - self.MIN_SLOTS
        self.init_timing_defaults()
        # Set up the start code.
        for payload in self.payloads:
            payload[0] = self.START_CODE

    def init_timing_defaults(self) -> None:
        """Intialize the USITT DMX512-A timing defaults.

        Override this method to set different timings.
        """
        # fmt: off
        self.mark_after_frame_stop = 50  # last slot mark time, for stopping
        # Set mark_after_frame before setting mark_before_break.
        self.mark_before_break = 8      ## header[0]
        self.space_for_break = 172      ## header[1]
        self.mark_after_break = 8       ## header[2]
        # slot count                    ## header[3]
        # NULL START CODE               ## payload[0]
        self.mark_after_start_code = 8  ## payload[1]
        self.mark_between_slots = 8     ## payload[odd] except last payload.
        # fmt: on

    @property
    def auto_write(self):
        """Enable or disable auto_write.

        If auto_write is True: Changes appear right away.
        If auto_write is False: Call .show() for changes to appear.
        """
        if self.buffers == 1:
            return True
        return self.edit_buffer == self.show_buffer

    @auto_write.setter
    def auto_write(self, val):
        if val:
            # Turn on auto_write
            self.edit_buffer = self.show_buffer
        else:
            # Turn off auto_write
            if self.num_buffers < 2:
                raise ValueError("Not enough buffers to implement auto_write")
            # The edit_buffer will be 0 or 1, opposite than the show_buffer
            self.edit_buffer = 0 if self.show_buffer else 1
            # Copy show buffer to the edit buffer.
            self.buffers[self.edit_buffer][:] = self.buffers[self.show_buffer][:]

    def _send_init(self, callback):
        """Internal method for sending data to the state machine.

        Used to implement the .reinit() method."""
        callback(loop=self.buffers[self.show_buffer])

    def _send_show_buffer(self, callback):
        """Internal method for sending data to the state machine.

        Used to implement the .show() method."""
        if self.edit_buffer != self.show_buffer:
            # Swap buffers
            self.edit_buffer, self.show_buffer = (self.show_buffer, self.edit_buffer)
            # Send the new show buffer
            callback(loop=self.buffers[self.show_buffer])
            # Copy show buffer to the edit buffer.
            self.buffers[self.edit_buffer][:] = self.buffers[self.show_buffer][:]

    def _send_stop_buffer(self, callback):
        """Internal method for sending data to the state machine.

        Used to implement the .stop() method."""
        if self.edit_buffer == self.show_buffer:
            # autowrite is True, we'll use an unused buffer.
            stop_buffer = 0 if self.show_buffer else 1
        else:
            # autowrite is False, we'll reset the edit buffer.
            stop_buffer = self.edit_buffer
            # Copy show buffer to unused buffer.
        # Copy show buffer to stop buffer
        self.buffers[stop_buffer][:] = self.buffers[self.show_buffer][:]
        # Start stop
        self.buffers[stop_buffer][-1] = (
            self.mark_after_frame_stop - IntervalTimings.MAF - IntervalTimings.WAIT
        )
        callback(once=self.buffers[stop_buffer], loop=array.array("H", []))

    @property
    def mark_before_break(self) -> int:
        """Timing from the last frame to before the SPACE FOR BREAK.
        (microseconds)

        Minimum 5. Default 8. Maximum 65540.
        """
        return (
            self.headers[self.show_buffer][0]
            + IntervalTimings.MBB
            + IntervalTimings.MAF
        )

    @mark_before_break.setter
    def mark_before_break(self, val) -> None:
        val = int(val) - IntervalTimings.MBB - IntervalTimings.MAF
        if val < 0 or val >= 65536:
            raise ValueError(
                "'mark_before_break' out of range. "
                + f"Shall be at least {IntervalTimings.MBB + IntervalTimings.MAF} microseconds, "
                + f"but less than {IntervalTimings.MBB + IntervalTimings.MAF + 65536} microseconds."
            )
        for header in self.headers:
            header[0] = val

    @property
    def space_for_break(self) -> int:
        """Time for a DMX SPACE FOR BREAK.
        Indicates data stream is restarting. (microseconds)

        Minimum 4, Default 172, Standard minimum 88, Maximum 65539.
        """
        return self.headers[self.show_buffer][1] + IntervalTimings.BREAK

    @space_for_break.setter
    def space_for_break(self, val) -> None:
        val = int(val) - IntervalTimings.BREAK
        if val < 0 or val >= 65536:
            raise ValueError(
                "'space_for_break' out of range. "
                + f"Shall be at least {IntervalTimings.BREAK} microseconds, "
                + f"but less than {IntervalTimings.BREAK + 65536} microseconds."
            )
        for header in self.headers:
            header[1] = val

    @property
    def mark_after_break(self) -> int:
        """Time after a DMX SPACE FOR BREAK before serial data. (microseconds)

        Minimum 4, Default 8, Maximum 65539.
        """
        return (
            self.headers[self.show_buffer][2]
            + IntervalTimings.MAB
            + IntervalTimings.ASTART
        )

    @mark_after_break.setter
    def mark_after_break(self, val) -> None:
        val = int(val) - IntervalTimings.MAB - IntervalTimings.ASTART
        if val < 0 or val >= 65536:
            raise ValueError(
                "'mark_after_break' out of range. "
                "Shall be at least "
                + f"{IntervalTimings.MAB + IntervalTimings.ASTART} microseconds, "
                "but less than "
                + f"{IntervalTimings.MAB + IntervalTimings.ASTART + 65536} microseconds."
            )
        for header in self.headers:
            header[2] = val

    @property
    def slots(self) -> int:
        "Number slots of DMX data available. (count)"
        return self.headers[self.show_buffer][3] + self.MIN_SLOTS  # Fit into 2 bytes

    @property
    def start_code(self) -> int:
        "The DMX START CODE (byte)"
        return self.payloads[self.show_buffer][0]

    @property
    def mark_after_start_code(self) -> int:
        """The first byte is the START CODE.
        How long to wait before the next byte. (microseconds)

        Includes the two stop bits.

        Minimum 5, Default 8, Maximum 260.
        """
        val = self.payloads[self.show_buffer][1]
        return val + IntervalTimings.STOP + IntervalTimings.ASTART

    @mark_after_start_code.setter
    def mark_after_start_code(self, val) -> None:
        val = int(val) - IntervalTimings.STOP - IntervalTimings.ASTART
        if val < 0 or val >= 256:
            raise ValueError(
                "'mark_after_start_code' out of range. "
                "Shall be at least "
                + f"{IntervalTimings.STOP + IntervalTimings.ASTART} microseconds, "
                "but less than "
                + f"{IntervalTimings.STOP + IntervalTimings.ASTART + 256} microseconds."
            )
        for payload in self.payloads:
            payload[1] = val

    @property
    def mark_between_slots(self) -> int:
        """How long to wait before the next byte. (microseconds)
        Excludes the START CODE and excludes the last slot.

        Includes the two stop bits.

        Minimum 5, Default 8, Maximum 260.
        """
        # This has a instance variable because the array
        # won't have storage for this variable if slots == 1.
        return self._mark_between_slots + IntervalTimings.STOP + IntervalTimings.ASTART

    @mark_between_slots.setter
    def mark_between_slots(self, val) -> None:
        val = int(val) - IntervalTimings.STOP - IntervalTimings.ASTART
        if val < 0 or val >= 256:
            raise ValueError(
                "'mmark_between_slots' out of range. "
                "Shall be at least "
                + f"{IntervalTimings.STOP + IntervalTimings.ASTART} microseconds, "
                "but less than "
                + f"{IntervalTimings.STOP + IntervalTimings.ASTART + 256} microseconds."
            )
        self._mark_between_slots = val
        for payload in self.payloads:
            # payload[0] is the start bit
            # payload[1] is the post start bit mark length
            # payload[2] is the first slot
            # payload[3] is the post first slot bit mark length
            # payload[-3] is the penultimate slot bit mark length
            # payload[-2] is the last slot (frame end)
            # payload[-1] is mark_after_frame mark length (for stopping).
            for i in range(3, len(payload) - 2, 2):
                payload[i] = val

    @property
    def interval(self) -> int:
        """
        Indicates the calculated BREAK TO BREAK run time for each DMX frame.
        (microseconds)

        The standard defines an minimum BREAK TO BREAK time of 1204 microseconds.
        Your equipment probably doesn't care.

        If a longer interval is needed, adjust the timing parameters.
        """
        return (
            self.mark_before_break
            + self.space_for_break
            + self.mark_after_break
            + 4  # 4 microseconds. Start code start bit.
            + 32  # 32 microseconds. Start code eight data bits.
            + self.mark_after_start_code
            + (self.slots - 1)
            * (
                4  # 4 microseconds. Data slot start bit.
                + 32  # 32 microseconds. Eight slot data bits.
                + self.mark_between_slots  # microseconds. Stop bits and mark time.
            )
            + 4  # 4 microseconds. Terminal slot start bit.
            + 32  # 32 microseconds. Eight terminal slot data bits.
            # Including the two stop bits & extra mark time.
        )

    def clear(self, start=None, end=None, step=None):
        """Clear all values, or those specified.

        :param int start: the first slot to clear.
        :param int end: the last slot to clear.
        :param int step: the step for each slot to clear.
        """
        payload = self.payloads[self.edit_buffer]
        for slot in range(*slice(start, end, step).indices(len(self))):
            payload[slot * 2 + 2] = 0

    def fill(self, value, start=None, end=None, step=None):
        """Clear all values, or those specified.

        :param int value: the value to be filled into each slot.
        :param int start: the first slot to fill.
        :param int end: the last slot to fill.
        :param int step: the step for each slot to fill.
        """
        payload = self.payloads[self.edit_buffer]
        for slot in range(*slice(start, end, step).indices(len(self))):
            payload[slot * 2 + 2] = value

    def __len__(self):
        return self.slots

    def __getitem__(self, ixes: int) -> int:
        payload = self.payloads[self.edit_buffer]
        if isinstance(ixes, slice):
            return [payload[ix * 2 + 2] for ix in range(*ixes.indices(len(self)))]
        try:
            ixes = int(ixes)
        except TypeError as exc:
            raise TypeError(
                f"list indices must be integers or slices, not {str(type(ixes))}"
            ) from exc
        if ixes < 0:
            ixes = ixes + len(self)
        if ixes < 0 or ixes >= len(self):
            raise IndexError("Index out of range")
        return payload[ixes * 2 + 2]

    def __setitem__(
        self,
        ixes,
        val,
    ) -> None:
        payload = self.payloads[self.edit_buffer]
        if isinstance(ixes, slice):
            size = sum(1 for _ in range(*ixes.indices(len(self))))
            if len(val) != size:
                raise ValueError(f"Can only assign a slice of the same size. ({size})")
            # Attempt a slice to slice assignment.
            values = iter(val)
            for index in range(*ixes.indices(len(self))):
                val = int(next(values))
                payload[index * 2 + 2] = val
        else:
            # Attempt a scalar to scalar assignment.
            try:
                ixes = int(ixes)
            except TypeError as exc:
                raise TypeError(
                    f"list indices must be integers or slices, not {str(type(ixes))}"
                ) from exc
            if ixes < 0:
                ixes = ixes + len(self)
            if ixes < 0 or ixes > len(self):
                raise IndexError("Index out of range")
            payload[ixes * 2 + 2] = val
