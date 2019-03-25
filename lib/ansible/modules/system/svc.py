#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2015, Brian Coca <bcoca@ansible.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: svc
author:
- Brian Coca (@bcoca)
version_added: "1.9"
short_description:  Manage daemontools services
description:
    - Controls daemontools services on remote hosts using the svc utility.
options:
    name:
        description:
            - Name of the service to manage.
        type: str
        required: true
    state:
        description:
            - C(Started)/C(stopped) are idempotent actions that will not run
              commands unless necessary.  C(restarted) will always bounce the
              svc (svc -t) and C(killed) will always bounce the svc (svc -k).
              C(reloaded) will send a sigusr1 (svc -1).
              C(once) will run a normally downed svc once (svc -o), not really
              an idempotent operation.
        type: str
        choices: [ killed, once, reloaded, restarted, started, stopped ]
    downed:
        description:
            - Should a 'down' file exist or not, if it exists it disables auto startup.
              Defaults to no. Downed does not imply stopped.
        type: bool
        default: no
    enabled:
        description:
            - Whether the service is enabled or not, if disabled it also implies stopped.
              Take note that a service can be enabled and downed (no auto restart).
        type: bool
    service_dir:
        description:
            - Directory svscan watches for services
        type: str
        default: /service
    service_src:
        description:
            - Directory where services are defined, the source of symlinks to service_dir.
        type: str
        default: /etc/service
'''

EXAMPLES = '''
- name: Start svc dnscache, if not running
  svc:
    name: dnscache
    state: started

- name: Stop svc dnscache, if running
  svc:
    name: dnscache
    state: stopped

- name: Kill svc dnscache, in all cases
  svc:
    name: dnscache
    state: killed

- name: Restart svc dnscache, in all cases
  svc:
    name: dnscache
    state: restarted

- name: Reload svc dnscache, in all cases
  svc:
    name: dnscache
    state: reloaded

- name: Using alternative svc directory location
  svc:
    name: dnscache
    state: reloaded
    service_dir: /var/service
'''

import os
import re
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


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
    Main class that handles daemontools, can be subclassed and overridden in case
    we want to use a 'derivative' like encore, s6, etc
    """

    # def __new__(cls, *args, **kwargs):
    #    return _load_dist_subclass(cls, args, kwargs)

    def __init__(self, module):
        self.extra_paths = ['/command', '/usr/local/bin']
        self.report_vars = ['state', 'enabled', 'downed', 'svc_full', 'src_full', 'pid', 'duration', 'full_state']

        self.module = module

        self.name = module.params['name']
        self.service_dir = module.params['service_dir']
        self.service_src = module.params['service_src']
        self.enabled = None
        self.downed = None
        self.full_state = None
        self.state = None
        self.pid = None
        self.duration = None

        self.svc_cmd = module.get_bin_path('svc', opt_dirs=self.extra_paths)
        self.svstat_cmd = module.get_bin_path('svstat', opt_dirs=self.extra_paths)
        self.svc_full = '/'.join([self.service_dir, self.name])
        self.src_full = '/'.join([self.service_src, self.name])

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
            except OSError as e:
                self.module.fail_json(path=self.src_full, msg='Error while linking: %s' % to_native(e))
        else:
            self.module.fail_json(msg="Could not find source for service to enable (%s)." % self.src_full)

    def disable(self):
        try:
            os.unlink(self.svc_full)
        except OSError as e:
            self.module.fail_json(path=self.svc_full, msg='Error while unlinking: %s' % to_native(e))
        self.execute_command([self.svc_cmd, '-dx', self.src_full])

        src_log = '%s/log' % self.src_full
        if os.path.exists(src_log):
            self.execute_command([self.svc_cmd, '-dx', src_log])

    def get_status(self):
        (rc, out, err) = self.execute_command([self.svstat_cmd, self.svc_full])

        if err is not None and err:
            self.full_state = self.state = err
        else:
            self.full_state = out

            m = re.search(r'\(pid (\d+)\)', out)
            if m:
                self.pid = m.group(1)

            m = re.search(r'(\d+) seconds', out)
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
        except Exception as e:
            self.module.fail_json(msg="failed to execute: %s" % to_native(e), exception=traceback.format_exc())
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
        argument_spec=dict(
            name=dict(type='str', required=True),
            state=dict(type='str', choices=['killed', 'once', 'reloaded', 'restarted', 'started', 'stopped']),
            enabled=dict(type='bool'),
            downed=dict(type='bool'),
            service_dir=dict(type='str', default='/service'),
            service_src=dict(type='str', default='/etc/service'),
        ),
        supports_check_mode=True,
    )

    module.run_command_environ_update = dict(LANG='C', LC_ALL='C', LC_MESSAGES='C', LC_CTYPE='C')

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
            except (OSError, IOError) as e:
                module.fail_json(msg="Could not change service link: %s" % to_native(e))

    if state is not None and state != svc.state:
        changed = True
        if not module.check_mode:
            getattr(svc, state[:-2])()

    if downed is not None and downed != svc.downed:
        changed = True
        if not module.check_mode:
            d_file = "%s/down" % svc.svc_full
            try:
                if downed:
                    open(d_file, "a").close()
                else:
                    os.unlink(d_file)
            except (OSError, IOError) as e:
                module.fail_json(msg="Could not change downed file: %s " % (to_native(e)))

    module.exit_json(changed=changed, svc=svc.report())


if __name__ == '__main__':
    main()
