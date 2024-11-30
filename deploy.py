# SPDX-FileCopyrightText: Copyright (c) 2024 Dana Runge
#
# SPDX-License-Identifier: Unlicense
"Deploy tests to a microcontroller"
import argparse
import os
import shutil

import circup


class BoardNotFound(RuntimeError):
    """Error when circup couldn't find the CircuitPython board.

    See if it's connected, and if the host operating system can find it."""


class StoreVar(argparse.Action):
    """Capture variables for code.py."""

    def __call__(self, _, namespace, vals, option_string=None):
        dest_var = getattr(namespace, self.dest, None)
        if not dest_var:
            dest_var = {}
            setattr(namespace, self.dest, dest_var)
        attr, _, val = vals.partition("=")
        if not attr.isidentifier():
            raise argparse.ArgumentTypeError(
                "--val {attr} not a legal Python identifier."
            )
        if not attr.isupper():
            raise argparse.ArgumentTypeError("--val {attr} is not upper case.")
        # Get the from the environment, keep val if not found.
        dest_var[attr] = os.environ.get(attr, val)


parser = argparse.ArgumentParser(description="Upload code to the microcontroller.")
parser.add_argument("--code", nargs="?", help="File to deploy as code.py")
parser.add_argument(
    "--var",
    action=StoreVar,
    help="Replace the global variable in code.py with "
    "the value of an environment variable of the same name. "
    "If no environment variable exists, set this value instead.",
)
parser.add_argument("lib", nargs="*", help="Files to deploy as libraries")

args = parser.parse_args()
cwd = circup.os.getcwd()
dest = circup.command_utils.find_device()

for lib_file in args.lib:
    if dest is None:
        raise BoardNotFound(
            "CircuitPython board not found.  "
            "Check if the board is connected, and the host operating system can find it."
        )
    from_path = circup.os.path.join(cwd, lib_file)
    to_path = circup.os.path.join(dest, "lib", lib_file)
    print("from:", from_path)
    print("to:", to_path)
    shutil.copyfile(from_path, to_path)
if args.code is not None:
    if dest is None:
        raise BoardNotFound(
            "CircuitPython board not found.  "
            "Check if the board is connected, and the host operating system can find it."
        )
    from_path = circup.os.path.join(cwd, args.code)
    to_path = circup.os.path.join(dest, "code.py")
    print("from:", from_path)
    print("to:", to_path)
    code = open(from_path, "r").readlines()  # pylint: disable=consider-using-with
    with open(to_path, "w") as write_file:
        for line in code:
            for var, value in args.var.items():
                line_start = f"{var} ="
                if line.startswith(line_start):
                    print(f"new global:{var} = {value}")
                    line = f"{var} = {value}"
            write_file.write(line)
