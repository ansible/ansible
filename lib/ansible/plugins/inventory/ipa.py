# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    inventory: ipa
    version_added: "2.5"
    short_description: Uses the FreeIPA/RHIdM API to populate an inventory
    description:
        - "FreeIPA/RHIdM based inventory, starts with the 'all' group and has hosts/vars/children entries."
        - Host entries can have sub-entries defined, which will be treated as variables.
        - Vars entries are normal group vars.
    notes:
        - To function it requires being whitelisted in configuration.
        - Requires the [python_freeipa](https://pypi.org/project/python-freeipa/) module
    options:
      ipahttps:
        description: toggles the use of HTTPS authentication (with `python_freeipa`) or Kerberos Authentication (with `ipalib`)
        type: boolean
        default: False
        env:
          - name: ANSIBLE_IPAHTTPS
        ini:
          - key: ipa_https
            section: defaults
          - section: inventory_ipa
            key: ipa_server
      ipaserver:
        description: the FQDN of the FreeIPA/RHIdM server for HTTPS authentication
        type: string
        default: None
        env:
          - name: ANSIBLE_IPASERVER
        ini:
          - key: ipa_server
            section: defaults
          - section: inventory_ipa
            key: ipa_server
      ipauser:
        description: an unprivileged user account from the FreeIPA/RHIdM directory for HTTPS authentication
        type: string
        default: None
        env:
          - name: ANSIBLE_IPAUSER
        ini:
          - key: ipa_user
            section: defaults
          - section: inventory_ipa
            key: ipa_user
      ipapassword:
        description: the password for the FreeIPA/RHIdM user account for HTTPS authentication
        type: string
        default: None
        env:
          - name: ANSIBLE_IPAPASSWORD
        ini:
          - key: ipa_password
            section: defaults
          - section: inventory_ipa
            key: ipa_password
      ipaversion:
        description: the FreeIPA API version for the FreeIPA/RHIdM user account for HTTPS authentication
        type: string
        default: None
        env:
          - name: ANSIBLE_IPAVERSION
        ini:
          - key: ipa_version
            section: defaults
          - section: inventory_ipa
            key: ipa_version
'''

# Imports for Ansible AWX
from collections import MutableMapping
from ansible.errors import AnsibleParserError, AnsibleConnectionFailure, AnsibleError
from ansible.module_utils.six import string_types
from ansible.module_utils._text import to_native
from ansible.parsing.utils.addresses import parse_address
from ansible.plugins.inventory import BaseInventoryPlugin, Constructable, Cacheable

# Imports for this plugin
from distutils.version import LooseVersion
from ansible.module_utils.six import iteritems
from os import environ as env
import os
import sys
import json


class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):

    NAME = 'ipa'

    def __init__(self):
        super(InventoryModule, self).__init__()

        self.ipahttps = False
        self.ipaserver = None
        self.ipauser = None
        self.ipapassword = None
        self.ipaversion = '2.228'
        self.ipaconnection = None
        self._hosts = set()


    def parse(self, inventory, loader, path, cache=True):
        ''' parses the inventory file '''

        super(InventoryModule, self).parse(inventory, loader, path)
        self._read_config_data(path)

        self.ipahttps = bool(self.get_option('ipahttps'))
        self.ipaserver = self.get_option('ipaserver')
        self.ipauser = self.get_option('ipauser')
        self.ipapassword = self.get_option('ipapassword')
        self.ipaversion = str(self.get_option('ipaversion'))

        if self.ipahttps:
            # Connect via HTTPS and python_freeipa
            try:
                from python_freeipa import Client
                import urllib3
                # We don't need warnings
                urllib3.disable_warnings()
            except ImportError:
                sys.exit(
                    'The ipa dynamic inventory script requires python_freeipa '
                    'to use the FreeIPA API with HTTPS authentication'
                )

            try:
                self.ipaconnection = Client(
                    self.ipaserver,
                    version=self.ipaversion,
                    verify_ssl=False
                )
                self.ipaconnection.login(
                    self.ipauser,
                    self.ipapassword
                )
            except Exception as e:
                raise AnsibleConnectionFailure(e)
        else:
            # Connect via Kerberos using ipalib
            try:
                from ipalib import api, errors, __version__ as IPA_VERSION
            except ImportError:
                sys.exit('The ipa dynamic inventory script requires ipalib for Kerberos authentication')

            # Connect via Kerberos using ipalib

            self.ipaconnection = api.bootstrap(context='cli')

            if not os.path.isdir(self.ipaconnection.env.confdir):
                print("WARNING: IPA configuration directory (%s) is missing. "
                      "Environment variable IPA_CONFDIR could be used to override "
                      "default path." % self.ipaconnection.env.confdir)

            if LooseVersion(IPA_VERSION) < LooseVersion('4.6.2'):
                # With ipalib < 4.6.0 'server' and 'domain' have default values
                # ('localhost:8888', 'example.com'), newer versions don't and
                # DNS autodiscovery is broken, then one of jsonrpc_uri / xmlrpc_uri is
                # required.
                # ipalib 4.6.0 is unusable (https://pagure.io/freeipa/issue/7132)
                # that's why 4.6.2 is explicitely tested.
                sys.exit(
                    "ERROR: ipalib version newer than 4.6.2 required, current version is %s" %
                    IPA_VERSION
                )

            if 'server' not in self.ipaconnection.env or 'domain' not in self.ipaconnection.env:
                sys.exit(
                    "ERROR: ('jsonrpc_uri' or 'xmlrpc_uri') or 'domain' are not "
                    "defined in '[global]' section of '%s' nor in '%s'." %
                    (self.ipaconnection.env.conf, self.ipaconnection.env.conf_default)
                )

            self.ipaconnection.finalize()
            try:
                self.ipaconnection.Backend.rpcclient.connect()
            except AttributeError:
                # FreeIPA < 4.0 compatibility
                self.ipaconnection.Backend.xmlclient.connect()

        hostgroups = self._get_hostgroups()

        if isinstance(hostgroups, MutableMapping):
            for group_name in hostgroups:
                self._parse_group(group_name, hostgroups[group_name])
        else:
            raise AnsibleParserError("Invalid data from file, expected dictionary and got:\n\n%s" % to_native(data))

    def _parse_group(self, group, data):

        self.inventory.add_group(group)

        if not isinstance(data, dict):
            data = {'hosts': data}
        # is not those subkeys, then simplified syntax, host with vars
        elif not any(k in data for k in ('hosts', 'vars', 'children')):
            data = {'hosts': [group], 'vars': data}

        if 'hosts' in data:
            if not isinstance(data['hosts'], list):
                raise AnsibleError("You defined a group '%s' with bad data for the host list:\n %s" % (group, data))

            for hostname in data['hosts']:
                self._hosts.add(hostname)
                self.inventory.add_host(hostname, group)

        if 'vars' in data:
            if not isinstance(data['vars'], dict):
                raise AnsibleError("You defined a group '%s' with bad data for variables:\n %s" % (group, data))

            for k, v in iteritems(data['vars']):
                self.inventory.set_variable(group, k, v)

        if group != '_meta' and isinstance(data, dict) and 'children' in data:
            for child_name in data['children']:
                self.inventory.add_group(child_name)
                self.inventory.add_child(group, child_name)


    def _get_hostgroups(
        self
    ):
        inventory = {}
        hostvars = {}
        result = {}

        if self.ipahttps:
            result = self.ipaconnection._request(
                'hostgroup_find',
                '',
                {'all': True, 'raw': False}
            )['result']
        else:
            result = self.ipaconnection.Command.hostgroup_find(all=True)['result']

        for hostgroup in result:
            members = []
            children = []

            if 'member_host' in hostgroup:
                members = [host for host in hostgroup['member_host']]
            if 'member_hostgroup' in hostgroup:
                children = hostgroup['member_hostgroup']
            inventory[hostgroup['cn'][0]] = {
                'hosts': [host for host in members],
                'children': children
            }

            for member in members:
                # This should actually grab the hostvars for the hosts
                hostvars[member] = self._get_host(member)

        inventory['_meta'] = {'hostvars': hostvars}
        return inventory

    def _get_host(
        self,
        host
    ):
        if self.ipahttps:
            result = self.ipaconnection._request(
                'host_show',
                host,
                {'all': True, 'raw': False}
            )['result']
            if 'usercertificate' in result:
                del result['usercertificate']
        else:
            try:
                result = self.ipaconnection.Command.host_show(host)['result']
                if 'usercertificate' in result:
                    del result['usercertificate']
            except errors.NotFound as e:
                result = {}

        return result
