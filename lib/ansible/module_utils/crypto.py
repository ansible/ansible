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
#
# ----------------------------------------------------------------------
# A clearly marked portion of this file is licensed under the BSD license
# Copyright (c) 2015, 2016 Paul Kehrer (@reaperhulk)
# Copyright (c) 2017 Fraser Tweedale (@frasertweedale)
# For more details, search for the function _obj2txt().
# ---------------------------------------------------------------------
# A clearly marked portion of this file is extracted from a project that
# is licensed under the Apache License 2.0
# Copyright (c) the OpenSSL contributors
# For more details, search for the function _OID_MAP.


from distutils.version import LooseVersion

try:
    import OpenSSL
    from OpenSSL import crypto
except ImportError:
    # An error will be raised in the calling class to let the end
    # user know that OpenSSL couldn't be found.
    pass

try:
    import cryptography
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend as cryptography_backend
    from cryptography.hazmat.primitives.serialization import load_pem_private_key
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives import serialization
    import ipaddress

    # Older versions of cryptography (< 2.1) do not have __hash__ functions for
    # general name objects (DNSName, IPAddress, ...), while providing overloaded
    # equality and string representation operations. This makes it impossible to
    # use them in hash-based data structures such as set or dict. Since we are
    # actually doing that in openssl_certificate, and potentially in other code,
    # we need to monkey-patch __hash__ for these classes to make sure our code
    # works fine.
    if LooseVersion(cryptography.__version__) < LooseVersion('2.1'):
        # A very simply hash function which relies on the representation
        # of an object to be implemented. This is the case since at least
        # cryptography 1.0, see
        # https://github.com/pyca/cryptography/commit/7a9abce4bff36c05d26d8d2680303a6f64a0e84f
        def simple_hash(self):
            return hash(repr(self))

        # The hash functions for the following types were added for cryptography 2.1:
        # https://github.com/pyca/cryptography/commit/fbfc36da2a4769045f2373b004ddf0aff906cf38
        x509.DNSName.__hash__ = simple_hash
        x509.DirectoryName.__hash__ = simple_hash
        x509.GeneralName.__hash__ = simple_hash
        x509.IPAddress.__hash__ = simple_hash
        x509.OtherName.__hash__ = simple_hash
        x509.RegisteredID.__hash__ = simple_hash

        if LooseVersion(cryptography.__version__) < LooseVersion('1.2'):
            # The hash functions for the following types were added for cryptography 1.2:
            # https://github.com/pyca/cryptography/commit/b642deed88a8696e5f01ce6855ccf89985fc35d0
            # https://github.com/pyca/cryptography/commit/d1b5681f6db2bde7a14625538bd7907b08dfb486
            x509.RFC822Name.__hash__ = simple_hash
            x509.UniformResourceIdentifier.__hash__ = simple_hash

    # Test whether we have support for X25519, X448, Ed25519 and/or Ed448
    try:
        import cryptography.hazmat.primitives.asymmetric.x25519
        CRYPTOGRAPHY_HAS_X25519 = True
        try:
            cryptography.hazmat.primitives.asymmetric.x25519.X25519PrivateKey.private_bytes
            CRYPTOGRAPHY_HAS_X25519_FULL = True
        except AttributeError:
            CRYPTOGRAPHY_HAS_X25519_FULL = False
    except ImportError:
        CRYPTOGRAPHY_HAS_X25519 = False
        CRYPTOGRAPHY_HAS_X25519_FULL = False
    try:
        import cryptography.hazmat.primitives.asymmetric.x448
        CRYPTOGRAPHY_HAS_X448 = True
    except ImportError:
        CRYPTOGRAPHY_HAS_X448 = False
    try:
        import cryptography.hazmat.primitives.asymmetric.ed25519
        CRYPTOGRAPHY_HAS_ED25519 = True
    except ImportError:
        CRYPTOGRAPHY_HAS_ED25519 = False
    try:
        import cryptography.hazmat.primitives.asymmetric.ed448
        CRYPTOGRAPHY_HAS_ED448 = True
    except ImportError:
        CRYPTOGRAPHY_HAS_ED448 = False

except ImportError:
    # Error handled in the calling module.
    CRYPTOGRAPHY_HAS_X25519 = False
    CRYPTOGRAPHY_HAS_X25519_FULL = False
    CRYPTOGRAPHY_HAS_X448 = False
    CRYPTOGRAPHY_HAS_ED25519 = False
    CRYPTOGRAPHY_HAS_ED448 = False


import abc
import base64
import binascii
import datetime
import errno
import hashlib
import os
import re
import tempfile

from ansible.module_utils import six
from ansible.module_utils._text import to_bytes, to_text


class OpenSSLObjectError(Exception):
    pass


class OpenSSLBadPassphraseError(OpenSSLObjectError):
    pass


def get_fingerprint_of_bytes(source):
    """Generate the fingerprint of the given bytes."""

    fingerprint = {}

    try:
        algorithms = hashlib.algorithms
    except AttributeError:
        try:
            algorithms = hashlib.algorithms_guaranteed
        except AttributeError:
            return None

    for algo in algorithms:
        f = getattr(hashlib, algo)
        try:
            h = f(source)
        except ValueError:
            # This can happen for hash algorithms not supported in FIPS mode
            # (https://github.com/ansible/ansible/issues/67213)
            continue
        try:
            # Certain hash functions have a hexdigest() which expects a length parameter
            pubkey_digest = h.hexdigest()
        except TypeError:
            pubkey_digest = h.hexdigest(32)
        fingerprint[algo] = ':'.join(pubkey_digest[i:i + 2] for i in range(0, len(pubkey_digest), 2))

    return fingerprint


def get_fingerprint(path, passphrase=None):
    """Generate the fingerprint of the public key. """

    privatekey = load_privatekey(path, passphrase, check_passphrase=False)
    try:
        publickey = crypto.dump_publickey(crypto.FILETYPE_ASN1, privatekey)
    except AttributeError:
        # If PyOpenSSL < 16.0 crypto.dump_publickey() will fail.
        try:
            bio = crypto._new_mem_buf()
            rc = crypto._lib.i2d_PUBKEY_bio(bio, privatekey._pkey)
            if rc != 1:
                crypto._raise_current_error()
            publickey = crypto._bio_to_string(bio)
        except AttributeError:
            # By doing this we prevent the code from raising an error
            # yet we return no value in the fingerprint hash.
            return None
    return get_fingerprint_of_bytes(publickey)


def load_privatekey(path, passphrase=None, check_passphrase=True, content=None, backend='pyopenssl'):
    """Load the specified OpenSSL private key.

    The content can also be specified via content; in that case,
    this function will not load the key from disk.
    """

    try:
        if content is None:
            with open(path, 'rb') as b_priv_key_fh:
                priv_key_detail = b_priv_key_fh.read()
        else:
            priv_key_detail = content

        if backend == 'pyopenssl':

            # First try: try to load with real passphrase (resp. empty string)
            # Will work if this is the correct passphrase, or the key is not
            # password-protected.
            try:
                result = crypto.load_privatekey(crypto.FILETYPE_PEM,
                                                priv_key_detail,
                                                to_bytes(passphrase or ''))
            except crypto.Error as e:
                if len(e.args) > 0 and len(e.args[0]) > 0:
                    if e.args[0][0][2] in ('bad decrypt', 'bad password read'):
                        # This happens in case we have the wrong passphrase.
                        if passphrase is not None:
                            raise OpenSSLBadPassphraseError('Wrong passphrase provided for private key!')
                        else:
                            raise OpenSSLBadPassphraseError('No passphrase provided, but private key is password-protected!')
                raise OpenSSLObjectError('Error while deserializing key: {0}'.format(e))
            if check_passphrase:
                # Next we want to make sure that the key is actually protected by
                # a passphrase (in case we did try the empty string before, make
                # sure that the key is not protected by the empty string)
                try:
                    crypto.load_privatekey(crypto.FILETYPE_PEM,
                                           priv_key_detail,
                                           to_bytes('y' if passphrase == 'x' else 'x'))
                    if passphrase is not None:
                        # Since we can load the key without an exception, the
                        # key isn't password-protected
                        raise OpenSSLBadPassphraseError('Passphrase provided, but private key is not password-protected!')
                except crypto.Error as e:
                    if passphrase is None and len(e.args) > 0 and len(e.args[0]) > 0:
                        if e.args[0][0][2] in ('bad decrypt', 'bad password read'):
                            # The key is obviously protected by the empty string.
                            # Don't do this at home (if it's possible at all)...
                            raise OpenSSLBadPassphraseError('No passphrase provided, but private key is password-protected!')
        elif backend == 'cryptography':
            try:
                result = load_pem_private_key(priv_key_detail,
                                              None if passphrase is None else to_bytes(passphrase),
                                              cryptography_backend())
            except TypeError as dummy:
                raise OpenSSLBadPassphraseError('Wrong or empty passphrase provided for private key')
            except ValueError as dummy:
                raise OpenSSLBadPassphraseError('Wrong passphrase provided for private key')

        return result
    except (IOError, OSError) as exc:
        raise OpenSSLObjectError(exc)


def load_certificate(path, backend='pyopenssl'):
    """Load the specified certificate."""

    try:
        with open(path, 'rb') as cert_fh:
            cert_content = cert_fh.read()
        if backend == 'pyopenssl':
            return crypto.load_certificate(crypto.FILETYPE_PEM, cert_content)
        elif backend == 'cryptography':
            return x509.load_pem_x509_certificate(cert_content, cryptography_backend())
    except (IOError, OSError) as exc:
        raise OpenSSLObjectError(exc)


def load_certificate_request(path, backend='pyopenssl'):
    """Load the specified certificate signing request."""
    try:
        with open(path, 'rb') as csr_fh:
            csr_content = csr_fh.read()
    except (IOError, OSError) as exc:
        raise OpenSSLObjectError(exc)
    if backend == 'pyopenssl':
        return crypto.load_certificate_request(crypto.FILETYPE_PEM, csr_content)
    elif backend == 'cryptography':
        return x509.load_pem_x509_csr(csr_content, cryptography_backend())


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


def convert_relative_to_datetime(relative_time_string):
    """Get a datetime.datetime or None from a string in the time format described in sshd_config(5)"""

    parsed_result = re.match(
        r"^(?P<prefix>[+-])((?P<weeks>\d+)[wW])?((?P<days>\d+)[dD])?((?P<hours>\d+)[hH])?((?P<minutes>\d+)[mM])?((?P<seconds>\d+)[sS]?)?$",
        relative_time_string)

    if parsed_result is None or len(relative_time_string) == 1:
        # not matched or only a single "+" or "-"
        return None

    offset = datetime.timedelta(0)
    if parsed_result.group("weeks") is not None:
        offset += datetime.timedelta(weeks=int(parsed_result.group("weeks")))
    if parsed_result.group("days") is not None:
        offset += datetime.timedelta(days=int(parsed_result.group("days")))
    if parsed_result.group("hours") is not None:
        offset += datetime.timedelta(hours=int(parsed_result.group("hours")))
    if parsed_result.group("minutes") is not None:
        offset += datetime.timedelta(
            minutes=int(parsed_result.group("minutes")))
    if parsed_result.group("seconds") is not None:
        offset += datetime.timedelta(
            seconds=int(parsed_result.group("seconds")))

    if parsed_result.group("prefix") == "+":
        return datetime.datetime.utcnow() + offset
    else:
        return datetime.datetime.utcnow() - offset


def select_message_digest(digest_string):
    digest = None
    if digest_string == 'sha256':
        digest = hashes.SHA256()
    elif digest_string == 'sha384':
        digest = hashes.SHA384()
    elif digest_string == 'sha512':
        digest = hashes.SHA512()
    elif digest_string == 'sha1':
        digest = hashes.SHA1()
    elif digest_string == 'md5':
        digest = hashes.MD5()
    return digest


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

    def remove(self, module):
        """Remove the resource from the filesystem."""

        try:
            os.remove(self.path)
            self.changed = True
        except OSError as exc:
            if exc.errno != errno.ENOENT:
                raise OpenSSLObjectError(exc)
            else:
                pass


