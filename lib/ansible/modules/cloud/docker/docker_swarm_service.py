#!/usr/bin/python

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
module: docker_swarm_service
author: "Dario Zanzico (@dariko)"
short_description: docker swarm service
description: |
  Manage docker services. Allows live altering of already defined services
  (see examples)
version_added: "2.3"
options:
  name:
    required: true
    description:
    - Service name
  image:
    required: true
    description:
    - Service image path and tag.
      Maps docker service IMAGE parameter.
  state:
    required: true
    description:
    - Service state.
    choices:
    - present
    - absent
  args:
    required: false
    default: []
    description:
    - List comprised of the command and the arguments to be run inside
      the container
  constraints:
    required: false
    default: []
    description:
    - List of the service constraints.
      Maps docker service --constraint option.
  labels:
    required: false
    description:
    - List of the service labels.
      Maps docker service --label option.
  container_labels:
    required: false
    description:
    - List of the service containers labels.
      Maps docker service --container-label option.
    default: []
  endpoint_mode:
    required: false
    description:
    - Service endpoint mode.
      Maps docker service --endpoint-mode option.
    default: vip
    choices:
    - vip
    - dnsrr
  env:
    required: false
    default: []
    description:
    - List of the service environment variables.
      Maps docker service --env option.
  limit_cpu:
    required: false
    default: 0.000
    description:
    - Service CPU limit. 0 equals no limit.
      Maps docker service --limit-cpu option.
  reserve_cpu:
    required: false
    default: 0.000
    description:
    - Service CPU reservation. 0 equals no reservation.
      Maps docker service --reserve-cpu option.
  limit_memory:
    required: false
    default: 0
    description:
    - Service memory limit in MB. 0 equals no limit.
      Maps docker service --limit-memory option.
  reserve_memory:
    required: false
    default: 0
    description:
    - Service memory reservation in MB. 0 equals no reservation.
      Maps docker service --reserve-memory option.
  mode:
    required: false
    default: replicated
    description:
    - Service replication mode.
      Maps docker service --mode option.
  mounts:
    required: false
    description:
    - List of dictionaries describing the service mounts.
      Every item must be a dictionary exposing the keys
      source
      target
      type (defaults to 'bind')
      readonly (defaults to false)
      Maps docker service --mount option.
    default: []
  networks:
    required: false
    default: []
    description:
    - List of the service networks names.
      Maps docker service --network option.
  publish:
    default: []
    required: false
    description:
    - List of dictionaries describing the service published ports.
      Every item must be a dictionary exposing the keys
      published_port
      target_port
      protocol (defaults to 'tcp')
  replicas:
    required: false
    default: -1
    description:
    - Number of containers instantiated in the service. Valid only if
      ``mode=='replicated'``.
      If set to -1, and service is not present, service replicas will be
      set to 1.
      If set to -1, and service is present, service replicas will be
      unchanged.
      Maps docker service --replicas option.
  restart_policy:
    required: false
    default: none
    description:
    - Restart condition of the service.
      Maps docker service --restart-condition option.
    choices:
    - none
    - on-failure
    - any
  restart_policy_attempts:
    required: false
    default: 0
    description:
    - Maximum number of service restarts.
      Maps docker service --restart-max-attempts option.
  restart_policy_delay:
    required: false
    default: 0
    description:
    - Delay between restarts.
      Maps docker service --restart-delay option.
  restart_policy_window:
    required: false
    default: 0
    description:
    - Restart policy evaluation window.
      Maps docker service --restart-window option.
  user:
    required: false
    default: root
    description: username or UID
requirements:
  - "docker-py > https://github.com/docker/docker-py/commit/3ac73a285b2f370f6aa300d8a55c5af55660d0f4"
