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

    This virtual list has a fixed size, the number of slots.

    Like Python lists, slicing is supported, but because of the fixed size,
    slice assignment is limited. A slice assignment from a list-like object
    of the same size is allowed. Unlike Python lists, slice assignment from
    a scalar is also allowed.

    Timing parameters are set by decorators.

    Caution: Several timing parameters include the stop bits. To meet the
    DMX standards include at least 8 microseconds in these parameters.

    :param int slots: number of slots of DMX data available. (count)
        Consumes two or four bytes per slot per buffer. 1-3 buffers.
        Minimum: 1. Default: 512. Maximum: 512.
    """

    # pylint: disable=consider-using-f-string

    ##
    ## Index: 16 bits (1 universe)
    ##       +--------+-------+
    ##    0  | MBB            |
    ##       +--------+-------+
    ##    1  | BREAK          |
    ##       +--------+-------+
    ##    2  | MAB            |
    ##       +--------+-------+
    ##    3  | SLOTS          |
    ##       +--------+-------+
    ##       | mark   | start |
    ##    4  | after  | code  |
    ##       | start  |       |
    ##       +--------+-------+
    ##       | mark   | slot  |
    ##   5+  | after  | data  |
    ##       | slots  |       |
    ##       +--------+-------+
    ##       | mark   | last  |
    ##  Last | after  | slot  |
    ##       | frame  |       |
    ##       +--------+-------+
    ##
    slot_index = 5  # Index of first slot data

    class _MinimumTiming:  # pylint: disable=too-few-public-methods
        "Minimum timing from lib/dmx_transmitter/assembly_code.py"
        mark_after_frame = 5
        space_for_break = 4
        mark_between_slots = 5
        mark_after_break = 4
        mark_before_break_long = 5
        mark_before_break_short = 2

    def __init__(
        self,
        slots=512,
    ):
        "Sets up default USITT DMX512-A timings."
        self._mark_after_frame = None
        #
        # slots
        slots = int(slots) if slots is not None else 512  # cast to int.
        if slots < 1:
            raise ValueError("'slots' is too low. Shall be 1 to 512")
        if slots > 512:
            raise ValueError("'slots' is too high. Shall be 1 to 512")

        self.data_code = "H"
        self.bits = 16
        self.size = slots
        # These will be static methods:
        self._get_mark_val = type(self)._get16_mark_val
        self._set_mark_val = type(self)._set16_mark_val
        self._get_slot = type(self)._get16_slot
        self._set_slot = type(self)._set16_slot


        #
        # Create array
        self.array = array.array(
            self.data_code, (0 for _ in range(self.slot_index + slots))
        )
        #
        # Initialize the newly-created array
        self._mark_after_frame = None
        self.array[self.slot_index - 2] = slots - 1  # Slot count.
        self._init_timing_defaults()
        self._init_start_code()

    def _init_start_code(self, start_code=0x00) -> None:
        """Set the START CODE. Default NULL. (Byte)

        Useful for a subclass author.
        """
        start_code = int(start_code)
        self.array[4] = self._set_slot(self.array[4], start_code, 0)
        if self.bits == 32:
            self.array[4] = self._set_slot(
                self._set_slot(self.array[4], start_code, 1), start_code, 2
            )

    def _init_timing_defaults(self) -> None:
        "Set up default USITT DMX512-A timings."
        # fmt: off
        self.mark_after_frame = False  # last slot mark, bits 8-15 or 24-31
        self.mark_after_frame_default = 8  # last slot mark, for stopping
        # Set mark_after_frame before setting mark_before_break.
        self.mark_before_break = 8      ## self.array[0]
        self.space_for_break = 172      ## self.array[1]
        self.mark_after_break = 8       ## self.array[2]
        # slot count                    ## self.array[3]
        # NULL START CODE               ## self.array[4] bits 0-7
        self.mark_after_start_code = 8  ## self.array[4] bits 8-15 or 24-31
        self.mark_between_slots = 8     ## all slots, bits 8-15 or 24-31
        # fmt: on

    #
    # Get and set bits within the payload.
    @staticmethod
    def _get16_mark_val(existing: int) -> int:
        "Static method that get the mark timing for 16 bit words."
        return (existing & 0xFF00) >> 8

    @staticmethod
    def _set16_mark_val(existing: int, val: int) -> int:
        "Static method that joins existing data with mark timing data for 16 bit words."
        return (existing & 0x00FF) + ((val & 0xFF) << 8)

    @staticmethod
    def _get32_mark_val(existing: int) -> int:
        "Static method that get the mark timing for 32 bit words."
        return (existing & 0xFF000000) >> 24

    @staticmethod
    def _set32_mark_val(existing: int, val: int) -> int:
        "Static method that joins existing data with mark timing data for 32 bit words."
        return (existing & 0x00FFFFFF) + ((val & 0xFF) << 24)

    @staticmethod
    def _get16_slot(existing: int, universe: int) -> int:
        "Static method for getting slot data for 16 bit words."
        if universe != 0:
            raise IndexError("Index too large")
        return existing & 0x00FF

    @staticmethod
    def _set16_slot(existing: int, val: int, universe: int) -> None:
        "Static method for setting slot data for 16 bit words."
        if universe != 0:
            raise IndexError("Index too large")
        return (existing & ~0x00FF) + (val & 0x00FF)

    def array_copy(self):
        """Return a copy of the array. For sending."""
        return array.array(self.data_code, self.array)

    def array_stop(self):
        """Return a copy of the array. For the stopping."""
        val = array.array(self.data_code, self.array)
        val[-1] = self._set_mark_val(val[-1], self.mark_after_frame_default)
        return val

    def array_empty(self):
        """Return an empty array"""
        return array.array(self.data_code)

    def clear(self) -> None:
        "Set all slot values to 0."
        # Get the value of just the mark values
        val = self._set_mark_val(0, self._mark_between_slots)
        # The last slot has a different mark parameter.
        for i in range(self.slot_index, self.slot_index + self.slots - 1):
            self.array[i] = val
        # Clear the value(s) on the last slot.
        self.array[-1] = self._set_mark_val(0, self._get_mark_val(self.array[-1]))

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
        return self.array[0] + (
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
        self.array[0] = val

    @property
    def space_for_break(self) -> int:
        """Time for a DMX SPACE FOR BREAK.
        Indicates data stream is restarting. (microseconds)

        Minimum 4, Default 172, Standard minimum 88.
        """
        return self.array[1] + self._MinimumTiming.space_for_break

    @space_for_break.setter
    def space_for_break(self, val) -> None:
        val = int(val) - self._MinimumTiming.space_for_break
        if val < 0:
            raise ValueError(
                "'space_for_break' is too low. Shall be at least {0} microseconds.".format(
                    self._MinimumTiming.space_for_break
                )
            )
        self.array[1] = val

    @property
    def mark_after_break(self) -> int:
        """Time after a DMX SPACE FOR BREAK before serial data. (microseconds)

        Minimum 4, Default 8
        """
        return self.array[2] + self._MinimumTiming.mark_after_break

    @mark_after_break.setter
    def mark_after_break(self, val) -> None:
        val = int(val) - self._MinimumTiming.mark_after_break
        if val < 0:
            raise ValueError(
                "'mark_after_break' is too low. Shall be at least {0} microseconds.".format(
                    self._MinimumTiming.mark_after_break
                )
            )
        self.array[2] = val

    @property
    def slots(self) -> int:
        "Number slots of DMX data available. (count)"
        return self.array[3] + 1

    @property
    def start_code(self) -> int:
        "The DMX START CODE (byte)"
        return self._get_slot(self.array[4], 0)

    @property
    def mark_after_start_code(self) -> int:
        """The first byte is the START CODE.
        How long to wait before the next byte. (microseconds)

        Includes the two stop bits.

        Minimum 5, Default 8, Maximum 260.
        """
        val = self._get_mark_val(self.array[4])
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
        self.array[4] = self._set_mark_val(self.array[4], val)

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
        # The last slot has a different mark parameter.
        for i in range(self.slot_index, self.slot_index + self.slots - 1):
            self.array[i] = self._set_mark_val(self.array[i], val)

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
        val = self._get_mark_val(self.array[-1])
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
        self.array[-1] = self._set_mark_val(self.array[-1], val)

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
        return (
            self.mark_before_break
            + self.space_for_break
            + self.mark_after_break
            # Start code start bit.
            + 4
            # Start code data bits.
            + 32
            + self.mark_after_start_code
            + self.slots
            * (
                # Data slot start bit.
                4
                # Data slot data bits.
                + 32
                # Including the two stop bits & extra mark time.
                + self.mark_between_slots
            )
            # Terminal slot start bit.
            + 4
            # Terminal slot data bits.
            + 32
            # Including the two stop bits & extra mark time.
            + (self.mark_after_frame if self.mark_after_frame is not False else 0)
        )

    def __len__(self):
        return self.size

    def __getitem__(self, ixes: int) -> int:
        slots = self.slots
        if isinstance(ixes, slice):
            return [
                self._get_slot(self.array[ix % slots + self.slot_index], ix // slots)
                for ix in range(*ixes.indices(len(self)))
            ]
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
        return self._get_slot(self.array[ixes % slots + self.slot_index], ixes // slots)

    def __setitem__(
        self,
        ixes,
        val,
    ) -> None:
        slots = self.slots
        if isinstance(ixes, slice):
            size = sum(1 for _ in range(*ixes.indices(len(self))))
            try:
                if len(val) != size:
                    raise ValueError(
                        f"Can only assign a slice of the same size. ({size})"
                    )
            except TypeError:
                # Attempt a scalar to slice assignment.
                val = int(val)
                if val < 0 or val > 255:
                    # pylint: disable=raise-missing-from
                    raise ValueError("Value out of range")
                for index in range(*ixes.indices(len(self))):
                    self.array[index % slots + self.slot_index] = self._set_slot(
                        self.array[index % slots + self.slot_index], val, index // slots
                    )
                return
            # Attempt a slice to slice assignment.
            values = iter(val)
            for index in range(*ixes.indices(len(self))):
                val = int(next(values))
                if val < 0 or val > 255:
                    raise ValueError("Value out of range")
                self.array[index % slots + self.slot_index] = self._set_slot(
                    self.array[index % slots + self.slot_index], val, index // slots
                )
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
            if val < 0 or val > 255:
                raise ValueError("Value out of range")
            self.array[ixes % slots + self.slot_index] = self._set_slot(
                self.array[ixes % slots + self.slot_index], val, ixes // slots
            )
