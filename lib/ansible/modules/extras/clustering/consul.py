#!/usr/bin/python
#
# (c) 2015, Steve Gargan <steve.gargan@gmail.com>
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

DOCUMENTATION = """
module: consul
short_description: "Add, modify & delete services within a consul cluster."
description:
 - Registers services and checks for an agent with a consul cluster.
   A service is some process running on the agent node that should be advertised by
   consul's discovery mechanism. It may optionally supply a check definition,
   a periodic service test to notify the consul cluster of service's health.
 - "Checks may also be registered per node e.g. disk usage, or cpu usage and
   notify the health of the entire node to the cluster.
   Service level checks do not require a check name or id as these are derived
   by Consul from the Service name and id respectively by appending 'service:'
   Node level checks require a check_name and optionally a check_id."
 - Currently, there is no complete way to retrieve the script, interval or ttl
   metadata for a registered check. Without this metadata it is  not possible to
   tell if the data supplied with ansible represents a change to a check. As a
   result this does not attempt to determine changes and will always report a
   changed occurred. An api method is planned to supply this metadata so at that
   stage change management will be added.
 - "See http://consul.io for more details."
requirements:
  - "python >= 2.6"
  - python-consul
  - requests
version_added: "2.0"
author: "Steve Gargan (@sgargan)"
options:
    state:
        description:
          - register or deregister the consul service, defaults to present
        required: true
        choices: ['present', 'absent']
    service_name:
        description:
          - Unique name for the service on a node, must be unique per node,
            required if registering a service. May be ommitted if registering
            a node level check
        required: false
    service_id:
        description:
          - the ID for the service, must be unique per node, defaults to the
            service name if the service name is supplied
        required: false
        default: service_name if supplied
    host:
        description:
          - host of the consul agent defaults to localhost
        required: false
        default: localhost
    port:
        description:
          - the port on which the consul agent is running
        required: false
        default: 8500
    notes:
        description:
          - Notes to attach to check when registering it.
        required: false
        default: None
    service_port:
        description:
          - the port on which the service is listening required for
            registration of a service, i.e. if service_name or service_id is set
        required: false
    tags:
        description:
          - a list of tags that will be attached to the service registration.
        required: false
        default: None
    script:
        description:
          - the script/command that will be run periodically to check the health
            of the service. Scripts require an interval and vise versa
        required: false
        default: None
    interval:
        description:
          - the interval at which the service check will be run. This is a number
            with a s or m suffix to signify the units of seconds or minutes e.g
            15s or 1m. If no suffix is supplied, m will be used by default e.g.
            1 will be 1m. Required if the script param is specified.
        required: false
        default: None
    check_id:
        description:
          - an ID for the service check, defaults to the check name, ignored if
            part of a service definition.
        required: false
        default: None
    check_name:
        description:
          - a name for the service check, defaults to the check id. required if
            standalone, ignored if part of service definition.
        required: false
        default: None
    ttl:
        description:
          - checks can be registered with a ttl instead of a script and interval
            this means that the service will check in with the agent before the
            ttl expires. If it doesn't the check will be considered failed.
            Required if registering a check and the script an interval are missing
            Similar to the interval this is a number with a s or m suffix to
            signify the units of seconds or minutes e.g 15s or 1m. If no suffix
            is supplied, m will be used by default e.g. 1 will be 1m
        required: false
        default: None
    http:
        description:
          - checks can be registered with an http endpoint. This means that consul
            will check that the http endpoint returns a successful http status.
            Interval must also be provided with this option.
        required: false
        default: None
        version_added: "2.0"
    timeout:
        description:
          - A custom HTTP check timeout. The consul default is 10 seconds.
            Similar to the interval this is a number with a s or m suffix to
            signify the units of seconds or minutes, e.g. 15s or 1m.
        required: false
        default: None
        version_added: "2.0"
    token:
        description:
          - the token key indentifying an ACL rule set. May be required to register services.
        required: false
        default: None
"""

EXAMPLES = '''
  - name: register nginx service with the local consul agent
    consul:
      service_name: nginx
      service_port: 80

  - name: register nginx service with curl check
    consul:
      service_name: nginx
      service_port: 80
      script: "curl http://localhost"
      interval: 60s

  - name: register nginx with an http check
    consul:
      name: nginx
      service_port: 80
      interval: 60s
      http: /status

  - name: register nginx with some service tags
    consul:
      service_name: nginx
      service_port: 80
      tags:
        - prod
        - webservers

  - name: remove nginx service
    consul:
      service_name: nginx
      state: absent

  - name: create a node level check to test disk usage
    consul:
      check_name: Disk usage
      check_id: disk_usage
      script: "/opt/disk_usage.py"
      interval: 5m

'''

