# Copyright (C) 2003-2007  Robey Pointer <robeypointer@gmail.com>
# Copyright (C) 2013-2014 science + computing ag
# Author: Sebastian Deiss <sebastian.deiss@t-online.de>
#
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
This module provides GSS-API / SSPI Key Exchange as defined in :rfc:`4462`.

.. note:: Credential delegation is not supported in server mode.

.. note::
    `RFC 4462 Section 2.2
    <https://tools.ietf.org/html/rfc4462.html#section-2.2>`_ says we are not
    required to implement GSS-API error messages. Thus, in many methods within
    this module, if an error occurs an exception will be thrown and the
    connection will be terminated.

.. seealso:: :doc:`/api/ssh_gss`

.. versionadded:: 1.15
"""

import os
from hashlib import sha1

from paramiko.common import DEBUG, max_byte, zero_byte
from paramiko import util
from paramiko.message import Message
from paramiko.py3compat import byte_chr, byte_mask, byte_ord
from paramiko.ssh_exception import SSHException


(
    MSG_KEXGSS_INIT,
    MSG_KEXGSS_CONTINUE,
    MSG_KEXGSS_COMPLETE,
    MSG_KEXGSS_HOSTKEY,
    MSG_KEXGSS_ERROR,
) = range(30, 35)
(MSG_KEXGSS_GROUPREQ, MSG_KEXGSS_GROUP) = range(40, 42)
(
    c_MSG_KEXGSS_INIT,
    c_MSG_KEXGSS_CONTINUE,
    c_MSG_KEXGSS_COMPLETE,
    c_MSG_KEXGSS_HOSTKEY,
    c_MSG_KEXGSS_ERROR,
) = [byte_chr(c) for c in range(30, 35)]
(c_MSG_KEXGSS_GROUPREQ, c_MSG_KEXGSS_GROUP) = [
    byte_chr(c) for c in range(40, 42)
]


class KexGSSGroup1(object):
    """
    GSS-API / SSPI Authenticated Diffie-Hellman Key Exchange as defined in `RFC
    4462 Section 2 <https://tools.ietf.org/html/rfc4462.html#section-2>`_
    """

    # draft-ietf-secsh-transport-09.txt, page 17
    P = 0xFFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD129024E088A67CC74020BBEA63B139B22514A08798E3404DDEF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7EDEE386BFB5A899FA5AE9F24117C4B1FE649286651ECE65381FFFFFFFFFFFFFFFF  # noqa
    G = 2
    b7fffffffffffffff = byte_chr(0x7f) + max_byte * 7  # noqa
    b0000000000000000 = zero_byte * 8  # noqa
    NAME = "gss-group1-sha1-toWM5Slw5Ew8Mqkay+al2g=="

    def __init__(self, transport):
        self.transport = transport
        self.kexgss = self.transport.kexgss_ctxt
        self.gss_host = None
        self.x = 0
        self.e = 0
        self.f = 0

    def start_kex(self):
        """
        Start the GSS-API / SSPI Authenticated Diffie-Hellman Key Exchange.
        """
        self._generate_x()
        if self.transport.server_mode:
            # compute f = g^x mod p, but don't send it yet
            self.f = pow(self.G, self.x, self.P)
            self.transport._expect_packet(MSG_KEXGSS_INIT)
            return
        # compute e = g^x mod p (where g=2), and send it
        self.e = pow(self.G, self.x, self.P)
        # Initialize GSS-API Key Exchange
        self.gss_host = self.transport.gss_host
        m = Message()
        m.add_byte(c_MSG_KEXGSS_INIT)
        m.add_string(self.kexgss.ssh_init_sec_context(target=self.gss_host))
        m.add_mpint(self.e)
        self.transport._send_message(m)
        self.transport._expect_packet(
            MSG_KEXGSS_HOSTKEY,
            MSG_KEXGSS_CONTINUE,
            MSG_KEXGSS_COMPLETE,
            MSG_KEXGSS_ERROR,
        )

    def parse_next(self, ptype, m):
        """
        Parse the next packet.

        :param ptype: The (string) type of the incoming packet
        :param `.Message` m: The paket content
        """
        if self.transport.server_mode and (ptype == MSG_KEXGSS_INIT):
            return self._parse_kexgss_init(m)
        elif not self.transport.server_mode and (ptype == MSG_KEXGSS_HOSTKEY):
            return self._parse_kexgss_hostkey(m)
        elif self.transport.server_mode and (ptype == MSG_KEXGSS_CONTINUE):
            return self._parse_kexgss_continue(m)
        elif not self.transport.server_mode and (ptype == MSG_KEXGSS_COMPLETE):
            return self._parse_kexgss_complete(m)
        elif ptype == MSG_KEXGSS_ERROR:
            return self._parse_kexgss_error(m)
        msg = "GSS KexGroup1 asked to handle packet type {:d}"
        raise SSHException(msg.format(ptype))

    # ##  internals...

    def _generate_x(self):
        """
        generate an "x" (1 < x < q), where q is (p-1)/2.
        p is a 128-byte (1024-bit) number, where the first 64 bits are 1.
        therefore q can be approximated as a 2^1023.  we drop the subset of
        potential x where the first 63 bits are 1, because some of those will
        be larger than q (but this is a tiny tiny subset of potential x).
        """
        while 1:
            x_bytes = os.urandom(128)
            x_bytes = byte_mask(x_bytes[0], 0x7f) + x_bytes[1:]
            first = x_bytes[:8]
            if first not in (self.b7fffffffffffffff, self.b0000000000000000):
                break
        self.x = util.inflate_long(x_bytes)

    def _parse_kexgss_hostkey(self, m):
        """
        Parse the SSH2_MSG_KEXGSS_HOSTKEY message (client mode).

        :param `.Message` m: The content of the SSH2_MSG_KEXGSS_HOSTKEY message
        """
        # client mode
        host_key = m.get_string()
        self.transport.host_key = host_key
        sig = m.get_string()
        self.transport._verify_key(host_key, sig)
        self.transport._expect_packet(MSG_KEXGSS_CONTINUE, MSG_KEXGSS_COMPLETE)

    def _parse_kexgss_continue(self, m):
        """
        Parse the SSH2_MSG_KEXGSS_CONTINUE message.

        :param `.Message` m: The content of the SSH2_MSG_KEXGSS_CONTINUE
            message
        """
        if not self.transport.server_mode:
            srv_token = m.get_string()
            m = Message()
            m.add_byte(c_MSG_KEXGSS_CONTINUE)
            m.add_string(
                self.kexgss.ssh_init_sec_context(
                    target=self.gss_host, recv_token=srv_token
                )
            )
            self.transport.send_message(m)
            self.transport._expect_packet(
                MSG_KEXGSS_CONTINUE, MSG_KEXGSS_COMPLETE, MSG_KEXGSS_ERROR
            )
        else:
            pass

    def _parse_kexgss_complete(self, m):
        """
        Parse the SSH2_MSG_KEXGSS_COMPLETE message (client mode).

        :param `.Message` m: The content of the
            SSH2_MSG_KEXGSS_COMPLETE message
        """
        # client mode
        if self.transport.host_key is None:
            self.transport.host_key = NullHostKey()
        self.f = m.get_mpint()
        if (self.f < 1) or (self.f > self.P - 1):
            raise SSHException('Server kex "f" is out of range')
        mic_token = m.get_string()
        # This must be TRUE, if there is a GSS-API token in this message.
        bool = m.get_boolean()
        srv_token = None
        if bool:
            srv_token = m.get_string()
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
        hm.add_string(self.transport.host_key.__str__())
        hm.add_mpint(self.e)
        hm.add_mpint(self.f)
        hm.add_mpint(K)
        H = sha1(str(hm)).digest()
        self.transport._set_K_H(K, H)
        if srv_token is not None:
            self.kexgss.ssh_init_sec_context(
                target=self.gss_host, recv_token=srv_token
            )
            self.kexgss.ssh_check_mic(mic_token, H)
        else:
            self.kexgss.ssh_check_mic(mic_token, H)
        self.transport.gss_kex_used = True
        self.transport._activate_outbound()

    def _parse_kexgss_init(self, m):
        """
        Parse the SSH2_MSG_KEXGSS_INIT message (server mode).

        :param `.Message` m: The content of the SSH2_MSG_KEXGSS_INIT message
        """
        # server mode
        client_token = m.get_string()
        self.e = m.get_mpint()
        if (self.e < 1) or (self.e > self.P - 1):
            raise SSHException('Client kex "e" is out of range')
        K = pow(self.e, self.x, self.P)
        self.transport.host_key = NullHostKey()
        key = self.transport.host_key.__str__()
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
        srv_token = self.kexgss.ssh_accept_sec_context(
            self.gss_host, client_token
        )
        m = Message()
        if self.kexgss._gss_srv_ctxt_status:
            mic_token = self.kexgss.ssh_get_mic(
                self.transport.session_id, gss_kex=True
            )
            m.add_byte(c_MSG_KEXGSS_COMPLETE)
            m.add_mpint(self.f)
            m.add_string(mic_token)
            if srv_token is not None:
                m.add_boolean(True)
                m.add_string(srv_token)
            else:
                m.add_boolean(False)
            self.transport._send_message(m)
            self.transport.gss_kex_used = True
            self.transport._activate_outbound()
        else:
            m.add_byte(c_MSG_KEXGSS_CONTINUE)
            m.add_string(srv_token)
            self.transport._send_message(m)
            self.transport._expect_packet(
                MSG_KEXGSS_CONTINUE, MSG_KEXGSS_COMPLETE, MSG_KEXGSS_ERROR
            )

    def _parse_kexgss_error(self, m):
        """
        Parse the SSH2_MSG_KEXGSS_ERROR message (client mode).
        The server may send a GSS-API error message. if it does, we display
        the error by throwing an exception (client mode).

        :param `.Message` m: The content of the SSH2_MSG_KEXGSS_ERROR message
        :raise SSHException: Contains GSS-API major and minor status as well as
                             the error message and the language tag of the
                             message
        """
        maj_status = m.get_int()
        min_status = m.get_int()
        err_msg = m.get_string()
        m.get_string()  # we don't care about the language!
        raise SSHException(
            """GSS-API Error:
