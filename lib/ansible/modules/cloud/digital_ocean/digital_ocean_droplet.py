#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: digital_ocean_droplet
short_description: Create, rebuild, delete a DigitalOcean droplet.
description:
     - Create, rebuild, or delete a droplet in DigitalOcean.
version_added: "2.8"
author: "Gurchet Rai (@gurch101)"
options:
  state:
    description:
     - Ensure droplet is C(present) or C(absent). If C(present) and exists and I(rebuild=True), then rebuild it.
    default: present
    type: str
    choices: ['present', 'absent']
  id:
    description:
     - Numeric I(id) of the Droplet you want to check, delete or rebuild.
     - If both I(id) and I(name) are present and a droplet with that I(id) exists, I(name) will be ignored.
    type: int
    aliases: ['droplet_id']
  name:
    description:
     - Droplet name, must be a valid hostname or a FQDN in your domain.
     - DigitalOcean will make a DNS PTR record for public IPv4 (and IPv6 if I(ipv6=yes)) on droplet creation if it's FQDN.
     - Required when I(state=present) and the droplet does not yet exist.
    type: str
  unique_name:
    description:
     - Deprecated and ignored parameter. Consider it always True.
     - It contradicts FQDN use for name and my lead to unpredictable behaviour (i.e. bugs) in your plays.
     - DigitalOcean does not enforce it at the moment but dropped it from API docs and may deprecate it soon.
     - If droplet with I(name=mydroplet) exists in your account this module will return it
       and will not create a new one with the same name.
  size:
    description:
     - Droplet configuration slug, e.g. C(s-1vcpu-1gb), C(2gb), C(c-32vcpu-64gb), or C(s-32vcpu-192gb).
     - If you forget to supply that, the module will build the cheapest droplet C(s-1vcpu-1gb).
     - If you need to grow your droplet you may do that later.
    type: str
    aliases: ['size_id']
  image:
    description:
     - Image slug or ID for new or rebuilt droplet e.g. C(ubuntu-16-04-x64) or C(42251561).
     - Required when I(state=present) and the droplet does not yet exist.
    type: str
    aliases: ['image_id']
  region:
    description:
     - Datacenter slug you would like your droplet to be created in, e.g. C(sfo2), C(sfo1), or C(sgp1).
     - Required when I(state=present) and the droplet does not yet exist.
     - "New DigitalOcean users be aware: due to limited capacity, C(nyc2), c(ams2), and C(sfo1) are
      currently available only to resource owners in respective datacenters."
    type: str
    aliases: ['region_id']
  ssh_keys:
    description:
     - 'List of DigitalOcean registered SSH key numeric IDs or fingerprints to put in ~root/authorized_keys on creation, e.g.
       C(12345) or C("1e:f8:e3:b2:0d:dc:15:02:aa:54:15:23:bc:5c:ec:34").'
     - You may register keys with M(digital_ocean_sshkey) and list them with M(digital_ocean_sshkey_facts).
     - "Hint: compute fingerprint C(cut -f2 -d' ' ~/.ssh/do_key1.pub| base64 -d | md5sum -b | sed 's/../&:/g; s/: .*$//'),
     or grab it from M(digital_ocean_sshkey_facts), or from your tab U(https://cloud.digitalocean.com/account/security)"
    type: list
  private_networking:
    description:
     - Add an additional, private network interface to the newly created droplet.
     - Private networking isolates communication at the account or team level between Droplets located in the same datacenter.
     - Useful e.g. for a droplet behind DigitalOcean Load Balancer.
     - No Multicast or Broadcast support.
    default: False
    type: bool
  user_data:
    description:
     - string data >64KB, e.g. a 'cloud-config' file or a Bash script to configure the Droplet on first boot.
    type: str
  ipv6:
    description:
     - Enable IPv6 for new droplet if C(True).
    default: False
    type: bool
  wait:
    description:
     - Wait for the droplet IPv4 address, ensure the droplet is usable (locked=false).
    default: True
    type: bool
  wait_build:
    description:
     - 'When I(wait: True) and this droplet is built/rebuilt, wait I(wait_build) seconds before checking droplet status.'
    type: int
    default: 30
  wait_step:
    description:
     - 'When I(wait: True) after I(wait_build) seconds passed, query DigitalOcean API
      with I(wait_step) seconds pauses if I(wait_timeout) is not exceeded'
    type: float
    default: 2
  wait_timeout:
    description:
     - How long before wait gives up, in seconds, when creating/rebuilding a droplet.
     - If I(wait_build)>I(wait_timeout), timeout may happen only after I(wait_build).
    type: int
    default: 120
  backups:
    description:
     - indicates whether automated backups should be enabled.
    default: False
    type: bool
  monitoring:
    description:
     - Install DigitalOcean monitoring agent on a new Droplet if C(True).
    default: False
    type: bool
  tags:
    description:
     - A list of strings to tag the Droplet with on creation. A tag can be existing or new.
    type: list
  volumes:
    description:
     - A list of Block Storage volume identifiers to attach to new Droplet.
     - "Note: a volume can only be attached to a single Droplet."
    type: list
  rebuild:
    description:
     - force Droplet rebuild. You may supply I(image) id/slug if you want it changed or omit I(image) and just re-fresh your Droplet.
     - 'WARNING: droplet own data will be lost!'
    default: False
    type: bool
requirements:
  - "python >= 2.6"

extends_documentation_fragment: digital_ocean.documentation
'''


EXAMPLES = '''
- name: create new droplet. If droplet with this name exists other parameters ignored.
  digital_ocean_droplet:
    state: present
    name: mydroplet.example.com
    oauth_token: "{{ lookup('file', '~/.do/api-key1') }}"
    size: 1gb
    region: sfo1
    image: ubuntu-16-04-x64
    tags: [ 'foo', 'bar' ]
    wait_timeout: 500
  register: my_droplet

- debug:
    msg: "ID is {{ my_droplet.data.droplet.id }}, IP is {{ my_droplet.data.ip_address }}"

- name: Check droplet exists, get details
  digital_ocean_droplet:
    name: mydroplet.example.com
    oauth_token: "{{ lookup('file', '~/.do/api-key1') }}"
  register: my_droplet

- name: ensure a droplet is like new
  digital_ocean_droplet:
    name: mydroplet.example.com
    oauth_token: "{{ lookup('file', '~/.do/api-key1') }}"
    rebuild: yes
    image: debian-9-x64  # may be omitted.
    wait_step: 3.5
    wait_build: 16  # wait 16 seconds, then GET DigitalOcean API droplet status with 3.5 seconds pauses, unless default wait_timeout (120 s) is reached.
  register: my_droplet
'''


RETURN = '''
data:
  description: DigitalOcean API Response with IP addresses exposed
  returned: success and present
  type: complex
  contains:
    ip_address:
      description: public IPv4 address
      type: str
      returned: success and present
      sample: "139.59.144.10"
    ipv6_address:
      description: IPv6 address (public)
      type: str
      returned: success and present and ipv6
      sample: "2A03:B0C0:0003:00D0:0000:0000:0424:0001"
    private_ipv4_address:
      description: private IPv4 address
      type: str
      returned: success and present and private_networking
      sample: "10.135.133.25"
    ops:
      description: When building/rebuilding droplet with 'ansible-playbook -v' debug messages can be seen here.
      type: list
      returned: success and present and -v
      sample: |-
        ["1550503109.96 module start",
         "1550503130.08 status off locked True net {'type': 'public', 'netmask': '255.255.240.0', 'ip_address': '139.59.144.10', 'gateway': '139.59.144.1'}",
         "1550503134.6 status active locked False net {'type': 'public', 'netmask': '255.255.240.0', 'ip_address': '139.59.144.10', 'gateway': '139.59.144.1'}"
        ]
    droplet:
      description: exact DigitalOcean API Response
      returned: success and present
      type: complex
      contains:
        id:
          type: int
          sample: 3164494
        name:
          type: str
          sample: "mydroplet.example.com"
        locked:
          type: bool
          sample: false
        status:
          type: str
          sample: "active"
        tags:
          type: list
          sample: []
        created_at:
          type: str
          sample: "2017-11-14T16:36:31Z"
        backup_ids:
          type: list
          sample: []
        next_backup_window:
          sample: null
        snapshot_ids:
          type: list
          sample: []
        image:
          type: complex
          contains:
            id:
              type: int
              sample: 43130763
            slug:
              type: str
              sample: "debian-9-x64"
        volume_ids:
          type: list
          sample: []
        size:
          type: complex
          contains:
            transfer:
              type: float
              sample: 1.0
            price_monthly:
              type: float
              sample: 5.0
            price_hourly:
              type: float
              sample: 0.00744
            slug:
              type: str
              sample: "1gb"
        size_slug:
          sample: "1gb"
        networks:
          type: complex
          contains:
            v4:
              type: list
              sample:
                - {"ip_address": "139.59.144.10",
                 "type": "public", "gateway": "139.59.144.1", "netmask": "255.255.240.0"}
                - {"ip_address": "10.135.133.25",
                 "type": "private", "gateway": "10.135.0.1", "netmask": "255.255.0.0"}
            v6:
              type: list
              sample:
                 - {"ip_address": "2A03:B0C0:0003:00D0:0000:0000:0424:0001", "netmask": 64,
                  "type": "public", "gateway": "2A03:B0C0:0003:00D0:0000:0000:0000:0001"}
        region:
          type: complex
          contains:
            available:
              type: bool
              sample: True
            slug:
              type: str
              sample: "fra1"
            name:
              type: str
              sample: "Frankfurt 1"
            features:
              type: list
              sample: ["private_networking", "backups", "ipv6", "metadata", "install_agent", "storage", "image_transfer"]
            sizes:
              type: list
              sample: ["512mb", "1gb", "2gb", "s-1vcpu-1gb", "s-3vcpu-1gb", "s-1vcpu-2gb", "s-2vcpu-2gb", "s-1vcpu-3gb",
              "s-2vcpu-4gb", "4gb", "s-4vcpu-8gb", "8gb", "s-6vcpu-16gb", "16gb"]
        features:
          type: list
          sample: ["private_networking", "ipv6"]
        memory:
          type: int
          sample: 1024
        vcpus:
          type: int
          sample: 1
        disk:
          type: int
          sample: 25
        kernel:
          sample: null
'''

import time
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.digital_ocean import DigitalOceanHelper


class DODroplet(object):
    def __init__(self, module):
        self.ops = []
        if module._verbosity >= 1:
            self.ops.append('{0} module start'.format(time.time()))
        self.module = module
        self._id = self.module.params['id']
        self._name = self.module.params['name']
        self._droplet = None  # == _id if found by _id
        self.rest = DigitalOceanHelper(module)
        # pop all the parameters which we never POST as data
        self.rebuild = self.module.params.pop('rebuild')
        self.wait = self.module.params.pop('wait')
        self.wait_timeout = self.module.params.pop('wait_timeout')
        self.wait_step = self.module.params.pop('wait_step')
        self.wait_build = self.module.params.pop('wait_build')
        self.module.params.pop('timeout')
        self.module.params.pop('validate_certs')
        self.module.params.pop('oauth_token')
        if self.module.params.pop('unique_name', None) is not None:
            self.module.warn("Parameter `unique_name` is deprecated. Consider it always True.")
        if self._id and self._name:
            self.module.warn("Both id {0} and name {1} supplied. Your play may turn unexpectedly!".
                             format(self._id, self._name))

    def get_by_id(self, droplet_id):
        if not droplet_id:
            return None
        response = self.rest.get('droplets/{0}'.format(droplet_id))
        if response.status_code == 200:
            self._droplet = droplet_id
            return response.json
        return None

    def find_by_name(self, droplet_name):
        if not droplet_name:
            return None
        page = 1
        while page is not None:
            response = self.rest.get('droplets?page={0}'.format(page))
            json_data = response.json
            if response.status_code == 200:
                for droplet in json_data['droplets']:
                    if droplet['name'] == droplet_name:
                        self._droplet = droplet_name
                        return {'droplet': droplet}
                if 'links' in json_data and 'pages' in json_data['links'] and 'next' in json_data['links']['pages']:
                    page += 1
                else:
                    page = None
        return None

    def expose_addresses(self, data):
        """
         Expose IP addresses as their own property the same way M(digital_ocean) did.
         Append run log (if exists)
        """
        networks = data['droplet']['networks']
        for network in networks.get('v4', []):
            if network['type'] == 'public':
                data['ip_address'] = network['ip_address']
            elif network['type'] == 'private':
                data['private_ipv4_address'] = network['ip_address']
        for network in networks.get('v6', []):
            if network['type'] == 'public':
                data['ipv6_address'] = network['ip_address']
        if self.ops:
            data['ops'] = self.ops
        return data

    def find_droplet(self):
        json_data = self.get_by_id(self._id)
        if not json_data:
            json_data = self.find_by_name(self._name)
        return json_data

    def _params_ok(self, name, image, region):
        """
        When creating droplet we need at least name, image, and region.
        :return:
        True if all the parameters were supplied.
        """
        return name and image and region

    @staticmethod
    def same_dc(j, dc):
        if (
           j and dc and
           'droplet' in j and
           'region' in j['droplet'] and
           'slug' in j['droplet']['region']):
            return j['droplet']['region']['slug'] == dc
        return None

    @staticmethod
    def same_size(j, size):
        if (
           j and size and
           'droplet' in j and
           'size_slug' in j['droplet']):
            return j['droplet']['size_slug'] == size
        return None

    @staticmethod
    def same_image(j, image):
        if (
           j and image and
           'droplet' in j and
           'image' in j['droplet'] and
           'id' in j['droplet']['image'] and
           'slug' in j['droplet']['image']):
            return (j['droplet']['image']['slug'] == image
                    or str(j['droplet']['image']['id']) == image)
        return None

    @staticmethod
    def same_tags(j, tags):
        pt = tags if tags else []
        if (
           j and
           'droplet' in j and
           'tags' in j['droplet'] and
           len(j['droplet']['tags']) == len(pt)):
            return set(j['droplet']['tags']) - set(pt) == set([])
        return None

    def get(self):
        """
        Find the droplet (either by id or name), rebuild if requested so, build if not found.
        """
        json_data = self.find_droplet()
        if json_data and not self.same_dc(json_data, self.module.params['region']):
            self.module.warn("Droplet found but 'region' differs!")
        if json_data and not self.same_size(json_data, self.module.params['size']):
            self.module.warn("Droplet found but 'size' differs!")
        if json_data and not self.same_image(json_data, self.module.params['image']) and not self.rebuild:
            self.module.warn("Droplet found but 'image' differs! To re-image the droplet add 'rebuild=yes'")
        if json_data and not self.same_tags(json_data, self.module.params['tags']):
            self.module.warn("Droplet found but 'tags' differ!")

        if json_data and not self.rebuild:
            self.module.exit_json(changed=False, data=self.expose_addresses(json_data))
        elif self.rebuild and not json_data:
            self.module.fail_json(changed=False, msg='droplet {0} not found. Rebuild failed.'.format(self._droplet))
        elif self.rebuild and json_data:
            self._rebuild(json_data)
        else:
            self._build()

    def _build(self):
        _size = self.module.params['size']
        _image = self.module.params['image']
        _region = self.module.params['region']
        # we are going to build a new droplet now. Final checks.
        if self._id:
            self.module.warn("Trying to build {0}. Parameter id is found, it makes no sense here!".format(self._name))
        if not _size:
            _default_size = 's-1vcpu-1gb'
            self.module.warn("Missing 'size' parameter. Using size={0}".format(_default_size))
            _size = _default_size
        if not self._params_ok(self._name, _image, _region):
            self.module.fail_json(changed=False, msg='Droplet not created. Not enough parameters: name={0} region={1}'
                                                     ' image={2} size={3}'.format(self._name, _region, _image, _size))
        if self.module.check_mode:
            self.module.exit_json(changed=True)
        if self.ops:
            self.ops.append("{0} posting create droplet command.".format(time.time()))
        response = self.rest.post('droplets', data=self.module.params)
        if self.ops:
            if response.json and 'droplet' in response.json:
                dbg1 = response.json['droplet']
            elif response.json:
                dbg1 = response.json
            else:
                dbg1 = "! no JSON !"
            self.ops.append("{0} create droplet response: {1}".format(time.time(), dbg1))
        if response.status_code >= 400:
            self.module.fail_json(changed=False, msg=response.json['message'])
        jr = self.ready(response.json['droplet']['id'], action="create", build=True) if self.wait \
            else response.json
        self.module.exit_json(changed=True, data=self.expose_addresses(jr))

    def _rebuild(self, json_data):
        if self._id and self._name:
            self.module.warn("Trying to rebuild droplet id={0}. Parameter name is found too,"
                             " it makes no sense here!".format(self._id))
        if self.module.check_mode:
            self.module.exit_json(changed=True)
        droplet_id = json_data['droplet']['id']
        curr_image = json_data['droplet']['image']['id']
        do_image = self.module.params['image'] if 'image' in self.module.params and self.module.params['image'] \
            else curr_image
        cmd_data = {'type': "rebuild", 'image': do_image}
        response = self.rest.post('droplets/{0}/actions'.format(droplet_id), data=cmd_data)
        if response.status_code >= 400:
            self.module.fail_json(changed=False, msg=response.json['message'])
        self.module.exit_json(  # wait for rebuild to finish, enrich received JSON, then return it.
            changed=True, data=self.expose_addresses(
                self.ready(droplet_id, action="rebuild", build=True)))

    def delete(self):
        json_data = self.find_droplet()
        if json_data:
            if self.module.check_mode:
                self.module.exit_json(changed=True)
            response = self.rest.delete('droplets/{0}'.format(json_data['droplet']['id']))
            if response.status_code == 204:
                self.module.exit_json(changed=True, msg='Droplet deleted')
            self.module.fail_json(changed=False, msg='Failed to delete droplet {0}'.format(self._droplet))
        else:
            self.module.exit_json(changed=False, msg='Droplet {0} not found'.format(self._droplet))

    def ready(self, droplet_id, action, build=False):
        if build and self.wait_build > self.wait_timeout:
            timeout = self.wait_build
        else:
            timeout = self.wait_timeout
        end_time = time.time() + timeout + 0.2  # compensate for time.sleep() inaccuracy
        if build:
            time.sleep(self.wait_build)
        locked = True
        while time.time() < end_time:
            response = self.rest.get('droplets/{0}'.format(droplet_id))
            if self.ops:
                rj = response.json
                if 'droplet' in rj and 'locked' in rj['droplet']:
                    if 'v4' in rj['droplet']['networks'] and len(response.json['droplet']['networks']['v4']):
                        net = response.json['droplet']['networks']['v4'][0]
                    else:
                        net = rj['droplet']['networks']
                    lck = response.json['droplet']['locked']
                    sta = response.json['droplet']['status']
                self.ops.append("{0} status {1} locked {2} net {3}".format(time.time(), sta, lck, net))
            locked = response.json['droplet']['locked']
            has_net = len(response.json['droplet']['networks']['v4'])
            if not locked and has_net:
                return response.json
            time.sleep(min(self.wait_step, end_time - time.time()))
        if action == 'create' and not locked:  # but not has_net
            self.module.warn('Droplet created but no IPv4 net found in {0} seconds.'.format(timeout))
            return response.json
        self.module.fail_json(msg='Droplet {0} action "{1}" not finished in {2} seconds.'.format(self._droplet, action, timeout))


def main():
    argument_spec = DigitalOceanHelper.digital_ocean_argument_spec()
    argument_spec.update(
        state=dict(choices=['present', 'absent'], default='present'),
        name=dict(type='str'),
        size=dict(aliases=['size_id']),
        image=dict(aliases=['image_id']),
        rebuild=dict(type='bool', default=False),
        region=dict(aliases=['region_id']),
        ssh_keys=dict(type='list'),
        private_networking=dict(type='bool', default=False),
        backups=dict(type='bool', default=False),
        monitoring=dict(type='bool', default=False),
        id=dict(aliases=['droplet_id'], type='int'),
        user_data=dict(default=None),
        ipv6=dict(type='bool', default=False),
        volumes=dict(type='list'),
        tags=dict(type='list'),
        wait=dict(type='bool', default=True),
        wait_timeout=dict(default=120, type='int'),
        wait_step=dict(default=2.0, type='float'),
        wait_build=dict(default=30, type='int'),
        unique_name=dict(),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=(
            ['id', 'name'],
            ['oauth_token', 'api_token'],  # FIXME: oauth_token docs should have 'required: yes'
        ),
        supports_check_mode=True,
    )
    state = module.params.pop('state')
    droplet = DODroplet(module)
    if state == 'present':
        droplet.get()
    elif state == 'absent':
        droplet.delete()


if __name__ == '__main__':
    main()
