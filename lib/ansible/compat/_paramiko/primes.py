# Copyright (C) 2003-2007  Robey Pointer <robeypointer@gmail.com>
#
# This file is part of paramiko.
#
# Paramiko is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# Paramiko is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Paramiko; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA.

"""
Utility functions for dealing with primes.
"""

import os

from paramiko import util
from paramiko.py3compat import byte_mask, long
from paramiko.ssh_exception import SSHException


def _roll_random(n):
    """returns a random # from 0 to N-1"""
    bits = util.bit_length(n - 1)
    byte_count = (bits + 7) // 8
    hbyte_mask = pow(2, bits % 8) - 1

    # so here's the plan:
    # we fetch as many random bits as we'd need to fit N-1, and if the
    # generated number is >= N, we try again.  in the worst case (N-1 is a
    # power of 2), we have slightly better than 50% odds of getting one that
    # fits, so i can't guarantee that this loop will ever finish, but the odds
    # of it looping forever should be infinitesimal.
    while True:
        x = os.urandom(byte_count)
        if hbyte_mask > 0:
            x = byte_mask(x[0], hbyte_mask) + x[1:]
        num = util.inflate_long(x, 1)
        if num < n:
            break
    return num


class ModulusPack(object):
    """
    convenience object for holding the contents of the /etc/ssh/moduli file,
    on systems that have such a file.
    """

    def __init__(self):
        # pack is a hash of: bits -> [ (generator, modulus) ... ]
        self.pack = {}
        self.discarded = []

    def _parse_modulus(self, line):
        (
            timestamp,
            mod_type,
            tests,
            tries,
            size,
            generator,
            modulus,
        ) = line.split()
        mod_type = int(mod_type)
        tests = int(tests)
        tries = int(tries)
        size = int(size)
        generator = int(generator)
        modulus = long(modulus, 16)

        # weed out primes that aren't at least:
        # type 2 (meets basic structural requirements)
        # test 4 (more than just a small-prime sieve)
        # tries < 100 if test & 4 (at least 100 tries of miller-rabin)
        if (
            mod_type < 2
            or tests < 4
            or (tests & 4 and tests < 8 and tries < 100)
        ):
            self.discarded.append(
                (modulus, "does not meet basic requirements")
            )
            return
        if generator == 0:
            generator = 2

        # there's a bug in the ssh "moduli" file (yeah, i know: shock! dismay!
        # call cnn!) where it understates the bit lengths of these primes by 1.
        # this is okay.
        bl = util.bit_length(modulus)
        if (bl != size) and (bl != size + 1):
            self.discarded.append(
                (modulus, "incorrectly reported bit length {}".format(size))
            )
            return
        if bl not in self.pack:
            self.pack[bl] = []
        self.pack[bl].append((generator, modulus))

    def read_file(self, filename):
        """
        :raises IOError: passed from any file operations that fail.
        """
        self.pack = {}
        with open(filename, "r") as f:
            for line in f:
                line = line.strip()
                if (len(line) == 0) or (line[0] == "#"):
                    continue
                try:
                    self._parse_modulus(line)
                except:
                    continue

    def get_modulus(self, min, prefer, max):
        bitsizes = sorted(self.pack.keys())
        if len(bitsizes) == 0:
            raise SSHException("no moduli available")
        good = -1
        # find nearest bitsize >= preferred
        for b in bitsizes:
            if (b >= prefer) and (b <= max) and (b < good or good == -1):
                good = b
        # if that failed, find greatest bitsize >= min
        if good == -1:
            for b in bitsizes:
                if (b >= min) and (b <= max) and (b > good):
                    good = b
        if good == -1:
            # their entire (min, max) range has no intersection with our range.
            # if their range is below ours, pick the smallest.  otherwise pick
            # the largest.  it'll be out of their range requirement either way,
            # but we'll be sending them the closest one we have.
            good = bitsizes[0]
            if min > good:
                good = bitsizes[-1]
        # now pick a random modulus of this bitsize
        n = _roll_random(len(self.pack[good]))
        return self.pack[good][n]
