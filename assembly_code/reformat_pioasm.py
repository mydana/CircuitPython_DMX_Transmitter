"""Re-format and/or assemble RP2040 pio assembly code.

The RP2040 Programmable Input Output (pio) unit is a programmable state
machine designed for building interaces implementing various wire protocols,
which themselves have timing requirements.

While the RP2040 pio has facilities for adjusting timing, the programmer
still needs to consider both logic and timing. I found it helpful to code
the assembly code in a spreadsheet, and using a pivot table to calculate
the timings.

This script converts a tab separated values (TSV) into assembly code,
machine code, and/or a timing table.

"""
import argparse
import csv
import textwrap
import sys

from string import Template

import adafruit_pioasm


MAXSIDESET = 5  # Max number of sideset bits (hardware dependent)


def preparse_csv_file(csv_reader, template_arguments=None):
    """Read the tab (or comma) separated value file and pre-process
    some data:
        label column   - Shall start with dot(.), end with comma(:) or will
                         be converted to a comment.
        comment column - Pre-pended with semicolon(;) if needed.
        delay column   - Converted to an integer.
    Verifies that side and delay columns match operations.
    Applies Python templates ($argument) to all columns.
    """
    if not template_arguments:
        template_arguments = {}

    def substitute(string):
        "Insert template variables $var in cells"
        return Template(string).substitute(template_arguments)

    def preprocess_label(string):
        "Format label column."
        if string is None:
            raise KeyError("label column required")
        if not string:
            return ""
        if string.startswith("."):  # This is a declaration
            return string
        if string.endswith(":"):  # This is a label
            return string
        if string.startswith(";"):  # This a comment
            return string
        return f"; {string}"

    def preprocess_delay(string):
        "Format delay column"
        val = int(string.strip("[]") or 0)
        return f"[{val}]" if val else ""

    def preprocess_comments(string):
        "Format comment column"
        if not string:
            return ""
        if string.startswith(";"):
            return string
        return f"; {string}"

    #
    # Make column names case insensitive
    csv_reader.fieldnames = [x.lower().strip() for x in csv_reader.fieldnames]
    #
    # Column name definitions and if they are optional
    col_names = {
        "label": preprocess_label,
        "operation": False,
        "side": True,
        "delay": preprocess_delay,
        "interval": True,
        "comment": preprocess_comments,
    }
    intercode = []  # Assembly code lines.
    for line_no, raw_line in enumerate(csv_reader):
        line_array = {}
        for column_name, preprocessor in col_names.items():
            if preprocessor:
                cell = raw_line.get(column_name, "").strip()
            else:
                cell = raw_line[column_name].strip()
            try:
                cell = substitute(cell).strip()
            except KeyError as exc:
                raise KeyError(
                    f"Template error in column '{column_name}' in line {line_no + 1}"
                ) from exc
            if callable(preprocessor):
                cell = preprocessor(cell)
            line_array[column_name] = cell
        if not line_array["operation"]:
            assert not line_array["side"], "side set needs an operation column value"
            assert not line_array["delay"], "delay needs an operation column value"
        intercode.append(line_array)
    return intercode


def get_intervals(intercode):
    "Convert intercode to a dict of interval totals."
    timings = {}
    for line in intercode:
        if line["interval"] and line["operation"]:
            interval = line["interval"]
            if interval not in timings:
                timings[interval] = 0
            # delay in clock cycles plus one for the operation.
            delay = int(line["delay"].strip("[]") or 0)
            timings[interval] = timings[interval] + delay + 1
    return timings


def pretty_print_asm(intercode, indent="", first_indent="    ", intercolumn="  "):
    """Convert intercode into columns Padded with spaces.

    indent       - space at the beginning of all lines
    first_indent - space before operation
    intercolumn  - space between columns
    """
    # Convert intercode to columns
    matrix = []
    columns = [
        "label",
        "operation",
        lambda l: "side" if l.get("side") else "",
        "side",
        "delay",
        "comment",
    ]
    # Create an array of columns, and column lengths.
    col_lengths = [0] * len(columns)
    for line in intercode:
        new_line = []
        for col_num, col_name in enumerate(columns):
            if callable(col_name):
                cell = col_name(line)
            else:
                cell = line[col_name]
            if len(cell) > col_lengths[col_num]:
                col_lengths[col_num] = len(cell)
            new_line.append(cell)
        matrix.append(new_line)
    # Pad each column, pre-pend labels
    text_lines = []
    for line in matrix:
        new_line = [(indent + first_indent)]
        for col_num, cell in enumerate(line):
            if col_num:
                # Code lines
                cell_pad = " " * (col_lengths[col_num] - len(cell))
                new_line.append(cell + cell_pad)
            else:
                # Label lines
                if cell:
                    text_lines.append(indent + cell)
        code_line = intercolumn.join(new_line).rstrip()
        if code_line:
            text_lines.append(code_line)
    text_lines.append("")  # Add terminal \n
    return "\n".join(text_lines)


