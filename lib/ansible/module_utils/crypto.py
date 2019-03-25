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
import tempfile

from ansible.module_utils import six
from ansible.module_utils._text import to_bytes


class OpenSSLObjectError(Exception):
    pass


def get_fingerprint(path, passphrase=None):
    """Generate the fingerprint of the public key. """

    fingerprint = {}

    privatekey = load_privatekey(path, passphrase)
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
        if passphrase:
            privatekey = crypto.load_privatekey(crypto.FILETYPE_PEM,
                                                open(path, 'rb').read(),
                                                to_bytes(passphrase))
        else:
            privatekey = crypto.load_privatekey(crypto.FILETYPE_PEM,
                                                open(path, 'rb').read())

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


def load_certificate_request(path):
    """Load the specified certificate signing request."""

    try:
        csr_content = open(path, 'rb').read()
        csr = crypto.load_certificate_request(crypto.FILETYPE_PEM, csr_content)
        return csr
    except (IOError, OSError) as exc:
        raise OpenSSLObjectError(exc)


def parse_name_field(input_dict):
    """Take a dict with key: value or key: list_of_values mappings and return a list of tuples"""

    result = []
    for key in input_dict:
        if isinstance(input_dict[key], list):
            for entry in input_dict[key]:
                result.append((key, entry))
        else:
            result.append((key, input_dict[key]))
    return result


def write_file(module, content, default_mode=None):
    '''
    Writes content into destination file as securely as possible.
    Uses file arguments from module.
    '''
    # Find out parameters for file
    file_args = module.load_file_common_arguments(module.params)
    if file_args['mode'] is None:
        file_args['mode'] = default_mode
    # Create tempfile name
    tmp_fd, tmp_name = tempfile.mkstemp(prefix=b'.ansible_tmp')
    try:
        os.close(tmp_fd)
    except Exception as dummy:
        pass
    module.add_cleanup_file(tmp_name)  # if we fail, let Ansible try to remove the file
    try:
        try:
            # Create tempfile
            file = os.open(tmp_name, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            os.write(file, content)
            os.close(file)
        except Exception as e:
            try:
                os.remove(tmp_name)
            except Exception as dummy:
                pass
            module.fail_json(msg='Error while writing result into temporary file: {0}'.format(e))
        # Update destination to wanted permissions
        if os.path.exists(file_args['path']):
            module.set_fs_attributes_if_different(file_args, False)
        # Move tempfile to final destination
        module.atomic_move(tmp_name, file_args['path'])
        # Try to update permissions again
        module.set_fs_attributes_if_different(file_args, False)
    except Exception as e:
        try:
            os.remove(tmp_name)
        except Exception as dummy:
            pass
        module.fail_json(msg='Error while writing result: {0}'.format(e))


@six.add_metaclass(abc.ABCMeta)
class OpenSSLObject(object):

    def __init__(self, path, state, force, check_mode):
        self.path = path
        self.state = state
        self.force = force
        self.name = os.path.basename(path)
        self.changed = False
        self.check_mode = check_mode

    def check(self, module, perms_required=True):
        """Ensure the resource is in its desired state."""

        def _check_state():
            return os.path.exists(self.path)

        def _check_perms(module):
            file_args = module.load_file_common_arguments(module.params)
            return not module.set_fs_attributes_if_different(file_args, False)

        if not perms_required:
            return _check_state()

        return _check_state() and _check_perms(module)

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
