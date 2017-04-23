#!/usr/bin/python
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

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.0'}

DOCUMENTATION = """
module: consul_maint
short_description: "Enable & disable maintenance mode for a service or node within a consul cluster."
description:
  - Mark a single node or a single service across all nodes as 'under maintenance'.
    In this mode of operation, the service or node will not appear in DNS query results or API results.
    This effectively takes the service or node out of the pool of available 'healthy' nodes.
  - See U(http://consul.io) for more details.
requirements:
  - "python >= 2.6"
  - python-consul
  - requests
version_added: "2.4"
author: "Alan Loi (@loia)"
options:
    enabled:
        description:
          - True to enable maintenance mode for the service or node; False to disable.
        required: true
    reason:
        description:
          - The reason for enabling maintenance mode.
        required: false
    node_name:
        description:
          - The unique name of the node to update.
        required: false
    node_address:
        description:
          - The network address of the node to update.
        required: false
    service_name:
        description:
          - The unique name of the service to update across all nodes.
        required: false
    service_include_tags:
        description:
          - List of tags which the service must include for it to be updated.
        required: false
        default: None
    service_exclude_tags:
        description:
          - List of tags which the service must NOT include for it to be updated.
        required: false
        default: None
    host:
        description:
          - The host name of the consul agent.
        required: false
        default: localhost
    port:
        description:
          - The port on which the consul agent is running.
        required: false
        default: 8500
    scheme:
        description:
          - The protocol scheme on which the consul agent is running.
        required: false
        default: http
    validate_certs:
        description:
          - Whether to verify the tls certificate of the consul agent.
        required: false
        default: True
"""

RETURN = '''
node_found:
    description: The matching node found.
    returned: if I(node_name) or I(node_address) are supplied
    type: complex
services_found:
    description: The matching services found.
    returned: if I(service_name) is supplied
    type: complex
services_updated:
    description: The matching services which were updated (not already in the desired state)
    returned: if I(service_name) is supplied
    type: complex
'''

EXAMPLES = '''
  - name: enable maintenance mode for nginx service (across all nodes)
    consul_maint:
      enabled: true
      reason: Decommissioning legacy system
      service_name: nginx

  - name: disable maintenance mode for nginx service (across all nodes)
    consul_maint:
      enabled: false
      service_name: nginx

  - name: enable maintenance mode for nginx service with tags 'prod' and 'standby'
    consul_maint:
      enabled: true
      service_name: nginx
      service_include_tags:
        - prod
        - standby

  - name: enable maintenance mode for nginx service excluding those with tag 'version=1.0.1'
    consul_maint:
      enabled: true
      service_name: nginx
      service_exclude_tags:
        - version=1.0.1

  - name: enable maintenance mode for node 'app-server-1'
    consul_maint:
      enabled: true
      node_name: app-server-1

  - name: enable maintenance mode for node with address 10.1.1.1
    consul_maint:
      enabled: true
      node_address: 10.1.1.1
'''

# import module snippets
from ansible.module_utils.basic import AnsibleModule

try:
    import consul
    from requests.exceptions import ConnectionError
    python_consul_installed = True

except ImportError:
    python_consul_installed = False


def set_consul_maintenance_mode(module):
    if module.params.get('node_name') or module.params.get('node_address'):
        set_consul_node_maintenance_mode(module)

    elif module.params.get('service_name'):
        set_consul_service_maintenance_mode(module)

    else:
        module.exit_json(msg="Either node_name, node_address or service_name must be provided.")


def set_consul_node_maintenance_mode(module):
    enabled = module.params.get('enabled')
    reason = module.params.get('reason')
    node_name = module.params.get('node_name')
    node_address = module.params.get('node_address')

    result = dict(
        node_found=None,
        changed=False,
    )

    consul_api = get_consul_api(module)
    node = find_catalog_node(consul_api, node_name=node_name, node_address=node_address)
    if node:
        result['node_found'] = node
        result['changed'] = set_node_maintenance_mode(module, node=node, enabled=enabled, reason=reason)

    module.exit_json(**result)


def find_catalog_node(consul_api, node_name, node_address):
    consul_index, nodes = consul_api.catalog.nodes()

    for node in nodes:
        if node['Node'] == node_name or node['Address'] == node_address:
            return node

    # not found
    return None


def set_node_maintenance_mode(module, node, enabled, reason=None):
    '''Place the node into maintenance mode.  Returns true if the node was updated'''

    node_host = node['Address']
    node_name = node['Node']
    consul_node_api = get_consul_api(module, host_override=node_host)

    if get_node_maintenance_mode(consul_node_api, node_name=node_name) == enabled:
        return False  # already up to date

    if not module.check_mode:
        consul_node_api.agent.maintenance(enable=enabled, reason=reason)
    return True