# #####################################################################################
# #####################################################################################
# This has been extracted from the OpenSSL project's objects.txt:
#     https://github.com/openssl/openssl/blob/9537fe5757bb07761fa275d779bbd40bcf5530e4/crypto/objects/objects.txt
# Extracted with https://gist.github.com/felixfontein/376748017ad65ead093d56a45a5bf376
#
# In case the following data structure has any copyrightable content, note that it is licensed as follows:
# Copyright (c) the OpenSSL contributors
# Licensed under the Apache License 2.0
# https://github.com/openssl/openssl/blob/master/LICENSE
_OID_MAP = {
    '0': ('itu-t', 'ITU-T', 'ccitt'),
    '0.3.4401.5': ('ntt-ds', ),
    '0.3.4401.5.3.1.9': ('camellia', ),
    '0.3.4401.5.3.1.9.1': ('camellia-128-ecb', 'CAMELLIA-128-ECB'),
    '0.3.4401.5.3.1.9.3': ('camellia-128-ofb', 'CAMELLIA-128-OFB'),
    '0.3.4401.5.3.1.9.4': ('camellia-128-cfb', 'CAMELLIA-128-CFB'),
    '0.3.4401.5.3.1.9.6': ('camellia-128-gcm', 'CAMELLIA-128-GCM'),
    '0.3.4401.5.3.1.9.7': ('camellia-128-ccm', 'CAMELLIA-128-CCM'),
    '0.3.4401.5.3.1.9.9': ('camellia-128-ctr', 'CAMELLIA-128-CTR'),
    '0.3.4401.5.3.1.9.10': ('camellia-128-cmac', 'CAMELLIA-128-CMAC'),
    '0.3.4401.5.3.1.9.21': ('camellia-192-ecb', 'CAMELLIA-192-ECB'),
    '0.3.4401.5.3.1.9.23': ('camellia-192-ofb', 'CAMELLIA-192-OFB'),
    '0.3.4401.5.3.1.9.24': ('camellia-192-cfb', 'CAMELLIA-192-CFB'),
    '0.3.4401.5.3.1.9.26': ('camellia-192-gcm', 'CAMELLIA-192-GCM'),
    '0.3.4401.5.3.1.9.27': ('camellia-192-ccm', 'CAMELLIA-192-CCM'),
    '0.3.4401.5.3.1.9.29': ('camellia-192-ctr', 'CAMELLIA-192-CTR'),
    '0.3.4401.5.3.1.9.30': ('camellia-192-cmac', 'CAMELLIA-192-CMAC'),
    '0.3.4401.5.3.1.9.41': ('camellia-256-ecb', 'CAMELLIA-256-ECB'),
    '0.3.4401.5.3.1.9.43': ('camellia-256-ofb', 'CAMELLIA-256-OFB'),
    '0.3.4401.5.3.1.9.44': ('camellia-256-cfb', 'CAMELLIA-256-CFB'),
    '0.3.4401.5.3.1.9.46': ('camellia-256-gcm', 'CAMELLIA-256-GCM'),
    '0.3.4401.5.3.1.9.47': ('camellia-256-ccm', 'CAMELLIA-256-CCM'),
    '0.3.4401.5.3.1.9.49': ('camellia-256-ctr', 'CAMELLIA-256-CTR'),
    '0.3.4401.5.3.1.9.50': ('camellia-256-cmac', 'CAMELLIA-256-CMAC'),
    '0.9': ('data', ),
    '0.9.2342': ('pss', ),
    '0.9.2342.19200300': ('ucl', ),
    '0.9.2342.19200300.100': ('pilot', ),
    '0.9.2342.19200300.100.1': ('pilotAttributeType', ),
    '0.9.2342.19200300.100.1.1': ('userId', 'UID'),
    '0.9.2342.19200300.100.1.2': ('textEncodedORAddress', ),
    '0.9.2342.19200300.100.1.3': ('rfc822Mailbox', 'mail'),
    '0.9.2342.19200300.100.1.4': ('info', ),
    '0.9.2342.19200300.100.1.5': ('favouriteDrink', ),
    '0.9.2342.19200300.100.1.6': ('roomNumber', ),
    '0.9.2342.19200300.100.1.7': ('photo', ),
    '0.9.2342.19200300.100.1.8': ('userClass', ),
    '0.9.2342.19200300.100.1.9': ('host', ),
    '0.9.2342.19200300.100.1.10': ('manager', ),
    '0.9.2342.19200300.100.1.11': ('documentIdentifier', ),
    '0.9.2342.19200300.100.1.12': ('documentTitle', ),
    '0.9.2342.19200300.100.1.13': ('documentVersion', ),
    '0.9.2342.19200300.100.1.14': ('documentAuthor', ),
    '0.9.2342.19200300.100.1.15': ('documentLocation', ),
    '0.9.2342.19200300.100.1.20': ('homeTelephoneNumber', ),
    '0.9.2342.19200300.100.1.21': ('secretary', ),
    '0.9.2342.19200300.100.1.22': ('otherMailbox', ),
    '0.9.2342.19200300.100.1.23': ('lastModifiedTime', ),
    '0.9.2342.19200300.100.1.24': ('lastModifiedBy', ),
    '0.9.2342.19200300.100.1.25': ('domainComponent', 'DC'),
    '0.9.2342.19200300.100.1.26': ('aRecord', ),
    '0.9.2342.19200300.100.1.27': ('pilotAttributeType27', ),
    '0.9.2342.19200300.100.1.28': ('mXRecord', ),
    '0.9.2342.19200300.100.1.29': ('nSRecord', ),
    '0.9.2342.19200300.100.1.30': ('sOARecord', ),
    '0.9.2342.19200300.100.1.31': ('cNAMERecord', ),
    '0.9.2342.19200300.100.1.37': ('associatedDomain', ),
    '0.9.2342.19200300.100.1.38': ('associatedName', ),
    '0.9.2342.19200300.100.1.39': ('homePostalAddress', ),
    '0.9.2342.19200300.100.1.40': ('personalTitle', ),
    '0.9.2342.19200300.100.1.41': ('mobileTelephoneNumber', ),
    '0.9.2342.19200300.100.1.42': ('pagerTelephoneNumber', ),
    '0.9.2342.19200300.100.1.43': ('friendlyCountryName', ),
    '0.9.2342.19200300.100.1.44': ('uniqueIdentifier', 'uid'),
    '0.9.2342.19200300.100.1.45': ('organizationalStatus', ),
    '0.9.2342.19200300.100.1.46': ('janetMailbox', ),
    '0.9.2342.19200300.100.1.47': ('mailPreferenceOption', ),
    '0.9.2342.19200300.100.1.48': ('buildingName', ),
    '0.9.2342.19200300.100.1.49': ('dSAQuality', ),
    '0.9.2342.19200300.100.1.50': ('singleLevelQuality', ),
    '0.9.2342.19200300.100.1.51': ('subtreeMinimumQuality', ),
    '0.9.2342.19200300.100.1.52': ('subtreeMaximumQuality', ),
    '0.9.2342.19200300.100.1.53': ('personalSignature', ),
    '0.9.2342.19200300.100.1.54': ('dITRedirect', ),
    '0.9.2342.19200300.100.1.55': ('audio', ),
    '0.9.2342.19200300.100.1.56': ('documentPublisher', ),
    '0.9.2342.19200300.100.3': ('pilotAttributeSyntax', ),
    '0.9.2342.19200300.100.3.4': ('iA5StringSyntax', ),
    '0.9.2342.19200300.100.3.5': ('caseIgnoreIA5StringSyntax', ),
    '0.9.2342.19200300.100.4': ('pilotObjectClass', ),
    '0.9.2342.19200300.100.4.3': ('pilotObject', ),
    '0.9.2342.19200300.100.4.4': ('pilotPerson', ),
    '0.9.2342.19200300.100.4.5': ('account', ),
    '0.9.2342.19200300.100.4.6': ('document', ),
    '0.9.2342.19200300.100.4.7': ('room', ),
    '0.9.2342.19200300.100.4.9': ('documentSeries', ),
    '0.9.2342.19200300.100.4.13': ('Domain', 'domain'),
    '0.9.2342.19200300.100.4.14': ('rFC822localPart', ),
    '0.9.2342.19200300.100.4.15': ('dNSDomain', ),
    '0.9.2342.19200300.100.4.17': ('domainRelatedObject', ),
    '0.9.2342.19200300.100.4.18': ('friendlyCountry', ),
    '0.9.2342.19200300.100.4.19': ('simpleSecurityObject', ),
    '0.9.2342.19200300.100.4.20': ('pilotOrganization', ),
    '0.9.2342.19200300.100.4.21': ('pilotDSA', ),
    '0.9.2342.19200300.100.4.22': ('qualityLabelledData', ),
    '0.9.2342.19200300.100.10': ('pilotGroups', ),
    '1': ('iso', 'ISO'),
    '1.0.9797.3.4': ('gmac', 'GMAC'),
    '1.0.10118.3.0.55': ('whirlpool', ),
    '1.2': ('ISO Member Body', 'member-body'),
    '1.2.156': ('ISO CN Member Body', 'ISO-CN'),
    '1.2.156.10197': ('oscca', ),
    '1.2.156.10197.1': ('sm-scheme', ),
    '1.2.156.10197.1.104.1': ('sm4-ecb', 'SM4-ECB'),
    '1.2.156.10197.1.104.2': ('sm4-cbc', 'SM4-CBC'),
    '1.2.156.10197.1.104.3': ('sm4-ofb', 'SM4-OFB'),
    '1.2.156.10197.1.104.4': ('sm4-cfb', 'SM4-CFB'),
    '1.2.156.10197.1.104.5': ('sm4-cfb1', 'SM4-CFB1'),
    '1.2.156.10197.1.104.6': ('sm4-cfb8', 'SM4-CFB8'),
    '1.2.156.10197.1.104.7': ('sm4-ctr', 'SM4-CTR'),
    '1.2.156.10197.1.301': ('sm2', 'SM2'),
    '1.2.156.10197.1.401': ('sm3', 'SM3'),
    '1.2.156.10197.1.501': ('SM2-with-SM3', 'SM2-SM3'),
    '1.2.156.10197.1.504': ('sm3WithRSAEncryption', 'RSA-SM3'),
    '1.2.392.200011.61.1.1.1.2': ('camellia-128-cbc', 'CAMELLIA-128-CBC'),
    '1.2.392.200011.61.1.1.1.3': ('camellia-192-cbc', 'CAMELLIA-192-CBC'),
    '1.2.392.200011.61.1.1.1.4': ('camellia-256-cbc', 'CAMELLIA-256-CBC'),
    '1.2.392.200011.61.1.1.3.2': ('id-camellia128-wrap', ),
    '1.2.392.200011.61.1.1.3.3': ('id-camellia192-wrap', ),
    '1.2.392.200011.61.1.1.3.4': ('id-camellia256-wrap', ),
    '1.2.410.200004': ('kisa', 'KISA'),
    '1.2.410.200004.1.3': ('seed-ecb', 'SEED-ECB'),
    '1.2.410.200004.1.4': ('seed-cbc', 'SEED-CBC'),
    '1.2.410.200004.1.5': ('seed-cfb', 'SEED-CFB'),
    '1.2.410.200004.1.6': ('seed-ofb', 'SEED-OFB'),
    '1.2.410.200046.1.1': ('aria', ),
    '1.2.410.200046.1.1.1': ('aria-128-ecb', 'ARIA-128-ECB'),
    '1.2.410.200046.1.1.2': ('aria-128-cbc', 'ARIA-128-CBC'),
    '1.2.410.200046.1.1.3': ('aria-128-cfb', 'ARIA-128-CFB'),
    '1.2.410.200046.1.1.4': ('aria-128-ofb', 'ARIA-128-OFB'),
    '1.2.410.200046.1.1.5': ('aria-128-ctr', 'ARIA-128-CTR'),
    '1.2.410.200046.1.1.6': ('aria-192-ecb', 'ARIA-192-ECB'),
    '1.2.410.200046.1.1.7': ('aria-192-cbc', 'ARIA-192-CBC'),
    '1.2.410.200046.1.1.8': ('aria-192-cfb', 'ARIA-192-CFB'),
    '1.2.410.200046.1.1.9': ('aria-192-ofb', 'ARIA-192-OFB'),
    '1.2.410.200046.1.1.10': ('aria-192-ctr', 'ARIA-192-CTR'),
    '1.2.410.200046.1.1.11': ('aria-256-ecb', 'ARIA-256-ECB'),
    '1.2.410.200046.1.1.12': ('aria-256-cbc', 'ARIA-256-CBC'),
    '1.2.410.200046.1.1.13': ('aria-256-cfb', 'ARIA-256-CFB'),
    '1.2.410.200046.1.1.14': ('aria-256-ofb', 'ARIA-256-OFB'),
    '1.2.410.200046.1.1.15': ('aria-256-ctr', 'ARIA-256-CTR'),
    '1.2.410.200046.1.1.34': ('aria-128-gcm', 'ARIA-128-GCM'),
    '1.2.410.200046.1.1.35': ('aria-192-gcm', 'ARIA-192-GCM'),
    '1.2.410.200046.1.1.36': ('aria-256-gcm', 'ARIA-256-GCM'),
    '1.2.410.200046.1.1.37': ('aria-128-ccm', 'ARIA-128-CCM'),
    '1.2.410.200046.1.1.38': ('aria-192-ccm', 'ARIA-192-CCM'),
    '1.2.410.200046.1.1.39': ('aria-256-ccm', 'ARIA-256-CCM'),
    '1.2.643.2.2': ('cryptopro', ),
    '1.2.643.2.2.3': ('GOST R 34.11-94 with GOST R 34.10-2001', 'id-GostR3411-94-with-GostR3410-2001'),
    '1.2.643.2.2.4': ('GOST R 34.11-94 with GOST R 34.10-94', 'id-GostR3411-94-with-GostR3410-94'),
    '1.2.643.2.2.9': ('GOST R 34.11-94', 'md_gost94'),
    '1.2.643.2.2.10': ('HMAC GOST 34.11-94', 'id-HMACGostR3411-94'),
    '1.2.643.2.2.14.0': ('id-Gost28147-89-None-KeyMeshing', ),
    '1.2.643.2.2.14.1': ('id-Gost28147-89-CryptoPro-KeyMeshing', ),
    '1.2.643.2.2.19': ('GOST R 34.10-2001', 'gost2001'),
    '1.2.643.2.2.20': ('GOST R 34.10-94', 'gost94'),
    '1.2.643.2.2.20.1': ('id-GostR3410-94-a', ),
    '1.2.643.2.2.20.2': ('id-GostR3410-94-aBis', ),
    '1.2.643.2.2.20.3': ('id-GostR3410-94-b', ),
    '1.2.643.2.2.20.4': ('id-GostR3410-94-bBis', ),
    '1.2.643.2.2.21': ('GOST 28147-89', 'gost89'),
    '1.2.643.2.2.22': ('GOST 28147-89 MAC', 'gost-mac'),
    '1.2.643.2.2.23': ('GOST R 34.11-94 PRF', 'prf-gostr3411-94'),
    '1.2.643.2.2.30.0': ('id-GostR3411-94-TestParamSet', ),
    '1.2.643.2.2.30.1': ('id-GostR3411-94-CryptoProParamSet', ),
    '1.2.643.2.2.31.0': ('id-Gost28147-89-TestParamSet', ),
    '1.2.643.2.2.31.1': ('id-Gost28147-89-CryptoPro-A-ParamSet', ),
    '1.2.643.2.2.31.2': ('id-Gost28147-89-CryptoPro-B-ParamSet', ),
    '1.2.643.2.2.31.3': ('id-Gost28147-89-CryptoPro-C-ParamSet', ),
    '1.2.643.2.2.31.4': ('id-Gost28147-89-CryptoPro-D-ParamSet', ),
    '1.2.643.2.2.31.5': ('id-Gost28147-89-CryptoPro-Oscar-1-1-ParamSet', ),
    '1.2.643.2.2.31.6': ('id-Gost28147-89-CryptoPro-Oscar-1-0-ParamSet', ),
    '1.2.643.2.2.31.7': ('id-Gost28147-89-CryptoPro-RIC-1-ParamSet', ),
    '1.2.643.2.2.32.0': ('id-GostR3410-94-TestParamSet', ),
    '1.2.643.2.2.32.2': ('id-GostR3410-94-CryptoPro-A-ParamSet', ),
    '1.2.643.2.2.32.3': ('id-GostR3410-94-CryptoPro-B-ParamSet', ),
    '1.2.643.2.2.32.4': ('id-GostR3410-94-CryptoPro-C-ParamSet', ),
    '1.2.643.2.2.32.5': ('id-GostR3410-94-CryptoPro-D-ParamSet', ),
    '1.2.643.2.2.33.1': ('id-GostR3410-94-CryptoPro-XchA-ParamSet', ),
    '1.2.643.2.2.33.2': ('id-GostR3410-94-CryptoPro-XchB-ParamSet', ),
    '1.2.643.2.2.33.3': ('id-GostR3410-94-CryptoPro-XchC-ParamSet', ),
    '1.2.643.2.2.35.0': ('id-GostR3410-2001-TestParamSet', ),
    '1.2.643.2.2.35.1': ('id-GostR3410-2001-CryptoPro-A-ParamSet', ),
    '1.2.643.2.2.35.2': ('id-GostR3410-2001-CryptoPro-B-ParamSet', ),
    '1.2.643.2.2.35.3': ('id-GostR3410-2001-CryptoPro-C-ParamSet', ),
    '1.2.643.2.2.36.0': ('id-GostR3410-2001-CryptoPro-XchA-ParamSet', ),
    '1.2.643.2.2.36.1': ('id-GostR3410-2001-CryptoPro-XchB-ParamSet', ),
    '1.2.643.2.2.98': ('GOST R 34.10-2001 DH', 'id-GostR3410-2001DH'),
    '1.2.643.2.2.99': ('GOST R 34.10-94 DH', 'id-GostR3410-94DH'),
    '1.2.643.2.9': ('cryptocom', ),
    '1.2.643.2.9.1.3.3': ('GOST R 34.11-94 with GOST R 34.10-94 Cryptocom', 'id-GostR3411-94-with-GostR3410-94-cc'),
    '1.2.643.2.9.1.3.4': ('GOST R 34.11-94 with GOST R 34.10-2001 Cryptocom', 'id-GostR3411-94-with-GostR3410-2001-cc'),
    '1.2.643.2.9.1.5.3': ('GOST 34.10-94 Cryptocom', 'gost94cc'),
    '1.2.643.2.9.1.5.4': ('GOST 34.10-2001 Cryptocom', 'gost2001cc'),
    '1.2.643.2.9.1.6.1': ('GOST 28147-89 Cryptocom ParamSet', 'id-Gost28147-89-cc'),
    '1.2.643.2.9.1.8.1': ('GOST R 3410-2001 Parameter Set Cryptocom', 'id-GostR3410-2001-ParamSet-cc'),
    '1.2.643.3.131.1.1': ('INN', 'INN'),
    '1.2.643.7.1': ('id-tc26', ),
    '1.2.643.7.1.1': ('id-tc26-algorithms', ),
    '1.2.643.7.1.1.1': ('id-tc26-sign', ),
    '1.2.643.7.1.1.1.1': ('GOST R 34.10-2012 with 256 bit modulus', 'gost2012_256'),
    '1.2.643.7.1.1.1.2': ('GOST R 34.10-2012 with 512 bit modulus', 'gost2012_512'),
    '1.2.643.7.1.1.2': ('id-tc26-digest', ),
    '1.2.643.7.1.1.2.2': ('GOST R 34.11-2012 with 256 bit hash', 'md_gost12_256'),
    '1.2.643.7.1.1.2.3': ('GOST R 34.11-2012 with 512 bit hash', 'md_gost12_512'),
    '1.2.643.7.1.1.3': ('id-tc26-signwithdigest', ),
    '1.2.643.7.1.1.3.2': ('GOST R 34.10-2012 with GOST R 34.11-2012 (256 bit)', 'id-tc26-signwithdigest-gost3410-2012-256'),
    '1.2.643.7.1.1.3.3': ('GOST R 34.10-2012 with GOST R 34.11-2012 (512 bit)', 'id-tc26-signwithdigest-gost3410-2012-512'),
    '1.2.643.7.1.1.4': ('id-tc26-mac', ),
    '1.2.643.7.1.1.4.1': ('HMAC GOST 34.11-2012 256 bit', 'id-tc26-hmac-gost-3411-2012-256'),
    '1.2.643.7.1.1.4.2': ('HMAC GOST 34.11-2012 512 bit', 'id-tc26-hmac-gost-3411-2012-512'),
    '1.2.643.7.1.1.5': ('id-tc26-cipher', ),
    '1.2.643.7.1.1.5.1': ('id-tc26-cipher-gostr3412-2015-magma', ),
    '1.2.643.7.1.1.5.1.1': ('id-tc26-cipher-gostr3412-2015-magma-ctracpkm', ),
    '1.2.643.7.1.1.5.1.2': ('id-tc26-cipher-gostr3412-2015-magma-ctracpkm-omac', ),
    '1.2.643.7.1.1.5.2': ('id-tc26-cipher-gostr3412-2015-kuznyechik', ),
    '1.2.643.7.1.1.5.2.1': ('id-tc26-cipher-gostr3412-2015-kuznyechik-ctracpkm', ),
    '1.2.643.7.1.1.5.2.2': ('id-tc26-cipher-gostr3412-2015-kuznyechik-ctracpkm-omac', ),
    '1.2.643.7.1.1.6': ('id-tc26-agreement', ),
    '1.2.643.7.1.1.6.1': ('id-tc26-agreement-gost-3410-2012-256', ),
    '1.2.643.7.1.1.6.2': ('id-tc26-agreement-gost-3410-2012-512', ),
    '1.2.643.7.1.1.7': ('id-tc26-wrap', ),
    '1.2.643.7.1.1.7.1': ('id-tc26-wrap-gostr3412-2015-magma', ),
    '1.2.643.7.1.1.7.1.1': ('id-tc26-wrap-gostr3412-2015-magma-kexp15', 'id-tc26-wrap-gostr3412-2015-kuznyechik-kexp15'),
    '1.2.643.7.1.1.7.2': ('id-tc26-wrap-gostr3412-2015-kuznyechik', ),
    '1.2.643.7.1.2': ('id-tc26-constants', ),
    '1.2.643.7.1.2.1': ('id-tc26-sign-constants', ),
    '1.2.643.7.1.2.1.1': ('id-tc26-gost-3410-2012-256-constants', ),
    '1.2.643.7.1.2.1.1.1': ('GOST R 34.10-2012 (256 bit) ParamSet A', 'id-tc26-gost-3410-2012-256-paramSetA'),
    '1.2.643.7.1.2.1.1.2': ('GOST R 34.10-2012 (256 bit) ParamSet B', 'id-tc26-gost-3410-2012-256-paramSetB'),
    '1.2.643.7.1.2.1.1.3': ('GOST R 34.10-2012 (256 bit) ParamSet C', 'id-tc26-gost-3410-2012-256-paramSetC'),
    '1.2.643.7.1.2.1.1.4': ('GOST R 34.10-2012 (256 bit) ParamSet D', 'id-tc26-gost-3410-2012-256-paramSetD'),
    '1.2.643.7.1.2.1.2': ('id-tc26-gost-3410-2012-512-constants', ),
    '1.2.643.7.1.2.1.2.0': ('GOST R 34.10-2012 (512 bit) testing parameter set', 'id-tc26-gost-3410-2012-512-paramSetTest'),
    '1.2.643.7.1.2.1.2.1': ('GOST R 34.10-2012 (512 bit) ParamSet A', 'id-tc26-gost-3410-2012-512-paramSetA'),
    '1.2.643.7.1.2.1.2.2': ('GOST R 34.10-2012 (512 bit) ParamSet B', 'id-tc26-gost-3410-2012-512-paramSetB'),
    '1.2.643.7.1.2.1.2.3': ('GOST R 34.10-2012 (512 bit) ParamSet C', 'id-tc26-gost-3410-2012-512-paramSetC'),
    '1.2.643.7.1.2.2': ('id-tc26-digest-constants', ),
    '1.2.643.7.1.2.5': ('id-tc26-cipher-constants', ),
    '1.2.643.7.1.2.5.1': ('id-tc26-gost-28147-constants', ),
    '1.2.643.7.1.2.5.1.1': ('GOST 28147-89 TC26 parameter set', 'id-tc26-gost-28147-param-Z'),
    '1.2.643.100.1': ('OGRN', 'OGRN'),
    '1.2.643.100.3': ('SNILS', 'SNILS'),
    '1.2.643.100.111': ('Signing Tool of Subject', 'subjectSignTool'),
    '1.2.643.100.112': ('Signing Tool of Issuer', 'issuerSignTool'),
    '1.2.804': ('ISO-UA', ),
    '1.2.804.2.1.1.1': ('ua-pki', ),
    '1.2.804.2.1.1.1.1.1.1': ('DSTU Gost 28147-2009', 'dstu28147'),
    '1.2.804.2.1.1.1.1.1.1.2': ('DSTU Gost 28147-2009 OFB mode', 'dstu28147-ofb'),
    '1.2.804.2.1.1.1.1.1.1.3': ('DSTU Gost 28147-2009 CFB mode', 'dstu28147-cfb'),
    '1.2.804.2.1.1.1.1.1.1.5': ('DSTU Gost 28147-2009 key wrap', 'dstu28147-wrap'),
    '1.2.804.2.1.1.1.1.1.2': ('HMAC DSTU Gost 34311-95', 'hmacWithDstu34311'),
    '1.2.804.2.1.1.1.1.2.1': ('DSTU Gost 34311-95', 'dstu34311'),
    '1.2.804.2.1.1.1.1.3.1.1': ('DSTU 4145-2002 little endian', 'dstu4145le'),
    '1.2.804.2.1.1.1.1.3.1.1.1.1': ('DSTU 4145-2002 big endian', 'dstu4145be'),
    '1.2.804.2.1.1.1.1.3.1.1.2.0': ('DSTU curve 0', 'uacurve0'),
    '1.2.804.2.1.1.1.1.3.1.1.2.1': ('DSTU curve 1', 'uacurve1'),
    '1.2.804.2.1.1.1.1.3.1.1.2.2': ('DSTU curve 2', 'uacurve2'),
    '1.2.804.2.1.1.1.1.3.1.1.2.3': ('DSTU curve 3', 'uacurve3'),
    '1.2.804.2.1.1.1.1.3.1.1.2.4': ('DSTU curve 4', 'uacurve4'),
    '1.2.804.2.1.1.1.1.3.1.1.2.5': ('DSTU curve 5', 'uacurve5'),
    '1.2.804.2.1.1.1.1.3.1.1.2.6': ('DSTU curve 6', 'uacurve6'),
    '1.2.804.2.1.1.1.1.3.1.1.2.7': ('DSTU curve 7', 'uacurve7'),
    '1.2.804.2.1.1.1.1.3.1.1.2.8': ('DSTU curve 8', 'uacurve8'),
    '1.2.804.2.1.1.1.1.3.1.1.2.9': ('DSTU curve 9', 'uacurve9'),
    '1.2.840': ('ISO US Member Body', 'ISO-US'),
    '1.2.840.10040': ('X9.57', 'X9-57'),
    '1.2.840.10040.2': ('holdInstruction', ),
    '1.2.840.10040.2.1': ('Hold Instruction None', 'holdInstructionNone'),
    '1.2.840.10040.2.2': ('Hold Instruction Call Issuer', 'holdInstructionCallIssuer'),
    '1.2.840.10040.2.3': ('Hold Instruction Reject', 'holdInstructionReject'),
    '1.2.840.10040.4': ('X9.57 CM ?', 'X9cm'),
    '1.2.840.10040.4.1': ('dsaEncryption', 'DSA'),
    '1.2.840.10040.4.3': ('dsaWithSHA1', 'DSA-SHA1'),
    '1.2.840.10045': ('ANSI X9.62', 'ansi-X9-62'),
    '1.2.840.10045.1': ('id-fieldType', ),
    '1.2.840.10045.1.1': ('prime-field', ),
    '1.2.840.10045.1.2': ('characteristic-two-field', ),
    '1.2.840.10045.1.2.3': ('id-characteristic-two-basis', ),
    '1.2.840.10045.1.2.3.1': ('onBasis', ),
    '1.2.840.10045.1.2.3.2': ('tpBasis', ),
    '1.2.840.10045.1.2.3.3': ('ppBasis', ),
    '1.2.840.10045.2': ('id-publicKeyType', ),
    '1.2.840.10045.2.1': ('id-ecPublicKey', ),
    '1.2.840.10045.3': ('ellipticCurve', ),
    '1.2.840.10045.3.0': ('c-TwoCurve', ),
    '1.2.840.10045.3.0.1': ('c2pnb163v1', ),
    '1.2.840.10045.3.0.2': ('c2pnb163v2', ),
    '1.2.840.10045.3.0.3': ('c2pnb163v3', ),
    '1.2.840.10045.3.0.4': ('c2pnb176v1', ),
    '1.2.840.10045.3.0.5': ('c2tnb191v1', ),
    '1.2.840.10045.3.0.6': ('c2tnb191v2', ),
    '1.2.840.10045.3.0.7': ('c2tnb191v3', ),
    '1.2.840.10045.3.0.8': ('c2onb191v4', ),
    '1.2.840.10045.3.0.9': ('c2onb191v5', ),
    '1.2.840.10045.3.0.10': ('c2pnb208w1', ),
    '1.2.840.10045.3.0.11': ('c2tnb239v1', ),
    '1.2.840.10045.3.0.12': ('c2tnb239v2', ),
    '1.2.840.10045.3.0.13': ('c2tnb239v3', ),
    '1.2.840.10045.3.0.14': ('c2onb239v4', ),
    '1.2.840.10045.3.0.15': ('c2onb239v5', ),
    '1.2.840.10045.3.0.16': ('c2pnb272w1', ),
    '1.2.840.10045.3.0.17': ('c2pnb304w1', ),
    '1.2.840.10045.3.0.18': ('c2tnb359v1', ),
    '1.2.840.10045.3.0.19': ('c2pnb368w1', ),
    '1.2.840.10045.3.0.20': ('c2tnb431r1', ),
    '1.2.840.10045.3.1': ('primeCurve', ),
    '1.2.840.10045.3.1.1': ('prime192v1', ),
    '1.2.840.10045.3.1.2': ('prime192v2', ),
    '1.2.840.10045.3.1.3': ('prime192v3', ),
    '1.2.840.10045.3.1.4': ('prime239v1', ),
    '1.2.840.10045.3.1.5': ('prime239v2', ),
    '1.2.840.10045.3.1.6': ('prime239v3', ),
    '1.2.840.10045.3.1.7': ('prime256v1', ),
    '1.2.840.10045.4': ('id-ecSigType', ),
    '1.2.840.10045.4.1': ('ecdsa-with-SHA1', ),
    '1.2.840.10045.4.2': ('ecdsa-with-Recommended', ),
    '1.2.840.10045.4.3': ('ecdsa-with-Specified', ),
    '1.2.840.10045.4.3.1': ('ecdsa-with-SHA224', ),
    '1.2.840.10045.4.3.2': ('ecdsa-with-SHA256', ),
    '1.2.840.10045.4.3.3': ('ecdsa-with-SHA384', ),
    '1.2.840.10045.4.3.4': ('ecdsa-with-SHA512', ),
    '1.2.840.10046.2.1': ('X9.42 DH', 'dhpublicnumber'),
    '1.2.840.113533.7.66.10': ('cast5-cbc', 'CAST5-CBC'),
    '1.2.840.113533.7.66.12': ('pbeWithMD5AndCast5CBC', ),
    '1.2.840.113533.7.66.13': ('password based MAC', 'id-PasswordBasedMAC'),
    '1.2.840.113533.7.66.30': ('Diffie-Hellman based MAC', 'id-DHBasedMac'),
    '1.2.840.113549': ('RSA Data Security, Inc.', 'rsadsi'),
    '1.2.840.113549.1': ('RSA Data Security, Inc. PKCS', 'pkcs'),
    '1.2.840.113549.1.1': ('pkcs1', ),
    '1.2.840.113549.1.1.1': ('rsaEncryption', ),
    '1.2.840.113549.1.1.2': ('md2WithRSAEncryption', 'RSA-MD2'),
    '1.2.840.113549.1.1.3': ('md4WithRSAEncryption', 'RSA-MD4'),
    '1.2.840.113549.1.1.4': ('md5WithRSAEncryption', 'RSA-MD5'),
    '1.2.840.113549.1.1.5': ('sha1WithRSAEncryption', 'RSA-SHA1'),
    '1.2.840.113549.1.1.6': ('rsaOAEPEncryptionSET', ),
    '1.2.840.113549.1.1.7': ('rsaesOaep', 'RSAES-OAEP'),
    '1.2.840.113549.1.1.8': ('mgf1', 'MGF1'),
    '1.2.840.113549.1.1.9': ('pSpecified', 'PSPECIFIED'),
    '1.2.840.113549.1.1.10': ('rsassaPss', 'RSASSA-PSS'),
    '1.2.840.113549.1.1.11': ('sha256WithRSAEncryption', 'RSA-SHA256'),
    '1.2.840.113549.1.1.12': ('sha384WithRSAEncryption', 'RSA-SHA384'),
    '1.2.840.113549.1.1.13': ('sha512WithRSAEncryption', 'RSA-SHA512'),
    '1.2.840.113549.1.1.14': ('sha224WithRSAEncryption', 'RSA-SHA224'),
    '1.2.840.113549.1.1.15': ('sha512-224WithRSAEncryption', 'RSA-SHA512/224'),
    '1.2.840.113549.1.1.16': ('sha512-256WithRSAEncryption', 'RSA-SHA512/256'),
    '1.2.840.113549.1.3': ('pkcs3', ),
    '1.2.840.113549.1.3.1': ('dhKeyAgreement', ),
    '1.2.840.113549.1.5': ('pkcs5', ),
    '1.2.840.113549.1.5.1': ('pbeWithMD2AndDES-CBC', 'PBE-MD2-DES'),
    '1.2.840.113549.1.5.3': ('pbeWithMD5AndDES-CBC', 'PBE-MD5-DES'),
    '1.2.840.113549.1.5.4': ('pbeWithMD2AndRC2-CBC', 'PBE-MD2-RC2-64'),
    '1.2.840.113549.1.5.6': ('pbeWithMD5AndRC2-CBC', 'PBE-MD5-RC2-64'),
    '1.2.840.113549.1.5.10': ('pbeWithSHA1AndDES-CBC', 'PBE-SHA1-DES'),
    '1.2.840.113549.1.5.11': ('pbeWithSHA1AndRC2-CBC', 'PBE-SHA1-RC2-64'),
    '1.2.840.113549.1.5.12': ('PBKDF2', ),
    '1.2.840.113549.1.5.13': ('PBES2', ),
    '1.2.840.113549.1.5.14': ('PBMAC1', ),
    '1.2.840.113549.1.7': ('pkcs7', ),
    '1.2.840.113549.1.7.1': ('pkcs7-data', ),
    '1.2.840.113549.1.7.2': ('pkcs7-signedData', ),
    '1.2.840.113549.1.7.3': ('pkcs7-envelopedData', ),
    '1.2.840.113549.1.7.4': ('pkcs7-signedAndEnvelopedData', ),
    '1.2.840.113549.1.7.5': ('pkcs7-digestData', ),
    '1.2.840.113549.1.7.6': ('pkcs7-encryptedData', ),
    '1.2.840.113549.1.9': ('pkcs9', ),
    '1.2.840.113549.1.9.1': ('emailAddress', ),
    '1.2.840.113549.1.9.2': ('unstructuredName', ),
    '1.2.840.113549.1.9.3': ('contentType', ),
    '1.2.840.113549.1.9.4': ('messageDigest', ),
    '1.2.840.113549.1.9.5': ('signingTime', ),
    '1.2.840.113549.1.9.6': ('countersignature', ),
    '1.2.840.113549.1.9.7': ('challengePassword', ),
    '1.2.840.113549.1.9.8': ('unstructuredAddress', ),
    '1.2.840.113549.1.9.9': ('extendedCertificateAttributes', ),
    '1.2.840.113549.1.9.14': ('Extension Request', 'extReq'),
    '1.2.840.113549.1.9.15': ('S/MIME Capabilities', 'SMIME-CAPS'),
    '1.2.840.113549.1.9.16': ('S/MIME', 'SMIME'),
    '1.2.840.113549.1.9.16.0': ('id-smime-mod', ),
    '1.2.840.113549.1.9.16.0.1': ('id-smime-mod-cms', ),
    '1.2.840.113549.1.9.16.0.2': ('id-smime-mod-ess', ),
    '1.2.840.113549.1.9.16.0.3': ('id-smime-mod-oid', ),
    '1.2.840.113549.1.9.16.0.4': ('id-smime-mod-msg-v3', ),
    '1.2.840.113549.1.9.16.0.5': ('id-smime-mod-ets-eSignature-88', ),
    '1.2.840.113549.1.9.16.0.6': ('id-smime-mod-ets-eSignature-97', ),
    '1.2.840.113549.1.9.16.0.7': ('id-smime-mod-ets-eSigPolicy-88', ),
    '1.2.840.113549.1.9.16.0.8': ('id-smime-mod-ets-eSigPolicy-97', ),
    '1.2.840.113549.1.9.16.1': ('id-smime-ct', ),
    '1.2.840.113549.1.9.16.1.1': ('id-smime-ct-receipt', ),
    '1.2.840.113549.1.9.16.1.2': ('id-smime-ct-authData', ),
    '1.2.840.113549.1.9.16.1.3': ('id-smime-ct-publishCert', ),
    '1.2.840.113549.1.9.16.1.4': ('id-smime-ct-TSTInfo', ),
    '1.2.840.113549.1.9.16.1.5': ('id-smime-ct-TDTInfo', ),
    '1.2.840.113549.1.9.16.1.6': ('id-smime-ct-contentInfo', ),
    '1.2.840.113549.1.9.16.1.7': ('id-smime-ct-DVCSRequestData', ),
    '1.2.840.113549.1.9.16.1.8': ('id-smime-ct-DVCSResponseData', ),
    '1.2.840.113549.1.9.16.1.9': ('id-smime-ct-compressedData', ),
    '1.2.840.113549.1.9.16.1.19': ('id-smime-ct-contentCollection', ),
    '1.2.840.113549.1.9.16.1.23': ('id-smime-ct-authEnvelopedData', ),
    '1.2.840.113549.1.9.16.1.27': ('id-ct-asciiTextWithCRLF', ),
    '1.2.840.113549.1.9.16.1.28': ('id-ct-xml', ),
    '1.2.840.113549.1.9.16.2': ('id-smime-aa', ),
    '1.2.840.113549.1.9.16.2.1': ('id-smime-aa-receiptRequest', ),
    '1.2.840.113549.1.9.16.2.2': ('id-smime-aa-securityLabel', ),
    '1.2.840.113549.1.9.16.2.3': ('id-smime-aa-mlExpandHistory', ),
    '1.2.840.113549.1.9.16.2.4': ('id-smime-aa-contentHint', ),
    '1.2.840.113549.1.9.16.2.5': ('id-smime-aa-msgSigDigest', ),
    '1.2.840.113549.1.9.16.2.6': ('id-smime-aa-encapContentType', ),
    '1.2.840.113549.1.9.16.2.7': ('id-smime-aa-contentIdentifier', ),
    '1.2.840.113549.1.9.16.2.8': ('id-smime-aa-macValue', ),
    '1.2.840.113549.1.9.16.2.9': ('id-smime-aa-equivalentLabels', ),
    '1.2.840.113549.1.9.16.2.10': ('id-smime-aa-contentReference', ),
    '1.2.840.113549.1.9.16.2.11': ('id-smime-aa-encrypKeyPref', ),
    '1.2.840.113549.1.9.16.2.12': ('id-smime-aa-signingCertificate', ),
    '1.2.840.113549.1.9.16.2.13': ('id-smime-aa-smimeEncryptCerts', ),
    '1.2.840.113549.1.9.16.2.14': ('id-smime-aa-timeStampToken', ),
    '1.2.840.113549.1.9.16.2.15': ('id-smime-aa-ets-sigPolicyId', ),
    '1.2.840.113549.1.9.16.2.16': ('id-smime-aa-ets-commitmentType', ),
    '1.2.840.113549.1.9.16.2.17': ('id-smime-aa-ets-signerLocation', ),
    '1.2.840.113549.1.9.16.2.18': ('id-smime-aa-ets-signerAttr', ),
    '1.2.840.113549.1.9.16.2.19': ('id-smime-aa-ets-otherSigCert', ),
    '1.2.840.113549.1.9.16.2.20': ('id-smime-aa-ets-contentTimestamp', ),
    '1.2.840.113549.1.9.16.2.21': ('id-smime-aa-ets-CertificateRefs', ),
    '1.2.840.113549.1.9.16.2.22': ('id-smime-aa-ets-RevocationRefs', ),
    '1.2.840.113549.1.9.16.2.23': ('id-smime-aa-ets-certValues', ),
    '1.2.840.113549.1.9.16.2.24': ('id-smime-aa-ets-revocationValues', ),
    '1.2.840.113549.1.9.16.2.25': ('id-smime-aa-ets-escTimeStamp', ),
    '1.2.840.113549.1.9.16.2.26': ('id-smime-aa-ets-certCRLTimestamp', ),
    '1.2.840.113549.1.9.16.2.27': ('id-smime-aa-ets-archiveTimeStamp', ),
    '1.2.840.113549.1.9.16.2.28': ('id-smime-aa-signatureType', ),
    '1.2.840.113549.1.9.16.2.29': ('id-smime-aa-dvcs-dvc', ),
    '1.2.840.113549.1.9.16.2.47': ('id-smime-aa-signingCertificateV2', ),
    '1.2.840.113549.1.9.16.3': ('id-smime-alg', ),
    '1.2.840.113549.1.9.16.3.1': ('id-smime-alg-ESDHwith3DES', ),
    '1.2.840.113549.1.9.16.3.2': ('id-smime-alg-ESDHwithRC2', ),
    '1.2.840.113549.1.9.16.3.3': ('id-smime-alg-3DESwrap', ),
    '1.2.840.113549.1.9.16.3.4': ('id-smime-alg-RC2wrap', ),
    '1.2.840.113549.1.9.16.3.5': ('id-smime-alg-ESDH', ),
    '1.2.840.113549.1.9.16.3.6': ('id-smime-alg-CMS3DESwrap', ),
    '1.2.840.113549.1.9.16.3.7': ('id-smime-alg-CMSRC2wrap', ),
    '1.2.840.113549.1.9.16.3.8': ('zlib compression', 'ZLIB'),
    '1.2.840.113549.1.9.16.3.9': ('id-alg-PWRI-KEK', ),
    '1.2.840.113549.1.9.16.4': ('id-smime-cd', ),
    '1.2.840.113549.1.9.16.4.1': ('id-smime-cd-ldap', ),
    '1.2.840.113549.1.9.16.5': ('id-smime-spq', ),
    '1.2.840.113549.1.9.16.5.1': ('id-smime-spq-ets-sqt-uri', ),
    '1.2.840.113549.1.9.16.5.2': ('id-smime-spq-ets-sqt-unotice', ),
    '1.2.840.113549.1.9.16.6': ('id-smime-cti', ),
    '1.2.840.113549.1.9.16.6.1': ('id-smime-cti-ets-proofOfOrigin', ),
    '1.2.840.113549.1.9.16.6.2': ('id-smime-cti-ets-proofOfReceipt', ),
    '1.2.840.113549.1.9.16.6.3': ('id-smime-cti-ets-proofOfDelivery', ),
    '1.2.840.113549.1.9.16.6.4': ('id-smime-cti-ets-proofOfSender', ),
    '1.2.840.113549.1.9.16.6.5': ('id-smime-cti-ets-proofOfApproval', ),
    '1.2.840.113549.1.9.16.6.6': ('id-smime-cti-ets-proofOfCreation', ),
    '1.2.840.113549.1.9.20': ('friendlyName', ),
    '1.2.840.113549.1.9.21': ('localKeyID', ),
    '1.2.840.113549.1.9.22': ('certTypes', ),
    '1.2.840.113549.1.9.22.1': ('x509Certificate', ),
    '1.2.840.113549.1.9.22.2': ('sdsiCertificate', ),
    '1.2.840.113549.1.9.23': ('crlTypes', ),
    '1.2.840.113549.1.9.23.1': ('x509Crl', ),
    '1.2.840.113549.1.12': ('pkcs12', ),
    '1.2.840.113549.1.12.1': ('pkcs12-pbeids', ),
    '1.2.840.113549.1.12.1.1': ('pbeWithSHA1And128BitRC4', 'PBE-SHA1-RC4-128'),
    '1.2.840.113549.1.12.1.2': ('pbeWithSHA1And40BitRC4', 'PBE-SHA1-RC4-40'),
    '1.2.840.113549.1.12.1.3': ('pbeWithSHA1And3-KeyTripleDES-CBC', 'PBE-SHA1-3DES'),
    '1.2.840.113549.1.12.1.4': ('pbeWithSHA1And2-KeyTripleDES-CBC', 'PBE-SHA1-2DES'),
    '1.2.840.113549.1.12.1.5': ('pbeWithSHA1And128BitRC2-CBC', 'PBE-SHA1-RC2-128'),
    '1.2.840.113549.1.12.1.6': ('pbeWithSHA1And40BitRC2-CBC', 'PBE-SHA1-RC2-40'),
    '1.2.840.113549.1.12.10': ('pkcs12-Version1', ),
    '1.2.840.113549.1.12.10.1': ('pkcs12-BagIds', ),
    '1.2.840.113549.1.12.10.1.1': ('keyBag', ),
    '1.2.840.113549.1.12.10.1.2': ('pkcs8ShroudedKeyBag', ),
    '1.2.840.113549.1.12.10.1.3': ('certBag', ),
    '1.2.840.113549.1.12.10.1.4': ('crlBag', ),
    '1.2.840.113549.1.12.10.1.5': ('secretBag', ),
    '1.2.840.113549.1.12.10.1.6': ('safeContentsBag', ),
    '1.2.840.113549.2.2': ('md2', 'MD2'),
    '1.2.840.113549.2.4': ('md4', 'MD4'),
    '1.2.840.113549.2.5': ('md5', 'MD5'),
    '1.2.840.113549.2.6': ('hmacWithMD5', ),
    '1.2.840.113549.2.7': ('hmacWithSHA1', ),
    '1.2.840.113549.2.8': ('hmacWithSHA224', ),
    '1.2.840.113549.2.9': ('hmacWithSHA256', ),
    '1.2.840.113549.2.10': ('hmacWithSHA384', ),
    '1.2.840.113549.2.11': ('hmacWithSHA512', ),
    '1.2.840.113549.2.12': ('hmacWithSHA512-224', ),
    '1.2.840.113549.2.13': ('hmacWithSHA512-256', ),
    '1.2.840.113549.3.2': ('rc2-cbc', 'RC2-CBC'),
    '1.2.840.113549.3.4': ('rc4', 'RC4'),
    '1.2.840.113549.3.7': ('des-ede3-cbc', 'DES-EDE3-CBC'),
    '1.2.840.113549.3.8': ('rc5-cbc', 'RC5-CBC'),
    '1.2.840.113549.3.10': ('des-cdmf', 'DES-CDMF'),
    '1.3': ('identified-organization', 'org', 'ORG'),
    '1.3.6': ('dod', 'DOD'),
    '1.3.6.1': ('iana', 'IANA', 'internet'),
    '1.3.6.1.1': ('Directory', 'directory'),
    '1.3.6.1.2': ('Management', 'mgmt'),
    '1.3.6.1.3': ('Experimental', 'experimental'),
    '1.3.6.1.4': ('Private', 'private'),
    '1.3.6.1.4.1': ('Enterprises', 'enterprises'),
    '1.3.6.1.4.1.188.7.1.1.2': ('idea-cbc', 'IDEA-CBC'),
    '1.3.6.1.4.1.311.2.1.14': ('Microsoft Extension Request', 'msExtReq'),
    '1.3.6.1.4.1.311.2.1.21': ('Microsoft Individual Code Signing', 'msCodeInd'),
    '1.3.6.1.4.1.311.2.1.22': ('Microsoft Commercial Code Signing', 'msCodeCom'),
    '1.3.6.1.4.1.311.10.3.1': ('Microsoft Trust List Signing', 'msCTLSign'),
    '1.3.6.1.4.1.311.10.3.3': ('Microsoft Server Gated Crypto', 'msSGC'),
    '1.3.6.1.4.1.311.10.3.4': ('Microsoft Encrypted File System', 'msEFS'),
    '1.3.6.1.4.1.311.17.1': ('Microsoft CSP Name', 'CSPName'),
    '1.3.6.1.4.1.311.17.2': ('Microsoft Local Key set', 'LocalKeySet'),
    '1.3.6.1.4.1.311.20.2.2': ('Microsoft Smartcardlogin', 'msSmartcardLogin'),
    '1.3.6.1.4.1.311.20.2.3': ('Microsoft Universal Principal Name', 'msUPN'),
    '1.3.6.1.4.1.311.60.2.1.1': ('jurisdictionLocalityName', 'jurisdictionL'),
    '1.3.6.1.4.1.311.60.2.1.2': ('jurisdictionStateOrProvinceName', 'jurisdictionST'),
    '1.3.6.1.4.1.311.60.2.1.3': ('jurisdictionCountryName', 'jurisdictionC'),
    '1.3.6.1.4.1.1466.344': ('dcObject', 'dcobject'),
    '1.3.6.1.4.1.1722.12.2.1.16': ('blake2b512', 'BLAKE2b512'),
    '1.3.6.1.4.1.1722.12.2.2.8': ('blake2s256', 'BLAKE2s256'),
    '1.3.6.1.4.1.3029.1.2': ('bf-cbc', 'BF-CBC'),
    '1.3.6.1.4.1.11129.2.4.2': ('CT Precertificate SCTs', 'ct_precert_scts'),
    '1.3.6.1.4.1.11129.2.4.3': ('CT Precertificate Poison', 'ct_precert_poison'),
    '1.3.6.1.4.1.11129.2.4.4': ('CT Precertificate Signer', 'ct_precert_signer'),
    '1.3.6.1.4.1.11129.2.4.5': ('CT Certificate SCTs', 'ct_cert_scts'),
    '1.3.6.1.4.1.11591.4.11': ('scrypt', 'id-scrypt'),
    '1.3.6.1.5': ('Security', 'security'),
    '1.3.6.1.5.2.3': ('id-pkinit', ),
    '1.3.6.1.5.2.3.4': ('PKINIT Client Auth', 'pkInitClientAuth'),
    '1.3.6.1.5.2.3.5': ('Signing KDC Response', 'pkInitKDC'),
    '1.3.6.1.5.5.7': ('PKIX', ),
    '1.3.6.1.5.5.7.0': ('id-pkix-mod', ),
    '1.3.6.1.5.5.7.0.1': ('id-pkix1-explicit-88', ),
    '1.3.6.1.5.5.7.0.2': ('id-pkix1-implicit-88', ),
    '1.3.6.1.5.5.7.0.3': ('id-pkix1-explicit-93', ),
    '1.3.6.1.5.5.7.0.4': ('id-pkix1-implicit-93', ),
    '1.3.6.1.5.5.7.0.5': ('id-mod-crmf', ),
    '1.3.6.1.5.5.7.0.6': ('id-mod-cmc', ),
    '1.3.6.1.5.5.7.0.7': ('id-mod-kea-profile-88', ),
    '1.3.6.1.5.5.7.0.8': ('id-mod-kea-profile-93', ),
    '1.3.6.1.5.5.7.0.9': ('id-mod-cmp', ),
    '1.3.6.1.5.5.7.0.10': ('id-mod-qualified-cert-88', ),
    '1.3.6.1.5.5.7.0.11': ('id-mod-qualified-cert-93', ),
    '1.3.6.1.5.5.7.0.12': ('id-mod-attribute-cert', ),
    '1.3.6.1.5.5.7.0.13': ('id-mod-timestamp-protocol', ),
    '1.3.6.1.5.5.7.0.14': ('id-mod-ocsp', ),
    '1.3.6.1.5.5.7.0.15': ('id-mod-dvcs', ),
    '1.3.6.1.5.5.7.0.16': ('id-mod-cmp2000', ),
    '1.3.6.1.5.5.7.1': ('id-pe', ),
    '1.3.6.1.5.5.7.1.1': ('Authority Information Access', 'authorityInfoAccess'),
    '1.3.6.1.5.5.7.1.2': ('Biometric Info', 'biometricInfo'),
    '1.3.6.1.5.5.7.1.3': ('qcStatements', ),
    '1.3.6.1.5.5.7.1.4': ('ac-auditEntity', ),
    '1.3.6.1.5.5.7.1.5': ('ac-targeting', ),
    '1.3.6.1.5.5.7.1.6': ('aaControls', ),
    '1.3.6.1.5.5.7.1.7': ('sbgp-ipAddrBlock', ),
    '1.3.6.1.5.5.7.1.8': ('sbgp-autonomousSysNum', ),
    '1.3.6.1.5.5.7.1.9': ('sbgp-routerIdentifier', ),
    '1.3.6.1.5.5.7.1.10': ('ac-proxying', ),
    '1.3.6.1.5.5.7.1.11': ('Subject Information Access', 'subjectInfoAccess'),
    '1.3.6.1.5.5.7.1.14': ('Proxy Certificate Information', 'proxyCertInfo'),
    '1.3.6.1.5.5.7.1.24': ('TLS Feature', 'tlsfeature'),
    '1.3.6.1.5.5.7.2': ('id-qt', ),
    '1.3.6.1.5.5.7.2.1': ('Policy Qualifier CPS', 'id-qt-cps'),
    '1.3.6.1.5.5.7.2.2': ('Policy Qualifier User Notice', 'id-qt-unotice'),
    '1.3.6.1.5.5.7.2.3': ('textNotice', ),
    '1.3.6.1.5.5.7.3': ('id-kp', ),
    '1.3.6.1.5.5.7.3.1': ('TLS Web Server Authentication', 'serverAuth'),
    '1.3.6.1.5.5.7.3.2': ('TLS Web Client Authentication', 'clientAuth'),
    '1.3.6.1.5.5.7.3.3': ('Code Signing', 'codeSigning'),
    '1.3.6.1.5.5.7.3.4': ('E-mail Protection', 'emailProtection'),
    '1.3.6.1.5.5.7.3.5': ('IPSec End System', 'ipsecEndSystem'),
    '1.3.6.1.5.5.7.3.6': ('IPSec Tunnel', 'ipsecTunnel'),
    '1.3.6.1.5.5.7.3.7': ('IPSec User', 'ipsecUser'),
    '1.3.6.1.5.5.7.3.8': ('Time Stamping', 'timeStamping'),
    '1.3.6.1.5.5.7.3.9': ('OCSP Signing', 'OCSPSigning'),
    '1.3.6.1.5.5.7.3.10': ('dvcs', 'DVCS'),
    '1.3.6.1.5.5.7.3.17': ('ipsec Internet Key Exchange', 'ipsecIKE'),
    '1.3.6.1.5.5.7.3.18': ('Ctrl/provision WAP Access', 'capwapAC'),
    '1.3.6.1.5.5.7.3.19': ('Ctrl/Provision WAP Termination', 'capwapWTP'),
    '1.3.6.1.5.5.7.3.21': ('SSH Client', 'secureShellClient'),
    '1.3.6.1.5.5.7.3.22': ('SSH Server', 'secureShellServer'),
    '1.3.6.1.5.5.7.3.23': ('Send Router', 'sendRouter'),
    '1.3.6.1.5.5.7.3.24': ('Send Proxied Router', 'sendProxiedRouter'),
    '1.3.6.1.5.5.7.3.25': ('Send Owner', 'sendOwner'),
    '1.3.6.1.5.5.7.3.26': ('Send Proxied Owner', 'sendProxiedOwner'),
    '1.3.6.1.5.5.7.3.27': ('CMC Certificate Authority', 'cmcCA'),
    '1.3.6.1.5.5.7.3.28': ('CMC Registration Authority', 'cmcRA'),
    '1.3.6.1.5.5.7.4': ('id-it', ),
    '1.3.6.1.5.5.7.4.1': ('id-it-caProtEncCert', ),
    '1.3.6.1.5.5.7.4.2': ('id-it-signKeyPairTypes', ),
    '1.3.6.1.5.5.7.4.3': ('id-it-encKeyPairTypes', ),
    '1.3.6.1.5.5.7.4.4': ('id-it-preferredSymmAlg', ),
    '1.3.6.1.5.5.7.4.5': ('id-it-caKeyUpdateInfo', ),
    '1.3.6.1.5.5.7.4.6': ('id-it-currentCRL', ),
    '1.3.6.1.5.5.7.4.7': ('id-it-unsupportedOIDs', ),
    '1.3.6.1.5.5.7.4.8': ('id-it-subscriptionRequest', ),
    '1.3.6.1.5.5.7.4.9': ('id-it-subscriptionResponse', ),
    '1.3.6.1.5.5.7.4.10': ('id-it-keyPairParamReq', ),
    '1.3.6.1.5.5.7.4.11': ('id-it-keyPairParamRep', ),
    '1.3.6.1.5.5.7.4.12': ('id-it-revPassphrase', ),
    '1.3.6.1.5.5.7.4.13': ('id-it-implicitConfirm', ),
    '1.3.6.1.5.5.7.4.14': ('id-it-confirmWaitTime', ),
    '1.3.6.1.5.5.7.4.15': ('id-it-origPKIMessage', ),
    '1.3.6.1.5.5.7.4.16': ('id-it-suppLangTags', ),
    '1.3.6.1.5.5.7.5': ('id-pkip', ),
    '1.3.6.1.5.5.7.5.1': ('id-regCtrl', ),
    '1.3.6.1.5.5.7.5.1.1': ('id-regCtrl-regToken', ),
    '1.3.6.1.5.5.7.5.1.2': ('id-regCtrl-authenticator', ),
    '1.3.6.1.5.5.7.5.1.3': ('id-regCtrl-pkiPublicationInfo', ),
    '1.3.6.1.5.5.7.5.1.4': ('id-regCtrl-pkiArchiveOptions', ),
    '1.3.6.1.5.5.7.5.1.5': ('id-regCtrl-oldCertID', ),
    '1.3.6.1.5.5.7.5.1.6': ('id-regCtrl-protocolEncrKey', ),
    '1.3.6.1.5.5.7.5.2': ('id-regInfo', ),
    '1.3.6.1.5.5.7.5.2.1': ('id-regInfo-utf8Pairs', ),
    '1.3.6.1.5.5.7.5.2.2': ('id-regInfo-certReq', ),
    '1.3.6.1.5.5.7.6': ('id-alg', ),
    '1.3.6.1.5.5.7.6.1': ('id-alg-des40', ),
    '1.3.6.1.5.5.7.6.2': ('id-alg-noSignature', ),
    '1.3.6.1.5.5.7.6.3': ('id-alg-dh-sig-hmac-sha1', ),
    '1.3.6.1.5.5.7.6.4': ('id-alg-dh-pop', ),
    '1.3.6.1.5.5.7.7': ('id-cmc', ),
    '1.3.6.1.5.5.7.7.1': ('id-cmc-statusInfo', ),
    '1.3.6.1.5.5.7.7.2': ('id-cmc-identification', ),
    '1.3.6.1.5.5.7.7.3': ('id-cmc-identityProof', ),
    '1.3.6.1.5.5.7.7.4': ('id-cmc-dataReturn', ),
    '1.3.6.1.5.5.7.7.5': ('id-cmc-transactionId', ),
    '1.3.6.1.5.5.7.7.6': ('id-cmc-senderNonce', ),
    '1.3.6.1.5.5.7.7.7': ('id-cmc-recipientNonce', ),
    '1.3.6.1.5.5.7.7.8': ('id-cmc-addExtensions', ),
    '1.3.6.1.5.5.7.7.9': ('id-cmc-encryptedPOP', ),
    '1.3.6.1.5.5.7.7.10': ('id-cmc-decryptedPOP', ),
    '1.3.6.1.5.5.7.7.11': ('id-cmc-lraPOPWitness', ),
    '1.3.6.1.5.5.7.7.15': ('id-cmc-getCert', ),
    '1.3.6.1.5.5.7.7.16': ('id-cmc-getCRL', ),
    '1.3.6.1.5.5.7.7.17': ('id-cmc-revokeRequest', ),
    '1.3.6.1.5.5.7.7.18': ('id-cmc-regInfo', ),
    '1.3.6.1.5.5.7.7.19': ('id-cmc-responseInfo', ),
    '1.3.6.1.5.5.7.7.21': ('id-cmc-queryPending', ),
    '1.3.6.1.5.5.7.7.22': ('id-cmc-popLinkRandom', ),
    '1.3.6.1.5.5.7.7.23': ('id-cmc-popLinkWitness', ),
    '1.3.6.1.5.5.7.7.24': ('id-cmc-confirmCertAcceptance', ),
    '1.3.6.1.5.5.7.8': ('id-on', ),
    '1.3.6.1.5.5.7.8.1': ('id-on-personalData', ),
    '1.3.6.1.5.5.7.8.3': ('Permanent Identifier', 'id-on-permanentIdentifier'),
    '1.3.6.1.5.5.7.9': ('id-pda', ),
    '1.3.6.1.5.5.7.9.1': ('id-pda-dateOfBirth', ),
    '1.3.6.1.5.5.7.9.2': ('id-pda-placeOfBirth', ),
    '1.3.6.1.5.5.7.9.3': ('id-pda-gender', ),
    '1.3.6.1.5.5.7.9.4': ('id-pda-countryOfCitizenship', ),
    '1.3.6.1.5.5.7.9.5': ('id-pda-countryOfResidence', ),
    '1.3.6.1.5.5.7.10': ('id-aca', ),
    '1.3.6.1.5.5.7.10.1': ('id-aca-authenticationInfo', ),
    '1.3.6.1.5.5.7.10.2': ('id-aca-accessIdentity', ),
    '1.3.6.1.5.5.7.10.3': ('id-aca-chargingIdentity', ),
    '1.3.6.1.5.5.7.10.4': ('id-aca-group', ),
    '1.3.6.1.5.5.7.10.5': ('id-aca-role', ),
    '1.3.6.1.5.5.7.10.6': ('id-aca-encAttrs', ),
    '1.3.6.1.5.5.7.11': ('id-qcs', ),
    '1.3.6.1.5.5.7.11.1': ('id-qcs-pkixQCSyntax-v1', ),
    '1.3.6.1.5.5.7.12': ('id-cct', ),
    '1.3.6.1.5.5.7.12.1': ('id-cct-crs', ),
    '1.3.6.1.5.5.7.12.2': ('id-cct-PKIData', ),
    '1.3.6.1.5.5.7.12.3': ('id-cct-PKIResponse', ),
    '1.3.6.1.5.5.7.21': ('id-ppl', ),
    '1.3.6.1.5.5.7.21.0': ('Any language', 'id-ppl-anyLanguage'),
    '1.3.6.1.5.5.7.21.1': ('Inherit all', 'id-ppl-inheritAll'),
    '1.3.6.1.5.5.7.21.2': ('Independent', 'id-ppl-independent'),
    '1.3.6.1.5.5.7.48': ('id-ad', ),
    '1.3.6.1.5.5.7.48.1': ('OCSP', 'OCSP', 'id-pkix-OCSP'),
    '1.3.6.1.5.5.7.48.1.1': ('Basic OCSP Response', 'basicOCSPResponse'),
    '1.3.6.1.5.5.7.48.1.2': ('OCSP Nonce', 'Nonce'),
    '1.3.6.1.5.5.7.48.1.3': ('OCSP CRL ID', 'CrlID'),
    '1.3.6.1.5.5.7.48.1.4': ('Acceptable OCSP Responses', 'acceptableResponses'),
    '1.3.6.1.5.5.7.48.1.5': ('OCSP No Check', 'noCheck'),
    '1.3.6.1.5.5.7.48.1.6': ('OCSP Archive Cutoff', 'archiveCutoff'),
    '1.3.6.1.5.5.7.48.1.7': ('OCSP Service Locator', 'serviceLocator'),
    '1.3.6.1.5.5.7.48.1.8': ('Extended OCSP Status', 'extendedStatus'),
    '1.3.6.1.5.5.7.48.1.9': ('valid', ),
    '1.3.6.1.5.5.7.48.1.10': ('path', ),
    '1.3.6.1.5.5.7.48.1.11': ('Trust Root', 'trustRoot'),
    '1.3.6.1.5.5.7.48.2': ('CA Issuers', 'caIssuers'),
    '1.3.6.1.5.5.7.48.3': ('AD Time Stamping', 'ad_timestamping'),
    '1.3.6.1.5.5.7.48.4': ('ad dvcs', 'AD_DVCS'),
    '1.3.6.1.5.5.7.48.5': ('CA Repository', 'caRepository'),
    '1.3.6.1.5.5.8.1.1': ('hmac-md5', 'HMAC-MD5'),
    '1.3.6.1.5.5.8.1.2': ('hmac-sha1', 'HMAC-SHA1'),
    '1.3.6.1.6': ('SNMPv2', 'snmpv2'),
    '1.3.6.1.7': ('Mail', ),
    '1.3.6.1.7.1': ('MIME MHS', 'mime-mhs'),
    '1.3.6.1.7.1.1': ('mime-mhs-headings', 'mime-mhs-headings'),
    '1.3.6.1.7.1.1.1': ('id-hex-partial-message', 'id-hex-partial-message'),
    '1.3.6.1.7.1.1.2': ('id-hex-multipart-message', 'id-hex-multipart-message'),
    '1.3.6.1.7.1.2': ('mime-mhs-bodies', 'mime-mhs-bodies'),
    '1.3.14.3.2': ('algorithm', 'algorithm'),
    '1.3.14.3.2.3': ('md5WithRSA', 'RSA-NP-MD5'),
    '1.3.14.3.2.6': ('des-ecb', 'DES-ECB'),
    '1.3.14.3.2.7': ('des-cbc', 'DES-CBC'),
    '1.3.14.3.2.8': ('des-ofb', 'DES-OFB'),
    '1.3.14.3.2.9': ('des-cfb', 'DES-CFB'),
    '1.3.14.3.2.11': ('rsaSignature', ),
    '1.3.14.3.2.12': ('dsaEncryption-old', 'DSA-old'),
    '1.3.14.3.2.13': ('dsaWithSHA', 'DSA-SHA'),
    '1.3.14.3.2.15': ('shaWithRSAEncryption', 'RSA-SHA'),
    '1.3.14.3.2.17': ('des-ede', 'DES-EDE'),
    '1.3.14.3.2.18': ('sha', 'SHA'),
    '1.3.14.3.2.26': ('sha1', 'SHA1'),
    '1.3.14.3.2.27': ('dsaWithSHA1-old', 'DSA-SHA1-old'),
    '1.3.14.3.2.29': ('sha1WithRSA', 'RSA-SHA1-2'),
    '1.3.36.3.2.1': ('ripemd160', 'RIPEMD160'),
    '1.3.36.3.3.1.2': ('ripemd160WithRSA', 'RSA-RIPEMD160'),
    '1.3.36.3.3.2.8.1.1.1': ('brainpoolP160r1', ),
    '1.3.36.3.3.2.8.1.1.2': ('brainpoolP160t1', ),
    '1.3.36.3.3.2.8.1.1.3': ('brainpoolP192r1', ),
    '1.3.36.3.3.2.8.1.1.4': ('brainpoolP192t1', ),
    '1.3.36.3.3.2.8.1.1.5': ('brainpoolP224r1', ),
    '1.3.36.3.3.2.8.1.1.6': ('brainpoolP224t1', ),
    '1.3.36.3.3.2.8.1.1.7': ('brainpoolP256r1', ),
    '1.3.36.3.3.2.8.1.1.8': ('brainpoolP256t1', ),
    '1.3.36.3.3.2.8.1.1.9': ('brainpoolP320r1', ),
    '1.3.36.3.3.2.8.1.1.10': ('brainpoolP320t1', ),
    '1.3.36.3.3.2.8.1.1.11': ('brainpoolP384r1', ),
    '1.3.36.3.3.2.8.1.1.12': ('brainpoolP384t1', ),
    '1.3.36.3.3.2.8.1.1.13': ('brainpoolP512r1', ),
    '1.3.36.3.3.2.8.1.1.14': ('brainpoolP512t1', ),
    '1.3.36.8.3.3': ('Professional Information or basis for Admission', 'x509ExtAdmission'),
    '1.3.101.1.4.1': ('Strong Extranet ID', 'SXNetID'),
    '1.3.101.110': ('X25519', ),
    '1.3.101.111': ('X448', ),
    '1.3.101.112': ('ED25519', ),
    '1.3.101.113': ('ED448', ),
    '1.3.111': ('ieee', ),
    '1.3.111.2.1619': ('IEEE Security in Storage Working Group', 'ieee-siswg'),
    '1.3.111.2.1619.0.1.1': ('aes-128-xts', 'AES-128-XTS'),
    '1.3.111.2.1619.0.1.2': ('aes-256-xts', 'AES-256-XTS'),
    '1.3.132': ('certicom-arc', ),
    '1.3.132.0': ('secg_ellipticCurve', ),
    '1.3.132.0.1': ('sect163k1', ),
    '1.3.132.0.2': ('sect163r1', ),
    '1.3.132.0.3': ('sect239k1', ),
    '1.3.132.0.4': ('sect113r1', ),
    '1.3.132.0.5': ('sect113r2', ),
    '1.3.132.0.6': ('secp112r1', ),
    '1.3.132.0.7': ('secp112r2', ),
    '1.3.132.0.8': ('secp160r1', ),
    '1.3.132.0.9': ('secp160k1', ),
    '1.3.132.0.10': ('secp256k1', ),
    '1.3.132.0.15': ('sect163r2', ),
    '1.3.132.0.16': ('sect283k1', ),
    '1.3.132.0.17': ('sect283r1', ),
    '1.3.132.0.22': ('sect131r1', ),
    '1.3.132.0.23': ('sect131r2', ),
    '1.3.132.0.24': ('sect193r1', ),
    '1.3.132.0.25': ('sect193r2', ),
    '1.3.132.0.26': ('sect233k1', ),
    '1.3.132.0.27': ('sect233r1', ),
    '1.3.132.0.28': ('secp128r1', ),
    '1.3.132.0.29': ('secp128r2', ),
    '1.3.132.0.30': ('secp160r2', ),
    '1.3.132.0.31': ('secp192k1', ),
    '1.3.132.0.32': ('secp224k1', ),
    '1.3.132.0.33': ('secp224r1', ),
    '1.3.132.0.34': ('secp384r1', ),
    '1.3.132.0.35': ('secp521r1', ),
    '1.3.132.0.36': ('sect409k1', ),
    '1.3.132.0.37': ('sect409r1', ),
    '1.3.132.0.38': ('sect571k1', ),
    '1.3.132.0.39': ('sect571r1', ),
    '1.3.132.1': ('secg-scheme', ),
    '1.3.132.1.11.0': ('dhSinglePass-stdDH-sha224kdf-scheme', ),
    '1.3.132.1.11.1': ('dhSinglePass-stdDH-sha256kdf-scheme', ),
    '1.3.132.1.11.2': ('dhSinglePass-stdDH-sha384kdf-scheme', ),
    '1.3.132.1.11.3': ('dhSinglePass-stdDH-sha512kdf-scheme', ),
    '1.3.132.1.14.0': ('dhSinglePass-cofactorDH-sha224kdf-scheme', ),
    '1.3.132.1.14.1': ('dhSinglePass-cofactorDH-sha256kdf-scheme', ),
    '1.3.132.1.14.2': ('dhSinglePass-cofactorDH-sha384kdf-scheme', ),
    '1.3.132.1.14.3': ('dhSinglePass-cofactorDH-sha512kdf-scheme', ),
    '1.3.133.16.840.63.0': ('x9-63-scheme', ),
    '1.3.133.16.840.63.0.2': ('dhSinglePass-stdDH-sha1kdf-scheme', ),
    '1.3.133.16.840.63.0.3': ('dhSinglePass-cofactorDH-sha1kdf-scheme', ),
    '2': ('joint-iso-itu-t', 'JOINT-ISO-ITU-T', 'joint-iso-ccitt'),
    '2.5': ('directory services (X.500)', 'X500'),
    '2.5.1.5': ('Selected Attribute Types', 'selected-attribute-types'),
    '2.5.1.5.55': ('clearance', ),
    '2.5.4': ('X509', ),
    '2.5.4.3': ('commonName', 'CN'),
    '2.5.4.4': ('surname', 'SN'),
    '2.5.4.5': ('serialNumber', ),
    '2.5.4.6': ('countryName', 'C'),
    '2.5.4.7': ('localityName', 'L'),
    '2.5.4.8': ('stateOrProvinceName', 'ST'),
    '2.5.4.9': ('streetAddress', 'street'),
    '2.5.4.10': ('organizationName', 'O'),
    '2.5.4.11': ('organizationalUnitName', 'OU'),
    '2.5.4.12': ('title', 'title'),
    '2.5.4.13': ('description', ),
    '2.5.4.14': ('searchGuide', ),
    '2.5.4.15': ('businessCategory', ),
    '2.5.4.16': ('postalAddress', ),
    '2.5.4.17': ('postalCode', ),
    '2.5.4.18': ('postOfficeBox', ),
    '2.5.4.19': ('physicalDeliveryOfficeName', ),
    '2.5.4.20': ('telephoneNumber', ),
    '2.5.4.21': ('telexNumber', ),
    '2.5.4.22': ('teletexTerminalIdentifier', ),
    '2.5.4.23': ('facsimileTelephoneNumber', ),
    '2.5.4.24': ('x121Address', ),
    '2.5.4.25': ('internationaliSDNNumber', ),
    '2.5.4.26': ('registeredAddress', ),
    '2.5.4.27': ('destinationIndicator', ),
    '2.5.4.28': ('preferredDeliveryMethod', ),
    '2.5.4.29': ('presentationAddress', ),
    '2.5.4.30': ('supportedApplicationContext', ),
    '2.5.4.31': ('member', ),
    '2.5.4.32': ('owner', ),
    '2.5.4.33': ('roleOccupant', ),
    '2.5.4.34': ('seeAlso', ),
    '2.5.4.35': ('userPassword', ),
    '2.5.4.36': ('userCertificate', ),
    '2.5.4.37': ('cACertificate', ),
    '2.5.4.38': ('authorityRevocationList', ),
    '2.5.4.39': ('certificateRevocationList', ),
    '2.5.4.40': ('crossCertificatePair', ),
    '2.5.4.41': ('name', 'name'),
    '2.5.4.42': ('givenName', 'GN'),
    '2.5.4.43': ('initials', 'initials'),
    '2.5.4.44': ('generationQualifier', ),
    '2.5.4.45': ('x500UniqueIdentifier', ),
    '2.5.4.46': ('dnQualifier', 'dnQualifier'),
    '2.5.4.47': ('enhancedSearchGuide', ),
    '2.5.4.48': ('protocolInformation', ),
    '2.5.4.49': ('distinguishedName', ),
    '2.5.4.50': ('uniqueMember', ),
    '2.5.4.51': ('houseIdentifier', ),
    '2.5.4.52': ('supportedAlgorithms', ),
    '2.5.4.53': ('deltaRevocationList', ),
    '2.5.4.54': ('dmdName', ),
    '2.5.4.65': ('pseudonym', ),
    '2.5.4.72': ('role', 'role'),
    '2.5.4.97': ('organizationIdentifier', ),
    '2.5.4.98': ('countryCode3c', 'c3'),
    '2.5.4.99': ('countryCode3n', 'n3'),
    '2.5.4.100': ('dnsName', ),
    '2.5.8': ('directory services - algorithms', 'X500algorithms'),
    '2.5.8.1.1': ('rsa', 'RSA'),
    '2.5.8.3.100': ('mdc2WithRSA', 'RSA-MDC2'),
    '2.5.8.3.101': ('mdc2', 'MDC2'),
    '2.5.29': ('id-ce', ),
    '2.5.29.9': ('X509v3 Subject Directory Attributes', 'subjectDirectoryAttributes'),
    '2.5.29.14': ('X509v3 Subject Key Identifier', 'subjectKeyIdentifier'),
    '2.5.29.15': ('X509v3 Key Usage', 'keyUsage'),
    '2.5.29.16': ('X509v3 Private Key Usage Period', 'privateKeyUsagePeriod'),
    '2.5.29.17': ('X509v3 Subject Alternative Name', 'subjectAltName'),
    '2.5.29.18': ('X509v3 Issuer Alternative Name', 'issuerAltName'),
    '2.5.29.19': ('X509v3 Basic Constraints', 'basicConstraints'),
    '2.5.29.20': ('X509v3 CRL Number', 'crlNumber'),
    '2.5.29.21': ('X509v3 CRL Reason Code', 'CRLReason'),
    '2.5.29.23': ('Hold Instruction Code', 'holdInstructionCode'),
    '2.5.29.24': ('Invalidity Date', 'invalidityDate'),
    '2.5.29.27': ('X509v3 Delta CRL Indicator', 'deltaCRL'),
    '2.5.29.28': ('X509v3 Issuing Distribution Point', 'issuingDistributionPoint'),
    '2.5.29.29': ('X509v3 Certificate Issuer', 'certificateIssuer'),
    '2.5.29.30': ('X509v3 Name Constraints', 'nameConstraints'),
    '2.5.29.31': ('X509v3 CRL Distribution Points', 'crlDistributionPoints'),
    '2.5.29.32': ('X509v3 Certificate Policies', 'certificatePolicies'),
    '2.5.29.32.0': ('X509v3 Any Policy', 'anyPolicy'),
    '2.5.29.33': ('X509v3 Policy Mappings', 'policyMappings'),
    '2.5.29.35': ('X509v3 Authority Key Identifier', 'authorityKeyIdentifier'),
    '2.5.29.36': ('X509v3 Policy Constraints', 'policyConstraints'),
    '2.5.29.37': ('X509v3 Extended Key Usage', 'extendedKeyUsage'),
    '2.5.29.37.0': ('Any Extended Key Usage', 'anyExtendedKeyUsage'),
    '2.5.29.46': ('X509v3 Freshest CRL', 'freshestCRL'),
    '2.5.29.54': ('X509v3 Inhibit Any Policy', 'inhibitAnyPolicy'),
    '2.5.29.55': ('X509v3 AC Targeting', 'targetInformation'),
    '2.5.29.56': ('X509v3 No Revocation Available', 'noRevAvail'),
    '2.16.840.1.101.3': ('csor', ),
    '2.16.840.1.101.3.4': ('nistAlgorithms', ),
    '2.16.840.1.101.3.4.1': ('aes', ),
    '2.16.840.1.101.3.4.1.1': ('aes-128-ecb', 'AES-128-ECB'),
    '2.16.840.1.101.3.4.1.2': ('aes-128-cbc', 'AES-128-CBC'),
    '2.16.840.1.101.3.4.1.3': ('aes-128-ofb', 'AES-128-OFB'),
    '2.16.840.1.101.3.4.1.4': ('aes-128-cfb', 'AES-128-CFB'),
    '2.16.840.1.101.3.4.1.5': ('id-aes128-wrap', ),
    '2.16.840.1.101.3.4.1.6': ('aes-128-gcm', 'id-aes128-GCM'),
    '2.16.840.1.101.3.4.1.7': ('aes-128-ccm', 'id-aes128-CCM'),
    '2.16.840.1.101.3.4.1.8': ('id-aes128-wrap-pad', ),
    '2.16.840.1.101.3.4.1.21': ('aes-192-ecb', 'AES-192-ECB'),
    '2.16.840.1.101.3.4.1.22': ('aes-192-cbc', 'AES-192-CBC'),
    '2.16.840.1.101.3.4.1.23': ('aes-192-ofb', 'AES-192-OFB'),
    '2.16.840.1.101.3.4.1.24': ('aes-192-cfb', 'AES-192-CFB'),
    '2.16.840.1.101.3.4.1.25': ('id-aes192-wrap', ),
    '2.16.840.1.101.3.4.1.26': ('aes-192-gcm', 'id-aes192-GCM'),
    '2.16.840.1.101.3.4.1.27': ('aes-192-ccm', 'id-aes192-CCM'),
    '2.16.840.1.101.3.4.1.28': ('id-aes192-wrap-pad', ),
    '2.16.840.1.101.3.4.1.41': ('aes-256-ecb', 'AES-256-ECB'),
    '2.16.840.1.101.3.4.1.42': ('aes-256-cbc', 'AES-256-CBC'),
    '2.16.840.1.101.3.4.1.43': ('aes-256-ofb', 'AES-256-OFB'),
    '2.16.840.1.101.3.4.1.44': ('aes-256-cfb', 'AES-256-CFB'),
    '2.16.840.1.101.3.4.1.45': ('id-aes256-wrap', ),
    '2.16.840.1.101.3.4.1.46': ('aes-256-gcm', 'id-aes256-GCM'),
    '2.16.840.1.101.3.4.1.47': ('aes-256-ccm', 'id-aes256-CCM'),
    '2.16.840.1.101.3.4.1.48': ('id-aes256-wrap-pad', ),
    '2.16.840.1.101.3.4.2': ('nist_hashalgs', ),
    '2.16.840.1.101.3.4.2.1': ('sha256', 'SHA256'),
    '2.16.840.1.101.3.4.2.2': ('sha384', 'SHA384'),
    '2.16.840.1.101.3.4.2.3': ('sha512', 'SHA512'),
    '2.16.840.1.101.3.4.2.4': ('sha224', 'SHA224'),
    '2.16.840.1.101.3.4.2.5': ('sha512-224', 'SHA512-224'),
    '2.16.840.1.101.3.4.2.6': ('sha512-256', 'SHA512-256'),
    '2.16.840.1.101.3.4.2.7': ('sha3-224', 'SHA3-224'),
    '2.16.840.1.101.3.4.2.8': ('sha3-256', 'SHA3-256'),
    '2.16.840.1.101.3.4.2.9': ('sha3-384', 'SHA3-384'),
    '2.16.840.1.101.3.4.2.10': ('sha3-512', 'SHA3-512'),
    '2.16.840.1.101.3.4.2.11': ('shake128', 'SHAKE128'),
    '2.16.840.1.101.3.4.2.12': ('shake256', 'SHAKE256'),
    '2.16.840.1.101.3.4.2.13': ('hmac-sha3-224', 'id-hmacWithSHA3-224'),
    '2.16.840.1.101.3.4.2.14': ('hmac-sha3-256', 'id-hmacWithSHA3-256'),
    '2.16.840.1.101.3.4.2.15': ('hmac-sha3-384', 'id-hmacWithSHA3-384'),
    '2.16.840.1.101.3.4.2.16': ('hmac-sha3-512', 'id-hmacWithSHA3-512'),
    '2.16.840.1.101.3.4.3': ('dsa_with_sha2', 'sigAlgs'),
    '2.16.840.1.101.3.4.3.1': ('dsa_with_SHA224', ),
    '2.16.840.1.101.3.4.3.2': ('dsa_with_SHA256', ),
    '2.16.840.1.101.3.4.3.3': ('dsa_with_SHA384', 'id-dsa-with-sha384'),
    '2.16.840.1.101.3.4.3.4': ('dsa_with_SHA512', 'id-dsa-with-sha512'),
    '2.16.840.1.101.3.4.3.5': ('dsa_with_SHA3-224', 'id-dsa-with-sha3-224'),
    '2.16.840.1.101.3.4.3.6': ('dsa_with_SHA3-256', 'id-dsa-with-sha3-256'),
    '2.16.840.1.101.3.4.3.7': ('dsa_with_SHA3-384', 'id-dsa-with-sha3-384'),
    '2.16.840.1.101.3.4.3.8': ('dsa_with_SHA3-512', 'id-dsa-with-sha3-512'),
    '2.16.840.1.101.3.4.3.9': ('ecdsa_with_SHA3-224', 'id-ecdsa-with-sha3-224'),
    '2.16.840.1.101.3.4.3.10': ('ecdsa_with_SHA3-256', 'id-ecdsa-with-sha3-256'),
    '2.16.840.1.101.3.4.3.11': ('ecdsa_with_SHA3-384', 'id-ecdsa-with-sha3-384'),
    '2.16.840.1.101.3.4.3.12': ('ecdsa_with_SHA3-512', 'id-ecdsa-with-sha3-512'),
    '2.16.840.1.101.3.4.3.13': ('RSA-SHA3-224', 'id-rsassa-pkcs1-v1_5-with-sha3-224'),
    '2.16.840.1.101.3.4.3.14': ('RSA-SHA3-256', 'id-rsassa-pkcs1-v1_5-with-sha3-256'),
    '2.16.840.1.101.3.4.3.15': ('RSA-SHA3-384', 'id-rsassa-pkcs1-v1_5-with-sha3-384'),
    '2.16.840.1.101.3.4.3.16': ('RSA-SHA3-512', 'id-rsassa-pkcs1-v1_5-with-sha3-512'),
    '2.16.840.1.113730': ('Netscape Communications Corp.', 'Netscape'),
    '2.16.840.1.113730.1': ('Netscape Certificate Extension', 'nsCertExt'),
    '2.16.840.1.113730.1.1': ('Netscape Cert Type', 'nsCertType'),
    '2.16.840.1.113730.1.2': ('Netscape Base Url', 'nsBaseUrl'),
    '2.16.840.1.113730.1.3': ('Netscape Revocation Url', 'nsRevocationUrl'),
    '2.16.840.1.113730.1.4': ('Netscape CA Revocation Url', 'nsCaRevocationUrl'),
    '2.16.840.1.113730.1.7': ('Netscape Renewal Url', 'nsRenewalUrl'),
    '2.16.840.1.113730.1.8': ('Netscape CA Policy Url', 'nsCaPolicyUrl'),
    '2.16.840.1.113730.1.12': ('Netscape SSL Server Name', 'nsSslServerName'),
    '2.16.840.1.113730.1.13': ('Netscape Comment', 'nsComment'),
    '2.16.840.1.113730.2': ('Netscape Data Type', 'nsDataType'),
    '2.16.840.1.113730.2.5': ('Netscape Certificate Sequence', 'nsCertSequence'),
    '2.16.840.1.113730.4.1': ('Netscape Server Gated Crypto', 'nsSGC'),
    '2.23': ('International Organizations', 'international-organizations'),
    '2.23.42': ('Secure Electronic Transactions', 'id-set'),
    '2.23.42.0': ('content types', 'set-ctype'),
    '2.23.42.0.0': ('setct-PANData', ),
    '2.23.42.0.1': ('setct-PANToken', ),
    '2.23.42.0.2': ('setct-PANOnly', ),
    '2.23.42.0.3': ('setct-OIData', ),
    '2.23.42.0.4': ('setct-PI', ),
    '2.23.42.0.5': ('setct-PIData', ),
    '2.23.42.0.6': ('setct-PIDataUnsigned', ),
    '2.23.42.0.7': ('setct-HODInput', ),
    '2.23.42.0.8': ('setct-AuthResBaggage', ),
    '2.23.42.0.9': ('setct-AuthRevReqBaggage', ),
    '2.23.42.0.10': ('setct-AuthRevResBaggage', ),
    '2.23.42.0.11': ('setct-CapTokenSeq', ),
    '2.23.42.0.12': ('setct-PInitResData', ),
    '2.23.42.0.13': ('setct-PI-TBS', ),
    '2.23.42.0.14': ('setct-PResData', ),
    '2.23.42.0.16': ('setct-AuthReqTBS', ),
    '2.23.42.0.17': ('setct-AuthResTBS', ),
    '2.23.42.0.18': ('setct-AuthResTBSX', ),
    '2.23.42.0.19': ('setct-AuthTokenTBS', ),
    '2.23.42.0.20': ('setct-CapTokenData', ),
    '2.23.42.0.21': ('setct-CapTokenTBS', ),
    '2.23.42.0.22': ('setct-AcqCardCodeMsg', ),
    '2.23.42.0.23': ('setct-AuthRevReqTBS', ),
    '2.23.42.0.24': ('setct-AuthRevResData', ),
    '2.23.42.0.25': ('setct-AuthRevResTBS', ),
    '2.23.42.0.26': ('setct-CapReqTBS', ),
    '2.23.42.0.27': ('setct-CapReqTBSX', ),
    '2.23.42.0.28': ('setct-CapResData', ),
    '2.23.42.0.29': ('setct-CapRevReqTBS', ),
    '2.23.42.0.30': ('setct-CapRevReqTBSX', ),
    '2.23.42.0.31': ('setct-CapRevResData', ),
    '2.23.42.0.32': ('setct-CredReqTBS', ),
    '2.23.42.0.33': ('setct-CredReqTBSX', ),
    '2.23.42.0.34': ('setct-CredResData', ),
    '2.23.42.0.35': ('setct-CredRevReqTBS', ),
    '2.23.42.0.36': ('setct-CredRevReqTBSX', ),
    '2.23.42.0.37': ('setct-CredRevResData', ),
    '2.23.42.0.38': ('setct-PCertReqData', ),
    '2.23.42.0.39': ('setct-PCertResTBS', ),
    '2.23.42.0.40': ('setct-BatchAdminReqData', ),
    '2.23.42.0.41': ('setct-BatchAdminResData', ),
    '2.23.42.0.42': ('setct-CardCInitResTBS', ),
    '2.23.42.0.43': ('setct-MeAqCInitResTBS', ),
    '2.23.42.0.44': ('setct-RegFormResTBS', ),
    '2.23.42.0.45': ('setct-CertReqData', ),
    '2.23.42.0.46': ('setct-CertReqTBS', ),
    '2.23.42.0.47': ('setct-CertResData', ),
    '2.23.42.0.48': ('setct-CertInqReqTBS', ),
    '2.23.42.0.49': ('setct-ErrorTBS', ),
    '2.23.42.0.50': ('setct-PIDualSignedTBE', ),
    '2.23.42.0.51': ('setct-PIUnsignedTBE', ),
    '2.23.42.0.52': ('setct-AuthReqTBE', ),
    '2.23.42.0.53': ('setct-AuthResTBE', ),
    '2.23.42.0.54': ('setct-AuthResTBEX', ),
    '2.23.42.0.55': ('setct-AuthTokenTBE', ),
    '2.23.42.0.56': ('setct-CapTokenTBE', ),
    '2.23.42.0.57': ('setct-CapTokenTBEX', ),
    '2.23.42.0.58': ('setct-AcqCardCodeMsgTBE', ),
    '2.23.42.0.59': ('setct-AuthRevReqTBE', ),
    '2.23.42.0.60': ('setct-AuthRevResTBE', ),
    '2.23.42.0.61': ('setct-AuthRevResTBEB', ),
    '2.23.42.0.62': ('setct-CapReqTBE', ),
    '2.23.42.0.63': ('setct-CapReqTBEX', ),
    '2.23.42.0.64': ('setct-CapResTBE', ),
    '2.23.42.0.65': ('setct-CapRevReqTBE', ),
    '2.23.42.0.66': ('setct-CapRevReqTBEX', ),
    '2.23.42.0.67': ('setct-CapRevResTBE', ),
    '2.23.42.0.68': ('setct-CredReqTBE', ),
    '2.23.42.0.69': ('setct-CredReqTBEX', ),
    '2.23.42.0.70': ('setct-CredResTBE', ),
    '2.23.42.0.71': ('setct-CredRevReqTBE', ),
    '2.23.42.0.72': ('setct-CredRevReqTBEX', ),
    '2.23.42.0.73': ('setct-CredRevResTBE', ),
    '2.23.42.0.74': ('setct-BatchAdminReqTBE', ),
    '2.23.42.0.75': ('setct-BatchAdminResTBE', ),
    '2.23.42.0.76': ('setct-RegFormReqTBE', ),
    '2.23.42.0.77': ('setct-CertReqTBE', ),
    '2.23.42.0.78': ('setct-CertReqTBEX', ),
    '2.23.42.0.79': ('setct-CertResTBE', ),
    '2.23.42.0.80': ('setct-CRLNotificationTBS', ),
    '2.23.42.0.81': ('setct-CRLNotificationResTBS', ),
    '2.23.42.0.82': ('setct-BCIDistributionTBS', ),
    '2.23.42.1': ('message extensions', 'set-msgExt'),
    '2.23.42.1.1': ('generic cryptogram', 'setext-genCrypt'),
    '2.23.42.1.3': ('merchant initiated auth', 'setext-miAuth'),
    '2.23.42.1.4': ('setext-pinSecure', ),
    '2.23.42.1.5': ('setext-pinAny', ),
    '2.23.42.1.7': ('setext-track2', ),
    '2.23.42.1.8': ('additional verification', 'setext-cv'),
    '2.23.42.3': ('set-attr', ),
    '2.23.42.3.0': ('setAttr-Cert', ),
    '2.23.42.3.0.0': ('set-rootKeyThumb', ),
    '2.23.42.3.0.1': ('set-addPolicy', ),
    '2.23.42.3.1': ('payment gateway capabilities', 'setAttr-PGWYcap'),
    '2.23.42.3.2': ('setAttr-TokenType', ),
    '2.23.42.3.2.1': ('setAttr-Token-EMV', ),
    '2.23.42.3.2.2': ('setAttr-Token-B0Prime', ),
    '2.23.42.3.3': ('issuer capabilities', 'setAttr-IssCap'),
    '2.23.42.3.3.3': ('setAttr-IssCap-CVM', ),
    '2.23.42.3.3.3.1': ('generate cryptogram', 'setAttr-GenCryptgrm'),
    '2.23.42.3.3.4': ('setAttr-IssCap-T2', ),
    '2.23.42.3.3.4.1': ('encrypted track 2', 'setAttr-T2Enc'),
    '2.23.42.3.3.4.2': ('cleartext track 2', 'setAttr-T2cleartxt'),
    '2.23.42.3.3.5': ('setAttr-IssCap-Sig', ),
    '2.23.42.3.3.5.1': ('ICC or token signature', 'setAttr-TokICCsig'),
    '2.23.42.3.3.5.2': ('secure device signature', 'setAttr-SecDevSig'),
    '2.23.42.5': ('set-policy', ),
    '2.23.42.5.0': ('set-policy-root', ),
    '2.23.42.7': ('certificate extensions', 'set-certExt'),
    '2.23.42.7.0': ('setCext-hashedRoot', ),
    '2.23.42.7.1': ('setCext-certType', ),
    '2.23.42.7.2': ('setCext-merchData', ),
    '2.23.42.7.3': ('setCext-cCertRequired', ),
    '2.23.42.7.4': ('setCext-tunneling', ),
    '2.23.42.7.5': ('setCext-setExt', ),
    '2.23.42.7.6': ('setCext-setQualf', ),
    '2.23.42.7.7': ('setCext-PGWYcapabilities', ),
    '2.23.42.7.8': ('setCext-TokenIdentifier', ),
    '2.23.42.7.9': ('setCext-Track2Data', ),
    '2.23.42.7.10': ('setCext-TokenType', ),
    '2.23.42.7.11': ('setCext-IssuerCapabilities', ),
    '2.23.42.8': ('set-brand', ),
    '2.23.42.8.1': ('set-brand-IATA-ATA', ),
    '2.23.42.8.4': ('set-brand-Visa', ),
    '2.23.42.8.5': ('set-brand-MasterCard', ),
    '2.23.42.8.30': ('set-brand-Diners', ),
    '2.23.42.8.34': ('set-brand-AmericanExpress', ),
    '2.23.42.8.35': ('set-brand-JCB', ),
    '2.23.42.8.6011': ('set-brand-Novus', ),
    '2.23.43': ('wap', ),
    '2.23.43.1': ('wap-wsg', ),
    '2.23.43.1.4': ('wap-wsg-idm-ecid', ),
    '2.23.43.1.4.1': ('wap-wsg-idm-ecid-wtls1', ),
    '2.23.43.1.4.3': ('wap-wsg-idm-ecid-wtls3', ),
    '2.23.43.1.4.4': ('wap-wsg-idm-ecid-wtls4', ),
    '2.23.43.1.4.5': ('wap-wsg-idm-ecid-wtls5', ),
    '2.23.43.1.4.6': ('wap-wsg-idm-ecid-wtls6', ),
    '2.23.43.1.4.7': ('wap-wsg-idm-ecid-wtls7', ),
    '2.23.43.1.4.8': ('wap-wsg-idm-ecid-wtls8', ),
    '2.23.43.1.4.9': ('wap-wsg-idm-ecid-wtls9', ),
    '2.23.43.1.4.10': ('wap-wsg-idm-ecid-wtls10', ),
    '2.23.43.1.4.11': ('wap-wsg-idm-ecid-wtls11', ),
    '2.23.43.1.4.12': ('wap-wsg-idm-ecid-wtls12', ),
}
# #####################################################################################
# #####################################################################################

