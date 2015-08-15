#!/usr/bin/python

#
# Copyright (c) 2015 CenturyLink
#
# This file is part of Ansible.
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
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>
#

DOCUMENTATION = '''
module: clc_server
short_description: Create, Delete, Start and Stop servers in CenturyLink Cloud.
description:
  - An Ansible module to Create, Delete, Start and Stop servers in CenturyLink Cloud.
version_added: "2.0"
options:
  additional_disks:
    description:
      - The list of additional disks for the server
    required: False
    default: []
  add_public_ip:
    description:
      - Whether to add a public ip to the server
    required: False
    default: False
    choices: [False, True]
  alias:
    description:
      - The account alias to provision the servers under.
    required: False
    default: None
  anti_affinity_policy_id:
    description:
      - The anti-affinity policy to assign to the server. This is mutually exclusive with 'anti_affinity_policy_name'.
    required: False
    default: None
  anti_affinity_policy_name:
    description:
      - The anti-affinity policy to assign to the server. This is mutually exclusive with 'anti_affinity_policy_id'.
    required: False
    default: None
  alert_policy_id:
    description:
      - The alert policy to assign to the server. This is mutually exclusive with 'alert_policy_name'.
    required: False
    default: None
  alert_policy_name:
    description:
      - The alert policy to assign to the server. This is mutually exclusive with 'alert_policy_id'.
    required: False
    default: None
  count:
    description:
      - The number of servers to build (mutually exclusive with exact_count)
    required: False
    default: 1
  count_group:
    description:
      - Required when exact_count is specified.  The Server Group use to determine how many severs to deploy.
    required: False
    default: None
  cpu:
    description:
      - How many CPUs to provision on the server
    default: 1
    required: False
  cpu_autoscale_policy_id:
    description:
      - The autoscale policy to assign to the server.
    default: None
    required: False
  custom_fields:
    description:
      - The list of custom fields to set on the server.
    default: []
    required: False
  description:
    description:
      - The description to set for the server.
    default: None
    required: False
  exact_count:
    description:
      - Run in idempotent mode.  Will insure that this exact number of servers are running in the provided group,
        creating and deleting them to reach that count.  Requires count_group to be set.
    default: None
    required: False
  group:
    description:
      - The Server Group to create servers under.
    default: 'Default Group'
    required: False
  ip_address:
    description:
      - The IP Address for the server. One is assigned if not provided.
    default: None
    required: False
  location:
    description:
      - The Datacenter to create servers in.
    default: None
    required: False
  managed_os:
    description:
      - Whether to create the server as 'Managed' or not.
    default: False
    required: False
    choices: [True, False]
  memory:
    description:
      - Memory in GB.
    default: 1
    required: False
  name:
    description:
      - A 1 to 6 character identifier to use for the server. This is required when state is 'present'
    default: None
    required: False
  network_id:
    description:
      - The network UUID on which to create servers.
    default: None
    required: False
  packages:
    description:
      - The list of blue print packages to run on the server after its created.
    default: []
    required: False
  password:
    description:
      - Password for the administrator / root user
    default: None
    required: False
  primary_dns:
    description:
      - Primary DNS used by the server.
    default: None
    required: False
  public_ip_protocol:
    description:
      - The protocol to use for the public ip if add_public_ip is set to True.
    default: 'TCP'
    choices: ['TCP', 'UDP', 'ICMP']
    required: False
  public_ip_ports:
    description:
      - A list of ports to allow on the firewall to the servers public ip, if add_public_ip is set to True.
    default: []
    required: False
  secondary_dns:
    description:
      - Secondary DNS used by the server.
    default: None
    required: False
  server_ids:
    description:
      - Required for started, stopped, and absent states.
        A list of server Ids to insure are started, stopped, or absent.
    default: []
    required: False
  source_server_password:
    description:
      - The password for the source server if a clone is specified.
    default: None
    required: False
  state:
    description:
      - The state to insure that the provided resources are in.
    default: 'present'
    required: False
    choices: ['present', 'absent', 'started', 'stopped']
  storage_type:
    description:
      - The type of storage to attach to the server.
    default: 'standard'
    required: False
    choices: ['standard', 'hyperscale']
  template:
    description:
      - The template to use for server creation.  Will search for a template if a partial string is provided.
        This is required when state is 'present'
    default: None
    required: false
  ttl:
    description:
      - The time to live for the server in seconds.  The server will be deleted when this time expires.
    default: None
    required: False
  type:
    description:
      - The type of server to create.
    default: 'standard'
    required: False
    choices: ['standard', 'hyperscale']
  wait:
    description:
      - Whether to wait for the provisioning tasks to finish before returning.
    default: True
    required: False
    choices: [True, False]
requirements:
    - python = 2.7
    - requests >= 2.5.0
    - clc-sdk
notes:
    - To use this module, it is required to set the below environment variables which enables access to the
      Centurylink Cloud
          - CLC_V2_API_USERNAME, the account login id for the centurylink cloud
          - CLC_V2_API_PASSWORD, the account password for the centurylink cloud
    - Alternatively, the module accepts the API token and account alias. The API token can be generated using the
      CLC account login and password via the HTTP api call @ https://api.ctl.io/v2/authentication/login
          - CLC_V2_API_TOKEN, the API token generated from https://api.ctl.io/v2/authentication/login
          - CLC_ACCT_ALIAS, the account alias associated with the centurylink cloud
    - Users can set CLC_V2_API_URL to specify an endpoint for pointing to a different CLC environment.
'''

