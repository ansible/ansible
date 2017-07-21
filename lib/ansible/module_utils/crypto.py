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

import abc
import errno
import hashlib
import os

from ansible.module_utils import six


class OpenSSLObjectError(Exception):
    pass


def get_fingerprint(path, passphrase):
    """Generate the fingerprint of the public key. """

    fingerprint = {}

    privatekey = crypto.load_privatekey(crypto.FILETYPE_PEM,
                                        open(path, 'rb').read(),
                                        passphrase)

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


def load_privatekey(path, passphrase=None):
    """Load the specified OpenSSL private key."""

    try:
        privatekey_content = open(path, 'rb').read()
        privatekey = crypto.load_privatekey(crypto.FILETYPE_PEM,
                                            privatekey_content,
                                            passphrase)
        return privatekey
    except (IOError, OSError) as exc:
        raise OpenSSLObjectError(exc)


def load_certificate(path):
    """Load the specified certificate."""

    try:
        cert_content = open(path, 'rb').read()
        cert = crypto.load_certificate(crypto.FILETYPE_PEM, cert_content)
        return cert
    except (IOError, OSError) as exc:
        raise OpenSSLObjectError(exc)


@six.add_metaclass(abc.ABCMeta)
class OpenSSLObject(object):

    def __init__(self, path, state, force, check_mode):
        self.path = path
        self.state = state
        self.force = force
        self.name = os.path.basename(path)
        self.changed = False
        self.check_mode = check_mode

    @abc.abstractmethod
    def check(self):
        """Ensure the resource is in its desired state."""

        pass

    @abc.abstractmethod
    def dump(self):
        """Serialize the object into a dictionary."""

        pass

    @abc.abstractmethod
    def generate(self):
        """Generate the resource."""

        pass

    def remove(self):
        """Remove the resource from the filesystem."""

        try:
            os.remove(self.path)
            self.changed = True
        except OSError as exc:
            if exc.errno != errno.ENOENT:
                raise OpenSSLObjectError(exc)
            else:
                pass