_OID_LOOKUP = dict()
_NORMALIZE_NAMES = dict()

for dotted, names in _OID_MAP.items():
    for name in names:
        if name in _NORMALIZE_NAMES and _OID_LOOKUP[name] != dotted:
            raise AssertionError(
                'Name collision during setup: "{0}" for OIDs {1} and {2}'
                .format(name, dotted, _OID_LOOKUP[name])
            )
        _NORMALIZE_NAMES[name] = names[0]
        _OID_LOOKUP[name] = dotted
for alias, original in [('userID', 'userId')]:
    if alias in _NORMALIZE_NAMES:
        raise AssertionError(
            'Name collision during adding aliases: "{0}" (alias for "{1}") is already mapped to OID {2}'
            .format(alias, original, _OID_LOOKUP[alias])
        )
    _NORMALIZE_NAMES[alias] = original
    _OID_LOOKUP[alias] = _OID_LOOKUP[original]


def pyopenssl_normalize_name(name):
    nid = OpenSSL._util.lib.OBJ_txt2nid(to_bytes(name))
    if nid != 0:
        b_name = OpenSSL._util.lib.OBJ_nid2ln(nid)
        name = to_text(OpenSSL._util.ffi.string(b_name))
    return _NORMALIZE_NAMES.get(name, name)


