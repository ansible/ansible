# -*- coding: utf-8 -*-

# Ansible module to import third party repo keys to your rpm db
# Copyright: (c) 2013, Héctor Acosta <hector.acosta@gazzang.com>

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


DOCUMENTATION = """
---
module: rpm_key
author:
  - Hector Acosta (@hacosta) <hector.acosta@gazzang.com>
short_description: Adds or removes a gpg key from the rpm db
description:
  - Adds or removes C(rpm --import) a gpg key to your rpm database.
version_added: "1.3"
options:
    key:
      description:
        - Key that will be modified. Can be a url, a file on the managed node, or a keyid if the key
          already exists in the database.
      type: str
      required: true
    state:
      description:
        - If the key will be imported or removed from the rpm db.
      type: str
      default: present
      choices: [ absent, present ]
    validate_certs:
      description:
        - If V(false) and the O(key) is a url starting with V(https), SSL certificates will not be validated.
        - This should only be used on personally controlled sites using self-signed certificates.
      type: bool
      default: 'yes'
    fingerprint:
      description:
        - The long-form fingerprint of the key being imported.
        - This will be used to verify the specified key.
      type: list
      elements: str
      version_added: 2.9
extends_documentation_fragment:
    - action_common_attributes
attributes:
    check_mode:
        support: full
    diff_mode:
        support: none
    platform:
        platforms: rhel
"""

EXAMPLES = """
- name: Import a key from a url
  ansible.builtin.rpm_key:
    state: present
    key: http://apt.sw.be/RPM-GPG-KEY.dag.txt

- name: Import a key from a file
  ansible.builtin.rpm_key:
    state: present
    key: /path/to/key.gpg

- name: Ensure a key is not present in the db
  ansible.builtin.rpm_key:
    state: absent
    key: DEADB33F

- name: Verify the key, using a fingerprint, before import
  ansible.builtin.rpm_key:
    key: /path/to/RPM-GPG-KEY.dag.txt
    fingerprint: EBC6 E12C 62B1 C734 026B  2122 A20E 5214 6B8D 79E6

- name: Verify the key, using multiple fingerprints, before import
  ansible.builtin.rpm_key:
    key: /path/to/RPM-GPG-KEY.dag.txt
    fingerprint:
      - EBC6 E12C 62B1 C734 026B  2122 A20E 5214 6B8D 79E6
      - 19B7 913E 6284 8E3F 4D78 D6B4 ECD9 1AB2 2EB6 8D86
"""

RETURN = r"""#"""

import ctypes
import ctypes.util
import hashlib
import re
import os.path
import tempfile

from typing import Optional, Tuple, List, Any

# import module snippets
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url
from ansible.module_utils.common.text.converters import to_native

# Type alias for ctypes pointer to uint8 array (packet data)
# Using Any here because ctypes._Pointer is private, but documenting the actual type
PktPointer = Any  # Actually: ctypes.POINTER(ctypes.c_uint8)


