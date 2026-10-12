#!/usr/bin/env python3
"""Show immediate ECX/EDX arguments loaded just before calls to a target.

Usage: callargs.py <exe> <target va> <func va> <func size> [...]
Heuristic byte scan (no disassembler): looks for `mov ecx/edx, imm32` in the
16 bytes before each `call target` inside the given function ranges.
"""
import struct
import sys

import peread


def main():
    data, secs = peread.load(sys.argv[1])
    target = int(sys.argv[2], 16)
    rest = sys.argv[3:]
    for fva, size in zip(rest[0::2], rest[1::2]):
        fva, size = int(fva, 16), int(size)
        off = peread.offset(secs, fva)
        code = data[off:off + size]
        for i in range(len(code) - 5):
            if code[i] != 0xE8:
                continue
            dest = fva + i + 5 + struct.unpack_from("<i", code, i + 1)[0]
            if dest != target:
                continue
            args = {}
            for j in range(max(0, i - 16), i - 4):
                if code[j] == 0xB9:
                    args["ecx"] = struct.unpack_from("<i", code, j + 1)[0]
                elif code[j] == 0xBA:
                    args["edx"] = struct.unpack_from("<i", code, j + 1)[0]
            print(f"{fva:#x}: call at {fva + i:#x} {args} bytes={code[max(0, i - 12):i].hex(' ')}")


if __name__ == "__main__":
    main()
