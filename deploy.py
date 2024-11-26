# SPDX-FileCopyrightText: Copyright (c) 2024 Dana Runge
#
# SPDX-License-Identifier: Unlicense
"Deploy tests to a microcontroller"
import argparse
import os
import shutil

import circup


class StoreVar(argparse.Action):
    """Capture variables for code.py."""

    def __call__(self, _, namespace, vals, option_string=None):
        dest = getattr(namespace, self.dest, None)
        if not dest:
            dest = {}
            setattr(namespace, self.dest, dest)
        attr, _, val = vals.partition("=")
        if not attr.isidentifier():
            raise argparse.ArgumentTypeError(
                "--val {attr} not a legal Python identifier."
            )
        if not attr.isupper():
            raise argparse.ArgumentTypeError("--val {attr} is not upper case.")
        # Get the from the environment, keep val if not found.
        val = os.environ.get(attr, val)
        dest[attr] = val


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
    from_path = circup.os.path.join(cwd, lib_file)
    to_path = circup.os.path.join(dest, "lib", lib_file)
    print("from:", from_path)
    print("to:", to_path)
    shutil.copyfile(from_path, to_path)
if args.code is not None:
    from_path = circup.os.path.join(cwd, args.code)
    to_path = circup.os.path.join(dest, "code.py")
    print("from:", from_path)
    print("to:", to_path)
    code = open(from_path, "r").readlines()  # pylint: disable=consider-using-with
    with open(to_path, "w") as write_file:
        for line in code:
            for var, val in args.var.items():
                line_start = f"{var} ="
                if line.startswith(line_start):
                    print(f"new global:{var} = {val}")
                    line = f"{var} = {val}"
            write_file.write(line)