import sys

try:
    import consul
    from requests.exceptions import ConnectionError
    python_consul_installed = True
except ImportError, e:
    python_consul_installed = False

def register_with_consul(module):

    state = module.params.get('state')

    if state == 'present':
        add(module)
    else:
        remove(module)


def add(module):
    ''' adds a service or a check depending on supplied configuration'''
    check = parse_check(module)
    service = parse_service(module)

    if not service and not check:
        module.fail_json(msg='a name and port are required to register a service')

    if service:
        if check:
            service.add_check(check)
        add_service(module, service)
    elif check:
        add_check(module, check)


def remove(module):
    ''' removes a service or a check '''
    service_id = module.params.get('service_id') or module.params.get('service_name')
    check_id = module.params.get('check_id') or module.params.get('check_name')
    if not (service_id or check_id):
        module.fail_json(msg='services and checks are removed by id or name. please supply a service id/name or a check id/name')
    if service_id:
        remove_service(module, service_id)
    else:
        remove_check(module, check_id)


def add_check(module, check):
    ''' registers a check with the given agent. currently there is no way
    retrieve the full metadata of an existing check  through the consul api.
    Without this we can't compare to the supplied check and so we must assume
    a change. '''
    if not check.name:
        module.fail_json(msg='a check name is required for a node level check, one not attached to a service')

    consul_api = get_consul_api(module)
    check.register(consul_api)

    module.exit_json(changed=True,
                     check_id=check.check_id,
                     check_name=check.name,
                     script=check.script,
                     interval=check.interval,
                     ttl=check.ttl,
                     http=check.http,
                     timeout=check.timeout)


def remove_check(module, check_id):
    ''' removes a check using its id '''
    consul_api = get_consul_api(module)

    if check_id in consul_api.agent.checks():
        consul_api.agent.check.deregister(check_id)
        module.exit_json(changed=True, id=check_id)

    module.exit_json(changed=False, id=check_id)


def add_service(module, service):
    ''' registers a service with the the current agent '''
    result = service
    changed = False

    consul_api = get_consul_api(module)
    existing = get_service_by_id(consul_api, service.id)

    # there is no way to retreive the details of checks so if a check is present
    # in the service it must be reregistered
    if service.has_checks() or not existing or not existing == service:

        service.register(consul_api)
        # check that it registered correctly
        registered = get_service_by_id(consul_api, service.id)
        if registered:
            result = registered
            changed = True

    module.exit_json(changed=changed,
                     service_id=result.id,
                     service_name=result.name,
                     service_port=result.port,
                     checks=map(lambda x: x.to_dict(), service.checks),
                     tags=result.tags)


def remove_service(module, service_id):
    ''' deregister a service from the given agent using its service id '''
    consul_api = get_consul_api(module)
    service = get_service_by_id(consul_api, service_id)
    if service:
        consul_api.agent.service.deregister(service_id)
        module.exit_json(changed=True, id=service_id)

    module.exit_json(changed=False, id=service_id)


def get_consul_api(module, token=None):
    return consul.Consul(host=module.params.get('host'),
                         port=module.params.get('port'),
                         token=module.params.get('token'))


def get_service_by_id(consul_api, service_id):
    ''' iterate the registered services and find one with the given id '''
    for name, service in consul_api.agent.services().iteritems():
        if service['ID'] == service_id:
            return ConsulService(loaded=service)


def parse_check(module):

    if len(filter(None, [module.params.get('script'), module.params.get('ttl'), module.params.get('http')])) > 1:
        module.fail_json(
            msg='check are either script, http or ttl driven, supplying more than one does not make sense')

    if module.params.get('check_id') or module.params.get('script') or module.params.get('ttl') or module.params.get('http'):

       return ConsulCheck(
            module.params.get('check_id'),
            module.params.get('check_name'),
            module.params.get('check_node'),
            module.params.get('check_host'),
            module.params.get('script'),
            module.params.get('interval'),
            module.params.get('ttl'),
            module.params.get('notes'),
            module.params.get('http'),
            module.params.get('timeout')
        )


def parse_service(module):

    if module.params.get('service_name') and module.params.get('service_port'):
        return ConsulService(
            module.params.get('service_id'),
            module.params.get('service_name'),
            module.params.get('service_port'),
            module.params.get('tags'),
        )
    elif module.params.get('service_name') and not module.params.get('service_port'):

        module.fail_json( msg="service_name supplied but no service_port, a port is required to configure a service. Did you configure the 'port' argument meaning 'service_port'?")


