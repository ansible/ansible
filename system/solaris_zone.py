#!/usr/bin/python

# (c) 2015, Paul Markham <pmarkham@netrefinery.com>
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
  - Solaris 10 or 11
options:
  state:
    required: true
    description:
      - C(present), configure and install the zone.
      - C(installed), synonym for C(present).
      - C(running), if the zone already exists, boot it, otherwise, configure and install
          the zone first, then boot it.
      - C(started), synonym for C(running).
      - C(stopped), shutdown a zone.
      - C(absent), destroy the zone.
      - C(configured), configure the ready so that it's to be attached.
      - C(attached), attach a zone, but do not boot it.
      - C(detached), shutdown and detach a zone
    choices: ['present', 'installed', 'started', 'running', 'stopped', 'absent', 'configured', 'attached', 'detached']
    default: present
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
    description:
      - 'The zonecfg configuration commands for this zone. See zonecfg(1M) for the valid options
        and syntax. Typically this is a list of options separated by semi-colons or new lines, e.g.
        "set auto-boot=true;add net;set physical=bge0;set address=10.1.1.1;end"'
    required: false
    default: empty string
  create_options:
    description:
      - 'Extra options to the zonecfg(1M) create command.'
    required: false
    default: empty string
  install_options:
    description:
      - 'Extra options to the zoneadm(1M) install command. To automate Solaris 11 zone creation,
         use this to specify the profile XML file, e.g. install_options="-c sc_profile.xml"'
    required: false
    default: empty string
  attach_options:
    description:
      - 'Extra options to the zoneadm attach command. For example, this can be used to specify
        whether a minimum or full update of packages is required and if any packages need to
        be deleted. For valid values, see zoneadm(1M)'
    required: false
    default: empty string
  timeout:
    description:
      - Timeout, in seconds, for zone to boot.
    required: false
    default: 600
'''

EXAMPLES = '''
# Create and install a zone, but don't boot it
solaris_zone: name=zone1 state=present path=/zones/zone1 sparse=true root_password="Be9oX7OSwWoU."
      config='set autoboot=true; add net; set physical=bge0; set address=10.1.1.1; end'

# Create and install a zone and boot it
solaris_zone: name=zone1 state=running path=/zones/zone1 root_password="Be9oX7OSwWoU."
      config='set autoboot=true; add net; set physical=bge0; set address=10.1.1.1; end'

# Boot an already installed zone
solaris_zone: name=zone1 state=running

# Stop a zone
solaris_zone: name=zone1 state=stopped

# Destroy a zone
solaris_zone: name=zone1 state=absent

# Detach a zone
solaris_zone: name=zone1 state=detached

# Configure a zone, ready to be attached
solaris_zone: name=zone1 state=configured path=/zones/zone1 root_password="Be9oX7OSwWoU."
      config='set autoboot=true; add net; set physical=bge0; set address=10.1.1.1; end'

