# SPDX-FileCopyrightText: Copyright (c) 2023 Dana Runge
#
# SPDX-License-Identifier: MIT
"""Assemble code for CircuitPython_DMX512RP2040"""

import array
import adafruit_pioasm

__author__ = "Dana Runge"
__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/mydana/CircuitPython_DMX_Transmitter"


class AssemblyCode:
    "The assembly code that drives the DMX Transmitter."

    ## Wow! These are kinda long lines. So much for PEP 8 eh! Why these lines
    ## are so longs and in columns, they look almost like an input for a
    ## spreadsheet program. And that Interval column looks weird, like they
    ## codes for a pivot table or something like that.
    ##
    ## That's exactly what this is. Add one for each opcode, plus the delay,
    ## then run those values through the Interval column into a pivot table,
    ## and the spreadsheet calculates the timing intervals for you.
    ASSEMBLY_CODE = """
;Labels:          OPCODES                     Side Bits   Delay  Interval  Comments
.program dmx512tx
.side_set 2
next_frame:
                  out x, 16                   side 0b10          ;MBB      ; MARK BEFORE BREAK: microseconds
mark_before_break:
                  jmp x--, mark_before_break  side 0b10          ;MBB      ; MARK BEFORE BREAK: (MBB)

                  mov pins, null              side 0b10          ;BRK      ; SPACE FOR BREAK
                  out x, 16                   side 0b10          ;BRK      ; SPACE FOR BREAK: microseconds
spaceforbreak:
                  jmp x--, spaceforbreak      side 0b10          ;BRK      ; SPACE FOR BREAK (BRK)
                  out x, 16                   side 0b10          ;BRK      ; MARK AFTER BREAK (MAB)
                  mov pins, ~ null            side 0b11          ;MAB      ; MARK AFTER BREAK: microseconds
mark_after_break:
                  jmp x--, mark_after_break   side 0b11          ;MAB      ; MARK AFTER BREAK: wait

                  out y, 16                   side 0b11          ;MAB      ; Ctrl: Get the number of slots we'll display

data_byte:
                  pull ifempty block          side 0b11          ;AST      ; DATA: Present (Alt. Start)
                  mov pins, null              side 0b10   [2]    ;STA      ; DATA: Start bit (STA)
                  set x, 7                    side 0b10          ;STA      ; DATA: Set up 8 bits
data_bit:
                  out pins, 1                 side 0b10   [1]    ;DAT      ; DATA: Data bit (DAT)
                  nop                         side 0b10          ;DAT      ; DATA Toss a bit, maybe
                  jmp x--, data_bit           side 0b10          ;DAT      ; DATA: more bits?
                  mov pins, ~ null            side 0b10          ;STP      ; DATA: 2 stop bits MARK_BETWEEN_SLOTS
                  out x, 8                    side 0b10          ;STP      ; DATA: 2 stop bits microseconds
data_stop:
                  jmp x--, data_stop          side 0b10          ;STP      ; DATA: Stop (STP)
                  jmp y--, data_byte          side 0b10          ;STP      ; Ctrl: Count down the slots.

                  pull ifempty block          side 0b10          ;ATS      ; TERMINAL: Present (Alt. Start bit)
                  mov pins, null              side 0b10   [2]    ;TSA      ; TERMINAL: Start bit (TSA)
                  set x, 7                    side 0b10          ;TSA      ; TERMINAL: Set up 8 bits
term_bit:
                  out pins, 1                 side 0b10   [1]    ;TDA      ; TERMINAL: Data bit (TDA)
                  nop                         side 0b10          ;TDA      ; TERMINAL: Toss a bit, maybe
                  jmp x--, term_bit           side 0b10          ;TDA      ; TERMINAL: more bits?
                  mov pins, ~ null            side 0b10          ;MAF      ; TERMINAL: 2 stop bits MARK_AFTER_FRAME
                  out x, 8                    side 0b10          ;MAF      ; TERMINAL: 2 stop bits microseconds
                  jmp !x, next_frame          side 0b10          ;MAF      ; TERMINAL: MARK_AFTER_FRAME (MAF)
frame_stop:
                  jmp x--, frame_stop         side 0b10          ;WAT      ; TERMINAL: Wait (WAT) further.
                  pull block                  side 0b00          ;WAT      ; TERMINAL: Wait for data.
"""

    def __init__(self):
        prog = adafruit_pioasm.Program(self.ASSEMBLY_CODE)
        self.assembled = prog.assembled
        self.pio_kwargs = prog.pio_kwargs

    def filter_sideset(self, pins):
        "Return machine code with the specified number of sideset pins"
        pin_count = int(abs(pins))
        if pin_count > self.pio_kwargs["sideset_pin_count"]:
            raise ValueError("Too many sideset pins")
        desired = (2**pin_count - 1) << (12 - pin_count)
        sideset = (2 ** self.pio_kwargs["sideset_pin_count"] - 1) << (
            12 - self.pio_kwargs["sideset_pin_count"]
        )
        if not self.pio_kwargs["sideset_enable"]:
            desired = desired << 1
            sideset = sideset << 1
        mask = (2**16 - 1 - sideset) | desired
        invert = desired if bool(pins < 0) else 0
        return array.array("H", ((op & mask) ^ invert for op in self.assembled))

    @classmethod
    def get_timing(class_):
        """Minimum timing for the payload objects.

        This function returns a dictionary, but Payload_USITT_DMX512_A
        wants a class. To use this online, just add this filter::

            _MinimumTiming = type(
                '_MinimumTiming',
                (),
                AssemblyCode.get_timing()
            )
        """
        timing = {}
        intervals = {}
        for number, line in enumerate(class_.ASSEMBLY_CODE.split("\n")):
            code, _, comments = line.partition(";")
            # Find out what's not code.
            code = code.rstrip()
            if not code:  # Empty
                continue
            if code.startswith("."):  # Directives
                continue
            if code.endswith(":"):  # Labels
                continue
            # This is an opcode, get duration
            duration = 1
            if code.endswith("]"):  # Delay
                end = code[:-1].split("[")[1]
                duration = duration + (int(end) if end else 0)
            # Look for interval symbol
            interval, _, comments = comments.partition(";")
            interval = interval.strip()
            if not interval:
                raise ValueError(f"Line {number + 1} does not have a symbol.")
            if not comments:
                raise ValueError(f"Line {number + 1} does not have comments.")
            if interval not in intervals:
                intervals[interval] = 0
            intervals[interval] = intervals[interval] + duration
        timing["mark_before_break_short"] = intervals["MBB"]
        timing["mark_before_break_long"] = intervals["MBB"] + intervals["MAF"]
        timing["space_for_break"] = intervals["BRK"]
        timing["mark_after_break"] = intervals["MAB"] + intervals["AST"]
        assert 4 == intervals["STA"]  # Start bit SHALL be 4 µS
        assert 4 == intervals["DAT"]  # Data bit SHALL be 4 µS
        timing["mark_between_slots"] = intervals["STP"] + intervals["AST"]
        assert (
            intervals["AST"] == intervals["ATS"]
        )  # Clean transition to terminal slot.
        assert 4 == intervals["TSA"]  # Terminal start bit SHALL be 4 µS
        assert 4 == intervals["TDA"]  # Termainal data bit SHALL be 4 µS
        timing["mark_after_frame"] = intervals["MAF"] + intervals["WAT"]
        return timing


