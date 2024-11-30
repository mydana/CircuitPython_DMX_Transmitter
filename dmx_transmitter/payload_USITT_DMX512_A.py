# SPDX-FileCopyrightText: Copyright (c) 2023 Dana Runge
#
# SPDX-License-Identifier: MIT
# pylint: disable=invalid-name
# pylint: enable=invalid-name
"""
`dmx_transmitter.payload_USITT_DMX512_A`
========================================

Container that has data and timings for the state machine.

Implements the USITT-DMX512-A standard's timings.

Basic usage is handled via convenience methods provided by
the dmx_transmitter.dmx_transmitter.DMXTransmitter class.

This class can be used to adjust the DMX timing.

* Author: Dana Runge
"""

import array

from .machine_code import IntervalTimings

__author__ = "Dana Runge"
__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/mydana/CircuitPython_DMX_Transmitter"


class Payload_USITT_DMX512_A:  # pylint: disable=too-many-instance-attributes
    """This object mimics a list of byte values, and stores it and timing
    parameters into a data structure suitable for sending into a DMX512TxEngine
    state machine.

    Unlike DMX512, this virtual list is 0-based, just like Python lists.
    Therefore, there is an inherent off-by-one error between DMX addresses and
    the list indexes.

    Like Python lists, slicing is supported, but because of the fixed size,
    slice assignment is limited. A slice assignment from a list-like object
    of the same size is allowed.

    Timing parameters are set by decorators.

    Caution: Several timing parameters include the stop bits. To meet the
    DMX standards include at least 8 microseconds in these parameters.

    :param int slots: number of slots of DMX data available. (count)
        Consumes two bytes per slot per buffer.
        Minimum: 1. Default: 512. Maximum: 512.

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
    ##               Time before state machine shuts down. Usually 0.
    ##
    ## Timing between frames is determined by mark_before_break.
    ## While it's possible to set mark_after_frame to a value, and continue
    ## to send data to the state machine, there is no good reason to do this.

    #     @classmethod
    #     def get_timing(cls):
    #         """Minimum timing for the payload objects.
    #
    #         This function returns a dictionary, but Payload_USITT_DMX512_A
    #         wants a class. To use this online, just add this filter::
    #
    #             _MinimumTiming = type(
    #                 '_MinimumTiming',
    #                 (),
    #                 AssemblyCode.get_timing()
    #             )
    #         """
    #         timing = {}
    #         intervals = {}
    #         for number, line in enumerate(cls.pre_process(1).split("\n")):
    #             code, _, comments = line.partition(";")
    #             # Find out what's not code.
    #             code = code.rstrip()
    #             if not code:  # Empty
    #                 continue
    #             if code.startswith("."):  # Directives
    #                 continue
    #             if code.endswith(":"):  # Labels
    #                 continue
    #             # This is an opcode, get duration
    #             duration = 1
    #             if code.endswith("]"):  # Delay
    #                 end = code[:-1].split("[")[1]
    #                 duration = duration + (int(end) if end else 0)
    #             # Look for interval symbol
    #             interval, _, comments = comments.partition(";")
    #             interval = interval.strip()
    #             if not interval:
    #                 raise ValueError(f"Line {number + 1} does not have a symbol.")
    #             if not comments:
    #                 raise ValueError(f"Line {number + 1} does not have comments.")
    #             if interval not in intervals:
    #                 intervals[interval] = 0
    #             intervals[interval] = intervals[interval] + duration
    #         timing["mark_before_break_short"] = intervals["MBB"]
    #         timing["mark_before_break_long"] = intervals["MBB"] + intervals["MAF"]
    #         timing["space_for_break"] = intervals["BRK"]
    #         timing["mark_after_break"] = intervals["MAB"] + intervals["AST"]
    #         assert 4 == intervals["STA"]  # Start bit SHALL be 4 µS
    #         assert 4 == intervals["DAT"]  # Data bit SHALL be 4 µS
    #         timing["mark_between_slots"] = intervals["STP"] + intervals["AST"]
    #         assert (
    #             intervals["AST"] == intervals["ATS"]
    #         )  # Clean transition to terminal slot.
    #         assert 4 == intervals["TSA"]  # Terminal start bit SHALL be 4 µS
    #         assert 4 == intervals["TDA"]  # Termainal data bit SHALL be 4 µS
    #         timing["mark_after_frame"] = intervals["MAF"] + intervals["WAT"]
    #         return timing

    class _MinimumTiming:  # pylint: disable=too-few-public-methods
        "Minimum timing from lib/dmx_transmitter/assembly_code.py"
        # TODO
        mark_after_frame = 5
        space_for_break = 4
        mark_between_slots = 5
        mark_after_break = 4
        mark_before_break_long = 5
        mark_before_break_short = 2

    def __init__(
        self,
        slots=None,
        buffers=1,
    ):
        "Sets up default USITT DMX512-A timings."
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
        self._init_timing_defaults()
        # Set up the start code.
        for payload in self.payloads:
            payload[0] = self.START_CODE

    @property
    def auto_write(self):
        """Enable or disable auto_write.

        If auto_write is True: Changes appear right away.
        If auto_write is False: Call .show() for changes to appear."""
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

    def get_show_buffer(self):
        "Return show buffer. Switch buffers if autowrite is False"
        if self.edit_buffer == self.show_buffer:
            # autowrite is True, just return.
            return self.buffers[self.show_buffer]
        # Swap buffers
        self.edit_buffer, self.show_buffer = (self.show_buffer, self.edit_buffer)
        # Copy show buffer to the edit buffer.
        self.buffers[self.edit_buffer][:] = self.buffers[self.show_buffer][:]
        # Return the show buffer.
        return self.buffers[self.show_buffer]

    def get_stop_buffer(self, stop_mark_time):
        "Returns a buffer for stopping the operations"
        if self.edit_buffer == self.show_buffer:
            # autowrite is True, we'll use an unused buffer.
            stop_buffer = 0 if self.show_buffer else 1
            # Copy show buffer to stop buffer
            self.buffers[stop_buffer][:] = self.buffers[self.show_buffer][:]
        else:
            # autowrite is False, we'll reset the edit buffer.
            stop_buffer = self.edit_buffer
            # Copy show buffer to unused buffer.

    def _init_timing_defaults(self) -> None:
        "Set up default USITT DMX512-A timings."
        # TODO comments
        # fmt: off
        self.mark_after_frame = False  # last slot mark, bits 8-15 or 24-31
        self.mark_after_frame_default = 8  # last slot mark, for stopping
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
    def mark_before_break(self) -> int:
        """Timing from the last frame to before the SPACE FOR BREAK.
        (microseconds)

        mark_before_break is influenced by mark_after_frame.
        If mark_after_frame is False (the default) then mark_before_break
        is the time in microseconds from the last last frame, including the
        two stop bits from the last slot. Otherwise, this parameter is the
        time from transmitter enable to SPACE FOR BREAK.

        Minimum 5 if mark_after_frame is False, otherwise 2. Default 8.
        """
        return self.headers[self.show_buffer][0] + (
            self._MinimumTiming.mark_before_break_long
            if self.mark_after_frame is False
            else self._MinimumTiming.mark_before_break_short
        )

    @mark_before_break.setter
    def mark_before_break(self, val) -> None:
        if self.mark_after_frame is False:
            val = int(val) - self._MinimumTiming.mark_before_break_long
            if val < 0:
                raise ValueError(
                    "'mark_before_break' is too low. Shall be at least {0} microseconds.".format(
                        self._MinimumTiming.mark_before_break_long
                    )
                )
        else:
            val = int(val) - self._MinimumTiming.mark_before_break_short
            if val < 0:
                raise ValueError(
                    "'mark_before_break' is too low. Shall be at least {0} microseconds.".format(
                        self._MinimumTiming.mark_before_break_short
                    )
                )
        for header in self.headers:
            header[0] = val

    @property
    def space_for_break(self) -> int:
        """Time for a DMX SPACE FOR BREAK.
        Indicates data stream is restarting. (microseconds)

        Minimum 4, Default 172, Standard minimum 88.
        """
        return self.headers[self.show_buffer][1] + self._MinimumTiming.space_for_break

    @space_for_break.setter
    def space_for_break(self, val) -> None:
        val = int(val) - self._MinimumTiming.space_for_break
        if val < 0:
            raise ValueError(
                "'space_for_break' is too low. Shall be at least {0} microseconds.".format(
                    self._MinimumTiming.space_for_break
                )
            )
        for header in self.headers:
            header[1] = val

    @property
    def mark_after_break(self) -> int:
        """Time after a DMX SPACE FOR BREAK before serial data. (microseconds)

        Minimum 4, Default 8
        """
        return self.headers[self.show_buffer][2] + self._MinimumTiming.mark_after_break

    @mark_after_break.setter
    def mark_after_break(self, val) -> None:
        val = int(val) - self._MinimumTiming.mark_after_break
        if val < 0:
            raise ValueError(
                "'mark_after_break' is too low. Shall be at least {0} microseconds.".format(
                    self._MinimumTiming.mark_after_break
                )
            )
        for header in self.headers:
            header[2] = val

    @property
    def slots(self) -> int:
        "Number slots of DMX data available. (count)"
        return self.headers[self.show_buffer][2] + self.MIN_SLOTS  # Fit into 2 bytes

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
        return val + self._MinimumTiming.mark_between_slots

    @mark_after_start_code.setter
    def mark_after_start_code(self, val) -> None:
        val = int(val) - self._MinimumTiming.mark_between_slots
        if val < 0:
            raise ValueError(
                "'mark_after_start_code' is too low. Shall be at least {0} microseconds.".format(
                    self._MinimumTiming.mark_between_slots
                )
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
        return self._mark_between_slots + self._MinimumTiming.mark_between_slots

    @mark_between_slots.setter
    def mark_between_slots(self, val) -> None:
        val = int(val) - self._MinimumTiming.mark_between_slots
        if val < 0:
            raise ValueError(
                "'mark_between_slots' is too low. Shall be at least {0} microseconds.".format(
                    self._MinimumTiming.mark_between_slots
                )
            )
        self._mark_between_slots = val
        for payload in self.payloads:
            # payload[0] is the start bit
            # payload[1] is the post start bit mark length
            # payload[2] is the first slot
            # payload[3] is the post first slot bit mark length
            # payload[-3] is the penultimate slot bit mark length
            # payload[-2] is the last slot (frame end)
            # payload[-1] is mark_after_frame mark length
            # mark_after_frame mark length is ignored in this method.
            for i in range(3, len(payload) - 2, 2):
                payload[i] = val

    @property
    def mark_after_frame(self) -> int:
        """How long to wait before disabling the transmitter. (microseconds)

        If False, the state machine does not turn off the transmitter enable
        timing pin, and proceeds to send the next frame.

        Otherwise waits the specified microseconds to turn off the
        transmitter pin.

        Includes the two stop bits.

        Minimum 6, Default 8, Maximum 260.
        """
        val = self.payloads[self.show_buffer][-1]
        return (val + self._MinimumTiming.mark_after_frame) if val else False

    @mark_after_frame.setter
    def mark_after_frame(self, val) -> None:
        if val is False:
            val = 0
        elif val is True:
            val = self.mark_after_frame_default
        else:
            val = int(val) - self._MinimumTiming.mark_after_frame
            if val < 1:
                raise ValueError(
                    "'mark_after_frame' is too low. Shall be at least {0} microseconds.".format(
                        self._MinimumTiming.mark_after_frame + 1
                    )
                )
        for payload in self.payloads:
            payload[-1] = val

    @property
    def interval(self) -> int:
        """
        Indicates the calculated BREAK TO BREAK run time for each DMX frame.
        (microseconds)

        The USITT DMX512-A standard defines an minimum BREAK TO BREAK time
        of 1204 microseconds. Your equipment probably doesn't care.

        If a longer interval is needed, adjust the timing parameters in the
        class constructor.
        """
        # TODO revisit/simplify
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
            # TODO
            + (self.mark_after_frame if self.mark_after_frame is not False else 0)
        )

    def __len__(self):
        return self.slots

    def __getitem__(self, ixes: int) -> int:
        payload = self.payloads[self.edit_buffer]
        if isinstance(ixes, slice):
            return [payload[ix * 2 + 1] for ix in range(*ixes.indices(len(self)))]
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
