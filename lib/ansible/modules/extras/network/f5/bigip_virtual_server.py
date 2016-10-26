#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Etienne Carriere <etienne.carriere@gmail.com>
#
# This file is part of Ansible
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

DOCUMENTATION = '''
---
module: bigip_virtual_server
short_description: "Manages F5 BIG-IP LTM virtual servers"
description:
  - "Manages F5 BIG-IP LTM virtual servers via iControl SOAP API"
version_added: "2.1"
author:
  - Etienne Carriere (@Etienne-Carriere)
  - Tim Rupp (@caphrim007)
notes:
  - "Requires BIG-IP software version >= 11"
  - "F5 developed module 'bigsuds' required (see http://devcentral.f5.com)"
  - "Best run as a local_action in your playbook"
requirements:
  - bigsuds
options:
  state:
    description:
      - Virtual Server state
      - Absent, delete the VS if present
      - C(present) (and its synonym enabled), create if needed the VS and set
        state to enabled
      - C(disabled), create if needed the VS and set state to disabled
    required: false
    default: present
    choices:
      - present
      - absent
      - enabled
      - disabled
    aliases: []
  partition:
    description:
      - Partition
    required: false
    default: 'Common'
  name:
    description:
      - Virtual server name
    required: true
    aliases:
      - vs
  destination:
    description:
      - Destination IP of the virtual server (only host is currently supported).
        Required when state=present and vs does not exist.
    required: true
    aliases:
      - address
      - ip
  port:
    description:
      - Port of the virtual server . Required when state=present and vs does not exist
    required: false
    default: None
  all_profiles:
    description:
      - List of all Profiles (HTTP,ClientSSL,ServerSSL,etc) that must be used
        by the virtual server
    required: false
    default: None
  all_rules:
    version_added: "2.2"
    description:
      - List of rules to be applied in priority order
    required: false
    default: None
  enabled_vlans:
    version_added: "2.2"
    description:
      - List of vlans to be enabled. When a VLAN named C(ALL) is used, all
        VLANs will be allowed.
    required: false
    default: None
  pool:
    description:
      - Default pool for the virtual server
    required: false
    default: None
  snat:
    description:
      - Source network address policy
    required: false
    choices:
      - None
      - Automap
      - Name of a SNAT pool (eg "/Common/snat_pool_name") to enable SNAT with the specific pool
    default: None
  default_persistence_profile:
    description:
      - Default Profile which manages the session persistence
    required: false
    default: None
  route_advertisement_state:
    description:
      - Enable route advertisement for destination
    required: false
    default: disabled
    version_added: "2.3"
  description:
    description:
      - Virtual server description
    required: false
    default: None
extends_documentation_fragment: f5
'''

EXAMPLES = '''
- name: Add virtual server
  bigip_virtual_server:
      server: lb.mydomain.net
      user: admin
      password: secret
      state: present
      partition: MyPartition
      name: myvirtualserver
      destination: "{{ ansible_default_ipv4['address'] }}"
      port: 443
      pool: "{{ mypool }}"
      snat: Automap
      description: Test Virtual Server
      all_profiles:
          - http
          - clientssl
      enabled_vlans:
          - /Common/vlan2
  delegate_to: localhost

- name: Modify Port of the Virtual Server
  bigip_virtual_server:
      server: lb.mydomain.net
      user: admin
      password: secret
      state: present
      partition: MyPartition
      name: myvirtualserver
      port: 8080
  delegate_to: localhost

- name: Delete virtual server
  bigip_virtual_server:
      server: lb.mydomain.net
      user: admin
      password: secret
      state: absent
      partition: MyPartition
      name: myvirtualserver
  delegate_to: localhost
'''

RETURN = '''
---
deleted:
    description: Name of a virtual server that was deleted
    returned: changed
    type: string
    sample: "my-virtual-server"
'''


# map of state values
STATES = {
    'enabled': 'STATE_ENABLED',
    'disabled': 'STATE_DISABLED'
}

STATUSES = {
    'enabled': 'SESSION_STATUS_ENABLED',
    'disabled': 'SESSION_STATUS_DISABLED',
    'offline': 'SESSION_STATUS_FORCED_DISABLED'
}