# #####################################################################################
# #####################################################################################
# # This excerpt is dual licensed under the terms of the Apache License, Version
# # 2.0, and the BSD License. See the LICENSE file at
# # https://github.com/pyca/cryptography/blob/master/LICENSE for complete details.
# #
# # Adapted from cryptography's hazmat/backends/openssl/decode_asn1.py
# #
# # Copyright (c) 2015, 2016 Paul Kehrer (@reaperhulk)
# # Copyright (c) 2017 Fraser Tweedale (@frasertweedale)
# #
# # Relevant commits from cryptography project (https://github.com/pyca/cryptography):
# #    pyca/cryptography@719d536dd691e84e208534798f2eb4f82aaa2e07
# #    pyca/cryptography@5ab6d6a5c05572bd1c75f05baf264a2d0001894a
# #    pyca/cryptography@2e776e20eb60378e0af9b7439000d0e80da7c7e3
# #    pyca/cryptography@fb309ed24647d1be9e319b61b1f2aa8ebb87b90b
# #    pyca/cryptography@2917e460993c475c72d7146c50dc3bbc2414280d
# #    pyca/cryptography@3057f91ea9a05fb593825006d87a391286a4d828
# #    pyca/cryptography@d607dd7e5bc5c08854ec0c9baff70ba4a35be36f
def _obj2txt(openssl_lib, openssl_ffi, obj):
    # Set to 80 on the recommendation of
    # https://www.openssl.org/docs/crypto/OBJ_nid2ln.html#return_values
    #
    # But OIDs longer than this occur in real life (e.g. Active
    # Directory makes some very long OIDs).  So we need to detect
    # and properly handle the case where the default buffer is not
    # big enough.
    #
    buf_len = 80
    buf = openssl_ffi.new("char[]", buf_len)

    # 'res' is the number of bytes that *would* be written if the
    # buffer is large enough.  If 'res' > buf_len - 1, we need to
    # alloc a big-enough buffer and go again.
    res = openssl_lib.OBJ_obj2txt(buf, buf_len, obj, 1)
    if res > buf_len - 1:  # account for terminating null byte
        buf_len = res + 1
        buf = openssl_ffi.new("char[]", buf_len)
        res = openssl_lib.OBJ_obj2txt(buf, buf_len, obj, 1)
    return openssl_ffi.buffer(buf, res)[:].decode()
