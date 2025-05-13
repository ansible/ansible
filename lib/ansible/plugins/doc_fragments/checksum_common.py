# Copyright (c) 2024 ShIRann Chen <shirannx@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations


class ModuleDocFragment(object):

    DOCUMENTATION = r"""
options:
    checksum_algorithm:
        description:
        - Algorithm to determine checksum of file.
        - Will throw an error if the host is unable to use specified algorithm.
        - The remote host has to support the hashing method specified, V(md5)
            can be unavailable if the host is FIPS-140 compliant.
        - Availability might be restricted by the target system, for example FIPS systems won't allow md5 use
        type: str
        choices: [ md5, sha1, sha224, sha256, sha384, sha512 ]
        default: sha1
        aliases: [ checksum, checksum_algo ]
        version_added: "2.0"
    get_checksum:
        description:
        - Whether to return a checksum of the file.
        type: bool
        default: yes
"""
