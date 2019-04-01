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
Variant on `KexGroup1 <paramiko.kex_group1.KexGroup1>` where the prime "p" and
generator "g" are provided by the server.  A bit more work is required on the
client side, and a **lot** more on the server side.
"""

import os
from hashlib import sha1, sha256

from paramiko import util
from paramiko.common import DEBUG
from paramiko.message import Message
from paramiko.py3compat import byte_chr, byte_ord, byte_mask
from paramiko.ssh_exception import SSHException


(
    _MSG_KEXDH_GEX_REQUEST_OLD,
    _MSG_KEXDH_GEX_GROUP,
    _MSG_KEXDH_GEX_INIT,
    _MSG_KEXDH_GEX_REPLY,
    _MSG_KEXDH_GEX_REQUEST,
) = range(30, 35)

(
    c_MSG_KEXDH_GEX_REQUEST_OLD,
    c_MSG_KEXDH_GEX_GROUP,
    c_MSG_KEXDH_GEX_INIT,
    c_MSG_KEXDH_GEX_REPLY,
    c_MSG_KEXDH_GEX_REQUEST,
) = [byte_chr(c) for c in range(30, 35)]


class KexGex(object):

    name = "diffie-hellman-group-exchange-sha1"
    min_bits = 1024
    max_bits = 8192
    preferred_bits = 2048
    hash_algo = sha1

    def __init__(self, transport):
        self.transport = transport
        self.p = None
        self.q = None
        self.g = None
        self.x = None
        self.e = None
        self.f = None
        self.old_style = False

    def start_kex(self, _test_old_style=False):
        if self.transport.server_mode:
            self.transport._expect_packet(
                _MSG_KEXDH_GEX_REQUEST, _MSG_KEXDH_GEX_REQUEST_OLD
            )
            return
        # request a bit range: we accept (min_bits) to (max_bits), but prefer
        # (preferred_bits).  according to the spec, we shouldn't pull the
        # minimum up above 1024.
        m = Message()
        if _test_old_style:
            # only used for unit tests: we shouldn't ever send this
            m.add_byte(c_MSG_KEXDH_GEX_REQUEST_OLD)
            m.add_int(self.preferred_bits)
            self.old_style = True
        else:
            m.add_byte(c_MSG_KEXDH_GEX_REQUEST)
            m.add_int(self.min_bits)
            m.add_int(self.preferred_bits)
            m.add_int(self.max_bits)
        self.transport._send_message(m)
        self.transport._expect_packet(_MSG_KEXDH_GEX_GROUP)

    def parse_next(self, ptype, m):
        if ptype == _MSG_KEXDH_GEX_REQUEST:
            return self._parse_kexdh_gex_request(m)
        elif ptype == _MSG_KEXDH_GEX_GROUP:
            return self._parse_kexdh_gex_group(m)
        elif ptype == _MSG_KEXDH_GEX_INIT:
            return self._parse_kexdh_gex_init(m)
        elif ptype == _MSG_KEXDH_GEX_REPLY:
            return self._parse_kexdh_gex_reply(m)
        elif ptype == _MSG_KEXDH_GEX_REQUEST_OLD:
            return self._parse_kexdh_gex_request_old(m)
        msg = "KexGex {} asked to handle packet type {:d}"
        raise SSHException(msg.format(self.name, ptype))

    # ...internals...

    def _generate_x(self):
        # generate an "x" (1 < x < (p-1)/2).
        q = (self.p - 1) // 2
        qnorm = util.deflate_long(q, 0)
        qhbyte = byte_ord(qnorm[0])
        byte_count = len(qnorm)
        qmask = 0xff
        while not (qhbyte & 0x80):
            qhbyte <<= 1
            qmask >>= 1
        while True:
            x_bytes = os.urandom(byte_count)
            x_bytes = byte_mask(x_bytes[0], qmask) + x_bytes[1:]
            x = util.inflate_long(x_bytes, 1)
            if (x > 1) and (x < q):
                break
        self.x = x

    def _parse_kexdh_gex_request(self, m):
        minbits = m.get_int()
        preferredbits = m.get_int()
        maxbits = m.get_int()
        # smoosh the user's preferred size into our own limits
        if preferredbits > self.max_bits:
            preferredbits = self.max_bits
        if preferredbits < self.min_bits:
            preferredbits = self.min_bits
        # fix min/max if they're inconsistent.  technically, we could just pout
        # and hang up, but there's no harm in giving them the benefit of the
        # doubt and just picking a bitsize for them.
        if minbits > preferredbits:
            minbits = preferredbits
        if maxbits < preferredbits:
            maxbits = preferredbits
        # now save a copy
        self.min_bits = minbits
        self.preferred_bits = preferredbits
        self.max_bits = maxbits
        # generate prime
        pack = self.transport._get_modulus_pack()
        if pack is None:
            raise SSHException("Can't do server-side gex with no modulus pack")
        self.transport._log(
            DEBUG,
            "Picking p ({} <= {} <= {} bits)".format(
                minbits, preferredbits, maxbits
            ),
        )
        self.g, self.p = pack.get_modulus(minbits, preferredbits, maxbits)
        m = Message()
        m.add_byte(c_MSG_KEXDH_GEX_GROUP)
        m.add_mpint(self.p)
        m.add_mpint(self.g)
        self.transport._send_message(m)
        self.transport._expect_packet(_MSG_KEXDH_GEX_INIT)

    def _parse_kexdh_gex_request_old(self, m):
        # same as above, but without min_bits or max_bits (used by older
        # clients like putty)
        self.preferred_bits = m.get_int()
        # smoosh the user's preferred size into our own limits
        if self.preferred_bits > self.max_bits:
            self.preferred_bits = self.max_bits
        if self.preferred_bits < self.min_bits:
            self.preferred_bits = self.min_bits
        # generate prime
        pack = self.transport._get_modulus_pack()
        if pack is None:
            raise SSHException("Can't do server-side gex with no modulus pack")
        self.transport._log(
            DEBUG, "Picking p (~ {} bits)".format(self.preferred_bits)
        )
        self.g, self.p = pack.get_modulus(
            self.min_bits, self.preferred_bits, self.max_bits
        )
        m = Message()
        m.add_byte(c_MSG_KEXDH_GEX_GROUP)
        m.add_mpint(self.p)
        m.add_mpint(self.g)
        self.transport._send_message(m)
        self.transport._expect_packet(_MSG_KEXDH_GEX_INIT)
        self.old_style = True

    def _parse_kexdh_gex_group(self, m):
        self.p = m.get_mpint()
        self.g = m.get_mpint()
        # reject if p's bit length < 1024 or > 8192
        bitlen = util.bit_length(self.p)
        if (bitlen < 1024) or (bitlen > 8192):
            raise SSHException(
                "Server-generated gex p (don't ask) is out of range "
                "({} bits)".format(bitlen)
            )
        self.transport._log(DEBUG, "Got server p ({} bits)".format(bitlen))
        self._generate_x()
        # now compute e = g^x mod p
        self.e = pow(self.g, self.x, self.p)
        m = Message()
        m.add_byte(c_MSG_KEXDH_GEX_INIT)
        m.add_mpint(self.e)
        self.transport._send_message(m)
        self.transport._expect_packet(_MSG_KEXDH_GEX_REPLY)

    def _parse_kexdh_gex_init(self, m):
        self.e = m.get_mpint()
        if (self.e < 1) or (self.e > self.p - 1):
            raise SSHException('Client kex "e" is out of range')
        self._generate_x()
        self.f = pow(self.g, self.x, self.p)
        K = pow(self.e, self.x, self.p)
        key = self.transport.get_server_key().asbytes()
        # okay, build up the hash H of
        # (V_C || V_S || I_C || I_S || K_S || min || n || max || p || g || e || f || K)  # noqa
        hm = Message()
        hm.add(
            self.transport.remote_version,
            self.transport.local_version,
            self.transport.remote_kex_init,
            self.transport.local_kex_init,
            key,
        )
        if not self.old_style:
            hm.add_int(self.min_bits)
        hm.add_int(self.preferred_bits)
        if not self.old_style:
            hm.add_int(self.max_bits)
        hm.add_mpint(self.p)
        hm.add_mpint(self.g)
        hm.add_mpint(self.e)
        hm.add_mpint(self.f)
        hm.add_mpint(K)
        H = self.hash_algo(hm.asbytes()).digest()
        self.transport._set_K_H(K, H)
        # sign it
        sig = self.transport.get_server_key().sign_ssh_data(H)
        # send reply
        m = Message()
        m.add_byte(c_MSG_KEXDH_GEX_REPLY)
        m.add_string(key)
        m.add_mpint(self.f)
        m.add_string(sig)
        self.transport._send_message(m)
        self.transport._activate_outbound()

    def _parse_kexdh_gex_reply(self, m):
        host_key = m.get_string()
        self.f = m.get_mpint()
        sig = m.get_string()
        if (self.f < 1) or (self.f > self.p - 1):
            raise SSHException('Server kex "f" is out of range')
        K = pow(self.f, self.x, self.p)
        # okay, build up the hash H of
        # (V_C || V_S || I_C || I_S || K_S || min || n || max || p || g || e || f || K)  # noqa
        hm = Message()
        hm.add(
            self.transport.local_version,
            self.transport.remote_version,
            self.transport.local_kex_init,
            self.transport.remote_kex_init,
            host_key,
        )
        if not self.old_style:
            hm.add_int(self.min_bits)
        hm.add_int(self.preferred_bits)
        if not self.old_style:
            hm.add_int(self.max_bits)
        hm.add_mpint(self.p)
        hm.add_mpint(self.g)
        hm.add_mpint(self.e)
        hm.add_mpint(self.f)
        hm.add_mpint(K)
        self.transport._set_K_H(K, self.hash_algo(hm.asbytes()).digest())
        self.transport._verify_key(host_key, sig)
        self.transport._activate_outbound()


class KexGexSHA256(KexGex):
    name = "diffie-hellman-group-exchange-sha256"
    hash_algo = sha256
