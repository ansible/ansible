#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016-2017, Ross Basarevych <basarevych@gmail.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: freebsdport
version_added: "2.5"
short_description: Manage FreeBSD ports
description:
  - Configures, installs, updates and deinstalls FreeBSD ports in canonical
    way.
author:
    - Ross Basarevych (@basarevych)
notes:
  - This module might install (automatically) or refresh (when requested)
    the port tree using C(portsnap) utility.
  - With addition to C(make), C(pkg) utility is used which might be
    automatically installed if not present on target host.
  - Port options are stored in C(/etc/make.ports.conf) file on target host.
    Instructions to include this file are automatically added to
    C(/etc/make.conf) file.
  - Do not run C(make config) manually on target hosts as this configuration
    will be removed on next reinstall.
  - If port fails to build you can find build log in /var/log/freebsdport
    directory.
options:
  name:
    description:
      - Port name with category, e.g. C(sysutils/ansible) to work with
        Ansible port on the remote host.
      - Required for states C(configured), C(present) and C(absent). Ignored
        when no C(state) provided.
    required: false
    default: null
  state:
    description:
      - Whether to install (C(present) or C(latest)), force reinstall
        (C(reinstalled)), remove (C(absent)), or just modify options
        (C(configured)).
    choices: [ configured, present, latest, reinstalled, absent ]
    required: false
    default: null
  options:
    description:
      - Space separated list of all the port's options you wish to define.
        Each item is in the form of OPTION_NAME=state, where state is either
        C(on) or C(off), e.g. options="FOO=on BAR=on BAZ=off".
      - If this parameter is specified, options not listed will be reset to
        port's default values. Use parameters C(enable), C(disable) or C(reset)
        instead if you only want to modify some specific options without
        resetting all the others.
      - If C(state) is C(present) or C(latest) and new options differ from
        the ones saved the port will be reinstalled with the new options.
        Ignored when no C(name) provided.
    required: false
    default: null
  enable:
    description:
      - Space separated list of option names that will be enabled,
        e.g. enable="FOO BAR".
      - This parameter will only change options specified and leave all the
        other options unmodified.
      - If C(state) is C(present) or C(latest) and new options differ from
        saved ones the port will be reinstalled with the new options.
        Ignored when no C(name) provided.
    required: false
    default: null
  disable:
    description:
      - Space separated list of options names that will be disabled,
        e.g. disable="FOO BAR".
      - This parameter will only change options specified and leave all the
        other options unmodified.
      - If C(state) is C(present) or C(latest) and new options differ from
        saved ones the port will be reinstalled with the new options.
        Ignored when no C(name) provided.
    required: false
    default: null
  reset:
    description:
      - Space separated list of options names that will be reset to their
        default, e.g. reset="FOO BAR".
      - This parameter will only change options specified and leave all the
        other options unmodified.
      - If C(state) is C(present) or C(latest) and new options differ from
        saved ones the port will be reinstalled with the new options.
        Ignored when no C(name) provided.
    required: false
    default: null
  refresh_tree:
    description:
      - Refresh ports tree using C(portsnap) before doing anything else.
    required: false
    default: false
  cron:
    description:
      - Whether to use C(cron) or C(fetch) command of C(portsnap) when
        upgrading ports tree. Used with C(refresh_tree) is enabled.
    required: false
    default: false
  include_deps:
    description:
      - When C(state) is C(latest) or C(reinstalled) and C(name) is given this
        option will also upgrade/reinstall dependencies of given port.
    required: false
    default: true
  ignore_vulnerabilities:
    description:
      - Install port even if it has known vulnerabilities.
    required: false
    default: false
  ports_dir:
    description:
      - Ports directory on target host
    required: false
    default: /usr/ports
  conf_file:
    description:
      - Port options file on target host
    required: false
    default: /etc/make.ports.conf
'''

EXAMPLES = '''
# Set all Ansible port options
- freebsdport:
    name: sysutils/ansible
    options: DOCS=off EXAMPLES=on NETADDR=on
    state: configured

