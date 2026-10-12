#!/usr/bin/env python3
"""Read typed values from a PE file by virtual address.

Usage: peread.py <exe> <type> <va> [count]     type: f64 f32 i32 u8 i16 str
"""
import struct
import sys

FMT = {"f64": "<d", "f32": "<f", "i32": "<i", "u8": "<B", "i16": "<h"}


def load(path):
    data = open(path, "rb").read()
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    nsec = struct.unpack_from("<H", data, pe + 6)[0]
    opt = struct.unpack_from("<H", data, pe + 20)[0]
    base = struct.unpack_from("<I", data, pe + 24 + 28)[0]
    secs = []
    for i in range(nsec):
        o = pe + 24 + opt + 40 * i
        vsize, va, rsize, raw = struct.unpack_from("<4I", data, o + 8)
        secs.append((base + va, max(vsize, rsize), raw, rsize))
    return data, secs


def offset(secs, va):
    for start, size, raw, rsize in secs:
        if start <= va < start + size and va - start < rsize:
            return raw + va - start
    raise SystemExit(f"{va:#x}: not in file")


def main():
    data, secs = load(sys.argv[1])
    kind, va = sys.argv[2], int(sys.argv[3], 16)
    count = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    off = offset(secs, va)
    if kind == "str":
        print(data[off:data.index(b"\0", off)].decode("latin-1"))
        return
    size = struct.calcsize(FMT[kind])
    print(" ".join(str(struct.unpack_from(FMT[kind], data, off + i * size)[0]) for i in range(count)))


if __name__ == "__main__":
    main()