def vs_exists(api, vs):
    # hack to determine if pool exists
    result = False
    try:
        api.LocalLB.VirtualServer.get_object_status(virtual_servers=[vs])
        result = True
    except bigsuds.OperationFailed as e:
        if "was not found" in str(e):
            result = False
        else:
            # genuine exception
            raise
    return result


def vs_create(api, name, destination, port, pool):
    _profiles = [[{'profile_context': 'PROFILE_CONTEXT_TYPE_ALL', 'profile_name': 'tcp'}]]
    created = False
    # a bit of a hack to handle concurrent runs of this module.
    # even though we've checked the vs doesn't exist,
    # it may exist by the time we run create_vs().
    # this catches the exception and does something smart
    # about it!
    try:
        api.LocalLB.VirtualServer.create(
            definitions=[{'name': [name], 'address': [destination], 'port': port, 'protocol': 'PROTOCOL_TCP'}],
            wildmasks=['255.255.255.255'],
            resources=[{'type': 'RESOURCE_TYPE_POOL', 'default_pool_name': pool}],
            profiles=_profiles)
        created = True
        return created
    except bigsuds.OperationFailed as e:
        if "already exists" not in str(e):
            raise Exception('Error on creating Virtual Server : %s' % e)


def vs_remove(api, name):
    api.LocalLB.VirtualServer.delete_virtual_server(
        virtual_servers=[name]
    )


def get_rules(api, name):
    return api.LocalLB.VirtualServer.get_rule(
        virtual_servers=[name]
    )[0]


def set_rules(api, name, rules_list):
    updated = False
    if rules_list is None:
        return False
    rules_list = list(enumerate(rules_list))
    try:
        current_rules = map(lambda x: (x['priority'], x['rule_name']), get_rules(api, name))
        to_add_rules = []
        for i, x in rules_list:
            if (i, x) not in current_rules:
                to_add_rules.append({'priority': i, 'rule_name': x})
        to_del_rules = []
        for i, x in current_rules:
            if (i, x) not in rules_list:
                to_del_rules.append({'priority': i, 'rule_name': x})
        if len(to_del_rules) > 0:
            api.LocalLB.VirtualServer.remove_rule(
                virtual_servers=[name],
                rules=[to_del_rules]
            )
            updated = True
        if len(to_add_rules) > 0:
            api.LocalLB.VirtualServer.add_rule(
                virtual_servers=[name],
                rules=[to_add_rules]
            )
            updated = True
        return updated
    except bigsuds.OperationFailed as e:
        raise Exception('Error on setting rules : %s' % e)


def get_profiles(api, name):
    return api.LocalLB.VirtualServer.get_profile(
        virtual_servers=[name]
    )[0]


def set_profiles(api, name, profiles_list):
    updated = False
    try:
        if profiles_list is None:
            return False
        current_profiles = list(map(lambda x: x['profile_name'], get_profiles(api, name)))
        to_add_profiles = []
        for x in profiles_list:
            if x not in current_profiles:
                to_add_profiles.append({'profile_context': 'PROFILE_CONTEXT_TYPE_ALL', 'profile_name': x})
        to_del_profiles = []
        for x in current_profiles:
            if (x not in profiles_list) and (x != "/Common/tcp"):
                to_del_profiles.append({'profile_context': 'PROFILE_CONTEXT_TYPE_ALL', 'profile_name': x})
        if len(to_del_profiles) > 0:
            api.LocalLB.VirtualServer.remove_profile(
                virtual_servers=[name],
                profiles=[to_del_profiles]
            )
            updated = True
        if len(to_add_profiles) > 0:
            api.LocalLB.VirtualServer.add_profile(
                virtual_servers=[name],
                profiles=[to_add_profiles]
            )
            updated = True
        return updated
    except bigsuds.OperationFailed as e:
        raise Exception('Error on setting profiles : %s' % e)


def get_vlan(api, name):
    return api.LocalLB.VirtualServer.get_vlan(
        virtual_servers=[name]
    )[0]