# Enable DOCS and NETADDR, set EXAMPLES to default value and install Ansible
- freebsdport:
    name: sysutils/ansible
    enable: DOCS NETADDR
    reset: EXAMPLES
    state: present

# Update Ansible with dependencies after refreshing the ports tree
- freebsdport:
    name: sysutils/ansible
    state: latest
    refresh_tree: yes

# Reinstall all of the ports (or use the name parameter)
- freebsdport:
    state: reinstalled

# Deinstall Ansible port
- freebsdport:
    name: sysutils/ansible
    state: absent
'''

RETURN = '''
state:
    description: Requested state
    returned: when state provided
    type: string
    sample: "present"
success:
    description: Successful operation flag
    returned: always
    type: bool
    sample: True
deinstalled_ports:
    description: List of deinstalled ports during execution
    returned: always
    type: list
    sample: [ 'sysutils/ansible' ]
installed_ports:
    description: List of (re)installed ports during execution
    returned: always
    type: list
    sample: [ 'sysutils/ansible' ]
set_options:
    description: List of all enabled option names for the port
    returned: when port name and state are provided
    type: list
    sample: [ 'DOCS', 'EXAMPLES' ]
unset_options:
    description: List of all disabled option names for the port
    returned: when port name and state are provided
    type: list
    sample: [ 'NETADDR' ]
traceback:
    description: Stack trace of exception
    returned: failure
    type: list
