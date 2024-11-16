# SPDX-FileCopyrightText: Copyright (c) 2024 Dana Runge
#
# SPDX-License-Identifier: Unlicense
"Deploy tests to a microcontroller"

import argparse
import shutil

import circup

DMX_PIN_IN = "DMX_PIN"
DMX_PIN_OUT = "DMX_PIN = {}\n".format

parser = argparse.ArgumentParser(description="Upload code to the microcontroller.")
parser.add_argument("--code", nargs="?", help="File to deploy as code.py")
parser.add_argument("--pin", nargs="?", default="board.D1", help="Map DMX_PIN to this")
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
            if line.startswith(DMX_PIN_IN):
                line = DMX_PIN_OUT(args.pin)  # pylint: disable=invalid-name
            write_file.write(line)
