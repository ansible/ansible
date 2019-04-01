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
Standard SSH key exchange ("kex" if you wanna sound cool).  Diffie-Hellman of
1024 bit key halves, using a known "p" prime and "g" generator.
"""

import os
from hashlib import sha1

from paramiko import util
from paramiko.common import max_byte, zero_byte
from paramiko.message import Message
from paramiko.py3compat import byte_chr, long, byte_mask
from paramiko.ssh_exception import SSHException


_MSG_KEXDH_INIT, _MSG_KEXDH_REPLY = range(30, 32)
c_MSG_KEXDH_INIT, c_MSG_KEXDH_REPLY = [byte_chr(c) for c in range(30, 32)]

b7fffffffffffffff = byte_chr(0x7f) + max_byte * 7
b0000000000000000 = zero_byte * 8


class KexGroup1(object):

    # draft-ietf-secsh-transport-09.txt, page 17
    P = 0xFFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD129024E088A67CC74020BBEA63B139B22514A08798E3404DDEF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7EDEE386BFB5A899FA5AE9F24117C4B1FE649286651ECE65381FFFFFFFFFFFFFFFF  # noqa
    G = 2

    name = "diffie-hellman-group1-sha1"
    hash_algo = sha1

    def __init__(self, transport):
        self.transport = transport
        self.x = long(0)
        self.e = long(0)
        self.f = long(0)

    def start_kex(self):
        self._generate_x()
        if self.transport.server_mode:
            # compute f = g^x mod p, but don't send it yet
            self.f = pow(self.G, self.x, self.P)
            self.transport._expect_packet(_MSG_KEXDH_INIT)
            return
        # compute e = g^x mod p (where g=2), and send it
        self.e = pow(self.G, self.x, self.P)
        m = Message()
        m.add_byte(c_MSG_KEXDH_INIT)
        m.add_mpint(self.e)
        self.transport._send_message(m)
        self.transport._expect_packet(_MSG_KEXDH_REPLY)

    def parse_next(self, ptype, m):
        if self.transport.server_mode and (ptype == _MSG_KEXDH_INIT):
            return self._parse_kexdh_init(m)
        elif not self.transport.server_mode and (ptype == _MSG_KEXDH_REPLY):
            return self._parse_kexdh_reply(m)
        msg = "KexGroup1 asked to handle packet type {:d}"
        raise SSHException(msg.format(ptype))

    # ...internals...

    def _generate_x(self):
        # generate an "x" (1 < x < q), where q is (p-1)/2.
        # p is a 128-byte (1024-bit) number, where the first 64 bits are 1.
        # therefore q can be approximated as a 2^1023.  we drop the subset of
        # potential x where the first 63 bits are 1, because some of those
        # will be larger than q (but this is a tiny tiny subset of
        # potential x).
        while 1:
            x_bytes = os.urandom(128)
            x_bytes = byte_mask(x_bytes[0], 0x7f) + x_bytes[1:]
            if (
                x_bytes[:8] != b7fffffffffffffff
                and x_bytes[:8] != b0000000000000000
            ):
                break
        self.x = util.inflate_long(x_bytes)

    def _parse_kexdh_reply(self, m):
        # client mode
        host_key = m.get_string()
        self.f = m.get_mpint()
        if (self.f < 1) or (self.f > self.P - 1):
            raise SSHException('Server kex "f" is out of range')
        sig = m.get_binary()
        K = pow(self.f, self.x, self.P)
        # okay, build up the hash H of
        # (V_C || V_S || I_C || I_S || K_S || e || f || K)
        hm = Message()
        hm.add(
            self.transport.local_version,
            self.transport.remote_version,
            self.transport.local_kex_init,
            self.transport.remote_kex_init,
        )
        hm.add_string(host_key)
        hm.add_mpint(self.e)
        hm.add_mpint(self.f)
        hm.add_mpint(K)
        self.transport._set_K_H(K, sha1(hm.asbytes()).digest())
        self.transport._verify_key(host_key, sig)
        self.transport._activate_outbound()

    def _parse_kexdh_init(self, m):
        # server mode
        self.e = m.get_mpint()
        if (self.e < 1) or (self.e > self.P - 1):
            raise SSHException('Client kex "e" is out of range')
        K = pow(self.e, self.x, self.P)
        key = self.transport.get_server_key().asbytes()
        # okay, build up the hash H of
        # (V_C || V_S || I_C || I_S || K_S || e || f || K)
        hm = Message()
        hm.add(
            self.transport.remote_version,
            self.transport.local_version,
            self.transport.remote_kex_init,
            self.transport.local_kex_init,
        )
        hm.add_string(key)
        hm.add_mpint(self.e)
        hm.add_mpint(self.f)
        hm.add_mpint(K)
        H = sha1(hm.asbytes()).digest()
        self.transport._set_K_H(K, H)
        # sign it
        sig = self.transport.get_server_key().sign_ssh_data(H)
        # send reply
        m = Message()
        m.add_byte(c_MSG_KEXDH_REPLY)
        m.add_string(key)
        m.add_mpint(self.f)
        m.add_string(sig)
        self.transport._send_message(m)
        self.transport._activate_outbound()
