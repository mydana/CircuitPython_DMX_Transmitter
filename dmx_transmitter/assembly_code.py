# SPDX-FileCopyrightText: Copyright (c) 2023 Dana Runge
#
# SPDX-License-Identifier: MIT
"""Assemble code for CircuitPython_DMX512RP2040"""

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
.side_set 3
next_frame:
                  out x, {bits}               side 0b001         ;MBB      ; MARK BEFORE BREAK: microseconds
mark_before_break:
                  jmp x--, mark_before_break  side 0b001         ;MBB      ; MARK BEFORE BREAK: (MBB)

                  mov pins, null              side 0b101         ;BRK      ; SPACE FOR BREAK
                  out x, {bits}               side 0b101         ;BRK      ; SPACE FOR BREAK: microseconds
spaceforbreak:
                  jmp x--, spaceforbreak      side 0b101         ;BRK      ; SPACE FOR BREAK (BRK)
                  out x, {bits}               side 0b101         ;BRK      ; MARK AFTER BREAK (MAB)
                  mov pins, ~ null            side 0b011         ;MAB      ; MARK AFTER BREAK: microseconds
mark_after_break:
                  jmp x--, mark_after_break   side 0b011         ;MAB      ; MARK AFTER BREAK: wait

                  out y, {bits}               side 0b011         ;MAB      ; Ctrl: Get the number of slots we'll display

data_byte:
                  pull ifempty block          side 0b011         ;AST      ; DATA: Present (Alt. Start)
                  mov pins, null              side 0b001  [2]    ;STA      ; DATA: Start bit (STA)
                  set x, 7                    side 0b001         ;STA      ; DATA: Set up 8 bits
data_bit:
                  out pins, {pins}            side 0b001  [1]    ;DAT      ; DATA: Data bit (DAT)
                  {remnant_code}              side 0b001         ;DAT      ; DATA Toss a bit, maybe
                  jmp x--, data_bit           side 0b001         ;DAT      ; DATA: more bits?
                  mov pins, ~ null            side 0b001         ;STP      ; DATA: 2 stop bits MARK_BETWEEN_SLOTS
                  out x, 8                    side 0b001         ;STP      ; DATA: 2 stop bits microseconds
data_stop:
                  jmp x--, data_stop          side 0b001         ;STP      ; DATA: Stop (STP)
                  jmp y--, data_byte          side 0b001         ;STP      ; Ctrl: Count down the slots.

                  pull ifempty block          side 0b001         ;ATS      ; TERMINAL: Present (Alt. Start bit)
                  mov pins, null              side 0b001  [2]    ;TSA      ; TERMINAL: Start bit (TSA)
                  set x, 7                    side 0b001         ;TSA      ; TERMINAL: Set up 8 bits
term_bit:
                  out pins, {pins}            side 0b001  [1]    ;TDA      ; TERMINAL: Data bit (TDA)
                  {remnant_code}              side 0b001         ;TDA      ; TERMINAL: Toss a bit, maybe
                  jmp x--, term_bit           side 0b001         ;TDA      ; TERMINAL: more bits?
                  mov pins, ~ null            side 0b001         ;MAF      ; TERMINAL: 2 stop bits MARK_AFTER_FRAME
                  out x, 8                    side 0b001         ;MAF      ; TERMINAL: 2 stop bits microseconds
                  jmp !x, next_frame          side 0b001         ;MAF      ; TERMINAL: MARK_AFTER_FRAME (MAF)
frame_stop:
                  jmp x--, frame_stop         side 0b001         ;WAT      ; TERMINAL: Wait (WAT) further.
                  pull block                  side 0b000         ;WAT      ; TERMINAL: Wait for data.
"""

    def __init__(self, universes: int = None):
        self.universes = int(universes)
        # self.timing_pins = timing_pins
        prog = adafruit_pioasm.Program(self.pre_process(universes=universes))
        self.assembled = prog.assembled
        self.pio_kwargs = prog.pio_kwargs

    @classmethod
    def pre_process(cls, universes=1) -> str:
        "Assembly code in human-readable form."
        # Protect spacing!
        # fmt: off
        return cls.ASSEMBLY_CODE.format(
            bits={
                #  "{bits}"
                1: "16    ",
                2: "32    ",
                3: "32    "
            }[universes],
            pins={
                #  "{pins}"
                1: "1     ",
                2: "2     ",
                3: "3     "
            }[universes],
            remnant_code={
                #  "{remnant_code}"
                1: "nop           ",
                2: "out null, 1   ",
                3: "nop           "
            }[universes],
        )
        # fmt: on

    @classmethod
    def get_timing(cls):
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
        for number, line in enumerate(cls.pre_process(1).split("\n")):
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


def print_parameters():
    """Prints out the parameters that can be used to freeze the machine code.

    There isn't much of a memory savings, but it's much easier on the newbie
    because they don't need to import the assembler."""
    print("# Timing parameters are constant used in Payload_USITT_DMX512_A.")
    print("class _MinimumTiming:")
    print('    "Minimum timing from lib/dmx_transmitter/assembly_code.py"')
    for name, value in AssemblyCode.get_timing().items():
        print(f"    {name} = {value}")
    print()
    print()
    print("# Code varies by universe.")
    print("# These are used in lib/dmx_transmitter/DMXtx.py")
    print("class MachineCode:")
    print('    "Frozen machine code. From lib/dmx_transmitter/assembly_code."')
    print()
    print("    def __init__(universes):")
    print("        self.pio_kwargs = ", end="")
    print(str(AssemblyCode(universes=1).pio_kwargs).replace("'", '"'))
    print("        self.assembled = array.array(")
    print('            "H",')
    print("            (")
    for universes in range(1, 4):
        print(f"                # {universes} universes:")
        print("                (")
        print("                    # fmt: off")
        code = iter(AssemblyCode(universes=universes).assembled)
        try:
            while True:
                # pylint: disable=consider-using-f-string
                print("                    ", end="")
                print("0x{:04X},".format(next(code)), end="")
                for _ in range(7):
                    print(" 0x{:04X},".format(next(code)), end="")
                print()
        except StopIteration:
            print()
            print("                    # fmt: on")
            print("                ),")
            continue
    print("            )[universes - 1],")
    print("        )")
    print()


if "__main__" == __name__:
    print_parameters()