# #####################################################################################
# #####################################################################################


def cryptography_get_extensions_from_cert(cert):
    # Since cryptography won't give us the DER value for an extension
    # (that is only stored for unrecognized extensions), we have to re-do
    # the extension parsing outselves.
    result = dict()
    backend = cert._backend
    x509_obj = cert._x509

    for i in range(backend._lib.X509_get_ext_count(x509_obj)):
        ext = backend._lib.X509_get_ext(x509_obj, i)
        if ext == backend._ffi.NULL:
            continue
        crit = backend._lib.X509_EXTENSION_get_critical(ext)
        data = backend._lib.X509_EXTENSION_get_data(ext)
        backend.openssl_assert(data != backend._ffi.NULL)
        der = backend._ffi.buffer(data.data, data.length)[:]
        entry = dict(
            critical=(crit == 1),
            value=base64.b64encode(der),
        )
        oid = _obj2txt(backend._lib, backend._ffi, backend._lib.X509_EXTENSION_get_object(ext))
        result[oid] = entry
    return result


def cryptography_get_extensions_from_csr(csr):
    # Since cryptography won't give us the DER value for an extension
    # (that is only stored for unrecognized extensions), we have to re-do
    # the extension parsing outselves.
    result = dict()
    backend = csr._backend

    extensions = backend._lib.X509_REQ_get_extensions(csr._x509_req)
    extensions = backend._ffi.gc(
        extensions,
        lambda ext: backend._lib.sk_X509_EXTENSION_pop_free(
            ext,
            backend._ffi.addressof(backend._lib._original_lib, "X509_EXTENSION_free")
        )
    )

    for i in range(backend._lib.sk_X509_EXTENSION_num(extensions)):
        ext = backend._lib.sk_X509_EXTENSION_value(extensions, i)
        if ext == backend._ffi.NULL:
            continue
        crit = backend._lib.X509_EXTENSION_get_critical(ext)
        data = backend._lib.X509_EXTENSION_get_data(ext)
        backend.openssl_assert(data != backend._ffi.NULL)
        der = backend._ffi.buffer(data.data, data.length)[:]
        entry = dict(
            critical=(crit == 1),
            value=base64.b64encode(der),
        )
        oid = _obj2txt(backend._lib, backend._ffi, backend._lib.X509_EXTENSION_get_object(ext))
        result[oid] = entry
    return result


