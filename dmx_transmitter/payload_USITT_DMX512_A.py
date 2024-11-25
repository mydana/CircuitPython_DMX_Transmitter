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

MAX_SLOTS = 512  # Defined in the DMX512 definition.
MIN_SLOTS = 1  # Offset of slot count

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

    ##  mv_index:
    ##
    ##   0 - mark_before_break (microseconds)
    ##   1 - * MSB mark_before_break
    ##   2 - space_for_break (microseconds)
    ##   3 - * MSB space_for_break
    ##   4 - mark_after_break (microseconds) 
    ##   5 - * MSB mark_after_break
    ##   6 - LSB slots
    ##   7 - MSB slots - !!!
    ##   8 - Start code
    ##   9 - Start code stop
    ## 10+ - Slot Data [0]
    ## 11+ - Mark after slot 0
    ## pen - Last data slot   - n * 2 + 10
    ## ult - Mark after frame - n * 2 + 11

    slot_index = 10 # Index of first slot data

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
        slots=MAX_SLOTS,
    ):
        "Sets up default USITT DMX512-A timings."
        self._mark_after_frame = None
        #
        # slots
        slots = int(slots) if slots is not None else 512
        if slots < MIN_SLOTS:
            raise ValueError(f"'slots' is too low. Shall be {MIN_SLOTS} to {MAX_SLOTS}")
        if slots > MAX_SLOTS:
            raise ValueError(f"'slots' is too high. Shall be {MIN_SLOTS} to {MAX_SLOTS}")

        #
        # Create array
        self.array = array.array("B", (0 for _ in range(self.slot_index + slots * 2)))

        #
        # Initialize the newly-created array
        self._mark_after_frame = None
        self.array[7], self.array[6] = divmod(slots - MIN_SLOTS, 256)  # Fit into 2 bytes
        self._init_timing_defaults()
        # Clones should take on the start code.
        self._init_start_code()

    def _init_start_code(self, start_code=0x00) -> None:
        """Set the START CODE. Default NULL. (Byte)

        Useful for a subclass author.
        """
        start_code = int(start_code)
        self.array[8] = start_code

    def _init_timing_defaults(self) -> None:
        "Set up default USITT DMX512-A timings."
        # fmt: off
        self.mark_after_frame = False  # last slot mark, bits 8-15 or 24-31
        self.mark_after_frame_default = 8  # last slot mark, for stopping
        # Set mark_after_frame before setting mark_before_break.
        self.mark_before_break = 8      ## self.array[0]
        self.space_for_break = 172      ## self.array[2]
        self.mark_after_break = 8       ## self.array[4]
        # slot count                    ## self.array[6], self.array[7]
        # NULL START CODE               ## self.array[8]
        self.mark_after_start_code = 8  ## self.array[9]
        self.mark_between_slots = 8     ## odd number bytes
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
        self.array[1] = 0 # MSB

    @property
    def space_for_break(self) -> int:
        """Time for a DMX SPACE FOR BREAK.
        Indicates data stream is restarting. (microseconds)

        Minimum 4, Default 172, Standard minimum 88.
        """
        return self.array[2] + self._MinimumTiming.space_for_break

    @space_for_break.setter
    def space_for_break(self, val) -> None:
        val = int(val) - self._MinimumTiming.space_for_break
        if val < 0:
            raise ValueError(
                "'space_for_break' is too low. Shall be at least {0} microseconds.".format(
                    self._MinimumTiming.space_for_break
                )
            )
        self.array[2] = val
        self.array[3] = 0 # MSB

    @property
    def mark_after_break(self) -> int:
        """Time after a DMX SPACE FOR BREAK before serial data. (microseconds)

        Minimum 4, Default 8
        """
        return self.array[4] + self._MinimumTiming.mark_after_break

    @mark_after_break.setter
    def mark_after_break(self, val) -> None:
        val = int(val) - self._MinimumTiming.mark_after_break
        if val < 0:
            raise ValueError(
                "'mark_after_break' is too low. Shall be at least {0} microseconds.".format(
                    self._MinimumTiming.mark_after_break
                )
            )
        self.array[4] = val
        self.array[5] = 0 # MSB

    @property
    def slots(self) -> int:
        "Number slots of DMX data available. (count)"
        return self.array[7] * 256 + self.array[6] + MIN_SLOTS  # Fit into 2 bytes

    @property
    def start_code(self) -> int:
        "The DMX START CODE (byte)"
        return self.array[8]

    @property
    def mark_after_start_code(self) -> int:
        """The first byte is the START CODE.
        How long to wait before the next byte. (microseconds)

        Includes the two stop bits.

        Minimum 5, Default 8, Maximum 260.
        """
        val = self.array[9]
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
        self.array[9] = val

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
        for i in range(self.slots - MIN_SLOTS):
            self.array[self.slot_index + i * 2 + MIN_SLOTS] = val

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
        val = self.array[-1]
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
        self.array[-1] = val

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
        return self.slots

    def __getitem__(self, ixes: int) -> int:
        if isinstance(ixes, slice):
            return [
                self.array[ix * 2 + self.slot_index]
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
        return self.array[ixes * 2 + self.slot_index]

    def __setitem__(
        self,
        ixes,
        val,
    ) -> None:
        if isinstance(ixes, slice):
            size = sum(1 for _ in range(*ixes.indices(len(self))))
            if len(val) != size:
                raise ValueError(
                    f"Can only assign a slice of the same size. ({size})"
                )
            # Attempt a slice to slice assignment.
            values = iter(val)
            for index in range(*ixes.indices(len(self))):
                val = int(next(values))
                self.array[index * 2 + self.slot_index] = val
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
            self.array[ixes * 2 + self.slot_index] = val
