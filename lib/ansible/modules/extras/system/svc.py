#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2015, Brian Coca <bcoca@ansible.com>
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
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>

DOCUMENTATION = '''
---
module: svc
author: "Brian Coca (@bcoca)"
version_added: "1.9"
short_description:  Manage daemontools services.
description:
    - Controls daemontools services on remote hosts using the svc utility.
options:
    name:
        required: true
        description:
            - Name of the service to manage.
    state:
        required: false
        choices: [ started, stopped, restarted, reloaded, once ]
        description:
            - C(Started)/C(stopped) are idempotent actions that will not run
              commands unless necessary.  C(restarted) will always bounce the
              svc (svc -t) and C(killed) will always bounce the svc (svc -k).
              C(reloaded) will send a sigusr1 (svc -1).
              C(once) will run a normally downed svc once (svc -o), not really
              an idempotent operation.
    downed:
        required: false
        choices: [ "yes", "no" ]
        default: no
        description:
            - Should a 'down' file exist or not, if it exists it disables auto startup.
              defaults to no. Downed does not imply stopped.
    enabled:
        required: false
        choices: [ "yes", "no" ]
        description:
            - Wheater the service is enabled or not, if disabled it also implies stopped.
              Make note that a service can be enabled and downed (no auto restart).
    service_dir:
        required: false
        default: /service
        description:
            - directory svscan watches for services
    service_src:
        required: false
        description:
            - directory where services are defined, the source of symlinks to service_dir.
'''

EXAMPLES = '''
# Example action to start svc dnscache, if not running
 - svc: name=dnscache state=started

# Example action to stop svc dnscache, if running
 - svc: name=dnscache state=stopped

# Example action to kill svc dnscache, in all cases
 - svc : name=dnscache state=killed

# Example action to restart svc dnscache, in all cases
 - svc : name=dnscache state=restarted

# Example action to reload svc dnscache, in all cases
 - svc: name=dnscache state=reloaded

# Example using alt svc directory location
 - svc: name=dnscache state=reloaded service_dir=/var/service
'''

import platform
import shlex

def _load_dist_subclass(cls, *args, **kwargs):
    '''
    Used for derivative implementations
    '''
    subclass = None

    distro = kwargs['module'].params['distro']

    # get the most specific superclass for this platform
    if distro is not None:
        for sc in cls.__subclasses__():
            if sc.distro is not None and sc.distro == distro:
                subclass = sc
    if subclass is None:
        subclass = cls

    return super(cls, subclass).__new__(subclass)