EXAMPLES = '''
# Note - You must set the CLC_V2_API_USERNAME And CLC_V2_API_PASSWD Environment variables before running these examples

- name: Provision a single Ubuntu Server
  clc_server:
    name: test
    template: ubuntu-14-64
    count: 1
    group: 'Default Group'
    state: present

- name: Ensure 'Default Group' has exactly 5 servers
  clc_server:
    name: test
    template: ubuntu-14-64
    exact_count: 5
    count_group: 'Default Group'
    group: 'Default Group'

- name: Stop a Server
  clc_server:
    server_ids: ['UC1ACCTTEST01']
    state: stopped

- name: Start a Server
  clc_server:
    server_ids: ['UC1ACCTTEST01']
    state: started

- name: Delete a Server
  clc_server:
    server_ids: ['UC1ACCTTEST01']
    state: absent
'''

__version__ = '${version}'

from time import sleep
from distutils.version import LooseVersion

try:
    import requests
except ImportError:
    REQUESTS_FOUND = False
else:
    REQUESTS_FOUND = True

#
#  Requires the clc-python-sdk.
#  sudo pip install clc-sdk
#
try:
    import clc as clc_sdk
    from clc import CLCException
    from clc import APIFailedResponse
except ImportError:
    CLC_FOUND = False
    clc_sdk = None
else:
    CLC_FOUND = True


