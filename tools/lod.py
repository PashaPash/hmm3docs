#!/usr/bin/env python3
"""Read Heroes III .lod archives: list entries or extract text tables.

Usage:
  lod.py list  <archive.lod> [suffix]
  lod.py dump  <archive.lod> <outdir> [suffix]   (default suffix .TXT)
"""
import struct
import sys
import zlib
from pathlib import Path


def entries(path):
    with open(path, "rb") as f:
        head = f.read(92)
        if head[:4] != b"LOD\0":
            raise SystemExit(f"{path}: not a LOD archive")
        count = struct.unpack_from("<I", head, 8)[0]
        table = f.read(32 * count)
    for i in range(count):
        raw = table[32 * i:32 * i + 32]
        name = raw[:16].split(b"\0")[0].decode("latin-1")
        offset, size, kind, csize = struct.unpack_from("<4I", raw, 16)
        yield name, offset, size, kind, csize


def read(path, offset, size, csize):
    with open(path, "rb") as f:
        f.seek(offset)
        data = f.read(csize or size)
    return zlib.decompress(data) if csize else data


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    cmd, path = sys.argv[1], sys.argv[2]
    if cmd == "list":
        suffix = sys.argv[3].upper() if len(sys.argv) > 3 else ""
        for name, _, size, kind, _ in entries(path):
            if name.upper().endswith(suffix):
                print(f"{name}\t{size}\t{kind}")
    elif cmd == "dump":
        out = Path(sys.argv[3])
        suffix = sys.argv[4].upper() if len(sys.argv) > 4 else ".TXT"
        out.mkdir(parents=True, exist_ok=True)
        for name, offset, size, _, csize in entries(path):
            if name.upper().endswith(suffix):
                (out / name.upper()).write_bytes(read(path, offset, size, csize))
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