class LibRPM:
    """Wrapper for librpm PGP key functions"""

    def __init__(self) -> None:
        # Load the librpm library
        lib_path = ctypes.util.find_library('rpm')
        if not lib_path:
            raise ImportError("Error: Could not find librpm library")

        try:
            self.lib = ctypes.CDLL(lib_path)
        except OSError:
            raise ImportError("Error: Could not load librpm library from %s" % lib_path)

        try:
            self.libc = ctypes.CDLL(None)
        except OSError:
            raise ImportError("Error: Could not load libC library")

        # Constants
        self.PGPTAG_PUBLIC_KEY = 6
        self.PGPTAG_PUBLIC_SUBKEY = 14

        self._define_signatures()

    def _define_signatures(self) -> None:
        """Define library function signatures"""
        # pgpArmor pgpParsePkts(const char *armor, uint8_t **pkt, size_t *pktlen)
        self.lib.pgpParsePkts.argtypes = [
            ctypes.c_char_p,
            ctypes.POINTER(ctypes.POINTER(ctypes.c_uint8)),
            ctypes.POINTER(ctypes.c_size_t)
        ]
        self.lib.pgpParsePkts.restype = ctypes.c_int

        # int pgpPubkeyKeyID(const uint8_t *pkt, size_t pktlen, pgpKeyID_t keyid)
        # pgpKeyID_t is uint8_t[8]
        self.lib.pgpPubkeyKeyID.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_uint8)
        ]
        self.lib.pgpPubkeyKeyID.restype = ctypes.c_int

        # int pgpPubkeyFingerprint(const uint8_t *pkt, size_t pktlen,
        #                          uint8_t **fp, size_t *fplen)
        self.lib.pgpPubkeyFingerprint.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.POINTER(ctypes.c_uint8)),
            ctypes.POINTER(ctypes.c_size_t)
        ]
        self.lib.pgpPubkeyFingerprint.restype = ctypes.c_int

        # int pgpPrtParams(const uint8_t *pkts, size_t pktlen, unsigned int pkttype,
        #                  pgpDigParams *ret)
        self.lib.pgpPrtParams.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_uint,
            ctypes.POINTER(ctypes.c_void_p)
        ]
        self.lib.pgpPrtParams.restype = ctypes.c_int

        # int pgpPrtParamsSubkeys(const uint8_t *pkts, size_t pktlen,
        #                         pgpDigParams mainkey, pgpDigParams **subkeys, int *subkeysCount)
        self.lib.pgpPrtParamsSubkeys.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p)),
            ctypes.POINTER(ctypes.c_int)
        ]
        self.lib.pgpPrtParamsSubkeys.restype = ctypes.c_int

        # pgpDigParams pgpDigParamsFree(pgpDigParams digp)
        self.lib.pgpDigParamsFree.argtypes = [ctypes.c_void_p]
        self.lib.pgpDigParamsFree.restype = ctypes.c_void_p

        # void free(void *ptr)
        self.libc.free.argtypes = [ctypes.c_void_p]
        self.libc.free.restype = None

    def _parse_armor(self, armor_string: str) -> Tuple[Optional[PktPointer], int]:
        """
        Parse ASCII armored PGP data using pgpParsePkts().
        Returns (pkt, pktlen) tuple or (None, 0) on error.
        """
        pkt = ctypes.POINTER(ctypes.c_uint8)()
        pktlen = ctypes.c_size_t()

        armor_bytes = armor_string.encode('utf-8')
        result = self.lib.pgpParsePkts(armor_bytes, ctypes.byref(pkt), ctypes.byref(pktlen))

        if result < 0 or not pkt:
            return None, 0

        return pkt, pktlen.value

    def _get_key_id(self, pkt: PktPointer, pktlen: int) -> Optional[str]:
        """
        Get key ID using pgpPubkeyKeyID().
        Returns hex string or None on error.
        """
        # Create buffer for key ID (8 bytes)
        keyid = (ctypes.c_uint8 * 8)()

        result = self.lib.pgpPubkeyKeyID(
            pkt,
            pktlen,
            ctypes.cast(keyid, ctypes.POINTER(ctypes.c_uint8))
        )

        if result != 0:
            return None

        # Convert bytes to hex string
        return bytes(keyid).hex().upper()

    def _get_fingerprint(self, pkt: PktPointer, pktlen: int) -> Optional[str]:
        """
        Get fingerprint using pgpPubkeyFingerprint().
        Returns hex string or None on error.
        """
        fp = ctypes.POINTER(ctypes.c_uint8)()
        fplen = ctypes.c_size_t()

        result = self.lib.pgpPubkeyFingerprint(
            pkt,
            pktlen,
            ctypes.byref(fp),
            ctypes.byref(fplen)
        )

        if result != 0 or not fp:
            return None

        # Convert fingerprint bytes to hex string
        fp_bytes = bytes([fp[i] for i in range(fplen.value)])
        fp_hex = fp_bytes.hex().upper()

        # Free the fingerprint buffer allocated by the library
        self.libc.free(fp)

        return fp_hex

    def _parse_packet_header(self, pkt: PktPointer, offset: int, pktlen: int) -> Tuple[Optional[int], int, int]:
        """
        Parse a PGP packet header to get tag and packet length.
        Returns (tag, body_length, header_length) or (None, 0, 0) on error.

        Per RFC 9580 - Section 4.2: Packet Headers
        https://www.rfc-editor.org/rfc/rfc9580.html#name-packet-headers
        """
        if offset >= pktlen:
            return None, 0, 0

        tag_byte = pkt[offset]

        # Check if it's a new format packet (bit 6 set)
        if tag_byte & 0x40:
            # New format
            tag = tag_byte & 0x3f  # bits 0-5 are packet type ID
            offset += 1

            if offset >= pktlen:
                return None, 0, 0

            first_len_byte = pkt[offset]

            if first_len_byte < 192:
                # One-octet length
                return tag, first_len_byte, 2
            elif first_len_byte < 224:
                # Two-octet length
                if offset + 1 >= pktlen:
                    return None, 0, 0
                length = ((first_len_byte - 192) << 8) + pkt[offset + 1] + 192
                return tag, length, 3
            elif first_len_byte == 255:
                # Five-octet length
                if offset + 4 >= pktlen:
                    return None, 0, 0
                length = (pkt[offset + 1] << 24) | (pkt[offset + 2] << 16) | \
                         (pkt[offset + 3] << 8) | pkt[offset + 4]
                return tag, length, 6
            else:
                # Partial body length (not supported here)
                return None, 0, 0
        else:
            # Old format
            tag = (tag_byte >> 2) & 0x0f
            length_type = tag_byte & 0x03

            if length_type == 0:
                # One-octet length
                if offset + 1 >= pktlen:
                    return None, 0, 0
                return tag, pkt[offset + 1], 2
            elif length_type == 1:
                # Two-octet length
                if offset + 2 >= pktlen:
                    return None, 0, 0
                length = (pkt[offset + 1] << 8) | pkt[offset + 2]
                return tag, length, 3
            elif length_type == 2:
                # Four-octet length
                if offset + 4 >= pktlen:
                    return None, 0, 0
                length = (pkt[offset + 1] << 24) | (pkt[offset + 2] << 16) | \
                         (pkt[offset + 3] << 8) | pkt[offset + 4]
                return tag, length, 5
            else:
                # Indeterminate length (not supported)
                return None, 0, 0

    def _find_subkey_packets(self, pkt: PktPointer, pktlen: int) -> List[Tuple[int, int]]:
        """
        Walk the packet stream and find all PGPTAG_PUBLIC_SUBKEY packets.
        Returns list of (offset, total_packet_length) tuples.
        """
        subkey_packets: List[Tuple[int, int]] = []
        offset = 0

        while offset < pktlen:
            tag, body_len, header_len = self._parse_packet_header(pkt, offset, pktlen)

            if tag is None:
                break

            if tag == self.PGPTAG_PUBLIC_SUBKEY:
                # Found a subkey packet
                total_len = header_len + body_len
                subkey_packets.append((offset, total_len))

            # Move to next packet
            offset += header_len + body_len

        return subkey_packets

    def _get_key_version(self, pkt: PktPointer, offset: int, pktlen: int) -> Optional[int]:
        """
        Get the version byte from a key packet.
        Returns version number (4 or 6) or None on error.
        """
        tag, body_len, header_len = self._parse_packet_header(pkt, offset, pktlen)

        if tag is None:
            return None

        # Extract packet body (skip the packet header)
        body_offset = offset + header_len
        if body_offset >= pktlen:
            return None

        # First byte of body is the version
        return pkt[body_offset]

    def _compute_v4_fingerprint(self, pkt: PktPointer, offset: int, pktlen: int) -> Optional[str]:
        """
        Compute V4 fingerprint from packet data.
        For V4 keys, fingerprint = SHA-1(0x99 || 2-byte-length || packet_body)
        Per RFC 4880 Section 12.2
        """
        tag, body_len, header_len = self._parse_packet_header(pkt, offset, pktlen)

        if tag is None:
            return None

        # Extract packet body (skip the packet header)
        body_offset = offset + header_len
        if body_offset + body_len > pktlen:
            return None

        # Check if it's a V4 key (first byte of body should be 0x04)
        if pkt[body_offset] != 0x04:
            return None

        # Build the data for fingerprint: 0x99 || 2-byte length || body
        fp_data = bytearray()
        fp_data.append(0x99)  # V4 public key packet tag
        fp_data.append((body_len >> 8) & 0xFF)  # Length high byte
        fp_data.append(body_len & 0xFF)  # Length low byte

        # Append the packet body
        for i in range(body_len):
            fp_data.append(pkt[body_offset + i])

        # Compute SHA-1 hash
        fingerprint = hashlib.sha1(fp_data).digest()
        return fingerprint.hex().upper()

    def _compute_v6_fingerprint(self, pkt: PktPointer, offset: int, pktlen: int) -> Optional[str]:
        """
        Compute V6 fingerprint from packet data.
        For V6 keys, fingerprint = SHA-256(0x9B || 4-byte-length || packet_body)
        Per RFC 9580 Section 5.5.4
        """
        tag, body_len, header_len = self._parse_packet_header(pkt, offset, pktlen)

        if tag is None:
            return None

        # Extract packet body (skip the packet header)
        body_offset = offset + header_len
        if body_offset + body_len > pktlen:
            return None

        # Check if it's a V6 key (first byte of body should be 0x06)
        if pkt[body_offset] != 0x06:
            return None

        # Build the data for fingerprint: 0x9B || 4-byte length || body
        fp_data = bytearray()
        fp_data.append(0x9B)  # V6 public key packet tag
        fp_data.append((body_len >> 24) & 0xFF)  # Length byte 1 (MSB)
        fp_data.append((body_len >> 16) & 0xFF)  # Length byte 2
        fp_data.append((body_len >> 8) & 0xFF)   # Length byte 3
        fp_data.append(body_len & 0xFF)          # Length byte 4 (LSB)

        # Append the packet body
        for i in range(body_len):
            fp_data.append(pkt[body_offset + i])

        # Compute SHA-256 hash
        fingerprint = hashlib.sha256(fp_data).digest()
        return fingerprint.hex().upper()

    def _identify_subkeys(self, pkt: PktPointer, pktlen: int) -> list[dict[str, str]]:
        """Return a list of dicts with key ID and fingerprint for each subkey"""
        subkey_info: list[dict[str, str]] = []

        # First, parse the main key
        main_key = ctypes.c_void_p()

        result = self.lib.pgpPrtParams(
            pkt,
            pktlen,
            self.PGPTAG_PUBLIC_KEY,
            ctypes.byref(main_key)
        )

        if result != 0 or not main_key:
            raise Exception("Unable to parse main key for subkey identification")

        # Get subkeys using pgpPrtParamsSubkeys
        subkeys = ctypes.POINTER(ctypes.c_void_p)()
        subkeys_count = ctypes.c_int()

        result = self.lib.pgpPrtParamsSubkeys(
            pkt,
            pktlen,
            main_key,
            ctypes.byref(subkeys),
            ctypes.byref(subkeys_count)
        )

        if result != 0:
            self.lib.pgpDigParamsFree(main_key)
            raise Exception("Unable to get subkey information")

        count = subkeys_count.value

        # Find all subkey packets in the stream and compute their fingerprints.
        # Note that librpm does not provide an API to extract the fingerprint of a subkey,
        # so we must compute this the hard way (manually).

        subkey_packets = self._find_subkey_packets(pkt, pktlen)

        for offset, packet_len in subkey_packets:
            # Detect key version
            version = self._get_key_version(pkt, offset, pktlen)

            if version == 0x04:
                # V4 key
                computed_fp = self._compute_v4_fingerprint(pkt, offset, pktlen)
                if computed_fp:
                    # V4: Key ID is the last 8 bytes (16 hex chars) of the fingerprint
                    keyid_from_fp = computed_fp[-16:]
                    subkey_info.append({'keyid': keyid_from_fp, 'fingerprint': computed_fp})
            elif version == 0x06:
                # V6 key
                computed_fp = self._compute_v6_fingerprint(pkt, offset, pktlen)
                if computed_fp:
                    # V6: Key ID is the first 8 bytes (16 hex chars) of the fingerprint
                    keyid_from_fp = computed_fp[:16]
                    subkey_info.append({'keyid': keyid_from_fp, 'fingerprint': computed_fp})

        # Free allocated memory
        for i in range(count):
            self.lib.pgpDigParamsFree(subkeys[i])

        self.libc.free(subkeys)
        self.lib.pgpDigParamsFree(main_key)

        return subkey_info

    def get_key_ids_from_armor(self, armor: str, include_subkeys: bool = False) -> str | list[str]:
        """
        Get the key IDs from the primary PGP key, and all subkeys of that key, from the ASCII armored key.

        'armor' is expected to be a single ASCII armored PGP key (v4 or v6).

        If 'include_subkeys' is True, this will return a list containing the key ID of the main PGP key,
        as well as all of its subkeys. If 'include_subkeys' is False, this will return only the main PGP key ID.
        """
        pkt, pktlen = self._parse_armor(armor)
        if not pkt:
            raise Exception("Unable to parse PGP key")

        # Get the key ID for the primary/main key
        key_id = self._get_key_id(pkt, pktlen)
        if not key_id:
            raise Exception("Failed to get main key id")

        if not include_subkeys:
            return key_id

        key_ids: list[str] = []
        key_ids.append(key_id)

        subkey_info = self._identify_subkeys(pkt, pktlen)
        for subkey in subkey_info:
            key_ids.append(subkey['keyid'])

        self.libc.free(pkt)
        return key_ids

    def get_fingerprints_from_armor(self, armor: str, include_subkeys: bool = False) -> str | list[str]:
        """
        Get the fingerprints from the primary PGP key, and all subkeys of that key, from the ASCII armored key.

        'armor' is expected to be a single ASCII armored PGP key (v4 or v6).

        If 'include_subkeys' is True, this will return a list containing the fingerprints of the main PGP key,
        as well as all of its subkeys. If 'include_subkeys' is False, this will return only the main PGP fingerprint.
        """
        fingerprints: list[str] = []

        pkt, pktlen = self._parse_armor(armor)
        if not pkt:
            raise Exception("Unable to parse PGP key")

        # Get the fingerprint for the primary/main key
        fingerprint = self._get_fingerprint(pkt, pktlen)
        if not fingerprint:
            raise Exception("Failed to get main key fingerprint")

        if not include_subkeys:
            return fingerprint

        fingerprints.append(fingerprint)

        subkey_info = self._identify_subkeys(pkt, pktlen)
        for subkey in subkey_info:
            fingerprints.append(subkey['fingerprint'])

        self.libc.free(pkt)
        return fingerprints


