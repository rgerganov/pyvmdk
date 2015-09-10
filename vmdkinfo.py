#!/usr/bin/env python
import struct
import sys


def vmdk_info(file):
    f = open(file, 'rb')
    data = f.read(512)
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
    print('VMDK version: {0}'.format(ver))
    print('Flags: {0:b}'.format(flags))
    if flags & 1:
        print('  valid new line')
    if flags & 2:
        print('  redundant grain table')
    if flags & 4:
        print('  zeroed-grain GTE will be used')
    if flags & (1 << 16):
        print('  the grains are compressed')
    if flags & (1 << 17):
        print('  metadata markers exist')
    print('Capacity (sectors): {0}'.format(capacity))
    print('Capacity (KB): {0}'.format(capacity * 512 / 1024))
    print('Grain size: {0}'.format(grain_size))
    print('Descriptor offset: {0}'.format(desc_off))
    print('Descriptor size: {0}'.format(desc_size))
    print('RGD offset: {0}'.format(rgd_off))
    print('GD offset: {0}'.format(gd_off))
    print('Metadata overhead: {0}'.format(overhead))
    print('Unclean shutdown: {0}'.format(unc))
    if not (c1 == '\n' and c2 == ' ' and c3 == '\r' and c4 == '\n'):
        print('!!! The extent is corrupted !!!')
    print('Compress algorithm: {0}'.format(algo))
    print('\n=========== Descriptor BEGIN ===================')
    f.seek(desc_off * 512)
    descriptor = f.read(desc_size * 512)
    print(descriptor)
    print('=========== Descriptor END ===================')
    f.close()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: {0} <foo.vmdk>".format(sys.argv[0]))
        sys.exit(1)
    vmdk_info(sys.argv[1])