'''

RETURN = '''
ansible_swarm_service:
  description:
  - Dictionary of variables representing the current state of the service.
    Matches the module parameters format.
  - Note that facts are not part of registered vars but accessible directly.
  sample: '{
    "args": [
      "sleep",
      "3600"
    ],
    "constraints": [],
    "container_labels": {},
    "endpoint_mode": "vip",
    "env": [
      "ENVVAR1=envvar1"
    ],
    "image": "alpine",
    "labels": {},
    "limit_cpu": 0.0,
    "limit_memory": 0,
    "mode": "replicated",
    "mounts": [
      {
        "source": "/tmp/",
        "target": "/remote_tmp/",
        "type": "bind"
      }
    ],
    "networks": [],
    "publish": [],
    "replicas": 1,
    "reserve_cpu": 0.0,
    "reserve_memory": 0,
    "restart_policy": "any",
    "restart_policy_attempts": 5,
    "restart_policy_delay": 0,
    "restart_policy_window": 30
  }'
changes:
  description:
  - List of changed service attributes if a service has been altered,
    [] otherwhise
  type: list
  sample: ['container_labels', 'replicas']
rebuilt:
  description:
  - True if the service has been recreated (removed and created)
  type: bool
  sample: True
'''

EXAMPLES = '''
- name: define myservice
    docker_swarm_service:
      name: myservice
      image: "alpine"
      args:
      - "sleep"
      - "3600"
      mounts:
      - source: /tmp/
        target: /remote_tmp/
        type: bind
      env:
        - "ENVVAR1=envvar1"
      restart_policy: any
      restart_policy_attempts: 5
      restart_policy_window: 30
    register: dss_out1
  - name: change myservice.env
    docker_swarm_service:
      name: myservice
      image: "alpine"
      args:
      - "sleep"
      - "7200"
      mounts:
      - source: /tmp/
        target: /remote_tmp/
        type: bind
      env:
        - "ENVVAR1=envvar1"
      restart_policy: any
      restart_policy_attempts: 5
      restart_policy_window: 30
    register: dss_out2
  - debug:
      var: dss_out1
  - fail:
  - name: test for changed myservice facts
    fail:
      msg: unchanged service
    when: "{{ dss_out1 == dss_out2 }}"
  - name: change myservice.image
    docker_swarm_service:
      name: myservice
      image: "alpine:edge"
      args:
      - "sleep"
      - "7200"
      mounts:
      - source: /tmp/
        target: /remote_tmp/
        type: bind
      env:
        - "ENVVAR1=envvar1"
      restart_policy: any
      restart_policy_attempts: 5
      restart_policy_window: 30
    register: dss_out3
  - name: test for changed myservice facts
    fail:
      msg: unchanged service
    when: "{{ dss_out2 == dss_out3 }}"
  - name: remove mount
    docker_swarm_service:
      name: myservice
      image: "alpine:edge"
      args:
      - "sleep"
      - "7200"
      env:
        - "ENVVAR1=envvar1"
      restart_policy: any
      restart_policy_attempts: 5
      restart_policy_window: 30
    register: dss_out4
  - name: test for changed myservice facts
    fail:
      msg: unchanged service
    when: "{{ dss_out3 == dss_out4 }}"
  - name: keep service as it is
    docker_swarm_service:
      name: myservice
      image: "alpine:edge"
      args:
      - "sleep"
      - "7200"
      env:
        - "ENVVAR1=envvar1"
      restart_policy: any
      restart_policy_attempts: 5
      restart_policy_window: 30
    register: dss_out5
  - name: test for changed service facts
    fail:
      msg: changed service
    when: "{{ dss_out5 != dss_out5 }}"
  - name: remove myservice
    docker_swarm_service:
      name: myservice
      state: absent