def get_node_maintenance_mode(consul_api, node_name):
    consul_index, node_checks = consul_api.health.node(node=node_name)

    for check in node_checks:
        if check['CheckID'].startswith('_node_maintenance'):
            return True
    return False


def set_consul_service_maintenance_mode(module):
    enabled = module.params.get('enabled')
    reason = module.params.get('reason')
    service_name = module.params.get('service_name')
    service_include_tags = module.params.get('service_include_tags')
    service_exclude_tags = module.params.get('service_exclude_tags')

    services_found = []
    services_updated = []
    result = dict(
        services_found=services_found,
        services_updated=services_updated,
        changed=False,
    )

    consul_api = get_consul_api(module)
    matching_services = find_health_services(consul_api,
                                             service_name=service_name,
                                             service_include_tags=service_include_tags,
                                             service_exclude_tags=service_exclude_tags)

    for service in matching_services:
        service_summary = get_service_summary(service)
        services_found.append(service_summary)

        updated = set_service_maintenance_mode(module, service=service, enabled=enabled, reason=reason)
        if updated:
            services_updated.append(service_summary)
            result['changed'] = True

    module.exit_json(**result)


def find_health_services(consul_api, service_name, service_include_tags=None, service_exclude_tags=None):
    consul_index, services = consul_api.health.service(service=service_name)
    if not service_include_tags and not service_exclude_tags:
        return services  # no filtering

    include_tags = set(service_include_tags) if service_include_tags else set()
    exclude_tags = set(service_exclude_tags) if service_exclude_tags else set()

    # The consul HTTP API doesn't support filtering on multiple tags or by
    # excluded tags so we have to do it client side
    filtered_services = []
    for service in services:
        tags = set(service['Service']['Tags'])
        if tags.issuperset(include_tags) and tags.isdisjoint(exclude_tags):
            filtered_services.append(service)

    return filtered_services


def set_service_maintenance_mode(module, service, enabled, reason=None):
    '''Place the service into maintenance mode.  Returns true if the service was updated'''

    if get_service_maintenance_mode(service) == enabled:
        return False  # already up to date

    node_host = service['Node']['Address']
    service_id = service['Service']['ID']

    consul_node_api = get_consul_api(module, host_override=node_host)
    if not module.check_mode:
        consul_node_api.agent.service.maintenance(service_id=service_id, enable=enabled, reason=reason)

    return True


def get_service_maintenance_mode(service):
    for service_check in service['Checks']:
        if service_check['CheckID'].startswith('_service_maintenance'):
            return True
    return False


def get_service_summary(service):
    return dict(
        ServiceName=service['Service']['Service'],
        ServiceID=service['Service']['ID'],
        ServiceTags=service['Service']['Tags'],
        ServiceAddress=service['Service']['Address'],
        ServicePort=service['Service']['Port'],
        NodeName=service['Node']['Node'],
        NodeAddress=service['Node']['Address'],
    )


def get_consul_api(module, host_override=None):
    host = host_override if host_override else module.params.get('host')
    return consul.Consul(host=host,
                         port=module.params.get('port'),
                         scheme=module.params.get('scheme'),
                         verify=module.params.get('validate_certs'))


def check_module_dependencies(module):
    if not python_consul_installed:
        module.fail_json(msg="python-consul required for this module. see http://python-consul.readthedocs.org/en/latest/#installation")


def main():
    module = AnsibleModule(
        argument_spec=dict(
            enabled=dict(type='bool'),
            reason=dict(required=False),
            host=dict(default='localhost'),
            port=dict(default=8500, type='int'),
            scheme=dict(required=False, default='http'),
            validate_certs=dict(required=False, default=True, type='bool'),
            node_name=dict(required=False),
            node_address=dict(required=False),
            service_name=dict(required=False),
            service_include_tags=dict(required=False, type='list'),
            service_exclude_tags=dict(required=False, type='list'),
        ),
        supports_check_mode=True,
    )

    check_module_dependencies(module)

    try:
        set_consul_maintenance_mode(module)

    except ConnectionError as e:
        module.fail_json(msg='Could not connect to consul agent, error was %s' % (str(e)))
    except Exception as e:
        module.fail_json(msg='Failed to update maintenance mode, error was %s' % (str(e)))

if __name__ == '__main__':
    main()