# Attach a zone
solaris_zone: name=zone1 state=attached attach_options='-u'
'''

class Zone(object):
    def __init__(self, module):
        self.changed = False
        self.msg     = []

        self.module          = module
        self.path            = self.module.params['path']
        self.name            = self.module.params['name']
        self.sparse          = self.module.params['sparse']
        self.root_password   = self.module.params['root_password']
        self.timeout         = self.module.params['timeout']
        self.config          = self.module.params['config']
        self.create_options  = self.module.params['create_options']
        self.install_options = self.module.params['install_options']
        self.attach_options  = self.module.params['attach_options']

        self.zoneadm_cmd    = self.module.get_bin_path('zoneadm', True)
        self.zonecfg_cmd    = self.module.get_bin_path('zonecfg', True)
        self.ssh_keygen_cmd = self.module.get_bin_path('ssh-keygen', True)

        if self.module.check_mode:
            self.msg.append('Running in check mode')

        if platform.system() != 'SunOS':
            self.module.fail_json(msg='This module requires Solaris')

        (self.os_major, self.os_minor) = platform.release().split('.')
        if int(self.os_minor) < 10:
            self.module.fail_json(msg='This module requires Solaris 10 or later')

    def configure(self):
        if not self.path:
            self.module.fail_json(msg='Missing required argument: path')

        if not self.module.check_mode:
            t = tempfile.NamedTemporaryFile(delete = False)

            if self.sparse:
                t.write('create %s\n' % self.create_options)
                self.msg.append('creating sparse-root zone')
            else:
                t.write('create -b %s\n' % self.create_options)
                self.msg.append('creating whole-root zone')

            t.write('set zonepath=%s\n' % self.path)
            t.write('%s\n' % self.config)
            t.close()

            cmd = '%s -z %s -f %s' % (self.zonecfg_cmd, self.name, t.name)
            (rc, out, err) = self.module.run_command(cmd)
            if rc != 0:
                self.module.fail_json(msg='Failed to create zone. %s' % (out + err))
            os.unlink(t.name)

        self.changed = True
        self.msg.append('zone configured')

    def install(self):
        if not self.module.check_mode:
            cmd = '%s -z %s install %s' % (self.zoneadm_cmd, self.name, self.install_options)
            (rc, out, err) = self.module.run_command(cmd)
            if rc != 0:
                self.module.fail_json(msg='Failed to install zone. %s' % (out + err))
            if int(self.os_minor) == 10:
                self.configure_sysid()
            self.configure_password()
            self.configure_ssh_keys()
        self.changed = True
        self.msg.append('zone installed')

    def uninstall(self):
        if self.is_installed():
            if not self.module.check_mode:
                cmd = '%s -z %s uninstall -F' % (self.zoneadm_cmd, self.name)
                (rc, out, err) = self.module.run_command(cmd)
                if rc != 0:
                    self.module.fail_json(msg='Failed to uninstall zone. %s' % (out + err))
            self.changed = True
            self.msg.append('zone uninstalled')

    def configure_sysid(self):
        if os.path.isfile('%s/root/etc/.UNCONFIGURED' % self.path):
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
        if not self.module.check_mode:
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
                rc = os.system('ps -z %s -o args|grep "ttymon.*-d /dev/console" > /dev/null 2>/dev/null' % self.name)
                if rc == 0:
                    break
                time.sleep(10)
                elapsed += 10
        self.changed = True
        self.msg.append('zone booted')

    def destroy(self):
        if self.is_running():
            self.stop()
        if self.is_installed():
            self.uninstall()
        if not self.module.check_mode:
            cmd = '%s -z %s delete -F' % (self.zonecfg_cmd, self.name)
            (rc, out, err) = self.module.run_command(cmd)
            if rc != 0:
                self.module.fail_json(msg='Failed to delete zone. %s' % (out + err))
        self.changed = True
        self.msg.append('zone deleted')

    def stop(self):
        if not self.module.check_mode:
            cmd = '%s -z %s halt' % (self.zoneadm_cmd, self.name)
            (rc, out, err) = self.module.run_command(cmd)
            if rc != 0:
                self.module.fail_json(msg='Failed to stop zone. %s' % (out + err))
        self.changed = True
        self.msg.append('zone stopped')

    def detach(self):
        if not self.module.check_mode:
            cmd = '%s -z %s detach' % (self.zoneadm_cmd, self.name)
            (rc, out, err) = self.module.run_command(cmd)
            if rc != 0:
                self.module.fail_json(msg='Failed to detach zone. %s' % (out + err))
        self.changed = True
        self.msg.append('zone detached')

    def attach(self):
        if not self.module.check_mode:
            cmd = '%s -z %s attach %s' % (self.zoneadm_cmd, self.name, self.attach_options)
            (rc, out, err) = self.module.run_command(cmd)
            if rc != 0:
                self.module.fail_json(msg='Failed to attach zone. %s' % (out + err))
        self.changed = True
        self.msg.append('zone attached')

    def exists(self):
        cmd = '%s -z %s list' % (self.zoneadm_cmd, self.name)
        (rc, out, err) = self.module.run_command(cmd)
        if rc == 0:
            return True
        else:
            return False

    def is_running(self):
        return self.status() == 'running'

    def is_installed(self):
        return self.status() == 'installed'

    def is_configured(self):
        return self.status() == 'configured'

    def status(self):
        cmd = '%s -z %s list -p' % (self.zoneadm_cmd, self.name)
        (rc, out, err) = self.module.run_command(cmd)
        if rc == 0:
            return out.split(':')[2]
        else:
            return 'undefined'

    def state_present(self):
        if self.exists():
            self.msg.append('zone already exists')
        else:
            self.configure()
            self.install()

    def state_running(self):
        self.state_present()
        if self.is_running():
            self.msg.append('zone already running')
        else:
            self.boot()

    def state_stopped(self):
        if self.exists():
            self.stop()
        else:
            self.module.fail_json(msg='zone does not exist')

    def state_absent(self):
        if self.exists():
            if self.is_running():
                self.stop()
            self.destroy()
        else:
            self.msg.append('zone does not exist')

    def state_configured(self):
        if self.exists():
            self.msg.append('zone already exists')
        else:
            self.configure()

    def state_detached(self):
        if not self.exists():
            self.module.fail_json(msg='zone does not exist')
        if self.is_configured():
            self.msg.append('zone already detached')
        else:
            self.stop()
            self.detach()

    def state_attached(self):
        if not self.exists():
            self.msg.append('zone does not exist')
        if self.is_configured():
            self.attach()
        else:
            self.msg.append('zone already attached')

def main():
    module = AnsibleModule(
        argument_spec       = dict(
            name            = dict(required=True),
            state           = dict(default='present', choices=['running', 'started', 'present', 'installed', 'stopped', 'absent', 'configured', 'detached', 'attached']),
            path            = dict(defalt=None),
            sparse          = dict(default=False, type='bool'),
            root_password   = dict(default=None),
            timeout         = dict(default=600, type='int'),
            config          = dict(default=''),
            create_options  = dict(default=''),
            install_options = dict(default=''),
            attach_options  = dict(default=''),
            ),
        supports_check_mode=True
    )

    zone = Zone(module)

    state = module.params['state']

    if state == 'running' or state == 'started':
        zone.state_running()
    elif state == 'present' or state == 'installed':
        zone.state_present()
    elif state == 'stopped':
        zone.state_stopped()
    elif state == 'absent':
        zone.state_absent()
    elif state == 'configured':
        zone.state_configured()
    elif state == 'detached':
        zone.state_detached()
    elif state == 'attached':
        zone.state_attached()
    else:
        module.fail_json(msg='Invalid state: %s' % state)

    module.exit_json(changed=zone.changed, msg=', '.join(zone.msg))

from ansible.module_utils.basic import *
main()
