#!/usr/bin/python

# (c) 2013, Paul Markham <pmarkham@netrefinery.com>
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

import sys
import os
import platform
import tempfile

DOCUMENTATION = '''
---
module: solaris_zone
short_description: Manage Solaris zones
description:
   - Create, start, stop and delete Solaris zones. This module doesn't currently allow
     changing of options for a zone that's already been created.
version_added: "2.0"
author: Paul Markham
requirements:
  - Solaris 10 or later
options:
  state:
    required: true
    description:
      - C(present), create the zone.
      - C(running), if the zone already exists, boot it, otherwise, create the zone
          first, then boot it.
      - C(started), synonym for C(running).
      - C(stopped), shutdown a zone.
      - C(absent), destroy the zone.
    choices: ['present', 'started', 'running', 'stopped', 'absent']
  name:
    description:
      - Zone name.
    required: true
  path:
    description:
      - The path where the zone will be created. This is required when the zone is created, but not
        used otherwise.
    required: false
    default: null
  sparse:
    description:
      - Whether to create a sparse (C(true)) or whole root (C(false)) zone.
    required: false
    default: false
  root_password:
    description:
      - The password hash for the root account. If not specified, the zone's root account
        will not have a password.
    required: false
    default: null
  config:
    required: false
    description:
      - 'The zonecfg configuration commands for this zone, separated by commas, e.g.
        "set auto-boot=true,add net,set physical=bge0,set address=10.1.1.1,end"
        See the Solaris Systems Administrator guide for a list of all configuration commands
        that can be used.'
    required: false
    default: null
  create_options:
    required: false
    description:
      - 'Extra options to the zonecfg create command. For example, this can be used to create a
        Solaris 11 kernel zone'
    required: false
    default: null
  timeout:
    description:
      - Timeout, in seconds, for zone to boot.
    required: false
    default: 600
'''

EXAMPLES = '''
# Create a zone, but don't boot it
solaris_zone: name=zone1 state=present path=/zones/zone1 sparse=true root_password="Be9oX7OSwWoU."
      config='set autoboot=true, add net, set physical=bge0, set address=10.1.1.1, end'

# Create a zone and boot it
solaris_zone: name=zone1 state=running path=/zones/zone1 root_password="Be9oX7OSwWoU."
      config='set autoboot=true, add net, set physical=bge0, set address=10.1.1.1, end'

# Boot an already created zone
solaris_zone: name=zone1 state=running

# Stop a zone
solaris_zone: name=zone1 state=stopped

# Destroy a zone
solaris_zone: name=zone1 state=absent
'''