def is_pubkey(string):
    """Verifies if string is a pubkey"""
    pgp_regex = ".*?(-----BEGIN PGP PUBLIC KEY BLOCK-----.*?-----END PGP PUBLIC KEY BLOCK-----).*"
    return bool(re.match(pgp_regex, to_native(string, errors='surrogate_or_strict'), re.DOTALL))


class RpmKey(object):

    def __init__(self, module):
        # If the key is a url, we need to check if it's present to be idempotent,
        # to do that, we need to check the keyid, which we can get from the armor.
        keyfile = None
        should_cleanup_keyfile = False
        self.module = module
        self.rpm = self.module.get_bin_path('rpm', True)
        state = module.params['state']
        key = module.params['key']
        fingerprint = module.params['fingerprint']
        fingerprints = set()

        if fingerprint:
            if not isinstance(fingerprint, list):
                fingerprint = [fingerprint]
            fingerprints = set(f.replace(' ', '').upper() for f in fingerprint)

        self.librpm = LibRPM()

        if '://' in key:
            keyfile = self.fetch_key(key)
            keyid = self.getkeyid(keyfile)
            should_cleanup_keyfile = True
        elif self.is_keyid(key):
            keyid = key
        elif os.path.isfile(key):
            keyfile = key
            keyid = self.getkeyid(keyfile)
        else:
            self.module.fail_json(msg="Not a valid key %s" % key)
        keyid = self.normalize_keyid(keyid)

        if state == 'present':
            if self.is_key_imported(keyid):
                module.exit_json(changed=False)
            else:
                if not keyfile:
                    self.module.fail_json(msg="When importing a key, a valid file must be given")
                if fingerprints:
                    keyfile_fingerprints = self.getfingerprints(keyfile)
                    if not fingerprints.issubset(keyfile_fingerprints):
                        self.module.fail_json(
                            msg=("The specified fingerprint, '%s', "
                                 "does not match any key fingerprints in '%s'") % (fingerprints, keyfile_fingerprints)
                        )
                self.import_key(keyfile)
                if should_cleanup_keyfile:
                    self.module.cleanup(keyfile)
                module.exit_json(changed=True)
        else:
            if self.is_key_imported(keyid):
                self.drop_key(keyid)
                module.exit_json(changed=True)
            else:
                module.exit_json(changed=False)

    def fetch_key(self, url):
        """Downloads a key from url, returns a valid path to a gpg key"""
        rsp, info = fetch_url(self.module, url)
        if info['status'] != 200:
            self.module.fail_json(msg="failed to fetch key at %s , error was: %s" % (url, info['msg']))

        key = rsp.read()
        if not is_pubkey(key):
            self.module.fail_json(msg="Not a public key: %s" % url)
        tmpfd, tmpname = tempfile.mkstemp()
        self.module.add_cleanup_file(tmpname)
        with os.fdopen(tmpfd, "w+b") as tmpfile:
            tmpfile.write(key)
        return tmpname

    def normalize_keyid(self, keyid):
        """Ensure a keyid doesn't have a leading 0x, has leading or trailing whitespace, and make sure is uppercase"""
        ret = keyid.strip().upper()
        if ret.startswith('0x'):
            return ret[2:]
        elif ret.startswith('0X'):
            return ret[2:]
        else:
            return ret

    def getkeyid(self, keyfile):
        with open(keyfile, "r") as key_fd:
            key_id = self.librpm.get_key_ids_from_armor(key_fd.read())
        if not key_id:
            self.module.fail_json(msg="Failed to get keyid")
        return key_id

    def getfingerprints(self, keyfile):
        with open(keyfile, "r") as key_fd:
            fingerprints = self.librpm.get_fingerprints_from_armor(key_fd.read(), include_subkeys=True)
        if not fingerprints:
            self.module.fail_json(msg="Failed to get fingerprint")
        return frozenset(fingerprints)

    def is_keyid(self, keystr):
        """Verifies if a key, as provided by the user is a keyid"""
        return re.match('(0x)?[0-9a-f]{8}', keystr, flags=re.IGNORECASE)

    def execute_command(self, cmd):
        rc, stdout, stderr = self.module.run_command(cmd, use_unsafe_shell=True)
        if rc != 0:
            self.module.fail_json(msg=stderr)
        return stdout, stderr

    def is_key_imported(self, keyid):
        """
        Uses 'rpm' CLI to output the ASCII armor of all imported keys, then gets the key ID
        for each to determine if the supplied key is among them.
        """
        cmd = self.rpm + ' -q  gpg-pubkey'
        rc, stdout, stderr = self.module.run_command(cmd)
        if rc != 0:  # No key is installed on system
            return False
        cmd += ' --qf "%{description}"'
        stdout, stderr = self.execute_command(cmd)

        # Split the content into individual key blocks
        key_blocks = []
        current_block = []
        in_key_block = False

        for line in stdout.splitlines():
            if line.strip() == '-----BEGIN PGP PUBLIC KEY BLOCK-----':
                in_key_block = True
                current_block = [line]
            elif line.strip() == '-----END PGP PUBLIC KEY BLOCK-----':
                current_block.append(line)
                key_blocks.append('\n'.join(current_block))
                current_block = []
                in_key_block = False
            elif in_key_block:
                current_block.append(line)

        for armor_string in key_blocks:
            key_id = self.librpm.get_key_ids_from_armor(armor_string)
            if keyid == key_id:
                return True

        return False

    def import_key(self, keyfile):
        if not self.module.check_mode:
            self.execute_command([self.rpm, '--import', keyfile])

    def drop_key(self, keyid):
        if not self.module.check_mode:
            self.execute_command([self.rpm, '--erase', '--allmatches', "gpg-pubkey-%s" % keyid[-8:].lower()])


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', default='present', choices=['absent', 'present']),
            key=dict(type='str', required=True, no_log=False),
            fingerprint=dict(type='list', elements='str'),
            validate_certs=dict(type='bool', default=True),
        ),
        supports_check_mode=True,
    )

    RpmKey(module)


if __name__ == '__main__':
    main()