def set_enabled_vlans(api, name, vlans_enabled_list):
    updated = False
    to_add_vlans = []
    try:
        if vlans_enabled_list is None:
            return updated
        current_vlans = get_vlan(api, name)

        # Set allowed list back to default ("all")
        #
        # This case allows you to undo what you may have previously done.
        # The default case is "All VLANs and Tunnels". This case will handle
        # that situation.
        if 'ALL' in vlans_enabled_list:
            # The user is coming from a situation where they previously
            # were specifying a list of allowed VLANs
            if len(current_vlans['vlans']) > 0 or \
               current_vlans['state'] is "STATE_ENABLED":
                api.LocalLB.VirtualServer.set_vlan(
                    virtual_servers=[name],
                    vlans=[{'state': 'STATE_DISABLED', 'vlans': []}]
                )
                updated = True
        else:
            if current_vlans['state'] is "STATE_DISABLED":
                to_add_vlans = vlans_enabled_list
            else:
                for vlan in vlans_enabled_list:
                    if vlan not in current_vlans['vlans']:
                        updated = True
                        to_add_vlans = vlans_enabled_list
                        break
            if updated:
                api.LocalLB.VirtualServer.set_vlan(
                    virtual_servers=[name],
                    vlans=[{
                        'state': 'STATE_ENABLED',
                        'vlans': [to_add_vlans]
                    }]
                )

        return updated
    except bigsuds.OperationFailed as e:
        raise Exception('Error on setting enabled vlans : %s' % e)


def set_snat(api, name, snat):
    updated = False
    try:
        current_state = get_snat_type(api, name)
        current_snat_pool = get_snat_pool(api, name)
        if snat is None:
            return updated
        elif snat == 'None' and current_state != 'SRC_TRANS_NONE':
            api.LocalLB.VirtualServer.set_source_address_translation_none(
                virtual_servers=[name]
            )
            updated = True
        elif snat == 'Automap' and current_state != 'SRC_TRANS_AUTOMAP':
            api.LocalLB.VirtualServer.set_source_address_translation_automap(
                virtual_servers=[name]
            )
            updated = True
        elif snat_settings_need_updating(snat, current_state, current_snat_pool):
            api.LocalLB.VirtualServer.set_source_address_translation_snat_pool(
                virtual_servers=[name],
                pools=[snat]
            )
        return updated
    except bigsuds.OperationFailed as e:
        raise Exception('Error on setting snat : %s' % e)


def get_snat_type(api, name):
    return api.LocalLB.VirtualServer.get_source_address_translation_type(
        virtual_servers=[name]
    )[0]


def get_snat_pool(api, name):
    return api.LocalLB.VirtualServer.get_source_address_translation_snat_pool(
        virtual_servers=[name]
    )[0]


def snat_settings_need_updating(snat, current_state, current_snat_pool):
    if snat == 'None' or snat == 'Automap':
        return False
    elif snat and current_state != 'SRC_TRANS_SNATPOOL':
        return True
    elif snat and current_state == 'SRC_TRANS_SNATPOOL' and current_snat_pool != snat:
        return True
    else:
        return False


def get_pool(api, name):
    return api.LocalLB.VirtualServer.get_default_pool_name(
        virtual_servers=[name]
    )[0]


def set_pool(api, name, pool):
    updated = False
    try:
        current_pool = get_pool(api, name)
        if pool is not None and (pool != current_pool):
            api.LocalLB.VirtualServer.set_default_pool_name(
                virtual_servers=[name],
                default_pools=[pool]
            )
            updated = True
        return updated
    except bigsuds.OperationFailed as e:
        raise Exception('Error on setting pool : %s' % e)


def get_destination(api, name):
    return api.LocalLB.VirtualServer.get_destination_v2(
        virtual_servers=[name]
    )[0]


def set_destination(api, name, destination):
    updated = False
    try:
        current_destination = get_destination(api, name)
        if destination is not None and destination != current_destination['address']:
            api.LocalLB.VirtualServer.set_destination_v2(
                virtual_servers=[name],
                destinations=[{'address': destination, 'port': current_destination['port']}]
            )
            updated = True
        return updated
    except bigsuds.OperationFailed as e:
        raise Exception('Error on setting destination : %s' % e)


