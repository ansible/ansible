#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2017, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: bigip_user
short_description: Manage user accounts and user attributes on a BIG-IP
description:
  - Manage user accounts and user attributes on a BIG-IP. Typically this
    module operates only on the REST API users and not the CLI users.
    When specifying C(root), you may only change the password.
    Your other parameters will be ignored in this case. Changing the C(root)
    password is not an idempotent operation. Therefore, it will change it
    every time this module attempts to change it.
version_added: 2.4
options:
  full_name:
    description:
      - Full name of the user.
    type: str
  username_credential:
    description:
      - Name of the user to create, remove or modify.
      - The C(root) user may not be removed.
    type: str
    required: True
    aliases:
      - name
  password_credential:
    description:
      - Set the users password to this unencrypted value.
        C(password_credential) is required when creating a new account.
    type: str
  shell:
    description:
      - Optionally set the users shell.
    type: str
    choices:
      - bash
      - none
      - tmsh
  partition_access:
    description:
      - Specifies the administrative partition to which the user has access.
        C(partition_access) is required when creating a new account.
        Should be in the form "partition:role".
      - Valid roles include C(acceleration-policy-editor), C(admin), C(application-editor),
        C(auditor), C(certificate-manager), C(guest), C(irule-manager), C(manager), C(no-access),
        C(operator), C(resource-admin), C(user-manager), C(web-application-security-administrator),
        and C(web-application-security-editor).
      - Partition portion of tuple should be an existing partition or the value 'all'.
    type: list
  state:
    description:
      - Whether the account should exist or not, taking action if the state is
        different from what is stated.
    type: str
    choices:
      - present
      - absent
    default: present
  update_password:
    description:
      - C(always) will allow to update passwords if the user chooses to do so.
        C(on_create) will only set the password for newly created users.
      - When C(username_credential) is C(root), this value will be forced to C(always).
    type: str
    choices:
      - always
      - on_create
    default: always
  partition:
    description:
      - Device partition to manage resources on.
    type: str
    default: Common
    version_added: 2.5
notes:
   - Requires BIG-IP versions >= 12.0.0
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Add the user 'johnd' as an admin
  bigip_user:
    username_credential: johnd
    password_credential: password
    full_name: John Doe
    partition_access: all:admin
    update_password: on_create
    state: present
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Change the user "johnd's" role and shell
  bigip_user:
    username_credential: johnd
    partition_access: NewPartition:manager
    shell: tmsh
    state: present
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Make the user 'johnd' an admin and set to advanced shell
  bigip_user:
    name: johnd
    partition_access: all:admin
    shell: bash
    state: present
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Remove the user 'johnd'
  bigip_user:
    name: johnd
    state: absent
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Update password
  bigip_user:
    state: present
    username_credential: johnd
    password_credential: newsupersecretpassword
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

# Note that the second time this task runs, it would fail because
# The password has been changed. Therefore, it is recommended that
# you either,
#
#   * Put this in its own playbook that you run when you need to
#   * Put this task in a `block`
#   * Include `ignore_errors` on this task
- name: Change the Admin password
  bigip_user:
    state: present
    username_credential: admin
    password_credential: NewSecretPassword
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Change the root user's password
  bigip_user:
    username_credential: root
    password_credential: secret
    state: present
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost
'''

RETURN = r'''
full_name:
  description: Full name of the user
  returned: changed and success
  type: str
  sample: John Doe
partition_access:
  description:
    - List of strings containing the user's roles and which partitions they
      are applied to. They are specified in the form "partition:role".
  returned: changed and success
  type: list
  sample: ['all:admin']
shell:
  description: The shell assigned to the user account
  returned: changed and success
  type: str
  sample: tmsh
