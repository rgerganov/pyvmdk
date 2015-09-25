#!/usr/bin/env python
from __future__ import division

import struct
import zlib
import sys


def roundup(x, y):
    return (x + y - 1) // y * y

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print 'Usage <streamOpt.vmdk> <flat.vmdk>'
        sys.exit(1)
    global fin
    fin = open(sys.argv[1], 'rb')
    fout = open(sys.argv[2], 'wb')

    header = fin.read(512)
    (magic, ver, flags, capacity, grain_size, desc_off,
     desc_size, gte_per_gt, rgd_off, gd_off, overhead, unc,
     c1, c2, c3, c4, algo, pad) = struct.unpack('<IIIQQQQIQQQ?ccccH433s', header)

    assert magic == 0x564d444b
    fin.seek(desc_off * 512)
    descriptor = fin.read(desc_size * 512)
    print descriptor.rstrip('\x00')
    print 'capacity in sectors', capacity
    print 'capacity in grains', capacity // grain_size
    print 'overhead', overhead
    fin.seek(overhead * 512)

    while True:
        marker = fin.read(12)
        lba, size = struct.unpack('<QI', marker)
        print '>>', lba, size
        if size > 0:
            data = fin.read(size)
            raw_data = zlib.decompress(data)
            fout.seek(lba * 512)
            print 'len(raw)', len(raw_data)
            fout.write(raw_data)
            size += 12
            fin.seek(roundup(size, 512) - size, 1)
        else:
            data = fin.read(12)
            type, value = struct.unpack('<IQ', data)
            print '>>>', type, value
            break
    fin.close()
    fout.seek(0, 2)
    written_bytes = fout.tell()
    print capacity * 512
    print written_bytes
    fout.write((capacity * 512 - written_bytes) * '\x00')
    fout.close()