class Svc(object):
    """
    Main class that handles daemontools, can be subclassed and overriden in case
    we want to use a 'derivative' like encore, s6, etc
    """


    #def __new__(cls, *args, **kwargs):
    #    return _load_dist_subclass(cls, args, kwargs)



    def __init__(self, module):
        self.extra_paths = [ '/command', '/usr/local/bin' ]
        self.report_vars = ['state', 'enabled', 'downed', 'svc_full', 'src_full', 'pid', 'duration', 'full_state']

        self.module         = module

        self.name           = module.params['name']
        self.service_dir    = module.params['service_dir']
        self.service_src    = module.params['service_src']
        self.enabled        = None
        self.downed         = None
        self.full_state     = None
        self.state          = None
        self.pid            = None
        self.duration       = None

        self.svc_cmd        = module.get_bin_path('svc', opt_dirs=self.extra_paths)
        self.svstat_cmd     = module.get_bin_path('svstat', opt_dirs=self.extra_paths)
        self.svc_full = '/'.join([ self.service_dir, self.name ])
        self.src_full = '/'.join([ self.service_src, self.name ])

        self.enabled = os.path.lexists(self.svc_full)
        if self.enabled:
            self.downed = os.path.lexists('%s/down' % self.svc_full)
            self.get_status()
        else:
            self.downed = os.path.lexists('%s/down' % self.src_full)
            self.state = 'stopped'


    def enable(self):
        if os.path.exists(self.src_full):
            try:
                os.symlink(self.src_full, self.svc_full)
            except OSError, e:
                self.module.fail_json(path=self.src_full, msg='Error while linking: %s' % str(e))
        else:
            self.module.fail_json(msg="Could not find source for service to enable (%s)." % self.src_full)

    def disable(self):
        try:
            os.unlink(self.svc_full)
        except OSError, e:
            self.module.fail_json(path=self.svc_full, msg='Error while unlinking: %s' % str(e))
        self.execute_command([self.svc_cmd,'-dx',self.src_full])

        src_log = '%s/log' % self.src_full
        if os.path.exists(src_log):
            self.execute_command([self.svc_cmd,'-dx',src_log])

    def get_status(self):
        (rc, out, err) = self.execute_command([self.svstat_cmd, self.svc_full])

        if err is not None and err:
            self.full_state = self.state = err
        else:
            self.full_state = out

            m = re.search('\(pid (\d+)\)', out)
            if m:
                self.pid = m.group(1)

            m = re.search('(\d+) seconds', out)
            if m:
                self.duration = m.group(1)

            if re.search(' up ', out):
                self.state = 'start'
            elif re.search(' down ', out):
                self.state = 'stopp'
            else:
                self.state = 'unknown'
                return

            if re.search(' want ', out):
                self.state += 'ing'
            else:
                self.state += 'ed'

    def start(self):
        return self.execute_command([self.svc_cmd, '-u', self.svc_full])

    def stopp(self):
        return self.stop()

    def stop(self):
        return self.execute_command([self.svc_cmd, '-d', self.svc_full])

    def once(self):
        return self.execute_command([self.svc_cmd, '-o', self.svc_full])

    def reload(self):
        return self.execute_command([self.svc_cmd, '-1', self.svc_full])

    def restart(self):
        return self.execute_command([self.svc_cmd, '-t', self.svc_full])

    def kill(self):
        return self.execute_command([self.svc_cmd, '-k', self.svc_full])

    def execute_command(self, cmd):
        try:
            (rc, out, err) = self.module.run_command(' '.join(cmd))
        except Exception, e:
            self.module.fail_json(msg="failed to execute: %s" % str(e))
        return (rc, out, err)

    def report(self):
        self.get_status()
        states = {}
        for k in self.report_vars:
            states[k] = self.__dict__[k]
        return states

# ===========================================
# Main control flow

def main():
    module = AnsibleModule(
        argument_spec = dict(
            name = dict(required=True),
            state = dict(choices=['started', 'stopped', 'restarted', 'killed', 'reloaded', 'once']),
            enabled = dict(required=False, type='bool'),
            downed = dict(required=False, type='bool'),
            dist = dict(required=False, default='daemontools'),
            service_dir = dict(required=False, default='/service'),
            service_src = dict(required=False, default='/etc/service'),
        ),
        supports_check_mode=True,
    )

    state = module.params['state']
    enabled = module.params['enabled']
    downed = module.params['downed']

    svc = Svc(module)
    changed = False
    orig_state = svc.report()

    if enabled is not None and enabled != svc.enabled:
        changed = True
        if not module.check_mode:
            try:
                if enabled:
                    svc.enable()
                else:
                    svc.disable()
            except (OSError, IOError), e:
                module.fail_json(msg="Could change service link: %s" % str(e))

    if state is not None and state != svc.state:
        changed = True
        if not module.check_mode:
            getattr(svc,state[:-2])()

    if downed is not None and downed != svc.downed:
        changed = True
        if not module.check_mode:
            d_file = "%s/down" % svc.svc_full
            try:
                if downed:
                    open(d_file, "a").close()
                else:
                    os.unlink(d_file)
            except (OSError, IOError), e:
                module.fail_json(msg="Could change downed file: %s " % (str(e)))

    module.exit_json(changed=changed, svc=svc.report())


# this is magic,  not normal python include
from ansible.module_utils.basic import *

main()
