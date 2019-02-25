#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Martin Migasiewicz <martin.sm@web.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
module: launchd
author:
- Martin Migasiewicz (@martinm82)
version_added: "2.8"
short_description:  Manage macOS services
description:
- This module can be used to control launchd services on target macOS hosts.
options:
    name:
      description:
      - Name of the service.
      type: str
      required: true
      aliases: [ service ]
    state:
      description:
      - C(started)/C(stopped) are idempotent actions that will not run
        commands unless necessary.
      - Launchd does not support C(restarted) nor C(reloaded) natively.
        These will trigger a stop/start (restarted) or an unload/load
        (reloaded).
      - C(restarted) unloads and loads the service before start to ensure
        that the latest job definition (plist) is used.
      - C(reloaded) unloads and loads the service to ensure that the latest
        job definition (plist) is used. Whether a service is started or
        stopped depends on the content of the definition file.
      type: str
      choices: [ reloaded, restarted, started, stopped, unloaded ]
    enabled:
      description:
      - Whether the service should start on boot.
      - B(At least one of state and enabled are required.)
      type: bool
    force_stop:
      description:
      - Whether the service should not be restarted automatically by launchd.
      - Services might have the 'KeepAlive' attribute set to true in a launchd configuration.
        In case this is set to true, stopping a service will cause that launchd starts the service again.
      - Set this option to C(yes) to let this module change the 'KeepAlive' attribute to false.
      type: bool
      default: no
notes:
- One option other than name is required.
requirements:
- A system managed by launchd
- The plistlib python library
'''

EXAMPLES = r'''
- name: Make sure spotify webhelper is started
  launchd:
    name: com.spotify.webhelper
    state: started
  become: yes

- name: Deploy custom memcached job definition
  template:
    src: org.memcached.plist.j2
    dest: /Library/LaunchDaemons/org.memcached.plist
  become: yes

- name: Run memcached
  launchd:
    name: org.memcached
    state: started
  become: yes

- name: Stop memcached
  launchd:
    name: org.memcached
    state: stopped
  become: yes

- name: Stop memcached
  launchd:
    name: org.memcached
    state: stopped
    force_stop: yes
  become: yes

- name: Restart memcached
  launchd:
    name: org.memcached
    state: restarted
  become: yes

- name: Unload memcached
  launchd:
    name: org.memcached
    state: unloaded
  become: yes
'''

RETURN = r'''
status:
    description: metadata about service status
    returned: always
    type: dict
    sample:
        {
            "current_pid": "-",
            "current_state": "stopped",
            "previous_pid": "82636",
            "previous_state": "running"
        }