class Zone(object):
    def __init__(self, module):
        self.changed        = False
        self.msg            = []

        self.module         = module
        self.path           = self.module.params['path']
        self.name           = self.module.params['name']
        self.sparse         = self.module.params['sparse']
        self.root_password  = self.module.params['root_password']
        self.timeout        = self.module.params['timeout']
        self.config         = self.module.params['config']
        self.create_options = self.module.params['create_options']

        self.zoneadm_cmd    = self.module.get_bin_path('zoneadm', True)
        self.zonecfg_cmd    = self.module.get_bin_path('zonecfg', True)
        self.ssh_keygen_cmd = self.module.get_bin_path('ssh-keygen', True)

    def create(self):
        if not self.path:
            self.module.fail_json(msg='Missing required argument: path')

        t = tempfile.NamedTemporaryFile(delete = False)

        if self.sparse:
            t.write('create %s\n' % self.create_options)
            self.msg.append('creating sparse root zone')
        else:
            t.write('create -b %s\n' % self.create_options)
            self.msg.append('creating whole root zone')

        t.write('set zonepath=%s\n' % self.path)

        if self.config:
            for line in self.config:
                t.write('%s\n' % line)
        t.close()

        cmd = '%s -z %s -f %s' % (self.zonecfg_cmd, self.name, t.name)
        (rc, out, err) = self.module.run_command(cmd)
        if rc != 0:
            self.module.fail_json(msg='Failed to create zone. %s' % (out + err))
        os.unlink(t.name)

        cmd = '%s -z %s install' % (self.zoneadm_cmd, self.name)
        (rc, out, err) = self.module.run_command(cmd)
        if rc != 0:
            self.module.fail_json(msg='Failed to install zone. %s' % (out + err))

        self.configure_sysid()
        self.configure_password()
        self.configure_ssh_keys()

    def configure_sysid(self):
        os.unlink('%s/root/etc/.UNCONFIGURED' % self.path)

        open('%s/root/noautoshutdown' % self.path, 'w').close()

        node = open('%s/root/etc/nodename' % self.path, 'w')
        node.write(self.name)
        node.close

        id = open('%s/root/etc/.sysIDtool.state' % self.path, 'w')
        id.write('1       # System previously configured?\n')
        id.write('1       # Bootparams succeeded?\n')
        id.write('1       # System is on a network?\n')
        id.write('1       # Extended network information gathered?\n')
        id.write('0       # Autobinder succeeded?\n')
        id.write('1       # Network has subnets?\n')
        id.write('1       # root password prompted for?\n')
        id.write('1       # locale and term prompted for?\n')
        id.write('1       # security policy in place\n')
        id.write('1       # NFSv4 domain configured\n')
        id.write('0       # Auto Registration Configured\n')
        id.write('vt100')
        id.close()

    def configure_ssh_keys(self):
        rsa_key_file = '%s/root/etc/ssh/ssh_host_rsa_key' % self.path
        dsa_key_file = '%s/root/etc/ssh/ssh_host_dsa_key' % self.path

        if not os.path.isfile(rsa_key_file):
            cmd = '%s -f %s -t rsa -N ""' % (self.ssh_keygen_cmd, rsa_key_file)
            (rc, out, err) = self.module.run_command(cmd)
            if rc != 0:
                self.module.fail_json(msg='Failed to create rsa key. %s' % (out + err))

        if not os.path.isfile(dsa_key_file):
            cmd = '%s -f %s -t dsa -N ""' % (self.ssh_keygen_cmd, dsa_key_file)
            (rc, out, err) = self.module.run_command(cmd)
            if rc != 0:
                self.module.fail_json(msg='Failed to create dsa key. %s' % (out + err))

    def configure_password(self):
        shadow = '%s/root/etc/shadow' % self.path
        if self.root_password:
            f = open(shadow, 'r')
            lines = f.readlines()
            f.close()

            for i in range(0, len(lines)):     
                fields = lines[i].split(':')   
                if fields[0] == 'root':
                    fields[1] = self.root_password 
                    lines[i] = ':'.join(fields)

            f = open(shadow, 'w')
            for line in lines:
                f.write(line)              
            f.close()
            
    def boot(self):
        cmd = '%s -z %s boot' % (self.zoneadm_cmd, self.name)
        (rc, out, err) = self.module.run_command(cmd)
        if rc != 0:
            self.module.fail_json(msg='Failed to boot zone. %s' % (out + err))

        """
        The boot command can return before the zone has fully booted. This is especially
        true on the first boot when the zone initializes the SMF services. Unless the zone
        has fully booted, subsequent tasks in the playbook may fail as services aren't running yet.
        Wait until the zone's console login is running; once that's running, consider the zone booted.
        """

        elapsed = 0
        while True:
            if elapsed > self.timeout:
                self.module.fail_json(msg='timed out waiting for zone to boot')
            rc = os.system('ps -z %s -o args|grep "/usr/lib/saf/ttymon.*-d /dev/console" > /dev/null 2>/dev/null' % self.name)
            if rc == 0:
                break
            time.sleep(10)
            elapsed += 10

    def destroy(self):
        cmd = '%s -z %s delete -F' % (self.zonecfg_cmd, self.name)
        (rc, out, err) = self.module.run_command(cmd)
        if rc != 0:
            self.module.fail_json(msg='Failed to delete zone. %s' % (out + err))

    def stop(self):
        cmd = '%s -z %s halt' % (self.zoneadm_cmd, self.name)
        (rc, out, err) = self.module.run_command(cmd)
        if rc != 0:
            self.module.fail_json(msg='Failed to stop zone. %s' % (out + err))

    def exists(self):
        cmd = '%s -z %s list' % (self.zoneadm_cmd, self.name)
        (rc, out, err) = self.module.run_command(cmd)
        if rc == 0:
            return True
        else:
            return False

    def running(self):
        cmd = '%s -z %s list -p' % (self.zoneadm_cmd, self.name)
        (rc, out, err) = self.module.run_command(cmd)
        if rc != 0:
            self.module.fail_json(msg='Failed to determine zone state. %s' % (out + err))

        if out.split(':')[2] == 'running':
            return True
        else:
            return False


    def state_present(self):
        if self.exists():
            self.msg.append('zone already exists')
        else:
            if not self.module.check_mode:
                self.create()
            self.changed = True
            self.msg.append('zone created')

    def state_running(self):
        self.state_present()
        if self.running():
            self.msg.append('zone already running')
        else:
            if not self.module.check_mode:
                self.boot()
            self.changed = True
            self.msg.append('zone booted')

    def state_stopped(self):
        if self.exists():
            if self.running():
                if not self.module.check_mode:
                    self.stop()
                self.changed = True
                self.msg.append('zone stopped')
            else:
                self.msg.append('zone not running')
        else:
            self.module.fail_json(msg='zone does not exist')

    def state_absent(self):
        if self.exists():
            self.state_stopped()
            if not self.module.check_mode:
                self.destroy()
            self.changed = True
            self.msg.append('zone deleted')
        else:
            self.msg.append('zone does not exist')

    def exit_with_msg(self):
        msg = ', '.join(self.msg)
        self.module.exit_json(changed=self.changed, msg=msg)

def main():
    module = AnsibleModule(
        argument_spec      = dict(
            name           = dict(required=True),
            state          = dict(required=True, choices=['running', 'started', 'present', 'stopped', 'absent']),
            path           = dict(defalt=None),
            sparse         = dict(default=False, type='bool'),
            root_password  = dict(default=None),
            timeout        = dict(default=600, type='int'),
            config         = dict(default=None, type='list'),
            create_options = dict(default=''),
            ),
        supports_check_mode=True
    )

    if platform.system() == 'SunOS':
        (major, minor) = platform.release().split('.')
        if minor < 10:
            module.fail_json(msg='This module requires Solaris 10 or later')
    else:
        module.fail_json(msg='This module requires Solaris')

    zone = Zone(module)
    
    state = module.params['state']

    if state == 'running' or state == 'started':
        zone.state_running()
    elif state == 'present':
        zone.state_present()
    elif state == 'stopped':
        zone.state_stopped()
    elif state == 'absent':
        zone.state_absent()
    else:
        module.fail_json(msg='Invalid state: %s' % state)

    zone.exit_with_msg()

from ansible.module_utils.basic import *
main()