def dump_array(the_array, prefix=""):
    "Print a copy of an array"
    code = iter(the_array)
    print(prefix, "array.array(")
    print(prefix, '    "H",')
    print(prefix, "    (")
    print(prefix, "        # fmt: off")
    try:
        while True:
            # pylint: disable=consider-using-f-string
            print(prefix, "        ", end="")
            print("0x{:04X},".format(next(code)), end="")
            for _ in range(7):
                print(" 0x{:04X},".format(next(code)), end="")
            print()
    except StopIteration:
        print()
        print(prefix, "        # fmt: on")
        print(prefix, "    ),")
        print(prefix, "),")


def print_parameters():
    """Prints out the parameters that can be used to freeze the machine code."""
    print('"""Machine code and timing parameters generated from')
    print("   CircuitPython_DMX_Transmitter/assembly_code.py")
    print("   These are consistent with Payload_USITT_DMX512_A.")
    print('"""')
    print()
    print("import array")
    print()
    print()
    print("class MachineCode:")
    print(
        '    "Machine code and timing parameters consistent with Payload_USITT_DMX512_A"'
    )
    print("    # Minimum timing parameters")
    for name, value in AssemblyCode.get_timing().items():
        print(f"    {name} = {value}")
    print()
    print(
        "    # Array of machine code options. These are 0, 1, 2, -2, -1 corresponding"
    )
    print("    # to the timing_pins configured. See the DMXTransmitter documentation.")
    print("    # Negative pins means that the pin sense is inverted.")
    print("    assembled = (")
    sideset = 0
    # Nero and positive sideset.
    try:
        while True:
            dump_array(AssemblyCode().filter_sideset(sideset), "       ")
            sideset = sideset + 1
    except ValueError:
        pass
    # Negative sideset.
    sideset = 1 - sideset
    try:
        while sideset:
            dump_array(AssemblyCode().filter_sideset(sideset), "       ")
            sideset = sideset + 1
    except ValueError:
        pass
    print("    )")


if "__main__" == __name__:
    print_parameters()