'''

import os
import plistlib
from abc import ABCMeta, abstractmethod
from time import sleep

from ansible.module_utils.basic import AnsibleModule

class ServiceState:
    UNKNOWN = 0
    LOADED = 1
    STOPPED = 2
    STARTED = 3
    UNLOADED = 4

    @staticmethod
    def to_string(state):
        strings = {
            ServiceState.UNKNOWN: 'unknown',
            ServiceState.LOADED: 'loaded',
            ServiceState.STOPPED: 'stopped',
            ServiceState.STARTED: 'started',
            ServiceState.UNLOADED: 'unloaded'
        }
        return strings[state]


class Plist:
    def __init__(self, module, service):
        self.__changed = False
        self.__service = service

        state, pid, dummy, dummy = LaunchCtlList(module, service).run()

        self.__file = self.__find_service_plist(service)
        if self.__file is None:
            msg = 'Unable to infer the path of %s service plist file' % service
            if pid is None and state == ServiceState.UNLOADED:
                msg += ' and it was not found among active services'
            module.fail_json(msg=msg)
        self.__update(module)

    def __find_service_plist(self, service_name):
        """Finds the plist file associated with a service"""

        launchd_paths = [
            '~/Library/LaunchAgents',
            '/Library/LaunchAgents',
            '/Library/LaunchDaemons',
            '/System/Library/LaunchAgents',
            '/System/Library/LaunchDaemons'
        ]

        for path in launchd_paths:
            try:
                files = os.listdir(os.path.expanduser(path))
            except OSError:
                continue

            for filename in files:
                if filename == '%s.plist' % service_name:
                    return os.path.join(path, filename)
        return None

    def __update(self, module):
        self.__handle_param_enabled(module)
        self.__handle_param_force_stop(module)

    def __handle_param_enabled(self, module):
        if module.params['enabled'] is not None:
            service_plist = plistlib.readPlist(self.__file)

            # Enable/disable service startup at boot if requested
            # Launchctl does not expose functionality to set the RunAtLoad
            # attribute of a job definition. So we parse and modify the job
            # definition plist file directly for this purpose.
            if module.params['enabled'] is not None:
                enabled = service_plist.get('RunAtLoad', False)
                if module.params['enabled'] != enabled:
                    service_plist['RunAtLoad'] = module.params['enabled']

                    # Update the plist with one of the changes done.
                    if not module.check_mode:
                        plistlib.writePlist(service_plist, self.__file)
                        self.__changed = True

    def __handle_param_force_stop(self, module):
        if module.params['force_stop'] is not None:
            service_plist = plistlib.readPlist(self.__file)

            # Set KeepAlive to false in case force_stop is defined to avoid
            # that the service gets restarted when stopping was requested.
            if module.params['force_stop'] is not None:
                keep_alive = service_plist.get('KeepAlive', False)
                if module.params['force_stop'] and keep_alive:
                    service_plist['KeepAlive'] = not module.params['force_stop']

                    # Update the plist with one of the changes done.
                    if not module.check_mode:
                        plistlib.writePlist(service_plist, self.__file)
                        self.__changed = True

    def is_changed(self):
        return self.__changed

    def get_file(self):
        return self.__file


class LaunchCtlTask(object):
    __metaclass__ = ABCMeta
    WAITING_TIME = 5  # seconds

    def __init__(self, module, service, plist):
        self._module = module
        self._service = service
        self._plist = plist
        self._launch = self._module.get_bin_path('launchctl', True)

    def run(self):
        """Runs a launchd command like 'load', 'unload', 'start', 'stop', etc.
        and returns the new state and pid.
        """
        self.runCommand()
        return self.get_state()

    @abstractmethod
    def runCommand(self):
        pass

    def get_state(self):
        rc, out, err = self._launchctl("list")
        if rc != 0:
            self._module.fail_json(
                msg='Failed to get status of %s' % (self._launch))

        state = ServiceState.UNLOADED
        service_pid = "-"
        status_code = None
        for line in out.splitlines():
            if line.strip():
                pid, last_exit_code, label = line.split('\t')
                if label.strip() == self._service:
                    service_pid = pid
                    status_code = last_exit_code

                    # From launchctl man page:
                    # If the number [...] is negative, it represents  the
                    # negative of the signal which killed the job.  Thus,
                    # "-15" would indicate that the job was terminated with
                    # SIGTERM.
                    if last_exit_code not in ['0', '-2', '-3', '-9', '-15']:
                        # Something strange happened and we have no clue in
                        # which state the service is now. Therefore we mark
                        # the service state as UNKNOWN.
                        state = ServiceState.UNKNOWN
                    elif pid != '-':
                        # PID seems to be an integer so we assume the service
                        # is started.
                        state = ServiceState.STARTED
                    else:
                        # Exit code is 0 and PID is not available so we assume
                        # the service is stopped.
                        state = ServiceState.STOPPED
                    break
        return (state, service_pid, status_code, err)

    def start(self):
        rc, out, err = self._launchctl("start")
        # Unfortunately launchd does not wait until the process really started.
        sleep(self.WAITING_TIME)
        return (rc, out, err)

    def stop(self):
        rc, out, err = self._launchctl("stop")
        # Unfortunately launchd does not wait until the process really stopped.
        sleep(self.WAITING_TIME)
        return (rc, out, err)

    def restart(self):
        # TODO: check for rc, out, err
        self.stop()
        return self.start()

    def reload(self):
        # TODO: check for rc, out, err
        self.unload()
        return self.load()

    def load(self):
        return self._launchctl("load")

    def unload(self):
        return self._launchctl("unload")

    def _launchctl(self, command):
        service_or_plist = self._plist.get_file() if command in [
            'load', 'unload'] else self._service if command in ['start', 'stop'] else ""

        rc, out, err = self._module.run_command(
            '%s %s %s' % (self._launch, command, service_or_plist))

        if rc != 0:
            msg = "Unable to %s '%s' (%s): '%s'" % (
                command, self._service, self._plist.get_file(), err)
            self._module.fail_json(msg=msg)

        return (rc, out, err)


class LaunchCtlStart(LaunchCtlTask):
    def __init__(self, module, service, plist):
        super(LaunchCtlStart, self).__init__(module, service, plist)

    def runCommand(self):
        state, dummy, dummy, dummy = self.get_state()

        if state == ServiceState.STOPPED or state == ServiceState.LOADED:
            self.reload()
            self.start()
        elif state == ServiceState.STARTED:
            # In case the service is already in started state but the
            # job definition was changed we need to unload/load the
            # service and start the service again.
            if self._plist.is_changed():
                self.reload()
                self.start()
        elif state == ServiceState.UNLOADED:
            self.load()
            self.start()
        elif state == ServiceState.UNKNOWN:
            # We are in an unknown state, let's try to reload the config
            # and start the service again.
            self.reload()
            self.start()


class LaunchCtlStop(LaunchCtlTask):
    def __init__(self, module, service, plist):
        super(LaunchCtlStop, self).__init__(module, service, plist)

    def runCommand(self):
        state, dummy, dummy, dummy = self.get_state()

        if state == ServiceState.STOPPED:
            # In case the service is stopped and we might later decide
            # to start it, we need to reload the job definition by
            # forcing an unload and load first.
            # Afterwards we need to stop it as it might have been
            # started again (KeepAlive or RunAtLoad).
            if self._plist.is_changed():
                self.reload()
                self.stop()
        elif state == ServiceState.STARTED or state == ServiceState.LOADED:
            if self._plist.is_changed():
                self.reload()
            self.stop()
        elif state == ServiceState.UNKNOWN:
            # We are in an unknown state, let's try to reload the config
            # and stop the service gracefully.
            self.reload()
            self.stop()


class LaunchCtlReload(LaunchCtlTask):
    def __init__(self, module, service, plist):
        super(LaunchCtlReload, self).__init__(module, service, plist)

    def runCommand(self):
        state, dummy, dummy, dummy = self.get_state()

        if state == ServiceState.UNLOADED:
            # launchd throws an error if we do an unload on an already
            # unloaded service.
            self.load()
        else:
            self.reload()


class LaunchCtlUnload(LaunchCtlTask):
    def __init__(self, module, service, plist):
        super(LaunchCtlUnload, self).__init__(module, service, plist)

    def runCommand(self):
        state, dummy, dummy, dummy = self.get_state()
        self.unload()


class LaunchCtlRestart(LaunchCtlReload):
    def __init__(self, module, service, plist):
        super(LaunchCtlRestart, self).__init__(module, service, plist)

    def runCommand(self):
        super(LaunchCtlRestart, self).runCommand()
        self.start()


class LaunchCtlList(LaunchCtlTask):
    def __init__(self, module, service):
        super(LaunchCtlList, self).__init__(module, service, None)

    def runCommand(self):
        # Do nothing, the list functionality is done by the
        # base class run method.
        pass


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(
                required=True,
                aliases=['service']
            ),
            state=dict(
                choices=['started', 'stopped', 'restarted', 'reloaded', 'unloaded'],
            ),
            enabled=dict(type='bool'),
            force_stop=dict(type='bool', required=False)
        ),
        supports_check_mode=True,
        required_one_of=[
            ['state', 'enabled']
        ],
    )

    service = module.params['name']
    action = module.params['state']
    rc = 0
    out = err = ''
    result = {
        'name': service,
        'changed': False,
        'status': {},
    }

    # We will tailor the plist file in case one of the options
    # (enabled, force_stop) was specified.
    plist = Plist(module, service)
    result['changed'] = plist.is_changed()

    # Gather information about the service to be controlled.
    state, pid, dummy, dummy = LaunchCtlList(module, service).run()
    result['status']['previous_state'] = ServiceState.to_string(state)
    result['status']['previous_pid'] = pid

    # Map the actions to specific tasks
    tasks = {
        'started': LaunchCtlStart(module, service, plist),
        'stopped': LaunchCtlStop(module, service, plist),
        'restarted': LaunchCtlRestart(module, service, plist),
        'reloaded': LaunchCtlReload(module, service, plist),
        'unloaded': LaunchCtlUnload(module, service, plist)
    }

    # Run the requested task
    state, pid, status_code, err = tasks[action].run()

    result['status']['current_state'] = ServiceState.to_string(state)
    result['status']['current_pid'] = pid
    result['status']['status_code'] = status_code
    result['status']['error'] = err

    if (result['status']['current_state'] != result['status']['previous_state'] or
            result['status']['current_pid'] != result['status']['previous_pid']):
        result['changed'] = True
    module.exit_json(**result)


if __name__ == '__main__':
    main()