'''

import sys
import re
import traceback
from ansible.module_utils.basic import AnsibleModule


class Node:

    def __init__(self, all_nodes, name):
        self.all_nodes = all_nodes
        self.name = name
        self.dependencies = None

    def add_dep(self, name):
        found = False
        for node in self.all_nodes:
            if node.name == name:
                self.dependencies.append(node)
                found = True
                break

        if not found:
            node = Node(self.all_nodes, name)
            self.all_nodes.append(node)
            self.dependencies.append(node)


class FreeBSDPort:

    def __init__(self, module, result):
        self.module = module
        self.result = result
        self.ports_dir = self.module.params['ports_dir']
        self.tmp_dir = '/tmp/freebsdport'
        self.log_dir = '/var/log/freebsdport'
        self.conf_file = self.module.params['conf_file']
        self.port_options_names = {}

    def refresh_tree(self):
        if self._init_system():
            return

        cmd = [
            '/usr/sbin/portsnap',
            '-p', self.ports_dir,
        ]
        if self.module.params['cron']:
            cmd.append('cron')
        else:
            cmd.append('--interactive')
            cmd.append('fetch')
        cmd.append('update')
        (rc, out, err) = self.module.run_command(cmd)
        if rc != 0:
            raise Exception('Updating of ports tree failed')

    def configure(self, name):
        if name is None:
            raise Exception('Name is required with this state')

        self._init_system()
        if not self._port_exists(name):
            raise Exception('Port not found: %s' % name)

        cur_set = self.get_set_options(name)
        cur_unset = self.get_unset_options(name)
        new_set = []
        new_unset = []

        options_str = self.module.params['options']
        if options_str is None:
            new_set = cur_set[:]
            new_unset = cur_unset[:]
        else:
            options = options_str.split(' ')
            for option in options:
                if len(option) == 0:
                    continue
                (key, value) = option.split('=')
                if len(key) == 0 or len(value) == 0:
                    raise Exception('Malformed options string')
                if value == 'on':
                    new_set.append(key)
                    while key in new_unset:
                        new_unset.remove(key)
                elif value == 'off':
                    new_unset.append(key)
                    while key in new_set:
                        new_set.remove(key)
                else:
                    raise Exception('Invalid option state: %s' % value)

        enable_str = self.module.params['enable']
        if enable_str is not None:
            for option in enable_str.split(' '):
                if len(option) == 0:
                    continue
                new_set.append(option)
                while option in new_unset:
                    new_unset.remove(option)

        disable_str = self.module.params['disable']
        if disable_str is not None:
            for option in disable_str.split(' '):
                if len(option) == 0:
                    continue
                new_unset.append(option)
                while option in new_set:
                    new_set.remove(option)

        reset_str = self.module.params['reset']
        if reset_str is not None:
            for option in reset_str.split(' '):
                if len(option) == 0:
                    continue
                while option in new_set:
                    new_set.remove(option)
                while option in new_unset:
                    new_unset.remove(option)

        new_set = list(set(new_set))
        new_unset = list(set(new_unset))
        for option in new_set:
            while option in new_unset:
                new_unset.remove(option)

        options_changed = not self._options_match(cur_set, new_set)
        if not options_changed:
            options_changed = not self._options_match(cur_unset, new_unset)

        if not options_changed:
            return self._get_options_changed(name)

        self.result['changed'] = True

        output = ''
        options_name = self._get_options_name(name)

        try:
            with open(self.conf_file, 'r') as fd:
                for line in fd:
                    match = re.match('^\s*' + options_name + '_CHANGED\s*[?+-]?=.*$', line)
                    if match is not None:
                        continue
                    match = re.match('^\s*' + options_name + '_SET\s*[?+-]?=.*$', line)
                    if match is not None:
                        continue
                    match = re.match('^\s*' + options_name + '_UNSET\s*[?+-]?=.*$', line)
                    if match is not None:
                        continue
                    output = output + line.rstrip() + '\n'
        except:
            pass

        with open(self.conf_file, 'w') as fd:
            if len(output):
                fd.write(output)
            fd.write(options_name + '_CHANGED=yes\n')
            fd.write(options_name + '_SET=' + ' '.join(new_set) + '\n')
            fd.write(options_name + '_UNSET=' + ' '.join(new_unset) + '\n')

        return True

    def install(self, name, automatic=None, reinstall=False):
        if name is None:
            raise Exception('Name is required with this state')

        self._init_system()
        if not self._port_exists(name):
            raise Exception('Port not found: %s' % name)

        port_installed = self._port_installed(name)
        options_changed = self.configure(name)
        backup = None

        if not reinstall and port_installed and not options_changed:
            if automatic is not None and self._get_automatic(name) != automatic:
                self._set_automatic(name, automatic)
            return False

        self.result['changed'] = True

        if port_installed:
            backup = self._make_backup(name)
            if automatic is None:
                automatic = self._get_automatic(name)
        else:
            if automatic is None:
                automatic = True

        cmd = [
            '/usr/bin/make',
            '-C', self.ports_dir + '/' + name,
            'rmconfig'
        ]
        (rc, out, err) = self.module.run_command(cmd)
        if rc != 0:
            raise Exception('Could not remove old config in %s' % name)

        cmd = [
            '/usr/bin/make',
            '-C', self.ports_dir + '/' + name,
            'clean',
            'build',
            'BATCH=yes'
        ]
        if self.module.params['ignore_vulnerabilities']:
            cmd.append('DISABLE_VULNERABILITIES=yes')
        self._run_make(name, cmd, 'Could not build the port: %s' % name)

        try:
            self.deinstall(name)

            cmd = [
                '/usr/bin/make',
                '-C', self.ports_dir + '/' + name,
                'install', 'clean', 'BATCH=yes'
            ]
            if self.module.params['ignore_vulnerabilities']:
                cmd.append('DISABLE_VULNERABILITIES=yes')
            self._run_make(name, cmd, 'Could not install the port: %s' % name)
        except Exception as e:
            if backup is not None:
                if not self._port_installed(name):
                    self._restore_backup(name, backup, automatic)
                self._remove_backup(name, backup)
                backup = None

            raise e

        if self._get_automatic(name) != automatic:
            self._set_automatic(name, automatic)

        if name not in self.result['installed_ports']:
            self.result['installed_ports'].append(name)

        if backup is not None:
            self._remove_backup(name, backup)

        if self._get_options_changed(name):
            output = ''
            options_name = self._get_options_name(name)

            try:
                with open(self.conf_file, 'r') as fd:
                    for line in fd:
                        match = re.match('^\s*' + options_name + '_CHANGED\s*[?+-]?=.*$', line)
                        if match is not None:
                            continue
                        output = output + line.rstrip() + '\n'
            except:
                pass

            with open(self.conf_file, 'w') as fd:
                if len(output):
                    fd.write(output)

        return True

    def upgrade(self, name, outdated_only):
        self._init_system()

        if outdated_only:
            outdated = self._get_outdated_ports()
        else:
            outdated = self._get_all_ports()

        all_nodes = []
        candidates = []

        if name is None:
            requested = outdated[:]
            self.module.params['options'] = None
            self.module.params['enable'] = None
            self.module.params['disable'] = None
            self.module.params['reset'] = None
        else:
            requested = [name]

        for candidate in requested:
            node = Node(all_nodes, candidate)
            all_nodes.append(node)
            candidates.append(node)

        for node in candidates:
            self._build_tree(node)

        if name is not None and self.module.params['include_deps']:
            candidates = self._tree_nodes(candidates[0])

        todo = []
        togo = all_nodes[:]
        level = []
        for node in togo:
            if node.dependencies is None or len(node.dependencies) == 0:
                togo.remove(node)
                todo.append(node)
                level.append(node)

        while len(level) > 0:
            next_level = []
            for togo_node in togo:
                for level_node in level:
                    if level_node in togo_node.dependencies:
                        next_level.append(togo_node)
                        break
            level = next_level

            for level_node in level:
                all_deps_built = True
                for node in level_node.dependencies:
                    if node not in todo:
                        all_deps_built = False
                        break
                if all_deps_built:
                    togo.remove(level_node)
                    todo.append(level_node)

        upgrade_list = []
        for node in todo + togo:
            if node in candidates:
                upgrade_list.append(node.name)

        for port in upgrade_list:
            if port == name:
                automatic = False
            else:
                automatic = None
            self.install(port, automatic, port in outdated)

        return (len(upgrade_list) > 0)

    def deinstall(self, name):
        if name is None:
            raise Exception('Name is required with this state')

        self._init_system()
        if not self._port_exists(name):
            raise Exception('Port not found: %s' % name)

        self.configure(name)
        if not self._port_installed(name):
            return False

        self.result['changed'] = True

        cmd = [
            '/usr/bin/make',
            '-C', self.ports_dir + '/' + name,
            'rmconfig'
        ]
        (rc, out, err) = self.module.run_command(cmd)
        if rc != 0:
            raise Exception('Could not remove old config in %s' % name)

        cmd = [
            '/usr/bin/make',
            '-C', self.ports_dir + '/' + name,
            'deinstall'
        ]
        self._run_make(name, cmd, 'Could not deinstall the port: %s' % name)

        if name not in self.result['deinstalled_ports']:
            self.result['deinstalled_ports'].append(name)

        return True

    def get_set_options(self, name):
        options_name = self._get_options_name(name)
        cmd = [
            '/usr/bin/make',
            '-C', self.ports_dir + '/' + name,
            '-V', options_name + '_SET'
        ]
        (rc, out, err) = self.module.run_command(cmd)
        if rc != 0:
            raise Exception('Could not get port set options for %s' % name)
        set_str = out.strip()
        set_options = []
        for option in set_str.split(' '):
            if len(option) == 0:
                continue
            if option not in set_options:
                set_options.append(option)
        return set_options

    def get_unset_options(self, name):
        options_name = self._get_options_name(name)
        cmd = [
            '/usr/bin/make',
            '-C', self.ports_dir + '/' + name,
            '-V', options_name + '_UNSET'
        ]
        (rc, out, err) = self.module.run_command(cmd)
        if rc != 0:
            raise Exception('Could not get port unset options for %s' % name)
        unset_str = out.strip()
        unset_options = []
        for option in unset_str.split(' '):
            if len(option) == 0:
                continue
            if option not in unset_options:
                unset_options.append(option)
        return unset_options

    def _init_system(self):
        cmd = [
            '/usr/bin/grep',
            '-E',
            '^\.include "' + re.escape(self.conf_file) + '"',
            '/etc/make.conf'
        ]
        (rc, out, err) = self.module.run_command(cmd)
        if rc != 0:
            self.result['changed'] = True
            with open('/etc/make.conf', 'a') as fd:
                fd.write(
                    '\n.if exists(' + self.conf_file + ')\n' +
                    '.include "' + self.conf_file + '"\n' + '.endif\n'
                )

        if self._get_ports_dir() != self.ports_dir:
            self.result['changed'] = True
            output = ''

            try:
                with open(self.conf_file, 'r') as fd:
                    for line in fd:
                        match = re.match('^\s*PORTSDIR\s*[?+-]?=.*$', line)
                        if match is not None:
                            continue
                        output = output + line.rstrip() + '\n'
            except:
                pass

            with open(self.conf_file, 'w') as fd:
                fd.write('PORTSDIR=' + self.ports_dir + '\n')
                if len(output):
                    fd.write(output)

            if self._get_ports_dir() != self.ports_dir:
                raise Exception('Could not set ports directory: check make.conf')

        if self._path_exists(self.ports_dir + '/Makefile'):
            return False

        self.result['changed'] = True

        cmd = [
            '/usr/sbin/portsnap',
            '-p', self.ports_dir,
            '--interactive',
            'fetch', 'extract'
        ]
        (rc, out, err) = self.module.run_command(cmd)
        if rc != 0:
            raise Exception('Installation of ports tree failed')

        return True

    def _path_exists(self, path):
        cmd = ['/usr/bin/stat', path]
        (rc, out, err) = self.module.run_command(cmd)
        return (rc == 0)

    def _port_exists(self, name):
        parts = name.split('/')
        if len(parts) != 2 or len(parts[0]) == 0 or len(parts[1]) == 0:
            return False

        cmd = ['/usr/bin/stat', self.ports_dir + '/' + name + '/Makefile']
        (rc, out, err) = self.module.run_command(cmd)
        return (rc == 0)

    def _port_installed(self, name):
        cmd = ['/bin/sh', '-c', '/usr/bin/yes | /usr/sbin/pkg info ' + name]
        (rc, out, err) = self.module.run_command(cmd)
        return (rc == 0)

    def _options_match(self, old_options, new_options):
        if len(old_options) != len(new_options):
            return False
        all_found = True
        for option in old_options:
            if option not in new_options:
                all_found = False
                break
        return all_found

    def _get_ports_dir(self):
        cmd = [
            '/usr/bin/make',
            '-f', '/etc/make.conf',
            '-V', 'PORTSDIR'
        ]
        (rc, out, err) = self.module.run_command(cmd)
        if rc != 0:
            raise Exception('Could not get ports directory')
        return out.strip()

    def _get_options_name(self, name):
        if name in self.port_options_names:
            return self.port_options_names[name]

        cmd = [
            '/usr/bin/make',
            '-C', self.ports_dir + '/' + name,
            '-V', 'OPTIONS_NAME'
        ]
        (rc, out, err) = self.module.run_command(cmd)
        if rc != 0:
            raise Exception('Could not get port options name for %s' % name)
        self.port_options_names[name] = out.strip()
        return self.port_options_names[name]

    def _get_options_changed(self, name):
        options_name = self._get_options_name(name)
        cmd = [
            '/usr/bin/make',
            '-C', self.ports_dir + '/' + name,
            '-V', options_name + '_CHANGED'
        ]
        (rc, out, err) = self.module.run_command(cmd)
        if rc != 0:
            raise Exception('Could not get port options status for %s' % name)
        return (len(out.strip()) > 0)

    def _get_origin(self, package):
        cmd = [
            '/bin/sh',
            '-c',
            "/usr/bin/yes | /usr/sbin/pkg query '%o' " + package
        ]
        (rc, out, err) = self.module.run_command(cmd)
        if rc != 0:
            raise Exception('Could not get origin of %s' % package)
        return out.strip()

    def _get_all_ports(self):
        cmd = [
            '/bin/sh',
            '-c',
            "/usr/bin/yes | /usr/sbin/pkg version --index | awk '{ print $1 }'"
        ]
        (rc, out, err) = self.module.run_command(cmd)
        if rc != 0:
            cmd = [
                '/bin/sh',
                '-c',
                "/usr/bin/yes | /usr/sbin/pkg version | awk '{ print $1 }'"
            ]
            (rc, out, err) = self.module.run_command(cmd)
            if rc != 0:
                raise Exception('Could not get list of all packages')

        ports = []
        for port in out.split('\n'):
            if len(port.strip()) == 0:
                continue
            ports.append(self._get_origin(port))

        return ports

    def _get_outdated_ports(self):
        cmd = [
            '/bin/sh',
            '-c',
            "/usr/bin/yes | /usr/sbin/pkg version --index --like '<' | awk '{ print $1 }'"
        ]
        (rc, out, err) = self.module.run_command(cmd)
        if rc != 0:
            cmd = [
                '/bin/sh',
                '-c',
                "/usr/bin/yes | /usr/sbin/pkg version --like '<' | awk '{ print $1 }'"
            ]
            (rc, out, err) = self.module.run_command(cmd)
            if rc != 0:
                raise Exception('Could not get list of outdated packages')

        candidates = []
        for port in out.split('\n'):
            if len(port.strip()) == 0:
                continue
            candidates.append(self._get_origin(port))

        return candidates

    def _set_automatic(self, name, automatic):
        if automatic:
            flag = '1'
        else:
            flag = '0'

        cmd = [
            '/bin/sh',
            '-c',
            '/usr/bin/yes | /usr/sbin/pkg set --automatic ' + flag + ' ' + name
        ]
        (rc, out, err) = self.module.run_command(cmd)
        if rc != 0:
            raise Exception('Could not set automatic status of %s' % name)

    def _get_automatic(self, name):
        cmd = [
            '/usr/sbin/pkg',
            'query',
            '%a',
            name
        ]
        (rc, out, err) = self.module.run_command(cmd)
        if rc != 0:
            raise Exception('Could not query automatic status of %s' % name)
        return (out.strip() == '1')

    def _make_backup(self, name):
        cmd = ['/bin/mkdir', '-p', self.tmp_dir]
        (rc, out, err) = self.module.run_command(cmd)
        if rc != 0:
            raise Exception('Could not create temporary directory')

        cmd = [
            '/bin/sh',
            '-c',
            "/usr/bin/yes | /usr/sbin/pkg query '%n-%v' " + name
        ]
        (rc, out, err) = self.module.run_command(cmd)
        if rc != 0:
            raise Exception('Could not get package name for %s' % name)
        package_name = out.strip()
        file_name = self.tmp_dir + '/' + package_name + '.txz'

        cmd = [
            '/usr/sbin/pkg',
            'create',
            '--format', 'txz',
            '--out-dir', self.tmp_dir,
            name
        ]
        (rc, out, err) = self.module.run_command(cmd)
        if rc != 0:
            raise Exception('Could not create backup package of %s' % name)

        cmd = ['/usr/bin/stat', file_name]
        (rc, out, err) = self.module.run_command(cmd)
        if rc != 0:
            raise Exception('Backup package for %s not found (%s)' % (name, file_name))

        return file_name

    def _restore_backup(self, name, file_name, automatic):
        cmd = ['/usr/sbin/pkg', 'add']
        if automatic:
            cmd.append('--automatic')
        cmd.append(file_name)
        (rc, out, err) = self.module.run_command(cmd)
        if rc != 0:
            raise Exception('Could not reinstall backup package of %s' % name)

        if name not in self.result['installed_ports']:
            self.result['installed_ports'].append(name)

    def _remove_backup(self, name, file_name):
        cmd = ['/bin/rm', '-f', file_name]
        (rc, out, err) = self.module.run_command(cmd)
        if rc != 0:
            raise Exception('Could not remove backup package of %s' % name)

    def _build_tree(self, parent):
        if parent.dependencies is not None:
            return

        parent.dependencies = []
        if not self._port_installed(parent.name):
            return

        cmd = [
            '/bin/sh',
            '-c',
            "/usr/bin/yes | /usr/sbin/pkg query '%do' " + parent.name
        ]
        (rc, out, err) = self.module.run_command(cmd)
        if rc != 0:
            raise Exception('Could not get dependencies of %s' % parent.name)

        for line in out.split('\n'):
            port = line.strip()
            if len(port) == 0:
                continue

            parent.add_dep(port)

        for node in parent.dependencies:
            self._build_tree(node)

    def _tree_nodes(self, parent):
        nodes = [parent]
        if parent.dependencies is None:
            return nodes

        for node in parent.dependencies:
            nodes = nodes + self._tree_nodes(node)

        return nodes

    def _run_make(self, name, cmd, error_msg):
        log_file = '%s/%s.log' % (self.log_dir, name.replace('/', '-'))
        do = [
            '/bin/sh',
            '-c',
            '%s >> %s 2>&1' % (' '.join(cmd), log_file)
        ]

        (rc, out, err) = self.module.run_command(['/bin/mkdir', '-p', self.log_dir])
        if rc != 0:
            raise Exception('Could not create %s' % self.log_dir)

        (rc, out, err) = self.module.run_command(['/bin/sh', '-c', 'echo "+ %s" > %s' % (' '.join(cmd), log_file)])
        if rc != 0:
            raise Exception('Could not create %s' % self.log_file)

        (rc, out, err) = self.module.run_command(do)
        if rc != 0:
            try:
                cmd = [
                    '/usr/bin/make',
                    '-C', self.ports_dir + '/' + name,
                    'clean'
                ]
                if self.module.params['ignore_vulnerabilities']:
                    cmd.append('DISABLE_VULNERABILITIES=yes')
                (rc, out, err) = self.module.run_command(cmd)
            except:
                pass

            raise Exception(error_msg)

        (rc, out, err) = self.module.run_command(['/bin/rm', '-f', log_file])
        if rc != 0:
            raise Exception('Could not remove log file')


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(
                type='str',
                required=False,
                choices=['configured', 'present', 'latest', 'reinstalled', 'absent']
            ),
            name=dict(
                type='str',
                required=False
            ),
            options=dict(
                type='str',
                required=False
            ),
            enable=dict(
                type='str',
                required=False
            ),
            disable=dict(
                type='str',
                required=False
            ),
            reset=dict(
                type='str',
                required=False
            ),
            refresh_tree=dict(
                type='bool',
                required=False,
                default=False
            ),
            cron=dict(
                type='bool',
                required=False,
                default=False
            ),
            include_deps=dict(
                type='bool',
                required=False,
                default=True
            ),
            ignore_vulnerabilities=dict(
                type='bool',
                required=False,
                default=False
            ),
            ports_dir=dict(
                type='str',
                required=False,
                default='/usr/ports'
            ),
            conf_file=dict(
                type='str',
                required=False,
                default='/etc/make.ports.conf'
            )
        )
    )

    state = module.params['state']
    result = {
        'changed': False,
        'success': True,
        'deinstalled_ports': [],
        'installed_ports': []
    }

    try:
        port = FreeBSDPort(module, result)

        if module.params['refresh_tree']:
            port.refresh_tree()

        name = module.params['name']
        if state == 'configured':
            port.configure(name)
        elif state == 'present':
            port.install(name, False)
        elif state == 'latest':
            port.upgrade(name, True)
        elif state == 'reinstalled':
            port.upgrade(name, False)
        elif state == 'absent':
            port.deinstall(name)
        else:
            state = None

        if state is not None:
            result['state'] = state

        if name is not None and state is not None:
            result['set_options'] = port.get_set_options(name)
            result['unset_options'] = port.get_unset_options(name)

        module.exit_json(**result)
    except Exception as e:
        result['success'] = False
        result['traceback'] = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
        result['msg'] = type(e).__name__ + ': ' + str(e)
        module.fail_json(**result)


if __name__ == '__main__':
    main()
