# (c) 2018, Mario Vazquez <mavazque@redhat.com>
# (c) 2012-18 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '0.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
    author:
      - Mario Vazquez (mavazque@redhat.com)
    lookup: ipa_vault
    version_added: "2.5"
    short_description: Gets info from IPA Vault
    requirements:
      - ipa client (command line utility)
    description:
      - Gets information from different types of IPA Vaults (standard, symmetric, asymmetric) and returns a list with the data gathered
    options:
      _terms:
        description: action to perform on the vault ['find', 'show', 'retrieve']
      vault_name:
        description: name of the vault to query
        default: None
      password:
        description: password to retrieve data from symmetric vaults
        default: None
      key:
        description: private key to retrieve data from asymmetric vaults
        default: None
      ipa_binary:
        description: alternative path for the ipa client binary
        default: /usr/bin/ipa
# TODO: All the stdout parsing should be re-implemented when ipa client implements json/yaml output
"""

EXAMPLES = """
- name: Query ipa for all vaults availabe for the krb token
  debug: msg="{{lookup('ipa_vault', 'find')}}"

- name: Query ipa for details about an specific vault
  debug: msg="{{lookup('ipa_vault', 'show', vault_name='ash')}}"

- name: Retrieve vault content for a symmetric vault
  debug: msg="{{lookup('ipa_vault', 'retrieve', vault_name='gary', password='fromKant0')}}"

- name: Retrieve vault content for an asymmetric vault
  debug: msg="{{lookup('ipa_vault', 'retrieve', vault_name='oak', key=vault_key)}}"
  vars:
    vault_key: "{{lookup('file', '/tmp/vault_keys.pem')}}"

- name: Retrieve vault content for a symmetric vault using a non-default location for ipa binary
  debug: msg="{{lookup('ipa_vault', 'retrieve', ipa_binary='/opt/freeipa/ipa', vault_name='brock', password='m1sty')}}"
"""

RETURN = """
  _list:
    description: Data requested
"""

import os
import base64

from ansible.plugins.lookup import LookupBase
from ansible.utils.cmd_functions import run_cmd
from ansible.errors import AnsibleError


class IPAVault(object):

    def __init__(self, ipa_cli='/usr/bin/ipa'):
        self.ipa_cli = ipa_cli
        if not os.path.isfile(self.ipa_cli):
            raise AnsibleError("IPA Client not found in the controll machine %s, install IPA Client and try againg." % self.ipa_cli)

    def _run(self, args, rc=0):
        pargs = " ".join(args)
        p = self.ipa_cli + " " + pargs
        cmd_rc, stdout, stderr = run_cmd(p)
        if cmd_rc is not rc:
            raise AnsibleError("IPA Client failed with: %s" % stderr)
        ret = self._format_stdout(stdout)
        return ret

    def _format_stdout(self, stdout):
        formatted_stdout = stdout.replace('-', '').replace(',', '').strip()
        _list = []
        temp_list = []
        ret_list = []
        last_line = len(formatted_stdout.split('\n'))
        curr_line = 0
        for line in formatted_stdout.split('\n'):
            curr_line = curr_line + 1
            item = line.strip()
            if len(item) > 0 and ":" in item:
                tmp_list = item.split(':')
                temp_list.append([tmp_list[0], tmp_list[1].strip()])
            if ((":" not in item and len(temp_list) > 0) or (":" in item and curr_line == last_line)):
                _list = {k: v for k, v in temp_list}
                temp_list = []
                ret_list.append([_list])
        return ret_list

    def got_krb_ticket(self):
        try:
            ping = self._run(["ping"])
        except AnsibleError as e:
            raise AnsibleError("IPA Client failed with: %s" % e)

    def vault_find(self, name=""):
        try:
            vault = self._run(["vault-find", str(name)])
        except AnsibleError as e:
            raise AnsibleError("IPA Client failed with: %s" % e)
        return vault

    def vault_show(self, name):
        try:
            vault = self._run(["vault-show", str(name)])
        except AnsibleError as e:
            raise AnsibleError("IPA Client failed with: %s" % e)
        return vault

    def vault_retrieve(self, name, password=None, key=None):
        try:
            vault_info = self.vault_show(str(name))
            vault_type = vault_info[0][0]['Type'].lower()
            if vault_type == "symmetric" and password is None:
                raise AnsibleError("Vault %s requires password to be retrieved" % str(name))
            if vault_type == "asymmetric" and key is None:
                raise AnsibleError("Vault %s requires private key to be retrieved" % str(name))
            if vault_type == "symmetric":
                vault = self._run(["vault-retrieve", str(name), "--password", str(password)])
            elif vault_type == "asymmetric":
                key_to_base64 = base64.b64encode(key.encode('utf-8'))
                vault = self._run(["vault-retrieve", str(name), "--private-key", key_to_base64])
            else:
                vault = self._run(["vault-retrieve", str(name)])
        except AnsibleError as e:
            raise AnsibleError("IPA Client failed with: %s" % e)
        return vault


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        vault_name = kwargs.get('vault_name', None)
        vault_key = kwargs.get('key', None)
        vault_password = kwargs.get('password', None)
        ipa_client_bin = kwargs.get('ipa_binary', '/usr/bin/ipa')
        try:
            action = terms[0].lower()
        except:
            raise AnsibleError("You must provide an action: [find show retrieve]")

        # Create the client and check that we have a valid krb tkn
        client = IPAVault(ipa_client_bin)
        client.got_krb_ticket()
        data = None
        if action == "find":
            data = client.vault_find()
        elif action == "show":
            if vault_name is not None:
                data = client.vault_show(str(vault_name))
            else:
                raise AnsibleError("Action show requires a vault name")
        elif action == "retrieve":
            if vault_name is not None:
                data = client.vault_retrieve(str(vault_name), vault_password, vault_key)
            else:
                raise AnsibleError("Action retrieve requires a vault name")
        else:
            raise AnsibleError("Unsupported action %s" % action)
        return data