def pretty_print_timing(intervals, intercolumn="\t", indent=""):
    "Convert interval timing as a tab-separated table."
    return "\n".join(
        f"{indent}{mnemonic}{intercolumn}{intervals[mnemonic]}"
        for mnemonic in sorted(intervals)
    )


def make_sideset_mask(prog, sideset_pins=None):
    "Generate a mask to fix sideset."
    code_sideset_pins = prog.pio_kwargs.get("sideset_pin_count", 0)
    code_sideset_enable = prog.pio_kwargs.get("sideset_enable", False)
    assert code_sideset_pins <= (4 if code_sideset_enable else 5)
    sideset_base = (12 if code_sideset_enable else 13) - code_sideset_pins
    sideset_mask = (2**code_sideset_pins) - 1 << sideset_base
    sideset_hole = 0xFFFF & ~sideset_mask
    desired_pins = min(code_sideset_pins, abs(sideset_pins))
    diff = int(code_sideset_pins - desired_pins)
    small_mask = (2**desired_pins) - 1
    if sideset_pins is None:

        def mask(word):
            "Remove all sideset pins."
            return word & sideset_hole

    else:

        def mask(word):
            "Remove some sideset pins, maybe."
            code = word & sideset_hole
            sideset = (word & sideset_mask) >> sideset_base
            # TODO we don't know if the sideset logic really works correctly or not.
            # sideset = sideset >> diff  # Shift the bits over
            # or should this be a inverse bits?
            sideset = sideset & small_mask
            if sideset_pins < 0:
                # Inverse pins
                sideset = ~sideset & small_mask
            sideset = sideset << (sideset_base + diff)
            assert not sideset & sideset_hole
            return code | sideset

    return mask