class ConsulService():

    def __init__(self, service_id=None, name=None, port=-1,
                 tags=None, loaded=None):
        self.id = self.name = name
        if service_id:
            self.id = service_id
        self.port = port
        self.tags = tags
        self.checks = []
        if loaded:
            self.id = loaded['ID']
            self.name = loaded['Service']
            self.port = loaded['Port']
            self.tags = loaded['Tags']

    def register(self, consul_api):
        if len(self.checks) > 0:
            check = self.checks[0]

            consul_api.agent.service.register(
                self.name,
                service_id=self.id,
                port=self.port,
                tags=self.tags,
                check=check.check)
        else:
            consul_api.agent.service.register(
                self.name,
                service_id=self.id,
                port=self.port,
                tags=self.tags)

    def add_check(self, check):
        self.checks.append(check)

    def checks(self):
        return self.checks

    def has_checks(self):
        return len(self.checks) > 0

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
                and self.id == other.id
                and self.name == other.name
                and self.port == other.port
                and self.tags == other.tags)

    def __ne__(self, other):
        return not self.__eq__(other)

    def to_dict(self):
        data = {'id': self.id, "name": self.name}
        if self.port:
            data['port'] = self.port
        if self.tags and len(self.tags) > 0:
            data['tags'] = self.tags
        if len(self.checks) > 0:
            data['check'] = self.checks[0].to_dict()
        return data


class ConsulCheck():

    def __init__(self, check_id, name, node=None, host='localhost',
                    script=None, interval=None, ttl=None, notes=None, http=None, timeout=None):
        self.check_id = self.name = name
        if check_id:
            self.check_id = check_id
        self.notes = notes
        self.node = node
        self.host = host

        self.interval = self.validate_duration('interval', interval)
        self.ttl = self.validate_duration('ttl', ttl)
        self.script = script
        self.http = http
        self.timeout = self.validate_duration('timeout', timeout)

        self.check = None

        if script:
            self.check = consul.Check.script(script, self.interval)

        if ttl:
            self.check = consul.Check.ttl(self.ttl)

        if http:
            if interval == None:
                raise Exception('http check must specify interval')

            self.check = consul.Check.http(http, self.interval, self.timeout)


    def validate_duration(self, name, duration):
        if duration:
            duration_units = ['ns', 'us', 'ms', 's', 'm', 'h']
            if not any((duration.endswith(suffix) for suffix in duration_units)):
                    raise Exception('Invalid %s %s you must specify units (%s)' %
                        (name, duration, ', '.join(duration_units)))
        return duration

    def register(self, consul_api):
        consul_api.agent.check.register(self.name, check_id=self.check_id,
                                        notes=self.notes,
                                        check=self.check)

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
                and self.check_id == other.check_id
                and self.name == other.name
                and self.script == script
                and self.interval == interval)

    def __ne__(self, other):
        return not self.__eq__(other)

    def to_dict(self):
        data = {}
        self._add(data, 'id', attr='check_id')
        self._add(data, 'name', attr='check_name')
        self._add(data, 'script')
        self._add(data, 'node')
        self._add(data, 'notes')
        self._add(data, 'host')
        self._add(data, 'interval')
        self._add(data, 'ttl')
        self._add(data, 'http')
        self._add(data, 'timeout')
        return data

    def _add(self, data, key, attr=None):
        try:
            if attr == None:
                attr = key
            data[key] = getattr(self, attr)
        except:
            pass

def test_dependencies(module):
    if not python_consul_installed:
        module.fail_json(msg="python-consul required for this module. see http://python-consul.readthedocs.org/en/latest/#installation")

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(default='localhost'),
            port=dict(default=8500, type='int'),
            check_id=dict(required=False),
            check_name=dict(required=False),
            check_node=dict(required=False),
            check_host=dict(required=False),
            notes=dict(required=False),
            script=dict(required=False),
            service_id=dict(required=False),
            service_name=dict(required=False),
            service_port=dict(required=False, type='int'),
            state=dict(default='present', choices=['present', 'absent']),
            interval=dict(required=False, type='str'),
            ttl=dict(required=False, type='str'),
            http=dict(required=False, type='str'),
            timeout=dict(required=False, type='str'),
            tags=dict(required=False, type='list'),
            token=dict(required=False, no_log=True)
        ),
        supports_check_mode=False,
    )

    test_dependencies(module)

    try:
        register_with_consul(module)
    except ConnectionError, e:
        module.fail_json(msg='Could not connect to consul agent at %s:%s, error was %s' % (
                            module.params.get('host'), module.params.get('port'), str(e)))
    except Exception, e:
        module.fail_json(msg=str(e))

# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
