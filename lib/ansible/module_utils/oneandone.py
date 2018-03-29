# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
import time


class OneAndOneResources:
    firewall_policy = 'firewall_policy'
    load_balancer = 'load_balancer'
    monitoring_policy = 'monitoring_policy'
    private_network = 'private_network'
    public_ip = 'public_ip'
    role = 'role'
    server = 'server'
    user = 'user'
    vpn = 'vpn'


def get_resource(oneandone_conn, resource_type, resource_id):
    switcher = {
        'firewall_policy': oneandone_conn.get_firewall,
        'load_balancer': oneandone_conn.get_load_balancer,
        'monitoring_policy': oneandone_conn.get_monitoring_policy,
        'private_network': oneandone_conn.get_private_network,
        'public_ip': oneandone_conn.get_public_ip,
        'role': oneandone_conn.get_role,
        'server': oneandone_conn.get_server,
        'user': oneandone_conn.get_user,
        'vpn': oneandone_conn.get_vpn,
    }

    return switcher.get(resource_type, None)(resource_id)


def get_datacenter(oneandone_conn, datacenter, full_object=False):
    """
    Validates the datacenter exists by ID or country code.
    Returns the datacenter ID.
    """
    for _datacenter in oneandone_conn.list_datacenters():
        if datacenter in (_datacenter['id'], _datacenter['country_code']):
            if full_object:
                return _datacenter
            return _datacenter['id']


def get_fixed_instance_size(oneandone_conn, fixed_instance_size, full_object=False):
    """
    Validates the fixed instance size exists by ID or name.
    Return the instance size ID.
    """
    for _fixed_instance_size in oneandone_conn.fixed_server_flavors():
        if fixed_instance_size in (_fixed_instance_size['id'],
                                   _fixed_instance_size['name']):
            if full_object:
                return _fixed_instance_size
            return _fixed_instance_size['id']


def get_appliance(oneandone_conn, appliance, full_object=False):
    """
    Validates the appliance exists by ID or name.
    Return the appliance ID.
    """
    for _appliance in oneandone_conn.list_appliances(q='IMAGE'):
        if appliance in (_appliance['id'], _appliance['name']):
            if full_object:
                return _appliance
            return _appliance['id']


def get_private_network(oneandone_conn, private_network, full_object=False):
    """
    Validates the private network exists by ID or name.
    Return the private network ID.
    """
    for _private_network in oneandone_conn.list_private_networks():
        if private_network in (_private_network['name'],
                               _private_network['id']):
            if full_object:
                return _private_network
            return _private_network['id']


def get_monitoring_policy(oneandone_conn, monitoring_policy, full_object=False):
    """
    Validates the monitoring policy exists by ID or name.
    Return the monitoring policy ID.
    """
    for _monitoring_policy in oneandone_conn.list_monitoring_policies():
        if monitoring_policy in (_monitoring_policy['name'],
                                 _monitoring_policy['id']):
            if full_object:
                return _monitoring_policy
            return _monitoring_policy['id']


def get_firewall_policy(oneandone_conn, firewall_policy, full_object=False):
    """
    Validates the firewall policy exists by ID or name.
    Return the firewall policy ID.
    """
    for _firewall_policy in oneandone_conn.list_firewall_policies():
        if firewall_policy in (_firewall_policy['name'],
                               _firewall_policy['id']):
            if full_object:
                return _firewall_policy
            return _firewall_policy['id']


def get_load_balancer(oneandone_conn, load_balancer, full_object=False):
    """
    Validates the load balancer exists by ID or name.
    Return the load balancer ID.
    """
    for _load_balancer in oneandone_conn.list_load_balancers():
        if load_balancer in (_load_balancer['name'],
                             _load_balancer['id']):
            if full_object:
                return _load_balancer
            return _load_balancer['id']