def pyopenssl_get_extensions_from_cert(cert):
    # While pyOpenSSL allows us to get an extension's DER value, it won't
    # give us the dotted string for an OID. So we have to do some magic to
    # get hold of it.
    result = dict()
    ext_count = cert.get_extension_count()
    for i in range(0, ext_count):
        ext = cert.get_extension(i)
        entry = dict(
            critical=bool(ext.get_critical()),
            value=base64.b64encode(ext.get_data()),
        )
        oid = _obj2txt(
            OpenSSL._util.lib,
            OpenSSL._util.ffi,
            OpenSSL._util.lib.X509_EXTENSION_get_object(ext._extension)
        )
        # This could also be done a bit simpler:
        #
        #   oid = _obj2txt(OpenSSL._util.lib, OpenSSL._util.ffi, OpenSSL._util.lib.OBJ_nid2obj(ext._nid))
        #
        # Unfortunately this gives the wrong result in case the linked OpenSSL
        # doesn't know the OID. That's why we have to get the OID dotted string
        # similarly to how cryptography does it.
        result[oid] = entry
    return result


def pyopenssl_get_extensions_from_csr(csr):
    # While pyOpenSSL allows us to get an extension's DER value, it won't
    # give us the dotted string for an OID. So we have to do some magic to
    # get hold of it.
    result = dict()
    for ext in csr.get_extensions():
        entry = dict(
            critical=bool(ext.get_critical()),
            value=base64.b64encode(ext.get_data()),
        )
        oid = _obj2txt(
            OpenSSL._util.lib,
            OpenSSL._util.ffi,
            OpenSSL._util.lib.X509_EXTENSION_get_object(ext._extension)
        )
        # This could also be done a bit simpler:
        #
        #   oid = _obj2txt(OpenSSL._util.lib, OpenSSL._util.ffi, OpenSSL._util.lib.OBJ_nid2obj(ext._nid))
        #
        # Unfortunately this gives the wrong result in case the linked OpenSSL
        # doesn't know the OID. That's why we have to get the OID dotted string
        # similarly to how cryptography does it.
        result[oid] = entry
    return result


