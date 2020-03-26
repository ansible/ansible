#!/usr/bin/python

# Copyright: (c) 2020, Ori Hoch
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: kamatera_compute

short_description: Create, start, stop, restart or terminate Kamatera servers

version_added: "2.9"

description:
    - "Create, start, stop, restart or terminate Kamatera servers"

options:
    api_client_id:
        description:
            - The Kamatera API Client ID, get it from the Kamatera console
            - Can be set via environment variable KAMATERA_API_CLIENT_ID
        required: true
    api_secret:
        description:
            - The Kamatera API Secret, get it from the Kamatera console
            - Can be set via environment variable KAMATERA_API_SECRET
        required: true
    server_name:
        description:
            - A server name to operate on or to create
        type: str
    server_names:
        description:
            - A list of server names to create or operate on
        type: list
    server_name_regex:
        description:
            - A regular expression to match server names to operate on
        type: str
    state:
        description:
            - Desried state of the server/s
        default: 'running'
        choices: ['present', 'running', 'stopped', 'restarted', 'absent']
    datacenter:
        description:
            - Datacenter ID to create the server in
        default: 'EU'
        type: 'str'
    image:
        description:
            - Image ID or name to deploy on the server
        default: 'ubuntu_server_18.04_64-bit'
        type: 'str'
    cpu_type:
        description:
            - CPU type ID
        default: 'B'
        type: 'str'
    cpu_cores:
        description:
            - Number of CPU cores
        default: 2
        type: 'int'
    ram_mb:
        description:
            - Amount of RAM in MB
        default: 2048
        type: 'int'
    disk_size_gb:
        description:
            - Primary disk size in GB
        default: 20
        type: 'int'
    extra_disk_sizes_gb:
        description:
            - Additional disk sizes in GB (up to 3 additional disks)
        default: []
        type: 'list'
    password:
        description:
            - Password to set for root access
            - If not set, password will be generated and available as generated_password in response
        type: 'str'
    ssh_pub_key:
        description:
            - Public SSH key to set for root access
        type: 'str'
    networks:
        description:
            - List of network interfaces (up to 4 interfaces)
            - By default, a single public interface is added
            - For example, to add a private LAN, create it in the Kamatera Console and set the following:
            - [{'name': 'wan', 'ip': 'auto'}, {'name': 'my-lan-id', 'ip': 'auto'}]
        default: [{'name': 'wan', 'ip': 'auto'}]
        type: 'list'
    daily_backup:
        description:
            - Whether to enable daily backups on the server
        type: bool
        default: false
    managed:
        description:
            - Whether to privde managed support for the server
        type: bool
        default: false
    billing_cycle:
        description:
            - Which billing cycle to use (hourly or monthly)
        default: 'hourly'
        choices: ['hourly', 'monthly']
    monthly_traffic_package:
        description:
            - ID of traffic package to use if monthly billing cycle is selected
        type: 'str'
    wait:
        description:
            - Whether to wait for operation to complete, otherwise returns the command id
        type: 'bool'
        default: true
    wait_timeout_seconds:
        description:
            - How long to wait for each operation
        type: 'int'
        default: 600
    wait_poll_interval_seconds:
        description:
            - How frequently to poll for operation progress
        type: 'int'
        default: 2

author:
    - Ori Hoch (@OriHoch)
'''

EXAMPLES = '''
- name: Provisioning and operations example
  hosts: localhost
  vars: 
    api_client_id: <Your Kamatera API Client ID>
    api_secret: <Your Kamatera API secret>
    server_name: my-test-server
  tasks:
    - name: create servers
      kamatera_compute:
        api_client_id: '{{ api_client_id }}'
        api_secret: '{{ api_secret }}'
        server_names: ['{{ server_name }}_1','{{ server_name }}_2','{{ server_name }}_3']
        state: present
      register: res
    - name: restart servers
      kamatera_compute:
        api_client_id: '{{ api_client_id }}'
        api_secret: '{{ api_secret }}'
        server_names: '{{ res.server_names }}'
        state: restarted
      register: res
    - name: stop servers
      kamatera_compute:
        api_client_id: '{{ api_client_id }}'
        api_secret: '{{ api_secret }}'
        server_names: '{{ res.server_names }}'
        state: stopped
      register: res
    - name: start servers
      kamatera_compute:
        api_client_id: '{{ api_client_id }}'
        api_secret: '{{ api_secret }}'
        server_names: '{{ res.server_names }}'
        state: started
      register: res
    - name: terminate servers
      kamatera_compute:
        api_client_id: '{{ api_client_id }}'
        api_secret: '{{ api_secret }}'
        server_names: '{{ res.server_names }}'
        state: absent
'''

RETURN = '''
command_ids:
    description: Kamatera Command IDs which started to achieve desired state 
    type: list
    returned: always
server_names:
    description: Server names which were affected by the changes
    type: list
    returned: always
servers:
    description: List of affected server objects with updated details
    type: list
    returned: always