'''

from ansible.module_utils.docker_common import *

try:
    from docker import utils
    from docker import types
    from docker.utils.types import Ulimit
except:
    # missing docker-py handled in ansible.module_utils.docker
    pass

class DockerService(DockerBaseClass):
  def __init__(self):
    self.constraints=[]
    self.image=""
    self.args = []
    self.endpoint_mode="vip"
    self.env=[]
    self.labels={}
    self.container_labels={}
    self.limit_cpu=0.000
    self.limit_memory=0
    self.reserve_cpu=0.000
    self.reserve_memory=0
    self.mode="replicated"
    self.user="root"
    self.mounts=[]
    self.constraints=[]
    self.networks=[]
    self.publish=[]
    self.replicas=-1
    self.service_id=False
    self.service_version=False
    self.restart_policy = None
    self.restart_policy_attempts = None
    self.restart_policy_delay = None
    self.restart_policy_window = None

  def get_facts(self):
    return {
      'image'                   : self.image,
      'mounts'                  : self.mounts,
      'networks'                : self.networks,
      'args'                    : self.args,
      'env'                     : self.env,
      'publish'                 : self.publish,
      'constraints'             : self.constraints,
      'labels'                  : self.labels,
      'container_labels'        : self.container_labels,
      'mode'                    : self.mode,
      'replicas'                : self.replicas,
      'endpoint_mode'           : self.endpoint_mode,
      'restart_policy'          : self.restart_policy,
      'limit_cpu'               : self.limit_cpu,
      'limit_memory'            : self.limit_memory,
      'reserve_cpu'             : self.reserve_cpu,
      'reserve_memory'          : self.reserve_memory,
      'restart_policy_delay'    : self.restart_policy_delay,
      'restart_policy_attempts' : self.restart_policy_attempts,
      'restart_policy_window'   : self.restart_policy_window
    }

  @staticmethod
  def from_ansible_params(ap, old_service):
    s=DockerService()
    s.constraints              = ap['constraints']
    s.image                    = ap['image']
    s.args                     = ap['args']
    s.endpoint_mode            = ap['endpoint_mode']
    s.env                      = ap['env']
    s.labels                   = ap['labels']
    s.container_labels         = ap['container_labels']
    s.limit_cpu                = ap['limit_cpu']
    s.limit_memory             = ap['limit_memory']
    s.reserve_cpu              = ap['reserve_cpu']
    s.reserve_memory           = ap['reserve_memory']
    s.mode                     = ap['mode']
    s.mounts                   = ap['mounts']
    s.constraints              = ap['constraints']
    s.networks                 = ap['networks']
    s.publish                  = ap['publish']
    s.restart_policy           = ap['restart_policy']
    s.restart_policy_attempts  = ap['restart_policy_attempts']
    s.restart_policy_delay     = ap['restart_policy_delay']
    s.restart_policy_window    = ap['restart_policy_window']
    s.user                     = ap['user']

    if ap['replicas'] == -1:
      if old_service:
        s.replicas = old_service.replicas
      else:
        s.replicas = 1
    else:
      s.replicas                 = ap['replicas']

    for param_name in ['reverve_memory', 'reserve_cpu',
                       'limit_memory'  , 'limit_cpu']:
      if ap.get(param_name):
        try:
          setattr(s, param_name, human_to_bytes(ap[param_name]))
        except ValueError as exc:
          raise Exception("Failed to convert %s to bytes: %s" % (param_name, exc))

    s.publish=[]
    for param_p in ap['publish']:
      service_p = {}
      service_p['protocol']       = param_p.get( 'protocol', 'tcp' )
      service_p['published_port'] = param_p['published_port']
      service_p['target_port']    = param_p['target_port']
      if service_p['protocol'] not in ['tcp', 'udp']:
        raise ValueError("got publish.protocol '%s', valid values:'tcp', 'udp'" %
                         service_p['protocol'])
      s.publish.append(service_p)
    s.mounts=[]
    for param_m in ap['mounts']:
      service_m = {}
      service_m['readonly'] = bool(param_m.get('readonly', False))
      service_m['type']     = param_m.get('type', 'bind')
      service_m['source']   = param_m['source']
      service_m['target']   = param_m['target']
      s.mounts.append(service_m)
    return s

  def compare(self,os):
    differences = []
    needs_rebuild = False
    if self.endpoint_mode!=os.endpoint_mode:
      differences.append('endpoint_mode')
    if self.env!=os.env:
      differences.append('env')
    if self.mode!=os.mode:
      needs_rebuild = True
      differences.append('mode')
    if self.mounts!=os.mounts:
      differences.append('mounts')
    if self.networks!=os.networks:
      differences.append('networks')
      needs_rebuild = True
    if self.replicas!=os.replicas:
      differences.append('replicas')
    if self.args!=os.args:
      differences.append('args')
    if self.constraints!=os.constraints:
      differences.append('constraints')
    if self.labels!=os.labels:
      differences.append('labels')
    if self.limit_cpu!=os.limit_cpu:
      differences.append('limit_cpu')
    if self.limit_memory!=os.limit_memory:
      differences.append('limit_memory')
    if self.reserve_cpu!=os.reserve_cpu:
      differences.append('reserve_cpu')
    if self.reserve_memory!=os.reserve_memory:
      differences.append('reserve_memory')
    if self.container_labels!=os.container_labels:
      differences.append('container_labels')
    if self.publish!=os.publish:
      differences.append('publish')
    if self.restart_policy!=os.restart_policy:
      differences.append('restart_policy')
    if self.restart_policy_attempts!=os.restart_policy_attempts:
      differences.append('restart_policy_attempts')
    if self.restart_policy_delay!=os.restart_policy_delay:
      differences.append('restart_policy_delay')
    if self.restart_policy_window!=os.restart_policy_window:
      differences.append('restart_policy_window')
    if self.image!=os.image:
      differences.append('image')
    if self.user!=os.user:
      differences.append('user')
    return len(differences)>0, differences, needs_rebuild

  def __str__(self):
    return str({
      'mode': self.mode,
      'env': self.env,
      'endpoint_mode': self.endpoint_mode,
      'mounts': self.mounts,
      'networks': self.networks,
      'replicas': self.replicas
    })
  def generate_docker_py_service_description(self, name, docker_networks):
      cspec={
        'Image': self.image,
        'User': self.user
      }
      cspec['Mounts']=[]
      for mount_config in self.mounts:
        cspec['Mounts'].append({
          'Target': mount_config['target'],
          'Source': mount_config['source'],
          'Type': mount_config['type'],
          'ReadOnly': mount_config['readonly']
        })
      cspec['Args']=self.args
      cspec['Env']=self.env
      cspec['Labels']=self.container_labels
      restart_policy=types.RestartPolicy(
        condition     = self.restart_policy,
        delay         = self.restart_policy_delay,
        max_attempts  = self.restart_policy_attempts,
        window        = self.restart_policy_window
      )
      resources={
        'Limits': {
          'NanoCPUs': int(self.limit_cpu * 1000000000),
          'MemoryBytes': self.limit_memory*1024*1024
        },
        'Reservations': {
          'NanoCPUs': int(self.reserve_cpu * 1000000000),
          'MemoryBytes': self.reserve_memory*1024*1024
        }
      }
      task_template=types.TaskTemplate(
        container_spec  = cspec,
        restart_policy  = restart_policy,
        placement       = self.constraints,
        resources       = resources
      )
      mode = { 'Replicated': {'Replicas': self.replicas} }
      if self.mode=='global':
        mode = { 'Global': {} }

      networks=[]
      for network_name in self.networks:
        network_id = None
        try:
          network_id = filter( lambda n: n['name']==network_name, docker_networks )[0]['id']
        except:
          pass
        if network_id:
          networks.append (
            { 'Target': network_id }
          )
        else:
          raise Exception("no docker networks named: %s" % network_name)

      endpoint_spec= {'Mode': self.endpoint_mode }
      endpoint_spec['Ports'] = []
      for port in self.publish:
        endpoint_spec['Ports'].append({
          'Protocol': port['protocol'],
          'PublishedPort': int(port['published_port']),
          'TargetPort': int(port['target_port'])
        })
      return task_template, networks, endpoint_spec, mode, self.labels

  def fail(self, msg):
    self.parameters.client.module.fail_json(msg=msg)

  @property
  def exists(self):
    return True if self.service else False

class DockerServiceManager():
  def get_networks_names_ids(self):
    return [{'name': n['Name'], 'id': n['Id']} for n in self.client.networks()]

  def get_service(self, name):
    raw_data=self.client.services( filters={'name': name} )
    if len(raw_data)==0:
      return None

    raw_data=raw_data[0]
    networks_names_ids=self.get_networks_names_ids()
    ds=DockerService()

    task_template_data = raw_data['Spec']['TaskTemplate']

    ds.image = task_template_data['ContainerSpec']['Image']
    ds.user  = task_template_data['ContainerSpec'].get('User','root')
    ds.env   = task_template_data['ContainerSpec'].get('Env',[])
    ds.args  = task_template_data['ContainerSpec'].get('Args',[])

    if 'Placement' in task_template_data.keys():
      ds.constraints = task_template_data['Placement'].get('Constraints',[])

    restart_policy_data = task_template_data.get('RestartPolicy',None)
    if restart_policy_data:
      ds.restart_policy           = restart_policy_data.get('Condition')
      ds.restart_policy_delay     = restart_policy_data.get('Delay')
      ds.restart_policy_attempts  = restart_policy_data.get('MaxAttempts')
      ds.restart_policy_window    = restart_policy_data.get('Window')

    raw_data_endpoint = raw_data.get('Endpoint',None)
    if raw_data_endpoint:
      raw_data_endpoint_spec = raw_data_endpoint.get('Spec',None)
      if raw_data_endpoint_spec:
        ds.endpoint_mode = raw_data_endpoint_spec.get('Mode','vip')
        for port in raw_data_endpoint_spec.get('Ports',[]):
          ds.publish.append({
            'protocol': port['Protocol'],
            'published_port': str(port['PublishedPort']),
            'target_port': str(port['TargetPort'])
          })

    if 'Resources' in task_template_data.keys():
      if 'Limits' in task_template_data['Resources'].keys():
        if 'NanoCPUs' in task_template_data['Resources']['Limits'].keys():
          ds.limit_cpu      = float(task_template_data['Resources']['Limits']['NanoCPUs'])/1000000000
        if 'MemoryBytes' in task_template_data['Resources']['Limits'].keys():
          ds.limit_memory   = int(task_template_data['Resources']['Limits']['MemoryBytes'])/1024/1024
      if 'Reservations' in task_template_data['Resources'].keys():
        if 'NanoCPUs' in task_template_data['Resources']['Reservations'].keys():
          ds.reserve_cpu    = float(task_template_data['Resources']['Reservations']['NanoCPUs'])/1000000000
        if 'MemoryBytes' in task_template_data['Resources']['Reservations'].keys():
          ds.reserve_memory = int(task_template_data['Resources']['Reservations']['MemoryBytes'])/1024/1024

    ds.labels=raw_data['Spec'].get('Labels',{})
    ds.container_labels = task_template_data['ContainerSpec'].get('Labels',{})
    mode=raw_data['Spec']['Mode']
    if 'Replicated' in mode.keys():
      ds.mode=unicode('replicated','utf-8')
      ds.replicas = mode['Replicated']['Replicas']
    elif 'Global' in mode.keys():
      ds.mode='global'
    else:
      raise Exception("Unknown service mode: %s" % mode)
    for mount_data in raw_data['Spec']['TaskTemplate']['ContainerSpec'].get('Mounts',[]):
      ds.mounts.append({
        'source': mount_data['Source'],
        'type': mount_data['Type'],
        'target': mount_data['Target'],
        'readonly': mount_data.get('ReadOnly', False)
      })
    for raw_network_data in raw_data['Spec'].get('Networks',[]):
      network_name=[network_name_id['name'] for network_name_id in networks_names_ids if network_name_id['id']==raw_network_data['Target']][0]
      ds.networks.append(network_name)
    ds.service_version  = raw_data['Version']['Index']
    ds.service_id       = raw_data['ID']

    return ds

  def update_service(self, name, old_service, new_service):
    task_template, networks, endpoint_spec, mode, labels = new_service.generate_docker_py_service_description(name,self.get_networks_names_ids())
    self.client.update_service(
      old_service.service_id,
      old_service.service_version,
      name = name,
      endpoint_config = endpoint_spec,
      networks        = networks,
      mode            = mode,
      task_template   = task_template,
      labels          = labels
    )

  def create_service(self, name, service):
    task_template, networks, endpoint_spec, mode, labels = service.generate_docker_py_service_description(name,self.get_networks_names_ids())
    self.client.create_service(
      name            = name,
      endpoint_config = endpoint_spec,
      mode            = mode,
      networks        = networks,
      task_template   = task_template,
      labels          = labels
    )

  def remove_service(self, name):
    self.client.remove_service(name)

  def __init__(self, client):
    self.client = client

  def run(self):
    module = self.client.module
    try:
      current_service = self.get_service(module.params['name'])
    except Exception as e:
      module.fail_json(
        msg = "Error looking for service named %s: %s" %
                         ( module.params['name'], e ))
    try:
      new_service = DockerService.from_ansible_params(module.params, current_service)
    except Exception as e:
      module.fail_json(
        msg = "Error parsing module parameters: %s" % e )

    changed=False
    msg='noop'
    rebuilt=False
    changes=[]
    facts = {}

    if current_service:
      if module.params['state'] == 'absent':
        if not module.check_mode:
          self.remove_service(module.params['name'])
        msg = 'Service removed'
        changed = True
      else:
        changed, changes, need_rebuild = new_service.compare(current_service)
        if changed:
          changed = True
          if need_rebuild:
            if not module.check_mode:
              self.remove_service(module.params['name'])
              self.create_service(module.params['name'], new_service)
            msg     = 'Service rebuilt'
            rebuilt = True
            changes = changes
          else:
            if not module.check_mode:
              self.update_service(module.params['name'],current_service,new_service)
            msg     = 'Service updated'
            rebuilt = False
            changes = changes
        else:
            msg     = 'Service unchanged'
        facts = new_service.get_facts()
    else:
      if module.params['state'] == 'absent':
        msg     = 'Service absent'
      else:
        if not module.check_mode:
          service_id=self.create_service( module.params['name'], new_service )
        msg='Service created'
        changed=True
        facts = new_service.get_facts()

    return msg, changed, rebuilt, changes, facts


def main():
  argument_spec = dict(
    name                    = dict( required=True ),
    image                   = dict(type='str'),
    state                   = dict( default= "present", choices=['present', 'absent'] ),
    mounts                  = dict( default=[], type='list'),
    networks                = dict( default=[], type='list'),
    args                    = dict( default=[], type='list' ),
    env                     = dict( default=[], type='list' ),
    publish                 = dict( default=[], type='list' ),
    constraints             = dict( default=[], type='list' ),
    labels                  = dict( default={}, type='dict' ),
    container_labels        = dict( default={}, type='dict' ),
    mode                    = dict( default="replicated" ),
    replicas                = dict( default=-1, type='int' ),
    endpoint_mode           = dict( default='vip', choices=['vip', 'dnsrr'] ),
    restart_policy          = dict( default='none', choices=['none', 'on-failure', 'any'] ),
    limit_cpu               = dict( default=0, type='float' ),
    limit_memory            = dict( default=0, type='int' ),
    reserve_cpu             = dict( default=0, type='float' ),
    reserve_memory          = dict( default=0, type='int' ),
    restart_policy_delay    = dict( default=0, type='int' ),
    restart_policy_attempts = dict( default=0, type='int' ),
    restart_policy_window   = dict( default=0, type='int' ),
    user                    = dict( default='root' )
  )
  required_if = [
    ('state', 'present', [
        'image',
      ]
    )
  ]
  client = AnsibleDockerClient(
    argument_spec=argument_spec,
    required_if=required_if,
    supports_check_mode=True
  )

  dsm = DockerServiceManager(client)
  msg, changed, rebuilt, changes, facts = dsm.run()

  client.module.exit_json(msg=msg, changed=changed, rebuilt=rebuilt, changes=changes, ansible_docker_service=facts )

if __name__ == '__main__':
  main()
