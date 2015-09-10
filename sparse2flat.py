#!/usr/bin/env python
from __future__ import division

import re
import struct
import zlib
import sys


def div_round_up(x, y):
    return (x + y - 1) // y


def save_descriptor(descriptor, desc_path, extent_path):
    p = re.compile('RW \d+ SPARSE "(.+?)"')
    m = p.search(descriptor)
    if not m:
        print('Cannot find extent description')
        sys.exit(1)
    descriptor = re.sub('RW (\d+) SPARSE ".+?"',
                        lambda m: 'RW {0} FLAT "{1}" 0'.format(
                            m.group(1), extent_path), descriptor)
    descriptor = re.sub('createType=".+?"', 'createType="monolithicFlat"',
                        descriptor)
    fout = open(desc_path, 'w')
    print('Saving descriptor...')
    fout.write(descriptor.rstrip('\x00'))
    fout.close()


def convert(sparse_path, desc_path):
    fin = open(sparse_path, 'rb')
    data = fin.read(512)
    if len(data) != 512:
        print('not a vmdk file')
        sys.exit(1)
    header = struct.unpack('<IIIQQQQIQQQ?ccccH433s', data)
    (magic, ver, flags, capacity, grain_size, desc_off,
     desc_size, gte_per_gt, rgd_off, gd_off, overhead, unc,
     c1, c2, c3, c4, algo, pad) = header
    if magic != 0x564d444b:
        print('not a vmdk file (wrong magic)')
        sys.exit(1)
    fin.seek(desc_off * 512)
    descriptor = fin.read(desc_size * 512)
    if desc_path.endswith('.vmdk'):
        extent_path = desc_path[:-5] + '-flat.vmdk'
    else:
        extent_path = desc_path + '-flat'
    save_descriptor(descriptor, desc_path, extent_path)
    print('Saving extent ...')
    compressed = (flags & (1 << 16)) > 0
    fout = open(extent_path, 'wb')
    gt_coverage = grain_size * 512
    gd_size = div_round_up(capacity, gt_coverage)
    all_gt = []
    for gde_ind in range(0, gd_size):
        fin.seek(gd_off * 512 + gde_ind * 4)
        gde = fin.read(4)
        gde = struct.unpack('<I', gde)[0]
        fin.seek(gde * 512)
        table = fin.read(2048)
        all_gt.extend(struct.unpack('<512I', table))

    for grain in range(0, capacity // grain_size):
        gte = all_gt[grain]
        if gte == 0 or gte == 1:
            fout.write(grain_size * 512 * '\x00')
        else:
            if compressed:
                fin.seek(gte * 512)
                marker = fin.read(12)
                lba, size = struct.unpack('<QI', marker)
                assert size > 0
                data = fin.read(size)
                raw_data = zlib.decompress(data)
                fout.write(raw_data)
            else:
                fin.seek(gte * 512)
                grain = fin.read(grain_size * 512)
                fout.write(grain)

    remainder = capacity % grain_size
    if remainder > 0:
        grain += 1
        gte = all_gt[grain]
        if gte == 0 or gte == 1:
            fout.write(remainder * 512 * '\x00')
        else:
            if compressed:
                fin.seek(gte * 512)
                marker = fin.read(12)
                lba, size = struct.unpack('<QI', marker)
                assert size > 0
                data = fin.read(size)
                raw_data = zlib.decompress(data)
                fout.write(raw_data)
            else:
                fin.seek(gte * 512)
                grain = fin.read(remainder * 512)
                fout.write(grain)
    fin.close()
    fout.close()

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: {0} <sparse.vmdk> <flat.vmdk>'.format(sys.argv[0]))
        sys.exit(1)
    convert(sys.argv[1], sys.argv[2])