Major Status: {}
Minor Status: {}
Error Message: {}
""".format(
                maj_status, min_status, err_msg
            )
        )


class KexGSSGroup14(KexGSSGroup1):
    """
    GSS-API / SSPI Authenticated Diffie-Hellman Group14 Key Exchange as defined
    in `RFC 4462 Section 2
    <https://tools.ietf.org/html/rfc4462.html#section-2>`_
    """

    P = 0xFFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD129024E088A67CC74020BBEA63B139B22514A08798E3404DDEF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7EDEE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3DC2007CB8A163BF0598DA48361C55D39A69163FA8FD24CF5F83655D23DCA3AD961C62F356208552BB9ED529077096966D670C354E4ABC9804F1746C08CA18217C32905E462E36CE3BE39E772C180E86039B2783A2EC07A28FB5C55DF06F4C52C9DE2BCBF6955817183995497CEA956AE515D2261898FA051015728E5A8AACAA68FFFFFFFFFFFFFFFF  # noqa
    G = 2
    NAME = "gss-group14-sha1-toWM5Slw5Ew8Mqkay+al2g=="


class KexGSSGex(object):
    """
    GSS-API / SSPI Authenticated Diffie-Hellman Group Exchange as defined in
    `RFC 4462 Section 2 <https://tools.ietf.org/html/rfc4462.html#section-2>`_
    """

    NAME = "gss-gex-sha1-toWM5Slw5Ew8Mqkay+al2g=="
    min_bits = 1024
    max_bits = 8192
    preferred_bits = 2048

    def __init__(self, transport):
        self.transport = transport
        self.kexgss = self.transport.kexgss_ctxt
        self.gss_host = None
        self.p = None
        self.q = None
        self.g = None
        self.x = None
        self.e = None
        self.f = None
        self.old_style = False

    def start_kex(self):
        """
        Start the GSS-API / SSPI Authenticated Diffie-Hellman Group Exchange
        """
        if self.transport.server_mode:
            self.transport._expect_packet(MSG_KEXGSS_GROUPREQ)
            return
        # request a bit range: we accept (min_bits) to (max_bits), but prefer
        # (preferred_bits).  according to the spec, we shouldn't pull the
        # minimum up above 1024.
        self.gss_host = self.transport.gss_host
        m = Message()
        m.add_byte(c_MSG_KEXGSS_GROUPREQ)
        m.add_int(self.min_bits)
        m.add_int(self.preferred_bits)
        m.add_int(self.max_bits)
        self.transport._send_message(m)
        self.transport._expect_packet(MSG_KEXGSS_GROUP)

    def parse_next(self, ptype, m):
        """
        Parse the next packet.

        :param ptype: The (string) type of the incoming packet
        :param `.Message` m: The paket content
        """
        if ptype == MSG_KEXGSS_GROUPREQ:
            return self._parse_kexgss_groupreq(m)
        elif ptype == MSG_KEXGSS_GROUP:
            return self._parse_kexgss_group(m)
        elif ptype == MSG_KEXGSS_INIT:
            return self._parse_kexgss_gex_init(m)
        elif ptype == MSG_KEXGSS_HOSTKEY:
            return self._parse_kexgss_hostkey(m)
        elif ptype == MSG_KEXGSS_CONTINUE:
            return self._parse_kexgss_continue(m)
        elif ptype == MSG_KEXGSS_COMPLETE:
            return self._parse_kexgss_complete(m)
        elif ptype == MSG_KEXGSS_ERROR:
            return self._parse_kexgss_error(m)
        msg = "KexGex asked to handle packet type {:d}"
        raise SSHException(msg.format(ptype))

    # ##  internals...

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

    def _parse_kexgss_groupreq(self, m):
        """
        Parse the SSH2_MSG_KEXGSS_GROUPREQ message (server mode).

        :param `.Message` m: The content of the
            SSH2_MSG_KEXGSS_GROUPREQ message
        """
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
            DEBUG,  # noqa
            "Picking p ({} <= {} <= {} bits)".format(
                minbits, preferredbits, maxbits
            ),
        )
        self.g, self.p = pack.get_modulus(minbits, preferredbits, maxbits)
        m = Message()
        m.add_byte(c_MSG_KEXGSS_GROUP)
        m.add_mpint(self.p)
        m.add_mpint(self.g)
        self.transport._send_message(m)
        self.transport._expect_packet(MSG_KEXGSS_INIT)

    def _parse_kexgss_group(self, m):
        """
        Parse the SSH2_MSG_KEXGSS_GROUP message (client mode).

        :param `Message` m: The content of the SSH2_MSG_KEXGSS_GROUP message
        """
        self.p = m.get_mpint()
        self.g = m.get_mpint()
        # reject if p's bit length < 1024 or > 8192
        bitlen = util.bit_length(self.p)
        if (bitlen < 1024) or (bitlen > 8192):
            raise SSHException(
                "Server-generated gex p (don't ask) is out of range "
                "({} bits)".format(bitlen)
            )
        self.transport._log(
            DEBUG, "Got server p ({} bits)".format(bitlen)
        )  # noqa
        self._generate_x()
        # now compute e = g^x mod p
        self.e = pow(self.g, self.x, self.p)
        m = Message()
        m.add_byte(c_MSG_KEXGSS_INIT)
        m.add_string(self.kexgss.ssh_init_sec_context(target=self.gss_host))
        m.add_mpint(self.e)
        self.transport._send_message(m)
        self.transport._expect_packet(
            MSG_KEXGSS_HOSTKEY,
            MSG_KEXGSS_CONTINUE,
            MSG_KEXGSS_COMPLETE,
            MSG_KEXGSS_ERROR,
        )

    def _parse_kexgss_gex_init(self, m):
        """
        Parse the SSH2_MSG_KEXGSS_INIT message (server mode).

        :param `Message` m: The content of the SSH2_MSG_KEXGSS_INIT message
        """
        client_token = m.get_string()
        self.e = m.get_mpint()
        if (self.e < 1) or (self.e > self.p - 1):
            raise SSHException('Client kex "e" is out of range')
        self._generate_x()
        self.f = pow(self.g, self.x, self.p)
        K = pow(self.e, self.x, self.p)
        self.transport.host_key = NullHostKey()
        key = self.transport.host_key.__str__()
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
        hm.add_int(self.min_bits)
        hm.add_int(self.preferred_bits)
        hm.add_int(self.max_bits)
        hm.add_mpint(self.p)
        hm.add_mpint(self.g)
        hm.add_mpint(self.e)
        hm.add_mpint(self.f)
        hm.add_mpint(K)
        H = sha1(hm.asbytes()).digest()
        self.transport._set_K_H(K, H)
        srv_token = self.kexgss.ssh_accept_sec_context(
            self.gss_host, client_token
        )
        m = Message()
        if self.kexgss._gss_srv_ctxt_status:
            mic_token = self.kexgss.ssh_get_mic(
                self.transport.session_id, gss_kex=True
            )
            m.add_byte(c_MSG_KEXGSS_COMPLETE)
            m.add_mpint(self.f)
            m.add_string(mic_token)
            if srv_token is not None:
                m.add_boolean(True)
                m.add_string(srv_token)
            else:
                m.add_boolean(False)
            self.transport._send_message(m)
            self.transport.gss_kex_used = True
            self.transport._activate_outbound()
        else:
            m.add_byte(c_MSG_KEXGSS_CONTINUE)
            m.add_string(srv_token)
            self.transport._send_message(m)
            self.transport._expect_packet(
                MSG_KEXGSS_CONTINUE, MSG_KEXGSS_COMPLETE, MSG_KEXGSS_ERROR
            )

    def _parse_kexgss_hostkey(self, m):
        """
        Parse the SSH2_MSG_KEXGSS_HOSTKEY message (client mode).

        :param `Message` m: The content of the SSH2_MSG_KEXGSS_HOSTKEY message
        """
        # client mode
        host_key = m.get_string()
        self.transport.host_key = host_key
        sig = m.get_string()
        self.transport._verify_key(host_key, sig)
        self.transport._expect_packet(MSG_KEXGSS_CONTINUE, MSG_KEXGSS_COMPLETE)

    def _parse_kexgss_continue(self, m):
        """
        Parse the SSH2_MSG_KEXGSS_CONTINUE message.

        :param `Message` m: The content of the SSH2_MSG_KEXGSS_CONTINUE message
        """
        if not self.transport.server_mode:
            srv_token = m.get_string()
            m = Message()
            m.add_byte(c_MSG_KEXGSS_CONTINUE)
            m.add_string(
                self.kexgss.ssh_init_sec_context(
                    target=self.gss_host, recv_token=srv_token
                )
            )
            self.transport.send_message(m)
            self.transport._expect_packet(
                MSG_KEXGSS_CONTINUE, MSG_KEXGSS_COMPLETE, MSG_KEXGSS_ERROR
            )
        else:
            pass

    def _parse_kexgss_complete(self, m):
        """
        Parse the SSH2_MSG_KEXGSS_COMPLETE message (client mode).

        :param `Message` m: The content of the SSH2_MSG_KEXGSS_COMPLETE message
        """
        if self.transport.host_key is None:
            self.transport.host_key = NullHostKey()
        self.f = m.get_mpint()
        mic_token = m.get_string()
        # This must be TRUE, if there is a GSS-API token in this message.
        bool = m.get_boolean()
        srv_token = None
        if bool:
            srv_token = m.get_string()
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
            self.transport.host_key.__str__(),
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
        H = sha1(hm.asbytes()).digest()
        self.transport._set_K_H(K, H)
        if srv_token is not None:
            self.kexgss.ssh_init_sec_context(
                target=self.gss_host, recv_token=srv_token
            )
            self.kexgss.ssh_check_mic(mic_token, H)
        else:
            self.kexgss.ssh_check_mic(mic_token, H)
        self.transport.gss_kex_used = True
        self.transport._activate_outbound()

    def _parse_kexgss_error(self, m):
        """
        Parse the SSH2_MSG_KEXGSS_ERROR message (client mode).
        The server may send a GSS-API error message. if it does, we display
        the error by throwing an exception (client mode).

        :param `Message` m:  The content of the SSH2_MSG_KEXGSS_ERROR message
        :raise SSHException: Contains GSS-API major and minor status as well as
                             the error message and the language tag of the
                             message
        """
        maj_status = m.get_int()
        min_status = m.get_int()
        err_msg = m.get_string()
        m.get_string()  # we don't care about the language (lang_tag)!
        raise SSHException(
            """GSS-API Error:
Major Status: {}
Minor Status: {}
Error Message: {}
""".format(
                maj_status, min_status, err_msg
            )
        )


class NullHostKey(object):
    """
    This class represents the Null Host Key for GSS-API Key Exchange as defined
    in `RFC 4462 Section 5
    <https://tools.ietf.org/html/rfc4462.html#section-5>`_
    """

    def __init__(self):
        self.key = ""

    def __str__(self):
        return self.key

    def get_name(self):
        return self.key