def get_server(oneandone_conn, instance, full_object=False):
    """
    Validates that the server exists whether by ID or name.
    Returns the server if one was found.
    """
    for server in oneandone_conn.list_servers(per_page=1000):
        if instance in (server['id'], server['name']):
            if full_object:
                return server
            return server['id']


def get_user(oneandone_conn, user, full_object=False):
    """
    Validates that the user exists by ID or a name.
    Returns the user if one was found.
    """
    for _user in oneandone_conn.list_users(per_page=1000):
        if user in (_user['id'], _user['name']):
            if full_object:
                return _user
            return _user['id']


def get_role(oneandone_conn, role, full_object=False):
    """
    Given a name, validates that the role exists
    whether it is a proper ID or a name.
    Returns the role if one was found, else None.
    """
    for _role in oneandone_conn.list_roles(per_page=1000):
        if role in (_role['id'], _role['name']):
            if full_object:
                return _role
            return _role['id']


def get_vpn(oneandone_conn, vpn, full_object=False):
    """
    Validates that the vpn exists by ID or a name.
    Returns the vpn if one was found.
    """
    for _vpn in oneandone_conn.list_vpns(per_page=1000):
        if vpn in (_vpn['id'], _vpn['name']):
            if full_object:
                return _vpn
            return _vpn['id']


def get_public_ip(oneandone_conn, public_ip, full_object=False):
    """
    Validates that the public ip exists by ID or a name.
    Returns the public ip if one was found.
    """
    for _public_ip in oneandone_conn.list_public_ips(per_page=1000):
        if public_ip in (_public_ip['id'], _public_ip['ip']):
            if full_object:
                return _public_ip
            return _public_ip['id']


def wait_for_resource_creation_completion(oneandone_conn,
                                          resource_type,
                                          resource_id,
                                          wait_timeout,
                                          wait_interval):
    """
    Waits for the resource create operation to complete based on the timeout period.
    """
    wait_timeout = time.time() + wait_timeout
    while wait_timeout > time.time():
        time.sleep(wait_interval)

        # Refresh the resource info
        resource = get_resource(oneandone_conn, resource_type, resource_id)

        if resource_type == OneAndOneResources.server:
            resource_state = resource['status']['state']
        else:
            resource_state = resource['state']

        if ((resource_type == OneAndOneResources.server and resource_state.lower() == 'powered_on') or
                (resource_type != OneAndOneResources.server and resource_state.lower() == 'active')):
            return
        elif resource_state.lower() == 'failed':
            raise Exception('%s creation failed for %s' % (resource_type, resource_id))
        elif resource_state.lower() in ('active',
                                        'enabled',
                                        'deploying',
                                        'configuring'):
            continue
        else:
            raise Exception(
                'Unknown %s state %s' % (resource_type, resource_state))

    raise Exception(
        'Timed out waiting for %s completion for %s' % (resource_type, resource_id))


def wait_for_resource_deletion_completion(oneandone_conn,
                                          resource_type,
                                          resource_id,
                                          wait_timeout,
                                          wait_interval):
    """
    Waits for the resource delete operation to complete based on the timeout period.
    """
    wait_timeout = time.time() + wait_timeout
    while wait_timeout > time.time():
        time.sleep(wait_interval)

        # Refresh the operation info
        logs = oneandone_conn.list_logs(q='DELETE',
                                        period='LAST_HOUR',
                                        sort='-start_date')

        if resource_type == OneAndOneResources.server:
            _type = 'VM'
        elif resource_type == OneAndOneResources.private_network:
            _type = 'PRIVATENETWORK'
        else:
            raise Exception(
                'Unsupported wait_for delete operation for %s resource' % resource_type)

        for log in logs:
            if (log['resource']['id'] == resource_id and
                    log['action'] == 'DELETE' and
                    log['type'] == _type and
                    log['status']['state'] == 'OK'):
                return
    raise Exception(
        'Timed out waiting for %s deletion for %s' % (resource_type, resource_id))
