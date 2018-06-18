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

'''

# Imports for Ansible AWX
from collections import MutableMapping
from ansible.errors import AnsibleParserError, AnsibleConnectionFailure
from ansible.module_utils.six import string_types
from ansible.module_utils._text import to_native
from ansible.parsing.utils.addresses import parse_address
from ansible.plugins.inventory import BaseFileInventoryPlugin, detect_range, expand_hostname_range

# Imports for this plugin
from distutils.version import LooseVersion
from os import environ as env
import os
import sys
import json


class InventoryModule(BaseFileInventoryPlugin):

    NAME = 'ipa'

    def __init__(self):

        super(InventoryModule, self).__init__()

        self.ipahttps = self.get_option('ipahttps')

        # Conditional imports
        if self.ipahttps:
            # Connect via HTTPS and python_freeipa
            try:
                from python_freeipa import Client
                import urllib3
            except ImportError:
                print(
                    'The ipa dynamic inventory script requires python_freeipa'
                    'to use the FreeIPA API with HTTPS authentication'
                )
        else:
            # Connect via Kerberos using ipalib
            try:
                from ipalib import api, errors, __version__ as IPA_VERSION
            except ImportError:
                print('The ipa dynamic inventory script requires ipalib for Kerberos authentication')


    def parse(
        self,
        inventory,
        loader,
        ipahttps,
        ipaserver,
        ipauser,
        ipapassword,
        ipaversion='2.228',
        cache=True
    ):
        ''' parses response from FreeIPA/API '''

        super(InventoryModule, self).parse(
            inventory,
            loader,
            ipahttps,
            ipaserver,
            ipauser,
            ipapassword,
            ipaversion
        )

        # Connect to the IPA server using the correct library
        if self.ipahttps:
            # Connect via HTTPS and python_freeipa
            try:
                self._ipaconnection = Client(
                    ipaserver,
                    version=ipaversion,
                    verify_ssl=False
                )
                self._ipaconnection.login(
                    ipauser,
                    ipapassword
                )
            except Exception as e:
                raise AnsibleConnectionFailure(e)

        else:
            # Connect via Kerberos using ipalib

            self._ipaconnection = api.bootstrap(context='cli')

            if not os.path.isdir(self._ipaconnection.env.confdir):
                print("WARNING: IPA configuration directory (%s) is missing. "
                      "Environment variable IPA_CONFDIR could be used to override "
                      "default path." % self._ipaconnection.env.confdir)

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

            if 'server' not in self._ipaconnection.env or 'domain' not in self._ipaconnection.env:
                sys.exit(
                    "ERROR: ('jsonrpc_uri' or 'xmlrpc_uri') or 'domain' are not "
                    "defined in '[global]' section of '%s' nor in '%s'." %
                    (self._ipaconnection.env.conf, self._ipaconnection.env.conf_default)
                )

            self._ipaconnection.finalize()
            try:
                self._ipaconnection.Backend.rpcclient.connect()
            except AttributeError:
                # FreeIPA < 4.0 compatibility
                self._ipaconnection.Backend.xmlclient.connect()

        hostgroups = self._get_hostgroups(ipahttps)

        try:
            data = self.loader(hostgroups, cache=False)
        except Exception as e:
            raise AnsibleParserError(e)

        if not data:
            raise AnsibleParserError('Parsed empty JSON inventory')
        elif not isinstance(data, MutableMapping):
            raise AnsibleParserError('JSON inventory has invalid structure, it should be a dictionary, got: %s' % type(data))
        elif data.get('plugin'):
            raise AnsibleParserError('Plugin configuration JSON file, not JSON inventory')

        # We expect top level keys to correspond to groups, iterate over them
        # to get host, vars and subgroups (which we iterate over recursivelly)
        if isinstance(data, MutableMapping):
            for group_name in data:
                self._parse_group(group_name, data[group_name])
        else:
            raise AnsibleParserError("Invalid data from file, expected dictionary and got:\n\n%s" % to_native(data))

    def _parse_group(self, group, group_data):

        if isinstance(group_data, MutableMapping):

            self.inventory.add_group(group)

            # make sure they are dicts
            for section in ['vars', 'children', 'hosts']:
                if section in group_data:
                    # convert strings to dicts as these are allowed
                    if isinstance(group_data[section], string_types):
                        group_data[section] = {group_data[section]: None}

                    if not isinstance(group_data[section], MutableMapping):
                        raise AnsibleParserError('Invalid "%s" entry for "%s" group, requires a dictionary, found "%s" instead.' %
                                                 (section, group, type(group_data[section])))

            for key in group_data:
                if key == 'vars':
                    for var in group_data['vars']:
                        self.inventory.set_variable(group, var, group_data['vars'][var])

                elif key == 'children':
                    for subgroup in group_data['children']:
                        self._parse_group(subgroup, group_data['children'][subgroup])
                        self.inventory.add_child(group, subgroup)

                elif key == 'hosts':
                    for host_pattern in group_data['hosts']:
                        hosts, port = self._parse_host(host_pattern)
                        self._populate_host_vars(hosts, group_data['hosts'][host_pattern] or {}, group, port)
                else:
                    self.display.warning('Skipping unexpected key (%s) in group (%s), only "vars", "children" and "hosts" are valid' % (key, group))

        else:
            self.display.warning("Skipping '%s' as this is not a valid group definition" % group)

    def _parse_host(self, host_pattern):
        '''
        Each host key can be a pattern, try to process it and add variables as needed
        '''
        (hostnames, port) = self._expand_hostpattern(host_pattern)

        return hostnames, port

    def _expand_hostpattern(self, hostpattern):
        '''
        Takes a single host pattern and returns a list of hostnames and an
        optional port number that applies to all of them.
        '''
        # Can the given hostpattern be parsed as a host with an optional port
        # specification?

        try:
            (pattern, port) = parse_address(hostpattern, allow_ranges=True)
        except Exception:
            # not a recognizable host pattern
            pattern = hostpattern
            port = None

        # Once we have separated the pattern, we expand it into list of one or
        # more hostnames, depending on whether it contains any [x:y] ranges.

        if detect_range(pattern):
            hostnames = expand_hostname_range(pattern)
        else:
            hostnames = [pattern]

        return (hostnames, port)

    def _get_hostgroups(
        self
    ):
        inventory = {}
        hostvars = {}
        result = {}

        if self.ipahttps:
            # We don't need warnings
            urllib3.disable_warnings()
            result = self._ipaconnection._request(
                'hostgroup_find',
                '',
                {'all': True, 'raw': False}
            )['result']
        else:
            result = self._ipaconnection.Command.hostgroup_find(all=True)['result']

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
                hostvars[member] = self._get_host(member, ipahttps)

        inventory['_meta'] = {'hostvars': hostvars}
        return inventory

    def _get_host(
        self,
        host
    ):
        if self.ipahttps:
            # We don't need warnings
            urllib3.disable_warnings()
            result = self._ipaconnection._request(
                'host_show',
                host,
                {'all': True, 'raw': False}
            )['result']
            if 'usercertificate' in result:
                del result['usercertificate']
        else:
            try:
                result = self._ipaconnection.Command.host_show(host)['result']
                if 'usercertificate' in result:
                    del result['usercertificate']
            except errors.NotFound as e:
                result = {}

        return result
