# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Stefan Scheglmann <scheglmann@strato.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt) # noqa: E501

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import json
import base64
import os
import io

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.serialization import (
    load_pem_public_key, load_pem_private_key)
from cryptography import x509
from ansible.module_utils.ipa import IPAClient

# Set max vault data size to 1MB
MAX_VAULT_DATA_SIZE = 2**20


class VaultIPAClient(IPAClient):
    """IPA Client Class overrides"""
    def vault_find(self):
        """Get vault information for given cn, equivalent to 'ipa vault_find'
        cli command with specified vault name."""
        item = {'all': True, 'cn': self.module.params['cn']}
        item = self._update_item(item=item,
                                 service=self.module.params.get('service'),
                                 username=self.module.params.get('username'))
        return self._post_json(method='vault_find', name=None, item=item)

    def _vault_config(self):
        """Get full vault configuration, equivalent to 'ipa vaultconfig_show'
        cli command"""
        return self._post_json(method='vaultconfig_show', name=None)

    def _vault_archive(self, vault, data=None, password=None):
        """Archive given data in the vault"""
        item = self._generate_vault_archive_item(vault, data, password)
        item = self._update_item(item=item,
                                 service=vault.get('service'),
                                 username=vault.get('username'))
        self._post_json(
            method='vault_archive_internal', name=vault['cn'][0], item=item)
        return data

    def _vault_retrieve(self, vault, password=None, private_key=None):
        """Retrieve data from given vault"""
        algo = self._generate_session_key()
        item = self._generate_vault_retrieve_item(algo)
        item = self._update_item(item=item,
                                 service=vault.get('service'),
                                 username=vault.get('username'))
        response = self._post_json(method='vault_retrieve_internal',
                                   name=vault['cn'][0],
                                   item=item)
        if response is None:
            return None
        vault_data = self._unwrap_response(algo, response)
        del algo

        data = base64.b64decode(vault_data['data'].encode('utf-8'))
        encrypted_key = None
        vault_type = vault['ipavaulttype'][0]
        if vault_type == 'symmetric':
            salt = base64.b64decode(vault['ipavaultsalt'][0]['__base64__'])
            encryption_key = self._generate_symmetric_key(password, salt)
            data = self._decrypt(data, symmetric_key=encryption_key)
        elif vault_type == 'asymmetric':
            if 'encrypted_key' in vault_data:
                encrypted_key = base64.b64decode(vault_data['encrypted_key']
                                                 .encode('utf-8'))
            else:
                self._fail(
                    "Vault Error",
                    "No encryption key in data, cannot be asymmetric vault."
                )
            encryption_key = self._decrypt(
                encrypted_key, private_key=private_key)
            data = self._decrypt(data, symmetric_key=encryption_key)
        return data

    def _vault_add_internal(self, name, item):
        """Add vault to ipa. Equivalent to 'ipa vault-add' cli command"""
        return self._post_json(
            method='vault_add_internal', name=name, item=item)

    def _vault_mod_internal(self, vault, item):
        """Modify ipa vault. Equivalent to 'ipa vault-mod' cli command"""
        item = self._update_item(item=item,
                                 service=vault.get('service'),
                                 username=vault.get('username'))
        return self._post_json(
            method='vault_mod_internal', name=vault['cn'][0], item=item)

    def vault_del(self, vault):
        """Delete ipa vault. Equivalent to 'ipa vault-del' cli command"""
        item = self._update_item(service=self.module.params.get('service'),
                                 username=self.module.params.get('username'))
        return self._post_json(method='vault_del',
                               name=vault['cn'][0],
                               item=item)

    def _vault_add_member(self, vault, member_users=None,
                          member_groups=None, member_services=None):
        """Add user, group or service member to vault"""
        item = self._update_item(service=vault.get('service'),
                                 username=vault.get('username'))
        if member_users:
            item.update({'user': member_users})
        if member_groups:
            item.update({'group': member_groups})
        if member_services:
            item.update({'services': member_services})
        return self._post_json(method='vault_add_member',
                               name=vault['cn'][0], item=item)

    def _vault_remove_member(self, vault, member_users=None,
                             member_groups=None, member_services=None):
        """Removes user, group or service member from vault"""
        item = self._update_item(service=vault.get('service'),
                                 username=vault.get('username'))
        if member_users:
            item.update({'user': member_users})
        if member_groups:
            item.update({'group': member_groups})
        if member_services:
            item.update({'services': member_services})
        return self._post_json(method='vault_remove_member',
                               name=vault['cn'][0], item=item)

    @staticmethod
    def _update_item(service, username, item=None):
        """Update item with username/service"""
        item = {} if item is None else item
        if service is not None:
            item.update({'service': service})
        elif username is not None:
            item.update({'username': username})
        return item

    def _wrap_session_key(self, crypt_key):
        """Encrypt crypt key using transport_cert to obtain session key

        params bytes crypt_key: crypt key
        returns: session key
        """

        transport_cert = x509.load_der_x509_certificate(
            base64.b64decode(
                self._vault_config().get('transport_cert').get('__base64__')
            ), backend=default_backend()
        )

        public_key = transport_cert.public_key()
        session_key = base64.b64encode(
            public_key.encrypt(crypt_key, padding.PKCS1v15())
        )

        return session_key

    @staticmethod
    def _wrap_data(algo, json_vault_data):
        """Encrypt data with wrapped session key and transport cert

        param bytes algo: wrapping algorithm instance
        param bytes json_vault_data: dumped vault data
        return:
        """
        nonce = os.urandom(algo.block_size // 8)

        padder = PKCS7(algo.block_size).padder()
        padded_data = padder.update(json_vault_data)
        padded_data += padder.finalize()

        cipher = Cipher(algo, modes.CBC(nonce), backend=default_backend())
        encryptor = cipher.encryptor()
        wrapped_vault_data = (encryptor.update(padded_data) +
                              encryptor.finalize())

        return nonce, wrapped_vault_data

    @staticmethod
    def _unwrap_response(algo, response):
        """Decrypt data with wrapped session key and transport cert

        param bytes algo: wrapping algorithm instance
        param bytes response: encrypted retrieval response
        return: vault_data dict
        """
        nonce = base64.b64decode(
            response['nonce']['__base64__'].encode('utf-8'))
        vault_data = base64.b64decode(
            response['vault_data']['__base64__'].encode('utf-8')
        )
        cipher = Cipher(algo, modes.CBC(nonce), backend=default_backend())
        # decrypt
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(vault_data)
        padded_data += decryptor.finalize()
        # remove padding
        unpadder = PKCS7(algo.block_size).unpadder()
        json_vault_data = unpadder.update(padded_data)
        json_vault_data += unpadder.finalize()
        # load JSON
        return json.loads(json_vault_data.decode('utf-8'))

    @staticmethod
    def _generate_session_key():
        """Generate encryption key"""
        key_len = max(algorithms.TripleDES.key_sizes)
        return algorithms.TripleDES(os.urandom(key_len // 8))

    def _generate_vault_archive_item(self, vault, data=None, password=None):
        """Updates item dict, with encrypted vault data, nonce and session key
        in place.

        param dict vault: the vault dict
        param string data: the data to vault
        param string password: the encryption pass for the vault
            (symmetric only)

        returns:
        """
        encrypted_key = None
        vault_type = vault['ipavaulttype'][0]

        if vault_type == 'symmetric':
            salt = base64.b64decode(vault['ipavaultsalt'][0]['__base64__'])
            encryption_key = self._generate_symmetric_key(password, salt)
            data = self._encrypt(data, symmetric_key=encryption_key)
        elif vault_type == 'asymmetric':
            public_key = base64.b64decode(
                vault.get('ipavaultpublickey')[0]['__base64__'])
            if not public_key:
                self._fail(
                    "Public Key Error",
                    "No public key defined for asymmetric vault."
                    " Cannot archive!"
                )
            encryption_key = base64.b64encode(os.urandom(32))
            data = self._encrypt(data, symmetric_key=encryption_key)
            encrypted_key = self._encrypt(encryption_key,
                                          public_key=public_key)

        vault_data = {
            'data': base64.b64encode(data).decode('utf-8')
        }

        if encrypted_key:
            vault_data['encrypted_key'] = base64.b64encode(encrypted_key)\
                .decode('utf-8')
        json_vault_data = json.dumps(vault_data).encode('utf-8')

        algo = self._generate_session_key()

        # wrap vault data and add encrypted session key
        nonce, wrapped_vault_data = self._wrap_data(algo, json_vault_data)
        return {
            'nonce': {'__base64__': base64.b64encode(nonce)},
            'vault_data': {
                '__base64__': base64.b64encode(wrapped_vault_data)
            },
            'session_key': {
                '__base64__': self._wrap_session_key(algo.key)
            }
        }

    def _generate_vault_retrieve_item(self, algo):
        """Generate vault dict with session key in place"""
        return {
            'session_key': {
                '__base64__': self._wrap_session_key(algo.key)
            }
        }

    @staticmethod
    def _generate_symmetric_key(password, salt):
        """Generates symmetric key from password and salt """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        return base64.b64encode(kdf.derive(password.encode('utf-8')))

    def _encrypt(self, data, symmetric_key=None, public_key=None):
        """Encrypts data with symmetric key or public key """
        if symmetric_key is not None:
            if public_key is not None:
                self._fail(
                    "Encryption Error",
                    "Either a symmetric or a public key is required, not both."
                )

            fernet = Fernet(symmetric_key)
            return fernet.encrypt(data)

        elif public_key is not None:
            public_key_obj = load_pem_public_key(
                data=public_key,
                backend=default_backend()
            )
            return public_key_obj.encrypt(
                data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA1()),
                    algorithm=hashes.SHA1(),
                    label=None
                )
            )
        else:
            self._fail(
                "Encryption Error",
                "Either a symmetric or a public key is required."
            )

    def _decrypt(self, data, symmetric_key=None, private_key=None):
        """Decrypts data with symmetric key or public key."""
        if symmetric_key is not None:
            if private_key is not None:
                self._fail(
                    "Decryption Error",
                    "Either a symmetric or a private key is required,"
                    " not both."
                )
            try:
                fernet = Fernet(symmetric_key)
                return fernet.decrypt(data)
            except InvalidToken as e:
                self._fail('Invalid credentials', e)

        elif private_key is not None:
            try:
                private_key_obj = load_pem_private_key(
                    data=private_key,
                    password=None,
                    backend=default_backend()
                )
                return private_key_obj.decrypt(
                    data,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA1()),
                        algorithm=hashes.SHA1(),
                        label=None
                    )
                )
            except ValueError as e:
                self._fail('Invalid credentials', e)
        else:
            self._fail(
                "Decryption Error",
                "Either a symmetric or a private key is required."
            )

    @staticmethod
    def _get_password(password=None, password_file=None):
        """Return password if specified otherwise read it from password file and
        return it"""
        if password_file:
            with io.open(password_file, mode='r', encoding='utf-8') as p_file:
                password = p_file.read().rstrip('\n')
        return password

    def _get_password_or_fail(self):
        """Get password or fail if not set."""
        password = self._get_password(
            password=self.module.params.get('ipavaultpassword'),
            password_file=self.module.params.get('ipavaultpasswordfile')
        )
        if not password:
            self._fail(
                "Password Error",
                "Cannot retrieve from or archive in symmetric vault"
                " '%s' without password" % self.module.params['cn']
            )
        return password

    @staticmethod
    def _get_key(key=None, key_file=None):
        """Return key or read and return it from keyfile"""
        if key_file:
            with io.open(key_file, mode='rb') as k_file:
                key = k_file.read()
        return key

    def _get_private_key_or_fail(self):
        """Get private key or fail if not set."""
        private_key = self._get_key(
            key=self.module.params.get('ipavaultprivatekey'),
            key_file=self.module.params.get('ipavaultprivatekeyfile')
        )
        if not private_key:
            self._fail(
                "Provate Key Error",
                "Cannot retrieve from asymmetric vault '%s' without private"
                " key" % self.module.params['cn']
            )
        return private_key

    @staticmethod
    def _get_salt(salt=None):
        """Get or create encryption salt"""
        if salt:
            if not base64.b64encode(base64.b64decode(salt)) == salt:
                salt = base64.b64encode(salt)
            return salt
        return base64.b64encode(os.urandom(16))

    def get_n_validate_data(self):
        """Validate given data or read and validate data from given file.
        Return it"""
        data = self.module.params.get('ipavaultdata')
        data_file = self.module.params.get('ipavaultdatafile')
        if data:
            if len(data) > MAX_VAULT_DATA_SIZE:
                self._fail(
                    "Data Error",
                    "Size of data exceeds the limit. Current vault data size"
                    " limit is %s" % MAX_VAULT_DATA_SIZE,
                )
        elif data_file:
            stat = os.stat(data_file)
            if stat.st_size > MAX_VAULT_DATA_SIZE:
                self._fail(
                    "Data Error",
                    "Size of data exceeds the limit. Current vault data size"
                    " limit is %s" % MAX_VAULT_DATA_SIZE
                )
            with io.open(data_file, mode='rb') as d_file:
                data = d_file.read()
        else:
            data = b''
        return data

    def get_or_create_vault(self):
        """Return the vault if existing otherwise create and return it"""
        changed = False
        ipa_vault = self.vault_find()
        if not ipa_vault:
            changed = True
            keys = ['description',
                    'ipavaulttype',
                    'ipavaultsalt',
                    'username',
                    'service']
            item = dict(
                (k, v) for (k, v) in self.module.params.items()
                if k in keys and v)

            if item['ipavaulttype'] == 'asymmetric':
                item.update(dict(
                    ipavaultpublickey=base64.b64encode(
                        self._get_key(
                            key=self.module.params['ipavaultpublickey'],
                            key_file=self.module.params[
                                'ipavaultpublickeyfile']
                        )
                    )
                ))
            elif item['ipavaulttype'] == 'symmetric':
                item.update(dict(
                    ipavaultsalt=self._get_salt(
                        salt=self.module.params.get('ipavaultsalt'))
                ))

            if not self.module.check_mode:
                ipa_vault = self._vault_add_internal(self.module.params['cn'],
                                                     item=item)
        return changed, ipa_vault

    def retrieve_data(self, vault):
        """Retrieve data from vault"""
        vault_type = vault['ipavaulttype'][0]
        password = None
        private_key = None
        # Get password for symmetric vaults.
        if vault_type == 'symmetric':
            password = self._get_password_or_fail()
        elif vault_type == 'asymmetric':
            private_key = self._get_private_key_or_fail()
        return False, self._vault_retrieve(vault,
                                           password=password,
                                           private_key=private_key)

    def archive_data_internal(self, vault, data):
        """Plain vault data archiving"""
        password = None
        if not self.module.check_mode:
            if vault['ipavaulttype'][0] == 'symmetric':
                password = self._get_password_or_fail()
            return self._vault_archive(vault, data=data,
                                       password=password)
        else:
            return data

    def archive_data(self, vault, data=None):
        """Archive data in vault.

        return (boolean, data): if changed and archived data"""
        if not data:
            data = self.get_n_validate_data()
        dummy, vault_data = self.retrieve_data(vault)
        changed = (data is not None and data != vault_data)
        if changed:
            vault_data = self.archive_data_internal(vault, data)
        vault.update({'data': vault_data})
        return changed, vault

    @staticmethod
    def _diff_members(m_l1, m_l2):
        """Diff vault member lists. Two list can be provided i(m_l1 and m_l2):
        - if both are provided return difference between both.
        - elif the first list is not provided return second list.
        - else return empty list.
        """
        return list(
            set(m_l1) - set(m_l2) if m_l1 and m_l2 else m_l2 if not m_l1 and
            m_l2 else [])

    def add_vault_members(self, vault):
        """Add members to vault"""
        users_add = self._diff_members(vault.get('member_user'),
                                       self.module.params.get('memberusers'))
        groups_add = self._diff_members(vault.get('member_group'),
                                        self.module.params.get('membergroups'))
        services_add = self._diff_members(
            vault.get('member_service'),
            self.module.params.get('memberservices'))
        changed = any([users_add, groups_add, services_add])
        if not self.module.check_mode:
            self._vault_add_member(vault, users_add, groups_add,
                                   services_add)
            vault = self.vault_find()
        else:
            vault = vault.update(dict(member_user=users_add,
                                      member_group=groups_add,
                                      member_service=services_add))
        return changed, vault

    @staticmethod
    def _intersect_members(m_l1, m_l2):
        """Intersect member sets"""
        return list(set(m_l1).intersection(set(m_l2)) if m_l1 and m_l2 else [])

    def remove_vault_members(self, vault):
        """Remove members from vault"""
        users_rm = self._intersect_members(
            self.module.params.get('memberusers'),
            vault.get('member_user'))
        groups_rm = self._intersect_members(
            self.module.params.get('membergroups'),
            vault.get('member_group'))
        services_rm = self._intersect_members(
            self.module.params.get('memberservices'),
            vault.get('member_service'))
        changed = any([users_rm, groups_rm, services_rm])
        if not self.module.check_mode:
            self._vault_remove_member(vault, users_rm, groups_rm,
                                      services_rm)
            vault = self.vault_find()
        else:
            users = set(vault.get('member_user')) - set(users_rm)
            groups = set(vault.get('member_group')) - set(groups_rm)
            services = set(vault.get('member_service')) - set(services_rm)
            vault = vault.update(dict(member_user=users,
                                      member_group=groups,
                                      member_service=services))
        return changed, vault

    def _create_update_item(self, password=None, salt=None, public_key=None,
                            item=None, new_desc=None):
        """Create vault update item"""
        if not item:
            item = {}
        if password or salt:
            item.update(
                dict(ipavaultsalt=dict(__base64__=self._get_salt(salt)),
                     ipavaultpublickey=None))
        elif public_key:
            item.update(dict(ipavaultsalt=None,
                             ipavaultpublickey=public_key))
        elif new_desc:
            item.update(dict(description=new_desc))

        return item

    def update_vault(self, vault):
        changed = False
        new_type = self.module.params.get('ipavaultnewtype')
        new_password = self.module.params['ipavaultnewpassword']
        new_desc = self.module.params.get('description')
        if new_type and new_type != vault['ipavaulttype'][0]:
            changed = True
            vault = self._update_vault_type(vault, new_type)
        elif new_password and new_password != \
                self.module.params['ipavaultpassword'] or (
                self.module.params['ipavaultnewpublickey'] or
                self.module.params['ipavaultnewpublickeyfile']):
            changed = True
            vault = self._update_vault_password(vault)
        if new_desc and new_desc != vault['description'][0]:
            changed = True
            item = self._create_update_item(new_desc=new_desc)
            vault = self._vault_mod_internal(vault, item)
        return changed, vault

    def _update_vault_password(self, vault):
        """Update vault password or keys"""
        dummy, data = self.retrieve_data(vault)
        if vault.get('ipavaulttype')[0] == 'symmetric':
            item = self._create_update_item(
                password=self._get_password(
                    password=self.module.params.get('ipavaultnewpassword'),
                    password_file=self.module.params.get(
                        'ipavaultnewpasswordfile')),
                salt=self.module.params.get('ipavaultsalt')
            )
            vault = self._vault_mod_internal(vault, item)
            self.module.params['ipavaultpassword'] = \
                self.module.params['ipavaultnewpassword']
        elif vault.get('ipavaulttype')[0] == 'asymmetric':
            item = self._create_update_item(
                public_key=base64.b64encode(
                    self._get_key(
                        key=self.module.params.get('ipavaultnewpublickey'),
                        key_file=self.module.params.get(
                            'ipavaultnewpublickeyfile')
                    )
                )
            )
            vault = self._vault_mod_internal(vault, item)
        self.archive_data_internal(vault, data=data)
        return vault

    def _update_vault_type(self, vault, new_type):
        """Change vault type"""
        dummy, data = self.retrieve_data(vault)
        item = {'ipavaulttype': new_type}
        if new_type == 'symmetric':
            item = self._create_update_item(
                password=self._get_password(
                    password=self.module.params.get('ipavaultnewpassword'),
                    password_file=self.module.params.get(
                        'ipavaultnewpasswordfile')),
                salt=self.module.params.get('ipavaultsalt'),
                item=item
            )
            self.module.params['ipavaultpassword'] = \
                self.module.params['ipavaultnewpassword']
        elif new_type == 'asymmetric':
            item = self._create_update_item(
                public_key=base64.b64encode(
                    self._get_key(
                        key=self.module.params.get('ipavaultnewpublickey'),
                        key_file=self.module.params.get(
                            'ipavaultnewpublickeyfile'))),
                item=item
            )
        vault = self._vault_mod_internal(vault, item)
        self.archive_data_internal(vault, data=data)
        return vault