def cryptography_name_to_oid(name):
    dotted = _OID_LOOKUP.get(name)
    if dotted is None:
        raise OpenSSLObjectError('Cannot find OID for "{0}"'.format(name))
    return x509.oid.ObjectIdentifier(dotted)


def cryptography_oid_to_name(oid):
    dotted_string = oid.dotted_string
    names = _OID_MAP.get(dotted_string)
    name = names[0] if names else oid._name
    return _NORMALIZE_NAMES.get(name, name)


def cryptography_get_name(name):
    '''
    Given a name string, returns a cryptography x509.Name object.
    Raises an OpenSSLObjectError if the name is unknown or cannot be parsed.
    '''
    try:
        if name.startswith('DNS:'):
            return x509.DNSName(to_text(name[4:]))
        if name.startswith('IP:'):
            return x509.IPAddress(ipaddress.ip_address(to_text(name[3:])))
        if name.startswith('email:'):
            return x509.RFC822Name(to_text(name[6:]))
        if name.startswith('URI:'):
            return x509.UniformResourceIdentifier(to_text(name[4:]))
    except Exception as e:
        raise OpenSSLObjectError('Cannot parse Subject Alternative Name "{0}": {1}'.format(name, e))
    if ':' not in name:
        raise OpenSSLObjectError('Cannot parse Subject Alternative Name "{0}" (forgot "DNS:" prefix?)'.format(name))
    raise OpenSSLObjectError('Cannot parse Subject Alternative Name "{0}" (potentially unsupported by cryptography backend)'.format(name))