def literal_machine_code(prog, sideset_pins=None, indent=""):
    """Convert RP2040 pio machine code to literal Python expression.

    machine_code is the output from adafruit_pioasm
    indent is how many spaces of indentation
    does not indent the first line.
    """
    mask = make_sideset_mask(prog, sideset_pins=sideset_pins)
    code_words = [
        # pylint: disable=consider-using-f-string
        # Convert the RP2040 PIO state machine code words into text
        # The RP2040 is little-endian so the lower-order byte comes first.
        "\\x{1:02x}\\x{0:02x}".format(*divmod(mask(c), 256))
        for c in prog.assembled
    ]
    # Format words
    min_words = 4
    line_length = 80
    # 3 characters for the initial (b") and for the trailing (")
    # 8 characters per word
    max_words = max(min_words, (line_length - len(indent) - 3) // 8)
    num_words = (max_words // 4) * 4
    # The returned code is an expression that will be inserted into other
    # code, therefore we do not start with an indent. The caller will
    # have to take care of the indents.
    lines = ["memoryview("]
    while code_words:
        my_words = code_words[:num_words]
        code_words = code_words[num_words:]
        lines.append(f'{indent}    b"{"".join(my_words)}"')
    lines.append(f'{indent}).cast("H")')
    return "\n".join(lines)


def python_print_machine_code(prog, sideset_pins, code_name, indent=""):
    """Print output machine code as python."""
    if sideset_pins is None:
        machine_code = literal_machine_code(
            prog, sideset_pins=sideset_pins, indent=indent
        )
        return (
            f"{indent}## Program for rp2pio.StateMachine\n"
            f"{indent}{code_name} = {machine_code}"
        )
    code_sideset_pins = prog.pio_kwargs.get("sideset_pin_count", 0)
    number_names = ("No", "One", "Two", "Three", "Four", "Five")
    quantity = abs(sideset_pins)
    assert (
        quantity <= code_sideset_pins
    ), f"Only {code_sideset_pins} sideset pins are available."
    assert number_names[quantity], "sideset_pins needs to be -5 to 5"
    lines = [
        f"{indent}## Tuple of programs for rp2pio.StateMachine",
        f"{indent}## The index is the number of desired sideset pins.",
        f"{indent}{code_name} = (",
    ]
    code_indent = indent + "    "
    for index in range(quantity + 1):
        number_name = number_names[index]
        lines.append(
            f"{code_indent}# index = {index}: {number_name} desired sideset_pins."
        )
        machine_code = literal_machine_code(
            prog, sideset_pins=index, indent=code_indent
        )
        lines.append(f"{code_indent}{machine_code},")
    if sideset_pins < 0:
        for index in range(quantity, 0, -1):
            number_name = number_names[index]
            lines.append(
                f"{code_indent}# index = {-index}: {number_name}"
                " desired logically-inverted sideset_pins."
            )
            machine_code = literal_machine_code(
                prog, sideset_pins=-index, indent=code_indent
            )
            lines.append(f"{code_indent}{machine_code},")
    lines.append(f"{indent})")
    lines.append("")  # Tailing newline
    return "\n".join(lines)


def python_print_pio_kwargs(
    pio_kwargs, sideset_pins, code_name, variable_name, indent=""
):
    """Print output PIO Kwargs as literal python."""
    code_sideset_pins = pio_kwargs.get("sideset_pin_count", 0)
    code_sideset_enable = pio_kwargs.get("sideset_enable", False)
    if code_name is None:
        code_name = "my_machine_code_variable"
    if sideset_pins is None:
        boilerplate = Template(
            textwrap.dedent(
                """\
                ## Parameters for rp2pio.StateMachine
                ## Parameters for rp2pio.StateMachine
                ## example: rp2pio.StateMachine(
                ##                              $code_name,
                ##                              **$variable_name,
                ##                              ...(additional parameters)...,
                ##                              )
                $variable_name = {
                    $kwargs
                }"""
            )
        )
        # Boilerplate parameters
        sideset_pins = 0
        sideset_enable = False
        pio_kwargs = dict(
            pio_kwargs,
            sideset_enable=False,
            # sideset_pin_count=0,  # Zero doesn't work, don't include it.
        )
        dict_indent = indent
    else:
        boilerplate = Template(
            textwrap.dedent(
                """\
                ## Sideset settings from the assembly code.
                SIDESET_PINS = $sideset_pins
                SIDESET_ENABLE = $sideset_enable
                
                
                ## A function that produces parameters for rp2pio.StateMachine"
                ## example: rp2pio.StateMachine(
                ##                              $code_name[sideset_pins],"
                ##                              **$variable_name(sideset_pins),"
                ##                              ...(additional parameters)...,"
                ##                              )
                def $variable_name(sideset_pins=0):
                    "Get parameters appropriate for the desired side-set pin count."
                    pin_count = min(SIDESET_PINS, abs(sideset_pins))
                    enable = bool(pin_count) and SIDESET_ENABLE
                    kwargs = {
                        $kwargs
                    }
                    if 0 == kwargs.get("sideset_pin_count", False):
                        kwargs.pop("sideset_pin_count")
                    return kwargs
                    """
            )
        )
        # Boilerplate parameters
        sideset_pins = min(code_sideset_pins, abs(sideset_pins))
        sideset_enable = bool(sideset_pins) and code_sideset_enable
        pio_kwargs = dict(
            pio_kwargs,
            sideset_enable="enable",
            sideset_pin_count="pin_count",
        )
        dict_indent = indent + "    "
    # Render the literal python code.
    literal_kwargs_dict = f"\n{dict_indent}    ".join(
        f'"{key}": {val},' for key, val in pio_kwargs.items()
    )
    return boilerplate.substitute(
        {
            "code_name": code_name,
            "variable_name": variable_name,
            "sideset_pins": sideset_pins,
            "sideset_enable": sideset_enable,
            "kwargs": literal_kwargs_dict,
        }
    )


def python_print_timings(intervals, variable_name, indent=""):
    """Print output timings as a python class."""
    if not intervals:
        return ""
    lines = [
        f"{indent}class {variable_name}:  # pylint: disable=too-few-public-methods",
        f'{indent}    """Named timing intervals. All are PIO clock tics.',
        f"{indent}    See documentation elsewhere in this project for the meaning of these names.",
        f'{indent}    """',
        "",
    ]
    for key in sorted(intervals):
        lines.append(f"{indent}    {key} = {intervals[key]}")
    lines.append("")  # Terminal \n
    return "\n".join(lines)


def python_print_all(prog, intervals, args, indent=""):
    """Print all the python-language output inside boilerplate"""
    boilerplate = Template(
        """\
$indent\"\"\"Machine-generated PIO machine code and parameters for rp2pio.StateMachine.

This machine-generated Python library contains the RP2040 PIO state machine
machine code, state machine parameters, and optionally a class of interval
timings. Because this library is generated by a generally-purpose formatter,
this documentation is necessarily general, refer to the code around this
project to understanding the meaning of the code.


Provenance:

This file was created by:
$reformatter

This formatter drew from a text-separated-values file likely exported from
a spreadsheet. The developer likely chose to develop the assembly code by
using a spreadsheet to manage both the logic and the timing intervals.

The text-separated-values source file is: $source


Side Set Pins:

In addition to the output pins, The RP2040 PIO has the ability to optionally
set additional pins with each operation, the side-set pins. These may be used
for example to send out diagnostic data, or enable/disable a data bus.
Unfortunately, the choice of the use of side-set pins is set in the assembly
code. In an effort to give the end user an ability to choose if they wish to
use side-set capability in the application or not, this formatter has the
option to output machine code variations customized for different number of
side-set pins desired. It also has the option to output code variations for
logically-inverted side-set pins.

The meaning of the side set pins can not be determined in this machine-
generated file. See elsewhere in the project for the meaning of these pins.


StateMachine Program:

$machine_code_variable_name is a either a memoryview object suitable for
use as a program for a rp2pio.StateMachine, or it is tuple of memoryview
objects. If it is a tuple, the index is the desired number of side-set pins,
and if negative, the desired number of logically-inverted side-set pins.

$pio_kwargs_variable_name is a either dictionary of parameters suitable for
rp2pio.StateMachine or a function that returns such a dictionary. If it is
a function, the one function parameter is the desired number of side-set pins,
and if negative, the desired number of logically-inverted side-set pins.

$timings_class_name, if present, is a class of interval timings. Likely, the
source spreadsheet has an additional column of interval names, additional
expressions, and a pivot table to re-calculate timing intervals on the fly
as the programmer worked on the logic. This formatter can read the interval
names and calculate timings and output a class of class constants for each
interval names. The meaning of each interval name can not be determined
from this machine-generated file. See elsewhere in the project for the
meaning of these interval names.\"\"\"
"""
    )
    do_not_edit = f"#  {'  '.join(['DO NOT EDIT THIS FILE']*3)}"
    return f"\n{indent}".join(
        [
            boilerplate.substitute(
                {
                    "indent": indent,
                    "reformatter": sys.argv[0],
                    "source": args.source,
                    "machine_code_variable_name": args.machine_code_variable_name,
                    "pio_kwargs_variable_name": args.pio_kwargs_variable_name,
                    "timings_class_name": args.timings_class_name,
                }
            ),
            "",
            do_not_edit,
            "",
            "",
            python_print_machine_code(
                prog,
                sideset_pins=args.sideset_pins,
                code_name=args.machine_code_variable_name or "machine_code",
                indent="",
            ),
            "",
            do_not_edit,
            "",
            "",
            python_print_pio_kwargs(
                prog.pio_kwargs,
                sideset_pins=args.sideset_pins,
                code_name=args.machine_code_variable_name,
                variable_name=args.pio_kwargs_variable_name or "pio_kwargs",
                indent="",
            ),
            "",
            do_not_edit,
            "",
            "",
            python_print_timings(
                intervals,
                variable_name=args.timings_class_name or "IntervalTimings",
                indent="",
            ),
        ]
    ).rstrip()


def main():
    "The code that runs this script."

    class StoreTemplateAction(argparse.Action):
        """Argparse template setup."""

        def __call__(self, _, namespace, vals, option_string=None):
            dest = getattr(namespace, self.dest, None)
            if not dest:
                dest = {}
                setattr(namespace, self.dest, dest)
            attr, val = vals.split("=", 1)
            dest[attr] = val

    def check_indent(val):
        "Indent has to be zero or a positive integer."
        val = int(val)
        if val < 0:
            raise argparse.ArgumentTypeError("zero or a positive integer required.")
        return val

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""Process RP2040 PIO assembly code from a spreadsheet.

        The RP2040 PIO (Programmable input/output unit) implements programmable
        state machines that implement I/O wire protocols. The programmer that
        codes the machine code for these state machines needs to pay attention
        to both the logic and the timing.

        One development strategy is to use a spreadsheet with the necessary
        expressions that re-calculate timing intervals in response to code
        changes. This script helps by converting a tab-separated-values file
        from a spreadsheet program into a text or python-code files as might
        be useful for a CircuitPython project.
""",
        epilog="""Column headers needed for the tab-separated-values file:

        header       Use case
        -----------  ---------------------------------------------------------
        label -----> Declarations. (Starts with a dot (.)).
           "   ----> Labels. (Ends in a colon (:)).
           "   ----> Full-line comments. (Optionally ends with a semicolon (;)).
        operation -> Code, such as "out x, 16".
        side ------> Side set value, if any. Do not precede with "side".
        delay -----> Delay time as an integer. Do not include the [].
        comment ---> End-of-the line comment.
        interval --> An optional column. Add a mnemonic (Python identifier)
                     for each desired operation. The total time for each
                     operation will be summed and reported in a timing
                     list or as a timing class.

        * Column headers are case-sensitive.
        * Any column headers not mentioned above are ignored.
""",
    )
    parser.add_argument(
        "source", help="PIO assembly code written as a tab separated values file.  "
    )
    parser.add_argument(
        "--include",
        action=StoreTemplateAction,
        help="If cells in the source file has includes preceded with a dollar"
        " sign($), such as $width. Specify the value here as such:"
        " --include width=30",
    )
    parser.add_argument(
        "--indent",
        type=check_indent,
        default=0,
        help="Output this many columns of text in front of each line.",
    )
    parser.add_argument(
        "--sideset-pins",
        choices=(0, 1, 2, 3, 4, 5, -5, -4, -3, -2, -1),
        type=int,
        default=None,
        help="Max number of sideset pins to be supported. A negative number"
        " also supports inverted sideset pins. If not specified, the"
        " python-outputted machine code will be printed as is."
        " If a zero or positive number machine code will have variants for"
        " a number of sideset pins, these will be in a list, where the key"
        " is the number of sideset pins. If a negative number, also creates"
        " machine code variants with the sideset pins logically inverted.",
    )
    parser.add_argument(
        "--assembly-code",
        action="store_true",
        help="Output assembly code as plain text."
        " Does not honor the --sideset parameter, above.",
    )
    parser.add_argument(
        "--timings",
        action="store_true",
        help="Output timings as a tab-separated text file.",
    )
    parser.add_argument(
        "--python",
        action="store_true",
        help="Print all Python code and boilerplate as a library.",
    )
    parser.add_argument(
        "--machine-code-variable-name",
        help="Python code for machine code. Specify the variable name.",
    )
    parser.add_argument(
        "--pio-kwargs-variable-name",
        help="Python code for pio keyword arguments. Specify the variable name.",
    )
    parser.add_argument(
        "--timings-class-name",
        help="Python code for timing intervals. Specify the class name."
        " If no intervals found, returns nothing.",
    )
    parser.add_argument(
        "--out",
        help="File to direct output to.",
    )
    args = parser.parse_args()
    if args.out:
        sys.stdout = open(args.out, 'w')
    with open(args.source, "r", newline="", encoding="ascii") as tsvfile:
        reader = csv.DictReader(tsvfile, dialect="excel-tab")
        intercode = preparse_csv_file(reader, args.include)
    intervals = get_intervals(intercode)
    prog = adafruit_pioasm.Program(pretty_print_asm(intercode))
    if args.assembly_code and not args.machine_code_variable_name:
        # Print out the assembly code
        print(pretty_print_asm(intercode, indent=" " * args.indent))
    if args.timings and not args.timings_class_name:
        # Print out timings as plain text
        print(pretty_print_timing(intervals, indent=" " * args.indent))
    if args.machine_code_variable_name and not args.python:
        # Print out the machine code
        print(
            python_print_machine_code(
                prog,
                sideset_pins=args.sideset_pins,
                code_name=args.machine_code_variable_name,
                indent=" " * args.indent,
            )
        )
    if args.pio_kwargs_variable_name and not args.python:
        # Print out pio kwargs as legal Python
        print(
            python_print_pio_kwargs(
                prog.pio_kwargs,
                sideset_pins=args.sideset_pins,
                code_name=args.machine_code_variable_name,
                variable_name=args.pio_kwargs_variable_name,
                indent=" " * args.indent,
            ),
            end="",
        )
    if args.timings_class_name and not args.python:
        # Print out timings as legal Python
        print(
            python_print_timings(
                intervals,
                variable_name=args.timings_class_name,
                indent=" " * args.indent,
            ),
            end="",
        )
    if args.python:
        # Print out an entire library of all code
        print(python_print_all(prog, intervals, args, indent=""))


if __name__ == "__main__":
    main()