def set_port(api, name, port):
    updated = False
    try:
        current_destination = get_destination(api, name)
        if port is not None and port != current_destination['port']:
            api.LocalLB.VirtualServer.set_destination_v2(
                virtual_servers=[name],
                destinations=[{'address': current_destination['address'], 'port': port}]
            )
            updated = True
        return updated
    except bigsuds.OperationFailed as e:
        raise Exception('Error on setting port : %s' % e)


def get_state(api, name):
    return api.LocalLB.VirtualServer.get_enabled_state(
        virtual_servers=[name]
    )[0]


def set_state(api, name, state):
    updated = False
    try:
        current_state = get_state(api, name)
        # We consider that being present is equivalent to enabled
        if state == 'present':
            state = 'enabled'
        if STATES[state] != current_state:
            api.LocalLB.VirtualServer.set_enabled_state(
                virtual_servers=[name],
                states=[STATES[state]]
            )
            updated = True
        return updated
    except bigsuds.OperationFailed as e:
        raise Exception('Error on setting state : %s' % e)


def get_description(api, name):
    return api.LocalLB.VirtualServer.get_description(
        virtual_servers=[name]
    )[0]


def set_description(api, name, description):
    updated = False
    try:
        current_description = get_description(api, name)
        if description is not None and current_description != description:
            api.LocalLB.VirtualServer.set_description(
                virtual_servers=[name],
                descriptions=[description]
            )
            updated = True
        return updated
    except bigsuds.OperationFailed as e:
        raise Exception('Error on setting description : %s ' % e)


def get_persistence_profiles(api, name):
    return api.LocalLB.VirtualServer.get_persistence_profile(
        virtual_servers=[name]
    )[0]


def set_default_persistence_profiles(api, name, persistence_profile):
    updated = False
    if persistence_profile is None:
        return updated
    try:
        current_persistence_profiles = get_persistence_profiles(api, name)
        default = None
        for profile in current_persistence_profiles:
            if profile['default_profile']:
                default = profile['profile_name']
                break
        if default is not None and default != persistence_profile:
            api.LocalLB.VirtualServer.remove_persistence_profile(
                virtual_servers=[name],
                profiles=[[{'profile_name': default, 'default_profile': True}]]
            )
        if default != persistence_profile:
            api.LocalLB.VirtualServer.add_persistence_profile(
                virtual_servers=[name],
                profiles=[[{'profile_name': persistence_profile, 'default_profile': True}]]
            )
            updated = True
        return updated
    except bigsuds.OperationFailed as e:
        raise Exception('Error on setting default persistence profile : %s' % e)


def get_route_advertisement_status(api, address):
    result = api.LocalLB.VirtualAddressV2.get_route_advertisement_state(virtual_addresses=[address]).pop(0)
    result = result.split("STATE_")[-1].lower()
    return result


def set_route_advertisement_state(api, destination, partition, route_advertisement_state):
    updated = False

    try:
        state = "STATE_%s" % route_advertisement_state.strip().upper()
        address = fq_name(partition, destination,)
        current_route_advertisement_state=get_route_advertisement_status(api,address)
        if current_route_advertisement_state != route_advertisement_state:
            api.LocalLB.VirtualAddressV2.set_route_advertisement_state(virtual_addresses=[address], states=[state])
            updated = True
        return updated
    except bigsuds.OperationFailed as e:
        raise Exception('Error on setting profiles : %s' % e)