class ClcServer:
    clc = clc_sdk

    def __init__(self, module):
        """
        Construct module
        """
        self.clc = clc_sdk
        self.module = module
        self.group_dict = {}

        if not CLC_FOUND:
            self.module.fail_json(
                msg='clc-python-sdk required for this module')
        if not REQUESTS_FOUND:
            self.module.fail_json(
                msg='requests library is required for this module')
        if requests.__version__ and LooseVersion(
                requests.__version__) < LooseVersion('2.5.0'):
            self.module.fail_json(
                msg='requests library  version should be >= 2.5.0')

        self._set_user_agent(self.clc)

    def process_request(self):
        """
        Process the request - Main Code Path
        :return: Returns with either an exit_json or fail_json
        """
        changed = False
        new_server_ids = []
        server_dict_array = []

        self._set_clc_credentials_from_env()
        self.module.params = self._validate_module_params(
            self.clc,
            self.module)
        p = self.module.params
        state = p.get('state')

        #
        #  Handle each state
        #
        partial_servers_ids = []
        if state == 'absent':
            server_ids = p['server_ids']
            if not isinstance(server_ids, list):
                return self.module.fail_json(
                    msg='server_ids needs to be a list of instances to delete: %s' %
                    server_ids)

            (changed,
             server_dict_array,
             new_server_ids) = self._delete_servers(module=self.module,
                                                    clc=self.clc,
                                                    server_ids=server_ids)

        elif state in ('started', 'stopped'):
            server_ids = p.get('server_ids')
            if not isinstance(server_ids, list):
                return self.module.fail_json(
                    msg='server_ids needs to be a list of servers to run: %s' %
                    server_ids)

            (changed,
             server_dict_array,
             new_server_ids) = self._start_stop_servers(self.module,
                                                        self.clc,
                                                        server_ids)

        elif state == 'present':
            # Changed is always set to true when provisioning new instances
            if not p.get('template'):
                return self.module.fail_json(
                    msg='template parameter is required for new instance')

            if p.get('exact_count') is None:
                (server_dict_array,
                 new_server_ids,
                 partial_servers_ids,
                 changed) = self._create_servers(self.module,
                                                 self.clc)
            else:
                (server_dict_array,
                 new_server_ids,
                 partial_servers_ids,
                 changed) = self._enforce_count(self.module,
                                                self.clc)

        self.module.exit_json(
            changed=changed,
            server_ids=new_server_ids,
            partially_created_server_ids=partial_servers_ids,
            servers=server_dict_array)

    @staticmethod
    def _define_module_argument_spec():
        """
        Define the argument spec for the ansible module
        :return: argument spec dictionary
        """
        argument_spec = dict(
            name=dict(),
            template=dict(),
            group=dict(default='Default Group'),
            network_id=dict(),
            location=dict(default=None),
            cpu=dict(default=1),
            memory=dict(default=1),
            alias=dict(default=None),
            password=dict(default=None, no_log=True),
            ip_address=dict(default=None),
            storage_type=dict(
                default='standard',
                choices=[
                    'standard',
                    'hyperscale']),
            type=dict(default='standard', choices=['standard', 'hyperscale']),
            primary_dns=dict(default=None),
            secondary_dns=dict(default=None),
            additional_disks=dict(type='list', default=[]),
            custom_fields=dict(type='list', default=[]),
            ttl=dict(default=None),
            managed_os=dict(type='bool', default=False),
            description=dict(default=None),
            source_server_password=dict(default=None),
            cpu_autoscale_policy_id=dict(default=None),
            anti_affinity_policy_id=dict(default=None),
            anti_affinity_policy_name=dict(default=None),
            alert_policy_id=dict(default=None),
            alert_policy_name=dict(default=None),
            packages=dict(type='list', default=[]),
            state=dict(
                default='present',
                choices=[
                    'present',
                    'absent',
                    'started',
                    'stopped']),
            count=dict(type='int', default=1),
            exact_count=dict(type='int', default=None),
            count_group=dict(),
            server_ids=dict(type='list', default=[]),
            add_public_ip=dict(type='bool', default=False),
            public_ip_protocol=dict(
                default='TCP',
                choices=[
                    'TCP',
                    'UDP',
                    'ICMP']),
            public_ip_ports=dict(type='list', default=[]),
            wait=dict(type='bool', default=True))

        mutually_exclusive = [
            ['exact_count', 'count'],
            ['exact_count', 'state'],
            ['anti_affinity_policy_id', 'anti_affinity_policy_name'],
            ['alert_policy_id', 'alert_policy_name'],
        ]
        return {"argument_spec": argument_spec,
                "mutually_exclusive": mutually_exclusive}

    def _set_clc_credentials_from_env(self):
        """
        Set the CLC Credentials on the sdk by reading environment variables
        :return: none
        """
        env = os.environ
        v2_api_token = env.get('CLC_V2_API_TOKEN', False)
        v2_api_username = env.get('CLC_V2_API_USERNAME', False)
        v2_api_passwd = env.get('CLC_V2_API_PASSWD', False)
        clc_alias = env.get('CLC_ACCT_ALIAS', False)
        api_url = env.get('CLC_V2_API_URL', False)

        if api_url:
            self.clc.defaults.ENDPOINT_URL_V2 = api_url

        if v2_api_token and clc_alias:
            self.clc._LOGIN_TOKEN_V2 = v2_api_token
            self.clc._V2_ENABLED = True
            self.clc.ALIAS = clc_alias
        elif v2_api_username and v2_api_passwd:
            self.clc.v2.SetCredentials(
                api_username=v2_api_username,
                api_passwd=v2_api_passwd)
        else:
            return self.module.fail_json(
                msg="You must set the CLC_V2_API_USERNAME and CLC_V2_API_PASSWD "
                    "environment variables")

    @staticmethod
    def _validate_module_params(clc, module):
        """
        Validate the module params, and lookup default values.
        :param clc: clc-sdk instance to use
        :param module: module to validate
        :return: dictionary of validated params
        """
        params = module.params
        datacenter = ClcServer._find_datacenter(clc, module)

        ClcServer._validate_types(module)
        ClcServer._validate_name(module)

        params['alias'] = ClcServer._find_alias(clc, module)
        params['cpu'] = ClcServer._find_cpu(clc, module)
        params['memory'] = ClcServer._find_memory(clc, module)
        params['description'] = ClcServer._find_description(module)
        params['ttl'] = ClcServer._find_ttl(clc, module)
        params['template'] = ClcServer._find_template_id(module, datacenter)
        params['group'] = ClcServer._find_group(module, datacenter).id
        params['network_id'] = ClcServer._find_network_id(module, datacenter)
        params['anti_affinity_policy_id'] = ClcServer._find_aa_policy_id(
            clc,
            module)
        params['alert_policy_id'] = ClcServer._find_alert_policy_id(
            clc,
            module)

        return params

    @staticmethod
    def _find_datacenter(clc, module):
        """
        Find the datacenter by calling the CLC API.
        :param clc: clc-sdk instance to use
        :param module: module to validate
        :return: clc-sdk.Datacenter instance
        """
        location = module.params.get('location')
        try:
            datacenter = clc.v2.Datacenter(location)
            return datacenter
        except CLCException:
            module.fail_json(
                msg=str(
                    "Unable to find location: {0}".format(location)))

    @staticmethod
    def _find_alias(clc, module):
        """
        Find or Validate the Account Alias by calling the CLC API
        :param clc: clc-sdk instance to use
        :param module: module to validate
        :return: clc-sdk.Account instance
        """
        alias = module.params.get('alias')
        if not alias:
            try:
                alias = clc.v2.Account.GetAlias()
            except CLCException as ex:
                module.fail_json(msg='Unable to find account alias. {0}'.format(
                    ex.message
                ))
        return alias

    @staticmethod
    def _find_cpu(clc, module):
        """
        Find or validate the CPU value by calling the CLC API
        :param clc: clc-sdk instance to use
        :param module: module to validate
        :return: Int value for CPU
        """
        cpu = module.params.get('cpu')
        group_id = module.params.get('group_id')
        alias = module.params.get('alias')
        state = module.params.get('state')

        if not cpu and state == 'present':
            group = clc.v2.Group(id=group_id,
                                 alias=alias)
            if group.Defaults("cpu"):
                cpu = group.Defaults("cpu")
            else:
                module.fail_json(
                    msg=str("Can\'t determine a default cpu value. Please provide a value for cpu."))
        return cpu

    @staticmethod
    def _find_memory(clc, module):
        """
        Find or validate the Memory value by calling the CLC API
        :param clc: clc-sdk instance to use
        :param module: module to validate
        :return: Int value for Memory
        """
        memory = module.params.get('memory')
        group_id = module.params.get('group_id')
        alias = module.params.get('alias')
        state = module.params.get('state')

        if not memory and state == 'present':
            group = clc.v2.Group(id=group_id,
                                 alias=alias)
            if group.Defaults("memory"):
                memory = group.Defaults("memory")
            else:
                module.fail_json(msg=str(
                    "Can\'t determine a default memory value. Please provide a value for memory."))
        return memory

    @staticmethod
    def _find_description(module):
        """
        Set the description module param to name if description is blank
        :param module: the module to validate
        :return: string description
        """
        description = module.params.get('description')
        if not description:
            description = module.params.get('name')
        return description

    @staticmethod
    def _validate_types(module):
        """
        Validate that type and storage_type are set appropriately, and fail if not
        :param module: the module to validate
        :return: none
        """
        state = module.params.get('state')
        server_type = module.params.get(
            'type').lower() if module.params.get('type') else None
        storage_type = module.params.get(
            'storage_type').lower() if module.params.get('storage_type') else None

        if state == "present":
            if server_type == "standard" and storage_type not in (
                    "standard", "premium"):
                module.fail_json(
                    msg=str("Standard VMs must have storage_type = 'standard' or 'premium'"))

            if server_type == "hyperscale" and storage_type != "hyperscale":
                module.fail_json(
                    msg=str("Hyperscale VMs must have storage_type = 'hyperscale'"))

    @staticmethod
    def _validate_name(module):
        """
        Validate that name is the correct length if provided, fail if it's not
        :param module: the module to validate
        :return: none
        """
        server_name = module.params.get('name')
        state = module.params.get('state')

        if state == 'present' and (
                len(server_name) < 1 or len(server_name) > 6):
            module.fail_json(msg=str(
                "When state = 'present', name must be a string with a minimum length of 1 and a maximum length of 6"))

    @staticmethod
    def _find_ttl(clc, module):
        """
        Validate that TTL is > 3600 if set, and fail if not
        :param clc: clc-sdk instance to use
        :param module: module to validate
        :return: validated ttl
        """
        ttl = module.params.get('ttl')

        if ttl:
            if ttl <= 3600:
                return module.fail_json(msg=str("Ttl cannot be <= 3600"))
            else:
                ttl = clc.v2.time_utils.SecondsToZuluTS(int(time.time()) + ttl)
        return ttl

    @staticmethod
    def _find_template_id(module, datacenter):
        """
        Find the template id by calling the CLC API.
        :param module: the module to validate
        :param datacenter: the datacenter to search for the template
        :return: a valid clc template id
        """
        lookup_template = module.params.get('template')
        state = module.params.get('state')
        result = None

        if state == 'present':
            try:
                result = datacenter.Templates().Search(lookup_template)[0].id
            except CLCException:
                module.fail_json(
                    msg=str(
                        "Unable to find a template: " +
                        lookup_template +
                        " in location: " +
                        datacenter.id))
        return result

    @staticmethod
    def _find_network_id(module, datacenter):
        """
        Validate the provided network id or return a default.
        :param module: the module to validate
        :param datacenter: the datacenter to search for a network id
        :return: a valid network id
        """
        network_id = module.params.get('network_id')

        if not network_id:
            try:
                network_id = datacenter.Networks().networks[0].id
                # -- added for clc-sdk 2.23 compatibility
                # datacenter_networks = clc_sdk.v2.Networks(
                #   networks_lst=datacenter._DeploymentCapabilities()['deployableNetworks'])
                # network_id = datacenter_networks.networks[0].id
                # -- end
            except CLCException:
                module.fail_json(
                    msg=str(
                        "Unable to find a network in location: " +
                        datacenter.id))

        return network_id

    @staticmethod
    def _find_aa_policy_id(clc, module):
        """
        Validate if the anti affinity policy exist for the given name and throw error if not
        :param clc: the clc-sdk instance
        :param module: the module to validate
        :return: aa_policy_id: the anti affinity policy id of the given name.
        """
        aa_policy_id = module.params.get('anti_affinity_policy_id')
        aa_policy_name = module.params.get('anti_affinity_policy_name')
        if not aa_policy_id and aa_policy_name:
            alias = module.params.get('alias')
            aa_policy_id = ClcServer._get_anti_affinity_policy_id(
                clc,
                module,
                alias,
                aa_policy_name)
            if not aa_policy_id:
                module.fail_json(
                    msg='No anti affinity policy was found with policy name : %s' % aa_policy_name)
        return aa_policy_id

    @staticmethod
    def _find_alert_policy_id(clc, module):
        """
        Validate if the alert policy exist for the given name and throw error if not
        :param clc: the clc-sdk instance
        :param module: the module to validate
        :return: alert_policy_id: the alert policy id of the given name.
        """
        alert_policy_id = module.params.get('alert_policy_id')
        alert_policy_name = module.params.get('alert_policy_name')
        if not alert_policy_id and alert_policy_name:
            alias = module.params.get('alias')
            alert_policy_id = ClcServer._get_alert_policy_id_by_name(
                clc=clc,
                module=module,
                alias=alias,
                alert_policy_name=alert_policy_name
            )
            if not alert_policy_id:
                module.fail_json(
                    msg='No alert policy exist with name : %s' % alert_policy_name)
        return alert_policy_id

    def _create_servers(self, module, clc, override_count=None):
        """
        Create New Servers in CLC cloud
        :param module: the AnsibleModule object
        :param clc: the clc-sdk instance to use
        :return: a list of dictionaries with server information about the servers that were created
        """
        p = module.params
        request_list = []
        servers = []
        server_dict_array = []
        created_server_ids = []
        partial_created_servers_ids = []

        add_public_ip = p.get('add_public_ip')
        public_ip_protocol = p.get('public_ip_protocol')
        public_ip_ports = p.get('public_ip_ports')

        params = {
            'name': p.get('name'),
            'template': p.get('template'),
            'group_id': p.get('group'),
            'network_id': p.get('network_id'),
            'cpu': p.get('cpu'),
            'memory': p.get('memory'),
            'alias': p.get('alias'),
            'password': p.get('password'),
            'ip_address': p.get('ip_address'),
            'storage_type': p.get('storage_type'),
            'type': p.get('type'),
            'primary_dns': p.get('primary_dns'),
            'secondary_dns': p.get('secondary_dns'),
            'additional_disks': p.get('additional_disks'),
            'custom_fields': p.get('custom_fields'),
            'ttl': p.get('ttl'),
            'managed_os': p.get('managed_os'),
            'description': p.get('description'),
            'source_server_password': p.get('source_server_password'),
            'cpu_autoscale_policy_id': p.get('cpu_autoscale_policy_id'),
            'anti_affinity_policy_id': p.get('anti_affinity_policy_id'),
            'packages': p.get('packages')
        }

        count = override_count if override_count else p.get('count')

        changed = False if count == 0 else True

        if not changed:
            return server_dict_array, created_server_ids, partial_created_servers_ids, changed
        for i in range(0, count):
            if not module.check_mode:
                req = self._create_clc_server(clc=clc,
                                              module=module,
                                              server_params=params)
                server = req.requests[0].Server()
                request_list.append(req)
                servers.append(server)

        self._wait_for_requests(module, request_list)
        self._refresh_servers(module, servers)

        ip_failed_servers = self._add_public_ip_to_servers(
            module=module,
            should_add_public_ip=add_public_ip,
            servers=servers,
            public_ip_protocol=public_ip_protocol,
            public_ip_ports=public_ip_ports)
        ap_failed_servers = self._add_alert_policy_to_servers(clc=clc,
                                                              module=module,
                                                              servers=servers)

        for server in servers:
            if server in ip_failed_servers or server in ap_failed_servers:
                partial_created_servers_ids.append(server.id)
            else:
                # reload server details
                server = clc.v2.Server(server.id)
                server.data['ipaddress'] = server.details[
                    'ipAddresses'][0]['internal']

                if add_public_ip and len(server.PublicIPs().public_ips) > 0:
                    server.data['publicip'] = str(
                        server.PublicIPs().public_ips[0])
                created_server_ids.append(server.id)
            server_dict_array.append(server.data)

        return server_dict_array, created_server_ids, partial_created_servers_ids, changed

    def _enforce_count(self, module, clc):
        """
        Enforce that there is the right number of servers in the provided group.
        Starts or stops servers as necessary.
        :param module: the AnsibleModule object
        :param clc: the clc-sdk instance to use
        :return: a list of dictionaries with server information about the servers that were created or deleted
        """
        p = module.params
        changed = False
        count_group = p.get('count_group')
        datacenter = ClcServer._find_datacenter(clc, module)
        exact_count = p.get('exact_count')
        server_dict_array = []
        partial_servers_ids = []
        changed_server_ids = []

        # fail here if the exact count was specified without filtering
        # on a group, as this may lead to a undesired removal of instances
        if exact_count and count_group is None:
            return module.fail_json(
                msg="you must use the 'count_group' option with exact_count")

        servers, running_servers = ClcServer._find_running_servers_by_group(
            module, datacenter, count_group)

        if len(running_servers) == exact_count:
            changed = False

        elif len(running_servers) < exact_count:
            to_create = exact_count - len(running_servers)
            server_dict_array, changed_server_ids, partial_servers_ids, changed \
                = self._create_servers(module, clc, override_count=to_create)

            for server in server_dict_array:
                running_servers.append(server)

        elif len(running_servers) > exact_count:
            to_remove = len(running_servers) - exact_count
            all_server_ids = sorted([x.id for x in running_servers])
            remove_ids = all_server_ids[0:to_remove]

            (changed, server_dict_array, changed_server_ids) \
                = ClcServer._delete_servers(module, clc, remove_ids)

        return server_dict_array, changed_server_ids, partial_servers_ids, changed

    @staticmethod
    def _wait_for_requests(module, request_list):
        """
        Block until server provisioning requests are completed.
        :param module: the AnsibleModule object
        :param request_list: a list of clc-sdk.Request instances
        :return: none
        """
        wait = module.params.get('wait')
        if wait:
            # Requests.WaitUntilComplete() returns the count of failed requests
            failed_requests_count = sum(
                [request.WaitUntilComplete() for request in request_list])

            if failed_requests_count > 0:
                module.fail_json(
                    msg='Unable to process server request')

    @staticmethod
    def _refresh_servers(module, servers):
        """
        Loop through a list of servers and refresh them.
        :param module: the AnsibleModule object
        :param servers: list of clc-sdk.Server instances to refresh
        :return: none
        """
        for server in servers:
            try:
                server.Refresh()
            except CLCException as ex:
                module.fail_json(msg='Unable to refresh the server {0}. {1}'.format(
                    server.id, ex.message
                ))

    @staticmethod
    def _add_public_ip_to_servers(
            module,
            should_add_public_ip,
            servers,
            public_ip_protocol,
            public_ip_ports):
        """
        Create a public IP for servers
        :param module: the AnsibleModule object
        :param should_add_public_ip: boolean - whether or not to provision a public ip for servers.  Skipped if False
        :param servers: List of servers to add public ips to
        :param public_ip_protocol: a protocol to allow for the public ips
        :param public_ip_ports: list of ports to allow for the public ips
        :return: none
        """
        failed_servers = []
        if not should_add_public_ip:
            return failed_servers

        ports_lst = []
        request_list = []
        server = None

        for port in public_ip_ports:
            ports_lst.append(
                {'protocol': public_ip_protocol, 'port': port})
        try:
            if not module.check_mode:
                for server in servers:
                    request = server.PublicIPs().Add(ports_lst)
                    request_list.append(request)
        except APIFailedResponse:
            failed_servers.append(server)
        ClcServer._wait_for_requests(module, request_list)
        return failed_servers

    @staticmethod
    def _add_alert_policy_to_servers(clc, module, servers):
        """
        Associate the alert policy to servers
        :param clc: the clc-sdk instance to use
        :param module: the AnsibleModule object
        :param servers: List of servers to add alert policy to
        :return: failed_servers: the list of servers which failed while associating alert policy
        """
        failed_servers = []
        p = module.params
        alert_policy_id = p.get('alert_policy_id')
        alias = p.get('alias')

        if alert_policy_id and not module.check_mode:
            for server in servers:
                try:
                    ClcServer._add_alert_policy_to_server(
                        clc=clc,
                        alias=alias,
                        server_id=server.id,
                        alert_policy_id=alert_policy_id)
                except CLCException:
                    failed_servers.append(server)
        return failed_servers

    @staticmethod
    def _add_alert_policy_to_server(
            clc, alias, server_id, alert_policy_id):
        """
        Associate an alert policy to a clc server
        :param clc: the clc-sdk instance to use
        :param alias: the clc account alias
        :param server_id: The clc server id
        :param alert_policy_id: the alert policy id to be associated to the server
        :return: none
        """
        try:
            clc.v2.API.Call(
                method='POST',
                url='servers/%s/%s/alertPolicies' % (alias, server_id),
                payload=json.dumps(
                    {
                        'id': alert_policy_id
                    }))
        except APIFailedResponse as e:
            raise CLCException(
                'Failed to associate alert policy to the server : {0} with Error {1}'.format(
                    server_id, str(e.response_text)))

    @staticmethod
    def _get_alert_policy_id_by_name(clc, module, alias, alert_policy_name):
        """
        Returns the alert policy id for the given alert policy name
        :param clc: the clc-sdk instance to use
        :param module: the AnsibleModule object
        :param alias: the clc account alias
        :param alert_policy_name: the name of the alert policy
        :return: alert_policy_id: the alert policy id
        """
        alert_policy_id = None
        policies = clc.v2.API.Call('GET', '/v2/alertPolicies/%s' % alias)
        if not policies:
            return alert_policy_id
        for policy in policies.get('items'):
            if policy.get('name') == alert_policy_name:
                if not alert_policy_id:
                    alert_policy_id = policy.get('id')
                else:
                    return module.fail_json(
                        msg='multiple alert policies were found with policy name : %s' % alert_policy_name)
        return alert_policy_id

    @staticmethod
    def _delete_servers(module, clc, server_ids):
        """
        Delete the servers on the provided list
        :param module: the AnsibleModule object
        :param clc: the clc-sdk instance to use
        :param server_ids: list of servers to delete
        :return: a list of dictionaries with server information about the servers that were deleted
        """
        terminated_server_ids = []
        server_dict_array = []
        request_list = []

        if not isinstance(server_ids, list) or len(server_ids) < 1:
            return module.fail_json(
                msg='server_ids should be a list of servers, aborting')

        servers = clc.v2.Servers(server_ids).Servers()
        for server in servers:
            if not module.check_mode:
                request_list.append(server.Delete())
        ClcServer._wait_for_requests(module, request_list)

        for server in servers:
            terminated_server_ids.append(server.id)

        return True, server_dict_array, terminated_server_ids

    @staticmethod
    def _start_stop_servers(module, clc, server_ids):
        """
        Start or Stop the servers on the provided list
        :param module: the AnsibleModule object
        :param clc: the clc-sdk instance to use
        :param server_ids: list of servers to start or stop
        :return: a list of dictionaries with server information about the servers that were started or stopped
        """
        p = module.params
        state = p.get('state')
        changed = False
        changed_servers = []
        server_dict_array = []
        result_server_ids = []
        request_list = []

        if not isinstance(server_ids, list) or len(server_ids) < 1:
            return module.fail_json(
                msg='server_ids should be a list of servers, aborting')

        servers = clc.v2.Servers(server_ids).Servers()
        for server in servers:
            if server.powerState != state:
                changed_servers.append(server)
                if not module.check_mode:
                    request_list.append(
                        ClcServer._change_server_power_state(
                            module,
                            server,
                            state))
                changed = True

        ClcServer._wait_for_requests(module, request_list)
        ClcServer._refresh_servers(module, changed_servers)

        for server in set(changed_servers + servers):
            try:
                server.data['ipaddress'] = server.details[
                    'ipAddresses'][0]['internal']
                server.data['publicip'] = str(
                    server.PublicIPs().public_ips[0])
            except (KeyError, IndexError):
                pass

            server_dict_array.append(server.data)
            result_server_ids.append(server.id)

        return changed, server_dict_array, result_server_ids

    @staticmethod
    def _change_server_power_state(module, server, state):
        """
        Change the server powerState
        :param module: the module to check for intended state
        :param server: the server to start or stop
        :param state: the intended powerState for the server
        :return: the request object from clc-sdk call
        """
        result = None
        try:
            if state == 'started':
                result = server.PowerOn()
            else:
                result = server.PowerOff()
        except CLCException:
            module.fail_json(
                msg='Unable to change power state for server {0}'.format(
                    server.id))
        return result

    @staticmethod
    def _find_running_servers_by_group(module, datacenter, count_group):
        """
        Find a list of running servers in the provided group
        :param module: the AnsibleModule object
        :param datacenter: the clc-sdk.Datacenter instance to use to lookup the group
        :param count_group: the group to count the servers
        :return: list of servers, and list of running servers
        """
        group = ClcServer._find_group(
            module=module,
            datacenter=datacenter,
            lookup_group=count_group)

        servers = group.Servers().Servers()
        running_servers = []

        for server in servers:
            if server.status == 'active' and server.powerState == 'started':
                running_servers.append(server)

        return servers, running_servers

    @staticmethod
    def _find_group(module, datacenter, lookup_group=None):
        """
        Find a server group in a datacenter by calling the CLC API
        :param module: the AnsibleModule instance
        :param datacenter: clc-sdk.Datacenter instance to search for the group
        :param lookup_group: string name of the group to search for
        :return: clc-sdk.Group instance
        """
        if not lookup_group:
            lookup_group = module.params.get('group')
        try:
            return datacenter.Groups().Get(lookup_group)
        except CLCException:
            pass

        # The search above only acts on the main
        result = ClcServer._find_group_recursive(
            module,
            datacenter.Groups(),
            lookup_group)

        if result is None:
            module.fail_json(
                msg=str(
                    "Unable to find group: " +
                    lookup_group +
                    " in location: " +
                    datacenter.id))

        return result

    @staticmethod
    def _find_group_recursive(module, group_list, lookup_group):
        """
        Find a server group by recursively walking the tree
        :param module: the AnsibleModule instance to use
        :param group_list: a list of groups to search
        :param lookup_group: the group to look for
        :return: list of groups
        """
        result = None
        for group in group_list.groups:
            subgroups = group.Subgroups()
            try:
                return subgroups.Get(lookup_group)
            except CLCException:
                result = ClcServer._find_group_recursive(
                    module,
                    subgroups,
                    lookup_group)

            if result is not None:
                break

        return result

    @staticmethod
    def _create_clc_server(
            clc,
            module,
            server_params):
        """
        Call the CLC Rest API to Create a Server
        :param clc: the clc-python-sdk instance to use
        :param module: the AnsibleModule instance to use
        :param server_params: a dictionary of params to use to create the servers
        :return: clc-sdk.Request object linked to the queued server request
        """

        try:
            res = clc.v2.API.Call(
                method='POST',
                url='servers/%s' %
                (server_params.get('alias')),
                payload=json.dumps(
                    {
                        'name': server_params.get('name'),
                        'description': server_params.get('description'),
                        'groupId': server_params.get('group_id'),
                        'sourceServerId': server_params.get('template'),
                        'isManagedOS': server_params.get('managed_os'),
                        'primaryDNS': server_params.get('primary_dns'),
                        'secondaryDNS': server_params.get('secondary_dns'),
                        'networkId': server_params.get('network_id'),
                        'ipAddress': server_params.get('ip_address'),
                        'password': server_params.get('password'),
                        'sourceServerPassword': server_params.get('source_server_password'),
                        'cpu': server_params.get('cpu'),
                        'cpuAutoscalePolicyId': server_params.get('cpu_autoscale_policy_id'),
                        'memoryGB': server_params.get('memory'),
                        'type': server_params.get('type'),
                        'storageType': server_params.get('storage_type'),
                        'antiAffinityPolicyId': server_params.get('anti_affinity_policy_id'),
                        'customFields': server_params.get('custom_fields'),
                        'additionalDisks': server_params.get('additional_disks'),
                        'ttl': server_params.get('ttl'),
                        'packages': server_params.get('packages')}))

            result = clc.v2.Requests(res)
        except APIFailedResponse as ex:
            return module.fail_json(msg='Unable to create the server: {0}. {1}'.format(
                server_params.get('name'),
                ex.response_text
            ))

        #
        # Patch the Request object so that it returns a valid server

        # Find the server's UUID from the API response
        server_uuid = [obj['id']
                       for obj in res['links'] if obj['rel'] == 'self'][0]

        # Change the request server method to a _find_server_by_uuid closure so
        # that it will work
        result.requests[0].Server = lambda: ClcServer._find_server_by_uuid_w_retry(
            clc,
            module,
            server_uuid,
            server_params.get('alias'))

        return result

    @staticmethod
    def _get_anti_affinity_policy_id(clc, module, alias, aa_policy_name):
        """
        retrieves the anti affinity policy id of the server based on the name of the policy
        :param clc: the clc-sdk instance to use
        :param module: the AnsibleModule object
        :param alias: the CLC account alias
        :param aa_policy_name: the anti affinity policy name
        :return: aa_policy_id: The anti affinity policy id
        """
        aa_policy_id = None
        try:
            aa_policies = clc.v2.API.Call(method='GET',
                                          url='antiAffinityPolicies/%s' % alias)
        except APIFailedResponse as ex:
            return module.fail_json(msg='Unable to fetch anti affinity policies for account: {0}. {1}'.format(
                alias, ex.response_text))
        for aa_policy in aa_policies.get('items'):
            if aa_policy.get('name') == aa_policy_name:
                if not aa_policy_id:
                    aa_policy_id = aa_policy.get('id')
                else:
                    return module.fail_json(
                        msg='multiple anti affinity policies were found with policy name : %s' % aa_policy_name)
        return aa_policy_id

    #
    #  This is the function that gets patched to the Request.server object using a lamda closure
    #

    @staticmethod
    def _find_server_by_uuid_w_retry(
            clc, module, svr_uuid, alias=None, retries=5, back_out=2):
        """
        Find the clc server by the UUID returned from the provisioning request.  Retry the request if a 404 is returned.
        :param clc: the clc-sdk instance to use
        :param module: the AnsibleModule object
        :param svr_uuid: UUID of the server
        :param retries: the number of retry attempts to make prior to fail. default is 5
        :param alias: the Account Alias to search
        :return: a clc-sdk.Server instance
        """
        if not alias:
            alias = clc.v2.Account.GetAlias()

        # Wait and retry if the api returns a 404
        while True:
            retries -= 1
            try:
                server_obj = clc.v2.API.Call(
                    method='GET', url='servers/%s/%s?uuid=true' %
                    (alias, svr_uuid))
                server_id = server_obj['id']
                server = clc.v2.Server(
                    id=server_id,
                    alias=alias,
                    server_obj=server_obj)
                return server

            except APIFailedResponse as e:
                if e.response_status_code != 404:
                    return module.fail_json(
                        msg='A failure response was received from CLC API when '
                        'attempting to get details for a server:  UUID=%s, Code=%i, Message=%s' %
                        (svr_uuid, e.response_status_code, e.message))
                if retries == 0:
                    return module.fail_json(
                        msg='Unable to reach the CLC API after 5 attempts')
                sleep(back_out)
                back_out *= 2

    @staticmethod
    def _set_user_agent(clc):
        if hasattr(clc, 'SetRequestsSession'):
            agent_string = "ClcAnsibleModule/" + __version__
            ses = requests.Session()
            ses.headers.update({"Api-Client": agent_string})
            ses.headers['User-Agent'] += " " + agent_string
            clc.SetRequestsSession(ses)


def main():
    """
    The main function.  Instantiates the module and calls process_request.
    :return: none
    """
    argument_dict = ClcServer._define_module_argument_spec()
    module = AnsibleModule(supports_check_mode=True, **argument_dict)
    clc_server = ClcServer(module)
    clc_server.process_request()

from ansible.module_utils.basic import *  # pylint: disable=W0614
if __name__ == '__main__':
    main()