def _get_hex(bytes):
    if bytes is None:
        return bytes
    data = binascii.hexlify(bytes)
    data = to_text(b':'.join(data[i:i + 2] for i in range(0, len(data), 2)))
    return data


def cryptography_decode_name(name):
    '''
    Given a cryptography x509.Name object, returns a string.
    Raises an OpenSSLObjectError if the name is not supported.
    '''
    if isinstance(name, x509.DNSName):
        return 'DNS:{0}'.format(name.value)
    if isinstance(name, x509.IPAddress):
        return 'IP:{0}'.format(name.value.compressed)
    if isinstance(name, x509.RFC822Name):
        return 'email:{0}'.format(name.value)
    if isinstance(name, x509.UniformResourceIdentifier):
        return 'URI:{0}'.format(name.value)
    if isinstance(name, x509.DirectoryName):
        # FIXME: test
        return 'DirName:' + ''.join(['/{0}:{1}'.format(attribute.oid._name, attribute.value) for attribute in name.value])
    if isinstance(name, x509.RegisteredID):
        # FIXME: test
        return 'RegisteredID:{0}'.format(name.value)
    if isinstance(name, x509.OtherName):
        # FIXME: test
        return '{0}:{1}'.format(name.type_id.dotted_string, _get_hex(name.value))
    raise OpenSSLObjectError('Cannot decode name "{0}"'.format(name))


def _cryptography_get_keyusage(usage):
    '''
    Given a key usage identifier string, returns the parameter name used by cryptography's x509.KeyUsage().
    Raises an OpenSSLObjectError if the identifier is unknown.
    '''
    if usage in ('Digital Signature', 'digitalSignature'):
        return 'digital_signature'
    if usage in ('Non Repudiation', 'nonRepudiation'):
        return 'content_commitment'
    if usage in ('Key Encipherment', 'keyEncipherment'):
        return 'key_encipherment'
    if usage in ('Data Encipherment', 'dataEncipherment'):
        return 'data_encipherment'
    if usage in ('Key Agreement', 'keyAgreement'):
        return 'key_agreement'
    if usage in ('Certificate Sign', 'keyCertSign'):
        return 'key_cert_sign'
    if usage in ('CRL Sign', 'cRLSign'):
        return 'crl_sign'
    if usage in ('Encipher Only', 'encipherOnly'):
        return 'encipher_only'
    if usage in ('Decipher Only', 'decipherOnly'):
        return 'decipher_only'
    raise OpenSSLObjectError('Unknown key usage "{0}"'.format(usage))


def cryptography_parse_key_usage_params(usages):
    '''
    Given a list of key usage identifier strings, returns the parameters for cryptography's x509.KeyUsage().
    Raises an OpenSSLObjectError if an identifier is unknown.
    '''
    params = dict(
        digital_signature=False,
        content_commitment=False,
        key_encipherment=False,
        data_encipherment=False,
        key_agreement=False,
        key_cert_sign=False,
        crl_sign=False,
        encipher_only=False,
        decipher_only=False,
    )
    for usage in usages:
        params[_cryptography_get_keyusage(usage)] = True
    return params


def cryptography_get_basic_constraints(constraints):
    '''
    Given a list of constraints, returns a tuple (ca, path_length).
    Raises an OpenSSLObjectError if a constraint is unknown or cannot be parsed.
    '''
    ca = False
    path_length = None
    if constraints:
        for constraint in constraints:
            if constraint.startswith('CA:'):
                if constraint == 'CA:TRUE':
                    ca = True
                elif constraint == 'CA:FALSE':
                    ca = False
                else:
                    raise OpenSSLObjectError('Unknown basic constraint value "{0}" for CA'.format(constraint[3:]))
            elif constraint.startswith('pathlen:'):
                v = constraint[len('pathlen:'):]
                try:
                    path_length = int(v)
                except Exception as e:
                    raise OpenSSLObjectError('Cannot parse path length constraint "{0}" ({1})'.format(v, e))
            else:
                raise OpenSSLObjectError('Unknown basic constraint "{0}"'.format(constraint))
    return ca, path_length


def binary_exp_mod(f, e, m):
    '''Computes f^e mod m in O(log e) multiplications modulo m.'''
    # Compute len_e = floor(log_2(e))
    len_e = -1
    x = e
    while x > 0:
        x >>= 1
        len_e += 1
    # Compute f**e mod m
    result = 1
    for k in range(len_e, -1, -1):
        result = (result * result) % m
        if ((e >> k) & 1) != 0:
            result = (result * f) % m
    return result


def simple_gcd(a, b):
    '''Compute GCD of its two inputs.'''
    while b != 0:
        a, b = b, a % b
    return a


def quick_is_not_prime(n):
    '''Does some quick checks to see if we can poke a hole into the primality of n.

    A result of `False` does **not** mean that the number is prime; it just means
    that we couldn't detect quickly whether it is not prime.
    '''
    if n <= 2:
        return True
    # The constant in the next line is the product of all primes < 200
    if simple_gcd(n, 7799922041683461553249199106329813876687996789903550945093032474868511536164700810) > 1:
        return True
    # TODO: maybe do some iterations of Miller-Rabin to increase confidence
    # (https://en.wikipedia.org/wiki/Miller%E2%80%93Rabin_primality_test)
    return False


def cryptography_key_needs_digest_for_signing(key):
    '''Tests whether the given private key requires a digest algorithm for signing.

    Ed25519 and Ed448 keys do not; they need None to be passed as the digest algorithm.
    '''
    if CRYPTOGRAPHY_HAS_ED25519 and isinstance(key, cryptography.hazmat.primitives.asymmetric.ed25519.Ed25519PrivateKey):
        return False
    if CRYPTOGRAPHY_HAS_ED448 and isinstance(key, cryptography.hazmat.primitives.asymmetric.ed448.Ed448PrivateKey):
        return False
    return True


def cryptography_compare_public_keys(key1, key2):
    '''Tests whether two public keys are the same.

    Needs special logic for Ed25519 and Ed448 keys, since they do not have public_numbers().
    '''
    if CRYPTOGRAPHY_HAS_ED25519:
        a = isinstance(key1, cryptography.hazmat.primitives.asymmetric.ed25519.Ed25519PublicKey)
        b = isinstance(key2, cryptography.hazmat.primitives.asymmetric.ed25519.Ed25519PublicKey)
        if a or b:
            if not a or not b:
                return False
            a = key1.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
            b = key2.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
            return a == b
    if CRYPTOGRAPHY_HAS_ED448:
        a = isinstance(key1, cryptography.hazmat.primitives.asymmetric.ed448.Ed448PublicKey)
        b = isinstance(key2, cryptography.hazmat.primitives.asymmetric.ed448.Ed448PublicKey)
        if a or b:
            if not a or not b:
                return False
            a = key1.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
            b = key2.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
            return a == b
    return key1.public_numbers() == key2.public_numbers()