'''

import time
import datetime
from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.kamatera import request


def list_servers(module, name_regex=None, names=None):
    request_data = {'allow-no-servers': True}
    if names:
        servers = []
        for name in names:
            for server in list_servers(module, name_regex=name):
                servers.append(server)
        return servers
    else:
        if not name_regex:
            name_regex = '.*'
        request_data['name'] = name_regex
    return list(map(get_server, request(module, '/service/server/info', method='POST', request_data=request_data)))


def get_server(server):
    server_cpu = server.pop('cpu')
    server_disk_sizes = server.pop('diskSizes')
    res_server = dict(
        id=server.pop('id'),
        name=server.pop('name'),
        state='running' if server.pop('power') == 'on' else 'stopped',
        datacenter=server.pop('datacenter'),
        cpu_type=server_cpu[-1],
        cpu_cores=int(server_cpu[:-1]),
        ram_mb=int(server.pop('ram')),
        disk_size_gb=int(server_disk_sizes[0]),
        extra_disk_sizes_gb=list(map(int, server_disk_sizes[1:])),
        networks=server.pop('networks'),
        daily_backup=server.pop('backup') == "1",
        managed=server.pop('managed') == "1",
        billing_cycle=server.pop('billing'),
        monthly_traffic_package=server.pop('traffic'),
        price_monthly_on=server.pop('priceMonthlyOn'),
        price_hourly_on=server.pop('priceHourlyOn'),
        price_hourly_off=server.pop('priceHourlyOff')
    )
    res_server['extra'] = server
    return res_server


def server_operation(module, server, operation):
    request_data = {'id': server['id']}
    if operation == 'terminate':
        request_data['force'] = True
    command_id = int(request(module, '/service/server/%s' % operation, 'POST', request_data)[0])
    if module.params['wait']:
        server['extra']['%s_command' % operation] = wait_command(module, command_id)
    else:
        server['extra']['%s_command_id' % operation] = command_id
    return command_id


def get_command_status(module, command_id):
    response = request(module, '/service/queue?id=' + str(command_id))
    if len(response) != 1:
        module.fail_json(msg='invalid response for command id ' + str(command_id))
    return response[0]


def wait_command(module, command_id):
    start_time = datetime.datetime.now()
    time.sleep(module.params['wait_poll_interval_seconds'])
    while True:
        max_time = start_time + datetime.timedelta(seconds=module.params['wait_timeout_seconds'])
        if max_time < datetime.datetime.now():
            module.fail_json(
                msg='Timeout waiting for command (timeout_seconds=%s, command_id=%s)' % (
                    str(module.params['wait_timeout_seconds']), str(command_id)))
        time.sleep(module.params['wait_poll_interval_seconds'])
        command = get_command_status(module, command_id)
        status = command.get('status')
        if status == 'complete':
            return command
        elif status == 'error':
            module.fail_json('Command failed: ' + command.get('log'))


def config_servers(module, servers):
    changed = False
    command_ids = []
    server_names = []
    created_servers = []
    listed_server_names = [server['name'] for server in servers]
    if module.params.get('server_names'):
        for server_name in module.params['server_names']:
            if server_name not in listed_server_names and module.params['state'] != 'absent':
                tmp_result = create_servers(module, server_name)
                created_servers += tmp_result['servers']
                server_names += tmp_result['server_names']
                command_ids += tmp_result['command_ids']
                changed = True
    for server in servers:
        server_names.append(server['name'])
        if module.params['state'] == 'running' and server['state'] == 'stopped':
            command_ids.append(server_operation(module, server, 'poweron'))
            changed = True
            server['state'] = 'running'
        elif module.params['state'] == 'stopped' and server['state'] == 'running':
            command_ids.append(server_operation(module, server, 'poweroff'))
            changed = True
            server['state'] = 'stopped'
        elif module.params['state'] == 'restarted':
            command_ids.append(server_operation(module, server, 'poweron' if server['state'] == 'stopped' else 'reboot'))
            changed = True
            server['state'] = 'restarted'
        elif module.params['state'] == 'absent':
            command_ids.append(server_operation(module, server, 'terminate'))
            changed = True
            server['state'] = 'absent'
    module.exit_json(changed=changed, command_ids=command_ids, servers=created_servers + servers, server_names=server_names)


def create_servers(module, server_name=None):
    if module.params.get('server_name_regex'):
        module.fail_json(msg='cannot create server using server_name_regex param')
    elif module.params.get('server_names') and not server_name:
        result = dict(changed=True, command_ids=[], server_names=[], servers=[])
        for server_name in module.params['server_names']:
            tmp_result = create_servers(module, server_name)
            result['command_ids'] += tmp_result['command_ids']
            result['server_names'] += tmp_result['server_names']
            result['servers'] += tmp_result['servers']
        module.exit_json(**result)
    else:
        if server_name:
            return_result = True
        else:
            return_result = False
            server_name = module.params['server_name']
        request_data = {
            "name": server_name,
            "password": module.params['password'] or '__generate__',
            "passwordValidate": module.params['password'] or '__generate__',
            'ssh-key': module.params['ssh_pub_key'] or '',
            "datacenter": module.params['datacenter'],
            "image": module.params['image'],
            "cpu": '%s%s' % (module.params['cpu_cores'], module.params['cpu_type']),
            "ram": module.params['ram_mb'],
            "disk": ' '.join([
                'size=%d' % disksize for disksize
                in [module.params['disk_size_gb']] + module.params['extra_disk_sizes_gb']
            ]),
            "dailybackup": 'yes' if module.params['daily_backup'] else 'no',
            "managed": 'yes' if module.params['managed'] else 'no',
            "network": ' '.join([','.join([
                '%s=%s' % (k, v) for k, v
                in network.items()]) for network in module.params['networks']]),
            "quantity": 1,
            "billingcycle": module.params['billing_cycle'],
            "monthlypackage": module.params['monthly_traffic_package'],
            "poweronaftercreate": 'no' if module.params['state'] == 'stopped' else 'yes'
        }
        response = request(module, 'service/server', 'POST', request_data)
        if not module.params['password']:
            command_ids = response['commandIds']
            generated_password = response['password']
        else:
            command_ids = response
            generated_password = None
        result = dict(changed=True, command_ids=command_ids, server_names=[], servers=[])
        if module.params['wait']:
            for command_id in command_ids:
                command = wait_command(module, command_id)
                create_log = command['log']
                try:
                    created_at = datetime.datetime.strptime(command['completed'], '%Y-%m-%d %H:%M:%S')
                except Exception:
                    created_at = None
                name_lines = [line for line in create_log.split("\n") if line.startswith('Name: ')]
                if len(name_lines) != 1:
                    module.fail_json(msg='invalid create log: ' + create_log)
                created_name = name_lines[0].replace('Name: ', '')
                tmp_servers = list_servers(module, name_regex=created_name)
                if len(tmp_servers) != 1:
                    module.fail_json(msg='invalid list servers response')
                server = tmp_servers[0]
                server['extra']['create_command'] = command
                server['extra']['created_at'] = created_at
                server['extra']['generated_password'] = generated_password
                result['servers'].append(server)
                result['server_names'].append(created_name)
        else:
            for command_id in command_ids:
                result['servers'].append({'extra': {'create_command': {'id': command_id}, 'generated_password': generated_password}})
        if return_result:
            return result
        else:
            module.exit_json(**result)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            api_client_id=dict(required=True, fallback=(env_fallback, ['KAMATERA_API_CLIENT_ID']), no_log=True),
            api_secret=dict(required=True, fallback=(env_fallback, ['KAMATERA_API_SECRET']), no_log=True),
            api_url=dict(fallback=(env_fallback, ['KAMATERA_API_URL']), default='https://cloudcli.cloudwm.com'),
            server_name=dict(type='str'),
            server_names=dict(type='list', default=[]),
            server_name_regex=dict(type='str'),
            state=dict(default='running', choices=['present', 'running', 'stopped', 'restarted', 'absent']),
            datacenter=dict(type='str', default='EU'),
            image=dict(type='str', default='ubuntu_server_18.04_64-bit'),
            cpu_type=dict(type='str', default='B'),
            cpu_cores=dict(type='int', default=2),
            ram_mb=dict(type='int', default=2048),
            disk_size_gb=dict(type='int', default=20),
            extra_disk_sizes_gb=dict(type='list', default=[]),
            password=dict(type='str', no_log=True),
            ssh_pub_key=dict(type='str'),
            networks=dict(type='list', default=[{'name': 'wan', 'ip': 'auto'}]),
            daily_backup=dict(type='bool', default=False),
            managed=dict(type='bool', default=False),
            billing_cycle=dict(default='hourly', choices=['monthly', 'hourly']),
            monthly_traffic_package=dict(type='str'),
            wait=dict(type='bool', default=True),
            wait_timeout_seconds=dict(type='int', default=600),
            wait_poll_interval_seconds=dict(type='int', default=2),
        )
    )
    server_params = [param for param in ['server_name', 'server_names', 'server_name_regex'] if
                     module.params.get(param)]
    if len(server_params) == 0:
        module.fail_json(msg='one of server_name, server_names, server_name_regex params must be provided')
    elif len(server_params) > 1:
        module.fail_json(msg='only one of server_name, server_names, server_name_regex params must be provided')
    server_param = server_params[0]
    if server_param == 'server_names':
        list_servers_kwargs = dict(names=module.params['server_names'])
    else:
        list_servers_kwargs = dict(name_regex=module.params[server_param])
    servers = list_servers(module, **list_servers_kwargs)
    if len(servers) == 0:
        if module.params['state'] == 'absent':
            module.exit_json(changed=False, command_ids=[], servers=[], server_names=[])
        elif module.params['state'] == 'restarted':
            module.fail_json(msg='Node is absent so cannot be restarted', servers=[])
        elif module.params['state'] in ['present', 'running', 'stopped']:
            create_servers(module)
        else:
            module.fail_json(msg='unknown state: ' + module.params['state'])
    elif len(servers) > 1 and server_param == 'server_name':
        module.fail_json(msg='invalid server_name param: matched multiple servers')
    else:
        config_servers(module, servers)


if __name__ == '__main__':
    main()