def main():
    argument_spec = f5_argument_spec()
    argument_spec.update(dict(
        state=dict(type='str', default='present',
                   choices=['present', 'absent', 'disabled', 'enabled']),
        name=dict(type='str', required=True, aliases=['vs']),
        destination=dict(type='str', aliases=['address', 'ip']),
        port=dict(type='int'),
        all_profiles=dict(type='list'),
        all_rules=dict(type='list'),
        enabled_vlans=dict(type='list'),
        pool=dict(type='str'),
        description=dict(type='str'),
        snat=dict(type='str'),
        route_advertisement_state=dict(type='str', default='disabled', choices=['enabled', 'disabled']),
        default_persistence_profile=dict(type='str')
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    if not bigsuds_found:
        module.fail_json(msg="the python bigsuds module is required")

    if module.params['validate_certs']:
        import ssl
        if not hasattr(ssl, 'SSLContext'):
            module.fail_json(msg='bigsuds does not support verifying certificates with python < 2.7.9.  Either update python or set validate_certs=False on the task')

    server = module.params['server']
    server_port = module.params['server_port']
    user = module.params['user']
    password = module.params['password']
    state = module.params['state']
    partition = module.params['partition']
    validate_certs = module.params['validate_certs']

    name = fq_name(partition, module.params['name'])
    destination = module.params['destination']
    port = module.params['port']
    all_profiles = fq_list_names(partition, module.params['all_profiles'])
    all_rules = fq_list_names(partition, module.params['all_rules'])

    enabled_vlans = module.params['enabled_vlans']
    if enabled_vlans is None or 'ALL' in enabled_vlans:
        all_enabled_vlans = enabled_vlans
    else:
        all_enabled_vlans = fq_list_names(partition, enabled_vlans)

    pool = fq_name(partition, module.params['pool'])
    description = module.params['description']
    snat = module.params['snat']
    route_advertisement_state = module.params['route_advertisement_state']
    default_persistence_profile = fq_name(partition, module.params['default_persistence_profile'])

    if 1 > port > 65535:
        module.fail_json(msg="valid ports must be in range 1 - 65535")

    try:
        api = bigip_api(server, user, password, validate_certs, port=server_port)
        result = {'changed': False}  # default

        if state == 'absent':
            if not module.check_mode:
                if vs_exists(api, name):
                    # hack to handle concurrent runs of module
                    # pool might be gone before we actually remove
                    try:
                        vs_remove(api, name)
                        result = {'changed': True, 'deleted': name}
                    except bigsuds.OperationFailed as e:
                        if "was not found" in str(e):
                            result['changed'] = False
                        else:
                            raise
            else:
                # check-mode return value
                result = {'changed': True}

        else:
            update = False
            if not vs_exists(api, name):
                if (not destination) or (not port):
                    module.fail_json(msg="both destination and port must be supplied to create a VS")
                if not module.check_mode:
                    # a bit of a hack to handle concurrent runs of this module.
                    # even though we've checked the virtual_server doesn't exist,
                    # it may exist by the time we run virtual_server().
                    # this catches the exception and does something smart
                    # about it!
                    try:
                        vs_create(api, name, destination, port, pool)
                        set_profiles(api, name, all_profiles)
                        set_enabled_vlans(api, name, all_enabled_vlans)
                        set_rules(api, name, all_rules)
                        set_snat(api, name, snat)
                        set_description(api, name, description)
                        set_default_persistence_profiles(api, name, default_persistence_profile)
                        set_state(api, name, state)
                        set_route_advertisement_state(api, destination, partition, route_advertisement_state)
                        result = {'changed': True}
                    except bigsuds.OperationFailed as e:
                        raise Exception('Error on creating Virtual Server : %s' % e)
                else:
                    # check-mode return value
                    result = {'changed': True}
            else:
                update = True
            if update:
                # VS exists
                if not module.check_mode:
                    # Have a transaction for all the changes
                    try:
                        api.System.Session.start_transaction()
                        result['changed'] |= set_destination(api, name, fq_name(partition, destination))
                        result['changed'] |= set_port(api, name, port)
                        result['changed'] |= set_pool(api, name, pool)
                        result['changed'] |= set_description(api, name, description)
                        result['changed'] |= set_snat(api, name, snat)
                        result['changed'] |= set_profiles(api, name, all_profiles)
                        result['changed'] |= set_enabled_vlans(api, name, all_enabled_vlans)
                        result['changed'] |= set_rules(api, name, all_rules)
                        result['changed'] |= set_default_persistence_profiles(api, name, default_persistence_profile)
                        result['changed'] |= set_state(api, name, state)
                        result['changed'] |= set_route_advertisement_state(api, destination, partition, route_advertisement_state)
                        api.System.Session.submit_transaction()
                    except Exception as e:
                        raise Exception("Error on updating Virtual Server : %s" % e)
                else:
                    # check-mode return value
                    result = {'changed': True}

    except Exception as e:
        module.fail_json(msg="received exception: %s" % e)

    module.exit_json(**result)
# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.f5 import *

if __name__ == '__main__':
    main()