'''

import os
import tempfile

from ansible.module_utils._text import to_bytes

try:
    from BytesIO import BytesIO
except ImportError:
    from io import BytesIO

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.six import string_types
from distutils.version import LooseVersion

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.icontrol import tmos_version
    from library.module_utils.network.f5.icontrol import upload_file
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.icontrol import tmos_version
    from ansible.module_utils.network.f5.icontrol import upload_file


try:
    # Crypto is used specifically for changing the root password via
    # tmsh over REST.
    #
    # We utilize the crypto library to encrypt the contents of a file
    # before we upload it, and then decrypt it on-box to change the
    # password.
    #
    # To accomplish such a process, we need to be able to encrypt the
    # temporary file with the public key found on the box.
    #
    # These libraries are used to do the encryption.
    #
    # Note that, if these are not available, the ability to change the
    # root password is disabled and the user will be notified as such
    # by a failure of the module.
    #
    # These libraries *should* be available on most Ansible controllers
    # by default though as crypto is a dependency of Ansible.
    #
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives import hashes
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False


class Parameters(AnsibleF5Parameters):
    api_map = {
        'partitionAccess': 'partition_access',
        'description': 'full_name',
    }

    updatables = [
        'partition_access',
        'full_name',
        'shell',
        'password_credential',
    ]

    returnables = [
        'shell',
        'partition_access',
        'full_name',
        'username_credential',
        'password_credential',
    ]

    api_attributes = [
        'shell',
        'partitionAccess',
        'description',
        'name',
        'password',
    ]

    @property
    def partition_access(self):
        """Partition access values will require some transformation.

        This operates on both user and device returned values.
        Check if the element is a string from user input in the format of
        name:role, if it is split  it and create dictionary out of it.

        If the access value is a dictionary (returned from device,
        or already processed) and contains nameReference
        key, delete it and append the remaining dictionary element into
        a list.

        If the nameReference key is removed just append the dictionary
        into the list.

        Returns:
            List of dictionaries. Each item in the list is a dictionary
            which contains the ``name`` of the partition and the ``role`` to
            allow on that partition.
        """
        if self._values['partition_access'] is None:
            return
        result = []
        part_access = self._values['partition_access']
        for access in part_access:
            if isinstance(access, dict):
                if 'nameReference' in access:
                    del access['nameReference']

                    result.append(access)
                else:
                    result.append(access)
            if isinstance(access, string_types):
                acl = access.split(':')
                if acl[0].lower() == 'all':
                    acl[0] = 'all-partitions'
                value = dict(
                    name=acl[0],
                    role=acl[1]
                )

                result.append(value)
        return result

    @property
    def temp_upload_file(self):
        if self._values['temp_upload_file'] is None:
            f = tempfile.NamedTemporaryFile()
            name = os.path.basename(f.name)
            self._values['temp_upload_file'] = name
        return self._values['temp_upload_file']


class ApiParameters(Parameters):
    @property
    def shell(self):
        if self._values['shell'] in [None, 'none']:
            return None
        return self._values['shell']


class ModuleParameters(Parameters):
    @property
    def shell(self):
        if self._values['shell'] in [None, 'none']:
            return None
        return self._values['shell']


class Changes(Parameters):
    def to_return(self):
        result = {}
        for returnable in self.returnables:
            try:
                result[returnable] = getattr(self, returnable)
            except Exception:
                pass
            result = self._filter_params(result)
        return result


class UsableChanges(Changes):
    @property
    def password(self):
        if self._values['password_credential'] is None:
            return None
        return self._values['password_credential']


class ReportableChanges(Changes):
    pass


class Difference(object):
    def __init__(self, want, have=None):
        self.want = want
        self.have = have

    def compare(self, param):
        try:
            result = getattr(self, param)
            return result
        except AttributeError:
            return self.__default(param)

    def __default(self, param):
        attr1 = getattr(self.want, param)
        try:
            attr2 = getattr(self.have, param)
            if attr1 != attr2:
                return attr1
        except AttributeError:
            return attr1

    @property
    def password_credential(self):
        if self.want.password_credential is None:
            return None
        if self.want.update_password in ['always']:
            return self.want.password_credential
        return None

    @property
    def shell(self):
        if self.want.shell is None:
            if self.have.shell is not None:
                return 'none'
            else:
                return None
        if self.want.shell == 'bash':
            self._validate_shell_parameter()
            if self.want.shell == self.have.shell:
                return None
            else:
                return self.want.shell
        if self.want.shell != self.have.shell:
            return self.want.shell

    def _validate_shell_parameter(self):
        """Method to validate shell parameters.

        Raise when shell attribute is set to 'bash' with roles set to
        either 'admin' or 'resource-admin'.

        NOTE: Admin and Resource-Admin roles automatically enable access to
        all partitions, removing any other roles that the user might have
        had. There are few other roles which do that but those roles,
        do not allow bash.
        """

        err = "Shell access is only available to " \
              "'admin' or 'resource-admin' roles."
        permit = ['admin', 'resource-admin']

        have = self.have.partition_access
        if not any(r['role'] for r in have if r['role'] in permit):
            raise F5ModuleError(err)

        if self.want.partition_access is not None:
            want = self.want.partition_access
            if not any(r['role'] for r in want if r['role'] in permit):
                raise F5ModuleError(err)


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)
        self.kwargs = kwargs

    def exec_module(self):
        if self.is_root_username_credential():
            manager = self.get_manager('root')
        elif self.is_version_less_than_13():
            manager = self.get_manager('v1')
        else:
            manager = self.get_manager('v2')
        return manager.exec_module()

    def get_manager(self, type):
        if type == 'root':
            return RootUserManager(**self.kwargs)
        elif type == 'v1':
            return UnpartitionedManager(**self.kwargs)
        elif type == 'v2':
            return PartitionedManager(**self.kwargs)

    def is_version_less_than_13(self):
        """Checks to see if the TMOS version is less than 13

        Anything less than BIG-IP 13.x does not support users
        on different partitions.

        :return: Bool
        """
        version = tmos_version(self.client)
        if LooseVersion(version) < LooseVersion('13.0.0'):
            return True
        else:
            return False

    def is_root_username_credential(self):
        user = self.module.params.get('username_credential', None)
        if user == 'root':
            return True
        return False


class BaseManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)
        self.want = ModuleParameters(params=self.module.params)
        self.have = ApiParameters()
        self.changes = UsableChanges()

    def _announce_deprecations(self, result):
        warnings = result.pop('__warnings', [])
        for warning in warnings:
            self.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

    def _set_changed_options(self):
        changed = {}
        for key in Parameters.returnables:
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = UsableChanges(params=changed)

    def _update_changed_options(self):
        diff = Difference(self.want, self.have)
        updatables = Parameters.updatables
        changed = dict()
        for k in updatables:
            change = diff.compare(k)
            if change is None:
                continue
            else:
                if isinstance(change, dict):
                    changed.update(change)
                else:
                    changed[k] = change
        if changed:
            self.changes = UsableChanges(params=changed)
            return True
        return False

    def exec_module(self):
        changed = False
        result = dict()
        state = self.want.state

        if state == "present":
            changed = self.present()
        elif state == "absent":
            changed = self.absent()

        reportable = ReportableChanges(params=self.changes.to_return())
        changes = reportable.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        self._announce_deprecations(result)
        return result

    def present(self):
        if self.exists():
            return self.update()
        else:
            return self.create()

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def should_update(self):
        result = self._update_changed_options()
        if result:
            return True
        return False

    def update(self):
        self.have = self.read_current_from_device()
        if not self.should_update():
            return False
        if self.module.check_mode:
            return True
        self.update_on_device()
        return True

    def remove(self):
        if self.module.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the user.")
        return True

    def create(self):
        self.validate_create_parameters()
        if self.want.shell == 'bash':
            self.validate_shell_parameter()
        self._set_changed_options()
        if self.module.check_mode:
            return True
        self.create_on_device()
        return True

    def validate_shell_parameter(self):
        """Method to validate shell parameters.

        Raise when shell attribute is set to 'bash' with roles set to
        either 'admin' or 'resource-admin'.

        NOTE: Admin and Resource-Admin roles automatically enable access to
        all partitions, removing any other roles that the user might have
        had. There are few other roles which do that but those roles,
        do not allow bash.
        """

        err = "Shell access is only available to " \
              "'admin' or 'resource-admin' roles."
        permit = ['admin', 'resource-admin']

        if self.want.partition_access is not None:
            want = self.want.partition_access
            if not any(r['role'] for r in want if r['role'] in permit):
                raise F5ModuleError(err)

    def validate_create_parameters(self):
        if self.want.partition_access is None:
            err = "The 'partition_access' option " \
                  "is required when creating a resource."
            raise F5ModuleError(err)


class UnpartitionedManager(BaseManager):
    def exists(self):
        uri = "https://{0}:{1}/mgmt/tm/auth/user/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.name
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError:
            return False
        if resp.status == 404 or 'code' in response and response['code'] == 404:
            return False
        return True

    def create_on_device(self):
        params = self.changes.api_params()
        params['name'] = self.want.name
        uri = "https://{0}:{1}/mgmt/tm/auth/user/".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 403]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        return response['selfLink']

    def update_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/auth/user/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.name
        )
        resp = self.client.api.patch(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/auth/user/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.name
        )
        response = self.client.api.delete(uri)
        if response.status == 200:
            return True
        raise F5ModuleError(response.content)

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/auth/user/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.name
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        return ApiParameters(params=response)


class PartitionedManager(BaseManager):
    def exists(self):
        response = self.list_users_on_device()
        if 'items' in response:
            collection = [x for x in response['items'] if x['name'] == self.want.name]
            if len(collection) == 1:
                return True
            elif len(collection) == 0:
                return False
            else:
                raise F5ModuleError(
                    "Multiple users with the provided name were found!"
                )
        return False

    def create_on_device(self):
        params = self.changes.api_params()
        params['name'] = self.want.name
        params['partition'] = self.want.partition
        uri = "https://{0}:{1}/mgmt/tm/auth/user/".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 404, 409]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        return response['selfLink']

    def read_current_from_device(self):
        response = self.list_users_on_device()
        collection = [x for x in response['items'] if x['name'] == self.want.name]
        if len(collection) == 1:
            user = collection.pop()
            return ApiParameters(params=user)
        elif len(collection) == 0:
            raise F5ModuleError(
                "No accounts with the provided name were found."
            )
        else:
            raise F5ModuleError(
                "Multiple users with the provided name were found!"
            )

    def update_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/auth/user/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.name
        )
        resp = self.client.api.patch(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 404, 409]:
            if 'message' in response:
                if 'updated successfully' not in response['message']:
                    raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/auth/user/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.name
        )
        response = self.client.api.delete(uri)
        if response.status == 200:
            return True
        raise F5ModuleError(response.content)

    def list_users_on_device(self):
        uri = "https://{0}:{1}/mgmt/tm/auth/user/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        query = "?$filter=partition+eq+'{0}'".format(self.want.partition)
        resp = self.client.api.get(uri + query)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        return response


class RootUserManager(BaseManager):
    def exec_module(self):
        if not HAS_CRYPTO:
            raise F5ModuleError(
                "An installed and up-to-date python 'cryptography' package is "
                "required to change the 'root' password."
            )

        changed = False
        result = dict()
        state = self.want.state

        if state == "present":
            changed = self.present()
        elif state == "absent":
            raise F5ModuleError(
                "You may not remove the root user."
            )

        reportable = ReportableChanges(params=self.changes.to_return())
        changes = reportable.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        self._announce_deprecations(result)
        return result

    def exists(self):
        return True

    def update(self):
        public_key = self.get_public_key_from_device()
        public_key = self.extract_key(public_key)
        encrypted = self.encrypt_password_change_file(
            public_key, self.want.password_credential
        )
        self.upload_to_device(encrypted, self.want.temp_upload_file)
        result = self.update_on_device()
        self.remove_uploaded_file_from_device(self.want.temp_upload_file)
        return result

    def encrypt_password_change_file(self, public_key, password):
        # This function call requires that the public_key be expressed in bytes
        pub = serialization.load_pem_public_key(
            to_bytes(public_key),
            backend=default_backend()
        )

        message = to_bytes("{0}\n{0}\n".format(password))
        ciphertext = pub.encrypt(
            message,

            # OpenSSL craziness
            #
            # Using this padding because it is the only one that works with
            # the OpenSSL on BIG-IP at this time.
            padding.PKCS1v15(),

            #
            # OAEP is the recommended padding to use for encrypting, however, two
            # things are wrong with it on BIG-IP.
            #
            # The first is that one of the parameters required to decrypt the data
            # is not supported by the OpenSSL version on BIG-IP. A "parameter setting"
            # error is raised when you attempt to use the OAEP parameters to specify
            # hashing algorithms.
            #
            # This is validated by this thread here
            #
            #  https://mta.openssl.org/pipermail/openssl-dev/2017-September/009745.html
            #
            # Were is supported, we could use OAEP, but the second problem is that OAEP
            # is not the default mode of the ``openssl`` command. Therefore, we need
            # to adjust the command we use to decrypt the encrypted file when it is
            # placed on BIG-IP.
            #
            # The correct (and recommended if BIG-IP ever upgrades OpenSSL) code is
            # shown below.
            #
            #   padding.OAEP(
            #       mgf=padding.MGF1(algorithm=hashes.SHA256()),
            #       algorithm=hashes.SHA256(),
            #       label=None
            #   )
            #
            # Additionally, the code in ``update_on_device()`` would need to be changed
            # to pass the correct command line arguments to decrypt the file.
        )
        return BytesIO(ciphertext)

    def extract_key(self, content):
        """Extracts the public key from the openssl command output over REST

        The REST output includes some extra output that is not relevant to the
        public key. This function attempts to only return the valid public key
        data from the openssl output

        Args:
            content: The output from the REST API command to view the public key.

        Returns:
            string: The discovered public key
        """

        lines = content.split("\n")
        start = lines.index('-----BEGIN PUBLIC KEY-----')
        end = lines.index('-----END PUBLIC KEY-----')
        result = "\n".join(lines[start:end + 1])
        return result

    def update_on_device(self):
        errors = ['Bad password', 'password change canceled', 'based on a dictionary word']

        # Decrypting logic
        #
        # The following commented out command will **not** work on BIG-IP versions
        # utilizing OpenSSL 1.0.11-fips (15 Jan 2015).
        #
        # The reason is because that version of OpenSSL does not support the various
        # ``-pkeyopt`` parameters shown below.
        #
        # Nevertheless, I am including it here as a possible future enhancement in
        # case the method currently in use stops working.
        #
        # This command overrides defaults provided by OpenSSL because I am not
        # sure how long the defaults will remain the defaults. Probably as long
        # as it took OpenSSL to reach 1.0...
        #
        #    openssl = [
        #        'openssl', 'pkeyutl', '-in', '/var/config/rest/downloads/{0}'.format(self.want.temp_upload_file),
        #        '-decrypt', '-inkey', '/config/ssl/ssl.key/default.key',
        #        '-pkeyopt', 'rsa_padding_mode:oaep', '-pkeyopt', 'rsa_oaep_md:sha256',
        #        '-pkeyopt', 'rsa_mgf1_md:sha256'
        #    ]
        #
        # The command we actually use is (while not recommended) also the only one
        # that works. It forgoes the usage of OAEP and uses the defaults that come
        # with OpenSSL (PKCS1v15)
        #
        # See this link for information on the parameters used
        #
        #    https://www.openssl.org/docs/manmaster/man1/pkeyutl.html
        #
        # If you change the command below, you will need to additionally change
        # how the encryption is done in ``encrypt_password_change_file()``.
        #
        openssl = [
            'openssl', 'pkeyutl', '-in', '/var/config/rest/downloads/{0}'.format(self.want.temp_upload_file),
            '-decrypt', '-inkey', '/config/ssl/ssl.key/default.key',
        ]
        cmd = '-c "{0} | tmsh modify auth password root"'.format(' '.join(openssl))

        params = dict(
            command='run',
            utilCmdArgs=cmd
        )
        uri = "https://{0}:{1}/mgmt/tm/util/bash".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
            if 'commandResult' in response:
                if any(x for x in errors if x in response['commandResult']):
                    raise F5ModuleError(response['commandResult'])
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] in [400, 403]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        return True

    def upload_to_device(self, content, name):
        """Uploads a file-like object via the REST API to a given filename

        Args:
            content: The file-like object whose content to upload
            name: The remote name of the file to store the content in. The
                  final location of the file will be in /var/config/rest/downloads.

        Returns:
            void
        """
        url = 'https://{0}:{1}/mgmt/shared/file-transfer/uploads'.format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        try:
            upload_file(self.client, url, content, name)
        except F5ModuleError:
            raise F5ModuleError(
                "Failed to upload the file."
            )

    def remove_uploaded_file_from_device(self, name):
        filepath = '/var/config/rest/downloads/{0}'.format(name)
        params = {
            "command": "run",
            "utilCmdArgs": filepath
        }
        uri = "https://{0}:{1}/mgmt/tm/util/unix-rm".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] in [400, 403]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def get_public_key_from_device(self):
        cmd = '-c "openssl rsa -in /config/ssl/ssl.key/default.key -pubout"'

        params = dict(
            command='run',
            utilCmdArgs=cmd
        )
        uri = "https://{0}:{1}/mgmt/tm/util/bash".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] in [400, 403]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'commandResult' in response:
            return response['commandResult']
        return None


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            name=dict(
                required=True,
                aliases=['username_credential']
            ),
            password_credential=dict(
                no_log=True,
            ),
            partition_access=dict(
                type='list'
            ),
            full_name=dict(),
            shell=dict(
                choices=['none', 'bash', 'tmsh']
            ),
            update_password=dict(
                default='always',
                choices=['always', 'on_create']
            ),
            state=dict(default='present', choices=['absent', 'present']),
            partition=dict(
                default='Common',
                fallback=(env_fallback, ['F5_PARTITION'])
            )
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode
    )

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
