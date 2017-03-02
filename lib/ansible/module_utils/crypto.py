# -*- coding: utf-8 -*-
#
# (c) 2016, Yanis Guenane <yanis+ansible@guenane.org>
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.


try:
    from OpenSSL import crypto
except ImportError:
    # An error will be raised in the calling class to let the end
    # user know that OpenSSL couldn't be found.
    pass

import hashlib


def get_fingerprint(path):
    """Generate the fingerprint of the public key. """

    fingerprint = {}

    privatekey = crypto.load_privatekey(crypto.FILETYPE_PEM, open(path, 'r').read())

    try:
        publickey = crypto.dump_publickey(crypto.FILETYPE_ASN1, privatekey)
        for algo in hashlib.algorithms:
            f = getattr(hashlib, algo)
            pubkey_digest = f(publickey).hexdigest()
            fingerprint[algo] = ':'.join(pubkey_digest[i:i + 2] for i in range(0, len(pubkey_digest), 2))
    except AttributeError:
        # If PyOpenSSL < 16.0 crypto.dump_publickey() will fail.
        # By doing this we prevent the code from raising an error
        # yet we return no value in the fingerprint hash.
        pass

    return fingerprint
