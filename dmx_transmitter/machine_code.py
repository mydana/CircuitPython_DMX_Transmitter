"""Machine code and timing parameters generated from
   CircuitPython_DMX_Transmitter/assembly_code.py
   These are consistent with Payload_USITT_DMX512_A.
"""

import array


class MachineCode:
    "Machine code and timing parameters consistent with Payload_USITT_DMX512_A"
    # Minimum timing parameters
    mark_before_break_short = 2
    mark_before_break_long = 5
    space_for_break = 4
    mark_after_break = 4
    mark_between_slots = 5
    mark_after_frame = 5

    # Array of machine code options. These are 0, 1, 2, -2, -1 corresponding
    # to the timing_pins configured. See the DMXTransmitter documentation.
    # Negative pins means that the pin sense is inverted.
    assembled = (
        array.array(
            "H",
            (
                # fmt: off
                0x6030, 0x0041, 0xA003, 0x6030, 0x0044, 0x6030, 0xA00B, 0x0047,
                0x6050, 0x80E0, 0xA203, 0xE027, 0x6101, 0xA042, 0x004C, 0xA00B,
                0x6028, 0x0051, 0x0089, 0x80E0, 0xA203, 0xE027, 0x6101, 0xA042,
                0x0056, 0xA00B, 0x6028, 0x0020, 0x005C, 0x80A0,
                # fmt: on
            ),
        ),
        array.array(
            "H",
            (
                # fmt: off
                0x7030, 0x1041, 0xB003, 0x7030, 0x1044, 0x7030, 0xB00B, 0x1047,
                0x7050, 0x90E0, 0xB203, 0xF027, 0x7101, 0xB042, 0x104C, 0xB00B,
                0x7028, 0x1051, 0x1089, 0x90E0, 0xB203, 0xF027, 0x7101, 0xB042,
                0x1056, 0xB00B, 0x7028, 0x1020, 0x105C, 0x80A0,
                # fmt: on
            ),
        ),
        array.array(
            "H",
            (
                # fmt: off
                0x7030, 0x1041, 0xB003, 0x7030, 0x1044, 0x7030, 0xB80B, 0x1847,
                0x7850, 0x98E0, 0xB203, 0xF027, 0x7101, 0xB042, 0x104C, 0xB00B,
                0x7028, 0x1051, 0x1089, 0x90E0, 0xB203, 0xF027, 0x7101, 0xB042,
                0x1056, 0xB00B, 0x7028, 0x1020, 0x105C, 0x80A0,
                # fmt: on
            ),
        ),
        array.array(
            "H",
            (
                # fmt: off
                0x6830, 0x0841, 0xA803, 0x6830, 0x0844, 0x6830, 0xA00B, 0x0047,
                0x6050, 0x80E0, 0xAA03, 0xE827, 0x6901, 0xA842, 0x084C, 0xA80B,
                0x6828, 0x0851, 0x0889, 0x88E0, 0xAA03, 0xE827, 0x6901, 0xA842,
                0x0856, 0xA80B, 0x6828, 0x0820, 0x085C, 0x98A0,
                # fmt: on
            ),
        ),
        array.array(
            "H",
            (
                # fmt: off
                0x6030, 0x0041, 0xA003, 0x6030, 0x0044, 0x6030, 0xA00B, 0x0047,
                0x6050, 0x80E0, 0xA203, 0xE027, 0x6101, 0xA042, 0x004C, 0xA00B,
                0x6028, 0x0051, 0x0089, 0x80E0, 0xA203, 0xE027, 0x6101, 0xA042,
                0x0056, 0xA00B, 0x6028, 0x0020, 0x005C, 0x90A0,
                # fmt: on
            ),
        ),
    )
