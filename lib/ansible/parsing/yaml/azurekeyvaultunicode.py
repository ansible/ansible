# (c) 2018, Yunge Zhu <yungez@microsoft.com>
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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import yaml

from ansible.module_utils.six import text_type
from ansible.module_utils._text import to_bytes, to_text
from ansible.parsing.azurekeyvault import get_secret
from ansible.parsing.yaml.objects import AnsibleBaseYAMLObject

class AzureKeyVaultUnicode(yaml.YAMLObject, AnsibleBaseYAMLObject):
    yaml_tag = u'!azurekeyvault'

    def __init__(self, envelope):
        '''Azure Key Vault with vault uri and secret name, secret version(optional).

        The .data attribute is a property that returns the secret value in Azure Key Vault.
        '''
        super(AzureKeyVaultUnicode, self).__init__()

        self.envelope = envelope
        tempdata = envelope.strip().split(';')

        if len(tempdata) == 2:
            secret = tempdata[1]
            tempsecret = secret.split('/')

            self.vault_uri = tempdata[0]
            self.secret_name = tempsecret[0]
            self.secret_version = tempsecret[1] if len(tempsecret) >1 else ''

    @property
    def data(self):
        if hasattr(self, 'vault_uri') and hasattr(self, 'secret_name') and hasattr(self, 'secret_name'):
            return get_secret(self.vault_uri, self.secret_name, self.secret_version)
        else:
            self.envelope

    @data.setter
    def data(self, value):
        self.envelope = value

    def __repr__(self):
        return repr(self.data)

    def __eq__(self, other):
        return self.envelope == other

    def __hash__(self):
        return id(self)

    def __ne__(self, other):
        return self.envelope != other

    def __str__(self):
        return str(self.data)

    def __unicode__(self):
        return to_text(self.data, errors='surrogate_or_strict')

    def encode(self, encoding=None, errors=None):
        return self.data.encode(encoding, errors)
