#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2014, Kevin Carter <kevin.carter@rackspace.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: lxc_container
short_description: Manage LXC Containers
version_added: 1.8.0
description:
  - Management of LXC containers
author: "Kevin Carter (@cloudnull)"
options:
    name:
        description:
          - Name of a container.
        required: true
    backing_store:
        choices:
          - dir
          - lvm
          - loop
          - btrfs
          - overlayfs
          - zfs
        description:
          - Backend storage type for the container.
        required: false
        default: dir
    template:
        description:
          - Name of the template to use within an LXC create.
        required: false
        default: ubuntu
    template_options:
        description:
          - Template options when building the container.
        required: false
    config:
        description:
          - Path to the LXC configuration file.
        required: false
        default: null
    lv_name:
        description:
          - Name of the logical volume, defaults to the container name.
        default: $CONTAINER_NAME
        required: false
    vg_name:
        description:
          - If Backend store is lvm, specify the name of the volume group.
        default: lxc
        required: false
    thinpool:
        description:
          - Use LVM thin pool called TP.
        required: false
    fs_type:
        description:
          - Create fstype TYPE.
        default: ext4
        required: false
    fs_size:
        description:
          - File system Size.
        default: 5G
        required: false
    directory:
        description:
          - Place rootfs directory under DIR.
        required: false
    zfs_root:
        description:
          - Create zfs under given zfsroot.
        required: false
    container_command:
        description:
          - Run a command within a container.
        required: false
    lxc_path:
        description:
          - Place container under PATH
        required: false
    container_log:
        choices:
          - true
          - false
        description:
          - Enable a container log for host actions to the container.
        default: false
    container_log_level:
        choices:
          - INFO
          - ERROR
          - DEBUG
        description:
          - Set the log level for a container where *container_log* was set.
        required: false
        default: INFO
    clone_name:
        version_added: "2.0"
        description:
          - Name of the new cloned server. This is only used when state is
            clone.
        required: false
        default: false
    clone_snapshot:
        version_added: "2.0"
        required: false
        choices:
          - true
          - false
        description:
          - Create a snapshot a container when cloning. This is not supported
            by all container storage backends. Enabling this may fail if the
            backing store does not support snapshots.
        default: false
    archive:
        choices:
          - true
          - false
        description:
          - Create an archive of a container. This will create a tarball of the
            running container.
        default: false
    archive_path:
        description:
          - Path the save the archived container. If the path does not exist
            the archive method will attempt to create it.
        default: null
    archive_compression:
        choices:
          - gzip
          - bzip2
          - none
        description:
          - Type of compression to use when creating an archive of a running
            container.
        default: gzip
    state:
        choices:
          - started
          - stopped
          - restarted
          - absent
          - frozen
        description:
          - Define the state of a container. If you clone a container using
            `clone_name` the newly cloned container created in a stopped state.
            The running container will be stopped while the clone operation is
            happening and upon completion of the clone the original container
            state will be restored.
        required: false
        default: started
    container_config:
        description:
          - list of 'key=value' options to use when configuring a container.
        required: false
requirements:
  - 'lxc >= 1.0 # OS package'
  - 'python >= 2.6 # OS Package'
  - 'lxc-python2 >= 0.1 # PIP Package from https://github.com/lxc/python2-lxc'
notes:
  - Containers must have a unique name. If you attempt to create a container
    with a name that already exists in the users namespace the module will
    simply return as "unchanged".
  - The "container_command" can be used with any state except "absent". If
    used with state "stopped" the container will be "started", the command
    executed, and then the container "stopped" again. Likewise if the state
    is "stopped" and the container does not exist it will be first created,
    "started", the command executed, and then "stopped". If you use a "|"
    in the variable you can use common script formatting within the variable
    iteself The "container_command" option will always execute as BASH.
    When using "container_command" a log file is created in the /tmp/ directory
    which contains both stdout and stderr of any command executed.
  - If "archive" is **true** the system will attempt to create a compressed
    tarball of the running container. The "archive" option supports LVM backed
    containers and will create a snapshot of the running container when
    creating the archive.
  - If your distro does not have a package for "python2-lxc", which is a
    requirement for this module, it can be installed from source at
    "https://github.com/lxc/python2-lxc" or installed via pip using the package
    name lxc-python2.
"""

EXAMPLES = """
- name: Create a started container
  lxc_container:
    name: test-container-started
    container_log: true
    template: ubuntu
    state: started
    template_options: --release trusty

- name: Create a stopped container
  lxc_container:
    name: test-container-stopped
    container_log: true
    template: ubuntu
    state: stopped
    template_options: --release trusty

- name: Create a frozen container
  lxc_container:
    name: test-container-frozen
    container_log: true
    template: ubuntu
    state: frozen
    template_options: --release trusty
    container_command: |
      echo 'hello world.' | tee /opt/started-frozen

# Create filesystem container, configure it, and archive it, and start it.
- name: Create filesystem container
  lxc_container:
    name: test-container-config
    backing_store: dir
    container_log: true
    template: ubuntu
    state: started
    archive: true
    archive_compression: none
    container_config:
      - "lxc.aa_profile=unconfined"
      - "lxc.cgroup.devices.allow=a *:* rmw"
    template_options: --release trusty

# Create an lvm container, run a complex command in it, add additional
# configuration to it, create an archive of it, and finally leave the container
# in a frozen state. The container archive will be compressed using bzip2
- name: Create a frozen lvm container
  lxc_container:
    name: test-container-lvm
    container_log: true
    template: ubuntu
    state: frozen
    backing_store: lvm
    template_options: --release trusty
    container_command: |
      apt-get update
      apt-get install -y vim lxc-dev
      echo 'hello world.' | tee /opt/started
      if [[ -f "/opt/started" ]]; then
          echo 'hello world.' | tee /opt/found-started
      fi
    container_config:
      - "lxc.aa_profile=unconfined"
      - "lxc.cgroup.devices.allow=a *:* rmw"
    archive: true
    archive_compression: bzip2
  register: lvm_container_info

- name: Debug info on container "test-container-lvm"
  debug:
    var: lvm_container_info

- name: Run a command in a container and ensure its in a "stopped" state.
  lxc_container:
    name: test-container-started
    state: stopped
    container_command: |
      echo 'hello world.' | tee /opt/stopped

- name: Run a command in a container and ensure its it in a "frozen" state.
  lxc_container:
    name: test-container-stopped
    state: frozen
    container_command: |
      echo 'hello world.' | tee /opt/frozen

- name: Start a container
  lxc_container:
    name: test-container-stopped
    state: started

- name: Run a command in a container and then restart it
  lxc_container:
    name: test-container-started
    state: restarted
    container_command: |
      echo 'hello world.' | tee /opt/restarted

- name: Run a complex command within a "running" container
  lxc_container:
    name: test-container-started
    container_command: |
      apt-get update
      apt-get install -y curl wget vim apache2
      echo 'hello world.' | tee /opt/started
      if [[ -f "/opt/started" ]]; then
          echo 'hello world.' | tee /opt/found-started
      fi

# Create an archive of an existing container, save the archive to a defined
# path and then destroy it.
- name: Archive container
  lxc_container:
    name: test-container-started
    state: absent
    archive: true
    archive_path: /opt/archives

# Create a container using overlayfs, create an archive of it, create a
# snapshot clone of the container and and finally leave the container
# in a frozen state. The container archive will be compressed using gzip.
- name: Create an overlayfs container archive and clone it
  lxc_container:
    name: test-container-overlayfs
    container_log: true
    template: ubuntu
    state: started
    backing_store: overlayfs
    template_options: --release trusty
    clone_snapshot: true
    clone_name: test-container-overlayfs-clone-snapshot
    archive: true
    archive_compression: gzip
  register: clone_container_info

- name: debug info on container "test-container"
  debug:
    var: clone_container_info

- name: Clone a container using snapshot
  lxc_container:
    name: test-container-overlayfs-clone-snapshot
    backing_store: overlayfs
    clone_name: test-container-overlayfs-clone-snapshot2
    clone_snapshot: true

- name: Create a new container and clone it
  lxc_container:
    name: test-container-new-archive
    backing_store: dir
    clone_name: test-container-new-archive-clone

- name: Archive and clone a container then destroy it
  lxc_container:
    name: test-container-new-archive
    state: absent
    clone_name: test-container-new-archive-destroyed-clone
    archive: true
    archive_compression: gzip

- name: Start a cloned container.
  lxc_container:
    name: test-container-new-archive-destroyed-clone
    state: started

- name: Destroy a container
  lxc_container:
    name: '{{ item }}'
    state: absent
  with_items:
    - test-container-stopped
    - test-container-started
    - test-container-frozen
    - test-container-lvm
    - test-container-config
    - test-container-overlayfs
    - test-container-overlayfs-clone
    - test-container-overlayfs-clone-snapshot
    - test-container-overlayfs-clone-snapshot2
    - test-container-new-archive
    - test-container-new-archive-clone
    - test-container-new-archive-destroyed-clone
"""

RETURN = """
lxc_container:
    description: container information
    returned: success
    type: complex
    contains:
        name:
            description: name of the lxc container
            returned: success
            type: string
            sample: test_host
        init_pid:
            description: pid of the lxc init process
            returned: success
            type: int
            sample: 19786
        interfaces:
            description: list of the container's network interfaces
            returned: success
            type: list
            sample: [ "eth0", "lo" ]
        ips:
            description: list of ips
            returned: success
            type: list
            sample: [ "10.0.3.3" ]
        state:
            description: resulting state of the container
            returned: success
            type: string
            sample: "running"
        archive:
            description: resulting state of the container
            returned: success, when archive is true
            type: string
            sample: "/tmp/test-container-config.tar"
        clone:
            description: if the container was cloned
            returned: success, when clone_name is specified
            type: boolean
            sample: True
"""

import os
import os.path
import re
import shutil
import subprocess
import tempfile
import time

try:
    import lxc
except ImportError:
    HAS_LXC = False
else:
    HAS_LXC = True

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.parsing.convert_bool import BOOLEANS_FALSE, BOOLEANS_TRUE
from ansible.module_utils.six.moves import xrange
from ansible.module_utils._text import to_text, to_bytes


# LXC_COMPRESSION_MAP is a map of available compression types when creating
# an archive of a container.
LXC_COMPRESSION_MAP = {
    'gzip': {
        'extension': 'tar.tgz',
        'argument': '-czf'
    },
    'bzip2': {
        'extension': 'tar.bz2',
        'argument': '-cjf'
    },
    'none': {
        'extension': 'tar',
        'argument': '-cf'
    }
}


# LXC_COMMAND_MAP is a map of variables that are available to a method based
# on the state the container is in.
LXC_COMMAND_MAP = {
    'create': {
        'variables': {
            'config': '--config',
            'template': '--template',
            'backing_store': '--bdev',
            'lxc_path': '--lxcpath',
            'lv_name': '--lvname',
            'vg_name': '--vgname',
            'thinpool': '--thinpool',
            'fs_type': '--fstype',
            'fs_size': '--fssize',
            'directory': '--dir',
            'zfs_root': '--zfsroot'
        }
    },
    'clone': {
        'variables-lxc-copy': {
            'backing_store': '--backingstorage',
            'lxc_path': '--lxcpath',
            'fs_size': '--fssize',
            'name': '--name',
            'clone_name': '--newname'
        },
        # lxc-clone is deprecated in favor of lxc-copy
        'variables-lxc-clone': {
            'backing_store': '--backingstore',
            'lxc_path': '--lxcpath',
            'fs_size': '--fssize',
            'name': '--orig',
            'clone_name': '--new'
        }
    }
}


# LXC_BACKING_STORE is a map of available storage backends and options that
# are incompatible with the given storage backend.
LXC_BACKING_STORE = {
    'dir': [
        'lv_name', 'vg_name', 'fs_type', 'fs_size', 'thinpool'
    ],
    'lvm': [
        'zfs_root'
    ],
    'btrfs': [
        'lv_name', 'vg_name', 'thinpool', 'zfs_root', 'fs_type', 'fs_size'
    ],
    'loop': [
        'lv_name', 'vg_name', 'thinpool', 'zfs_root'
    ],
    'overlayfs': [
        'lv_name', 'vg_name', 'fs_type', 'fs_size', 'thinpool', 'zfs_root'
    ],
    'zfs': [
        'lv_name', 'vg_name', 'fs_type', 'fs_size', 'thinpool'
    ]
}


# LXC_LOGGING_LEVELS is a map of available log levels
LXC_LOGGING_LEVELS = {
    'INFO': ['info', 'INFO', 'Info'],
    'ERROR': ['error', 'ERROR', 'Error'],
    'DEBUG': ['debug', 'DEBUG', 'Debug']
}


# LXC_ANSIBLE_STATES is a map of states that contain values of methods used
# when a particular state is evoked.
LXC_ANSIBLE_STATES = {
    'started': '_started',
    'stopped': '_stopped',
    'restarted': '_restarted',
    'absent': '_destroyed',
    'frozen': '_frozen',
    'clone': '_clone'
}


# This is used to attach to a running container and execute commands from
# within the container on the host.  This will provide local access to a
# container without using SSH.  The template will attempt to work within the
# home directory of the user that was attached to the container and source
# that users environment variables by default.
ATTACH_TEMPLATE = """#!/usr/bin/env bash
pushd "$(getent passwd $(whoami)|cut -f6 -d':')"
    if [[ -f ".bashrc" ]];then
        source .bashrc
        unset HOSTNAME
    fi
popd

# User defined command
%(container_command)s
"""


def create_script(command):
    """Write out a script onto a target.

    This method should be backward compatible with Python 2.4+ when executing
    from within the container.

    :param command: command to run, this can be a script and can use spacing
                    with newlines as separation.
    :type command: ``str``
    """

    (fd, script_file) = tempfile.mkstemp(prefix='lxc-attach-script')
    f = os.fdopen(fd, 'wb')
    try:
        f.write(to_bytes(ATTACH_TEMPLATE % {'container_command': command}, errors='surrogate_or_strict'))
        f.flush()
    finally:
        f.close()

    # Ensure the script is executable.
    os.chmod(script_file, int('0700', 8))

    # Output log file.
    stdout_file = os.fdopen(tempfile.mkstemp(prefix='lxc-attach-script-log')[0], 'ab')

    # Error log file.
    stderr_file = os.fdopen(tempfile.mkstemp(prefix='lxc-attach-script-err')[0], 'ab')

    # Execute the script command.
    try:
        subprocess.Popen(
            [script_file],
            stdout=stdout_file,
            stderr=stderr_file
        ).communicate()
    finally:
        # Close the log files.
        stderr_file.close()
        stdout_file.close()

        # Remove the script file upon completion of execution.
        os.remove(script_file)


class LxcContainerManagement(object):
    def __init__(self, module):
        """Management of LXC containers via Ansible.

        :param module: Processed Ansible Module.
        :type module: ``object``
        """
        self.module = module
        self.state = self.module.params.get('state', None)
        self.state_change = False
        self.lxc_vg = None
        self.lxc_path = self.module.params.get('lxc_path', None)
        self.container_name = self.module.params['name']
        self.container = self.get_container_bind()
        self.archive_info = None
        self.clone_info = None

    def get_container_bind(self):
        return lxc.Container(name=self.container_name)

    @staticmethod
    def _roundup(num):
        """Return a rounded floating point number.

        :param num: Number to round up.
        :type: ``float``
        :returns: Rounded up number.
        :rtype: ``int``
        """
        num, part = str(num).split('.')
        num = int(num)
        if int(part) != 0:
            num += 1
        return num

    @staticmethod
    def _container_exists(container_name, lxc_path=None):
        """Check if a container exists.

        :param container_name: Name of the container.
        :type: ``str``
        :returns: True or False if the container is found.
        :rtype: ``bol``
        """
        if [i for i in lxc.list_containers(config_path=lxc_path) if i == container_name]:
            return True
        else:
            return False

    @staticmethod
    def _add_variables(variables_dict, build_command):
        """Return a command list with all found options.

        :param variables_dict: Pre-parsed optional variables used from a
                               seed command.
        :type variables_dict: ``dict``
        :param build_command: Command to run.
        :type build_command: ``list``
        :returns: list of command options.
        :rtype: ``list``
        """

        for key, value in variables_dict.items():
            build_command.append(
                '%s %s' % (key, value)
            )
        return build_command

    def _get_vars(self, variables):
        """Return a dict of all variables as found within the module.

        :param variables: Hash of all variables to find.
        :type variables: ``dict``
        """

        # Remove incompatible storage backend options.
        variables = variables.copy()
        for v in LXC_BACKING_STORE[self.module.params['backing_store']]:
            variables.pop(v, None)

        return_dict = dict()
        false_values = BOOLEANS_FALSE.union([None, ''])
        for k, v in variables.items():
            _var = self.module.params.get(k)
            if _var not in false_values:
                return_dict[v] = _var
        return return_dict

    def _run_command(self, build_command, unsafe_shell=False):
        """Return information from running an Ansible Command.

        This will squash the build command list into a string and then
        execute the command via Ansible. The output is returned to the method.
        This output is returned as `return_code`, `stdout`, `stderr`.

        :param build_command: Used for the command and all options.
        :type build_command: ``list``
        :param unsafe_shell: Enable or Disable unsafe sell commands.
        :type unsafe_shell: ``bol``
        """

        return self.module.run_command(
            ' '.join(build_command),
            use_unsafe_shell=unsafe_shell
        )

    def _config(self):
        """Configure an LXC container.

        Write new configuration values to the lxc config file. This will
        stop the container if it's running write the new options and then
        restart the container upon completion.
        """

        _container_config = self.module.params.get('container_config')
        if not _container_config:
            return False

        container_config_file = self.container.config_file_name
        with open(container_config_file, 'rb') as f:
            container_config = to_text(f.read(), errors='surrogate_or_strict').splitlines(True)

        # Note used ast literal_eval because AnsibleModule does not provide for
        # adequate dictionary parsing.
        # Issue: https://github.com/ansible/ansible/issues/7679
        # TODO(cloudnull) adjust import when issue has been resolved.
        import ast
        options_dict = ast.literal_eval(_container_config)
        parsed_options = [i.split('=', 1) for i in options_dict]

        config_change = False
        for key, value in parsed_options:
            key = key.strip()
            value = value.strip()
            new_entry = '%s = %s\n' % (key, value)
            keyre = re.compile(r'%s(\s+)?=' % key)
            for option_line in container_config:
                # Look for key in config
                if keyre.match(option_line):
                    _, _value = option_line.split('=', 1)
                    config_value = ' '.join(_value.split())
                    line_index = container_config.index(option_line)
                    # If the sanitized values don't match replace them
                    if value != config_value:
                        line_index += 1
                        if new_entry not in container_config:
                            config_change = True
                            container_config.insert(line_index, new_entry)
                    # Break the flow as values are written or not at this point
                    break
            else:
                config_change = True
                container_config.append(new_entry)

        # If the config changed restart the container.
        if config_change:
            container_state = self._get_state()
            if container_state != 'stopped':
                self.container.stop()

            with open(container_config_file, 'wb') as f:
                f.writelines([to_bytes(line, errors='surrogate_or_strict') for line in container_config])

            self.state_change = True
            if container_state == 'running':
                self._container_startup()
            elif container_state == 'frozen':
                self._container_startup()
                self.container.freeze()

    def _container_create_clone(self):
        """Clone a new LXC container from an existing container.

        This method will clone an existing container to a new container using
        the `clone_name` variable as the new container name. The method will
        create a container if the container `name` does not exist.

        Note that cloning a container will ensure that the original container
        is "stopped" before the clone can be done. Because this operation can
        require a state change the method will return the original container
        to its prior state upon completion of the clone.

        Once the clone is complete the new container will be left in a stopped
        state.
        """

        # Ensure that the state of the original container is stopped
        container_state = self._get_state()
        if container_state != 'stopped':
            self.state_change = True
            self.container.stop()

        # lxc-clone is deprecated in favor of lxc-copy
        clone_vars = 'variables-lxc-copy'
        clone_cmd = self.module.get_bin_path('lxc-copy')
        if not clone_cmd:
            clone_vars = 'variables-lxc-clone'
            clone_cmd = self.module.get_bin_path('lxc-clone', True)

        build_command = [
            clone_cmd,
        ]

        build_command = self._add_variables(
            variables_dict=self._get_vars(
                variables=LXC_COMMAND_MAP['clone'][clone_vars]
            ),
            build_command=build_command
        )

        # Load logging for the instance when creating it.
        if self.module.params.get('clone_snapshot') in BOOLEANS_TRUE:
            build_command.append('--snapshot')
        # Check for backing_store == overlayfs if so force the use of snapshot
        # If overlay fs is used and snapshot is unset the clone command will
        # fail with an unsupported type.
        elif self.module.params.get('backing_store') == 'overlayfs':
            build_command.append('--snapshot')

        rc, return_data, err = self._run_command(build_command)
        if rc != 0:
            message = "Failed executing %s." % os.path.basename(clone_cmd)
            self.failure(
                err=err, rc=rc, msg=message, command=' '.join(
                    build_command
                )
            )
        else:
            self.state_change = True
            # Restore the original state of the origin container if it was
            # not in a stopped state.
            if container_state == 'running':
                self.container.start()
            elif container_state == 'frozen':
                self.container.start()
                self.container.freeze()

        return True

    def _create(self):
        """Create a new LXC container.

        This method will build and execute a shell command to build the
        container. It would have been nice to simply use the lxc python library
        however at the time this was written the python library, in both py2
        and py3 didn't support some of the more advanced container create
        processes. These missing processes mainly revolve around backing
        LXC containers with block devices.
        """

        build_command = [
            self.module.get_bin_path('lxc-create', True),
            '--name %s' % self.container_name,
            '--quiet'
        ]

        build_command = self._add_variables(
            variables_dict=self._get_vars(
                variables=LXC_COMMAND_MAP['create']['variables']
            ),
            build_command=build_command
        )

        # Load logging for the instance when creating it.
        if self.module.params.get('container_log') in BOOLEANS_TRUE:
            # Set the logging path to the /var/log/lxc if uid is root. else
            # set it to the home folder of the user executing.
            try:
                if os.getuid() != 0:
                    log_path = os.getenv('HOME')
                else:
                    if not os.path.isdir('/var/log/lxc/'):
                        os.makedirs('/var/log/lxc/')
                    log_path = '/var/log/lxc/'
            except OSError:
                log_path = os.getenv('HOME')

            build_command.extend([
                '--logfile %s' % os.path.join(
                    log_path, 'lxc-%s.log' % self.container_name
                ),
                '--logpriority %s' % self.module.params.get(
                    'container_log_level'
                ).upper()
            ])

        # Add the template commands to the end of the command if there are any
        template_options = self.module.params.get('template_options', None)
        if template_options:
            build_command.append('-- %s' % template_options)

        rc, return_data, err = self._run_command(build_command)
        if rc != 0:
            message = "Failed executing lxc-create."
            self.failure(
                err=err, rc=rc, msg=message, command=' '.join(build_command)
            )
        else:
            self.state_change = True

    def _container_data(self):
        """Returns a dict of container information.

        :returns: container data
        :rtype: ``dict``
        """

        return {
            'interfaces': self.container.get_interfaces(),
            'ips': self.container.get_ips(),
            'state': self._get_state(),
            'init_pid': int(self.container.init_pid),
            'name': self.container_name,
        }

    def _unfreeze(self):
        """Unfreeze a container.

        :returns: True or False based on if the container was unfrozen.
        :rtype: ``bol``
        """

        unfreeze = self.container.unfreeze()
        if unfreeze:
            self.state_change = True
        return unfreeze

    def _get_state(self):
        """Return the state of a container.

        If the container is not found the state returned is "absent"

        :returns: state of a container as a lower case string.
        :rtype: ``str``
        """

        if self._container_exists(container_name=self.container_name, lxc_path=self.lxc_path):
            return str(self.container.state).lower()
        else:
            return str('absent')

    def _execute_command(self):
        """Execute a shell command."""

        container_command = self.module.params.get('container_command')
        if container_command:
            container_state = self._get_state()
            if container_state == 'frozen':
                self._unfreeze()
            elif container_state == 'stopped':
                self._container_startup()

            self.container.attach_wait(create_script, container_command)
            self.state_change = True

    def _container_startup(self, timeout=60):
        """Ensure a container is started.

        :param timeout: Time before the destroy operation is abandoned.
        :type timeout: ``int``
        """

        self.container = self.get_container_bind()
        for _ in xrange(timeout):
            if self._get_state() != 'running':
                self.container.start()
                self.state_change = True
                # post startup sleep for 1 second.
                time.sleep(1)
            else:
                return True
        self.failure(
            lxc_container=self._container_data(),
            error='Failed to start container'
                  ' [ %s ]' % self.container_name,
            rc=1,
            msg='The container [ %s ] failed to start. Check to lxc is'
                ' available and that the container is in a functional'
                ' state.' % self.container_name
        )

    def _check_archive(self):
        """Create a compressed archive of a container.

        This will store archive_info in as self.archive_info
        """

        if self.module.params.get('archive') in BOOLEANS_TRUE:
            self.archive_info = {
                'archive': self._container_create_tar()
            }

    def _check_clone(self):
        """Create a compressed archive of a container.

        This will store archive_info in as self.archive_info
        """

        clone_name = self.module.params.get('clone_name')
        if clone_name:
            if not self._container_exists(container_name=clone_name, lxc_path=self.lxc_path):
                self.clone_info = {
                    'cloned': self._container_create_clone()
                }
            else:
                self.clone_info = {
                    'cloned': False
                }

    def _destroyed(self, timeout=60):
        """Ensure a container is destroyed.

        :param timeout: Time before the destroy operation is abandoned.
        :type timeout: ``int``
        """

        for _ in xrange(timeout):
            if not self._container_exists(container_name=self.container_name, lxc_path=self.lxc_path):
                break

            # Check if the container needs to have an archive created.
            self._check_archive()

            # Check if the container is to be cloned
            self._check_clone()

            if self._get_state() != 'stopped':
                self.state_change = True
                self.container.stop()

            if self.container.destroy():
                self.state_change = True

            # post destroy attempt sleep for 1 second.
            time.sleep(1)
        else:
            self.failure(
                lxc_container=self._container_data(),
                error='Failed to destroy container'
                      ' [ %s ]' % self.container_name,
                rc=1,
                msg='The container [ %s ] failed to be destroyed. Check'
                    ' that lxc is available and that the container is in a'
                    ' functional state.' % self.container_name
            )

    def _frozen(self, count=0):
        """Ensure a container is frozen.

        If the container does not exist the container will be created.

        :param count: number of times this command has been called by itself.
        :type count: ``int``
        """

        self.check_count(count=count, method='frozen')
        if self._container_exists(container_name=self.container_name, lxc_path=self.lxc_path):
            self._execute_command()

            # Perform any configuration updates
            self._config()

            container_state = self._get_state()
            if container_state == 'frozen':
                pass
            elif container_state == 'running':
                self.container.freeze()
                self.state_change = True
            else:
                self._container_startup()
                self.container.freeze()
                self.state_change = True

            # Check if the container needs to have an archive created.
            self._check_archive()

            # Check if the container is to be cloned
            self._check_clone()
        else:
            self._create()
            count += 1
            self._frozen(count)

    def _restarted(self, count=0):
        """Ensure a container is restarted.

        If the container does not exist the container will be created.

        :param count: number of times this command has been called by itself.
        :type count: ``int``
        """

        self.check_count(count=count, method='restart')
        if self._container_exists(container_name=self.container_name, lxc_path=self.lxc_path):
            self._execute_command()

            # Perform any configuration updates
            self._config()

            if self._get_state() != 'stopped':
                self.container.stop()
                self.state_change = True

            # Run container startup
            self._container_startup()

            # Check if the container needs to have an archive created.
            self._check_archive()

            # Check if the container is to be cloned
            self._check_clone()
        else:
            self._create()
            count += 1
            self._restarted(count)

    def _stopped(self, count=0):
        """Ensure a container is stopped.

        If the container does not exist the container will be created.

        :param count: number of times this command has been called by itself.
        :type count: ``int``
        """

        self.check_count(count=count, method='stop')
        if self._container_exists(container_name=self.container_name, lxc_path=self.lxc_path):
            self._execute_command()

            # Perform any configuration updates
            self._config()

            if self._get_state() != 'stopped':
                self.container.stop()
                self.state_change = True

            # Check if the container needs to have an archive created.
            self._check_archive()

            # Check if the container is to be cloned
            self._check_clone()
        else:
            self._create()
            count += 1
            self._stopped(count)

    def _started(self, count=0):
        """Ensure a container is started.

        If the container does not exist the container will be created.

        :param count: number of times this command has been called by itself.
        :type count: ``int``
        """

        self.check_count(count=count, method='start')
        if self._container_exists(container_name=self.container_name, lxc_path=self.lxc_path):
            container_state = self._get_state()
            if container_state == 'running':
                pass
            elif container_state == 'frozen':
                self._unfreeze()
            elif not self._container_startup():
                self.failure(
                    lxc_container=self._container_data(),
                    error='Failed to start container'
                          ' [ %s ]' % self.container_name,
                    rc=1,
                    msg='The container [ %s ] failed to start. Check to lxc is'
                        ' available and that the container is in a functional'
                        ' state.' % self.container_name
                )

            # Return data
            self._execute_command()

            # Perform any configuration updates
            self._config()

            # Check if the container needs to have an archive created.
            self._check_archive()

            # Check if the container is to be cloned
            self._check_clone()
        else:
            self._create()
            count += 1
            self._started(count)

    def _get_lxc_vg(self):
        """Return the name of the Volume Group used in LXC."""

        build_command = [
            self.module.get_bin_path('lxc-config', True),
            "lxc.bdev.lvm.vg"
        ]
        rc, vg, err = self._run_command(build_command)
        if rc != 0:
            self.failure(
                err=err,
                rc=rc,
                msg='Failed to read LVM VG from LXC config',
                command=' '.join(build_command)
            )
        else:
            return str(vg.strip())

    def _lvm_lv_list(self):
        """Return a list of all lv in a current vg."""

        vg = self._get_lxc_vg()
        build_command = [
            self.module.get_bin_path('lvs', True)
        ]
        rc, stdout, err = self._run_command(build_command)
        if rc != 0:
            self.failure(
                err=err,
                rc=rc,
                msg='Failed to get list of LVs',
                command=' '.join(build_command)
            )

        all_lvms = [i.split() for i in stdout.splitlines()][1:]
        return [lv_entry[0] for lv_entry in all_lvms if lv_entry[1] == vg]

    def _get_vg_free_pe(self, vg_name):
        """Return the available size of a given VG.

        :param vg_name: Name of volume.
        :type vg_name: ``str``
        :returns: size and measurement of an LV
        :type: ``tuple``
        """

        build_command = [
            'vgdisplay',
            vg_name,
            '--units',
            'g'
        ]
        rc, stdout, err = self._run_command(build_command)
        if rc != 0:
            self.failure(
                err=err,
                rc=rc,
                msg='failed to read vg %s' % vg_name,
                command=' '.join(build_command)
            )

        vg_info = [i.strip() for i in stdout.splitlines()][1:]
        free_pe = [i for i in vg_info if i.startswith('Free')]
        _free_pe = free_pe[0].split()
        return float(_free_pe[-2]), _free_pe[-1]

    def _get_lv_size(self, lv_name):
        """Return the available size of a given LV.

        :param lv_name: Name of volume.
        :type lv_name: ``str``
        :returns: size and measurement of an LV
        :type: ``tuple``
        """

        vg = self._get_lxc_vg()
        lv = os.path.join(vg, lv_name)
        build_command = [
            'lvdisplay',
            lv,
            '--units',
            'g'
        ]
        rc, stdout, err = self._run_command(build_command)
        if rc != 0:
            self.failure(
                err=err,
                rc=rc,
                msg='failed to read lv %s' % lv,
                command=' '.join(build_command)
            )

        lv_info = [i.strip() for i in stdout.splitlines()][1:]
        _free_pe = [i for i in lv_info if i.startswith('LV Size')]
        free_pe = _free_pe[0].split()
        return self._roundup(float(free_pe[-2])), free_pe[-1]

    def _lvm_snapshot_create(self, source_lv, snapshot_name,
                             snapshot_size_gb=5):
        """Create an LVM snapshot.

        :param source_lv: Name of lv to snapshot
        :type source_lv: ``str``
        :param snapshot_name: Name of lv snapshot
        :type snapshot_name: ``str``
        :param snapshot_size_gb: Size of snapshot to create
        :type snapshot_size_gb: ``int``
        """

        vg = self._get_lxc_vg()
        free_space, messurement = self._get_vg_free_pe(vg_name=vg)

        if free_space < float(snapshot_size_gb):
            message = (
                'Snapshot size [ %s ] is > greater than [ %s ] on volume group'
                ' [ %s ]' % (snapshot_size_gb, free_space, vg)
            )
            self.failure(
                error='Not enough space to create snapshot',
                rc=2,
                msg=message
            )

        # Create LVM Snapshot
        build_command = [
            self.module.get_bin_path('lvcreate', True),
            "-n",
            snapshot_name,
            "-s",
            os.path.join(vg, source_lv),
            "-L%sg" % snapshot_size_gb
        ]
        rc, stdout, err = self._run_command(build_command)
        if rc != 0:
            self.failure(
                err=err,
                rc=rc,
                msg='Failed to Create LVM snapshot %s/%s --> %s'
                    % (vg, source_lv, snapshot_name)
            )

    def _lvm_lv_mount(self, lv_name, mount_point):
        """mount an lv.

        :param lv_name: name of the logical volume to mount
        :type lv_name: ``str``
        :param mount_point: path on the file system that is mounted.
        :type mount_point: ``str``
        """

        vg = self._get_lxc_vg()

        build_command = [
            self.module.get_bin_path('mount', True),
            "/dev/%s/%s" % (vg, lv_name),
            mount_point,
        ]
        rc, stdout, err = self._run_command(build_command)
        if rc != 0:
            self.failure(
                err=err,
                rc=rc,
                msg='failed to mountlvm lv %s/%s to %s'
                    % (vg, lv_name, mount_point)
            )

    def _create_tar(self, source_dir):
        """Create an archive of a given ``source_dir`` to ``output_path``.

        :param source_dir:  Path to the directory to be archived.
        :type source_dir: ``str``
        """

        old_umask = os.umask(int('0077', 8))

        archive_path = self.module.params.get('archive_path')
        if not os.path.isdir(archive_path):
            os.makedirs(archive_path)

        archive_compression = self.module.params.get('archive_compression')
        compression_type = LXC_COMPRESSION_MAP[archive_compression]

        # remove trailing / if present.
        archive_name = '%s.%s' % (
            os.path.join(
                archive_path,
                self.container_name
            ),
            compression_type['extension']
        )

        build_command = [
            self.module.get_bin_path('tar', True),
            '--directory=%s' % os.path.realpath(
                os.path.expanduser(source_dir)
            ),
            compression_type['argument'],
            archive_name,
            '.'
        ]

        rc, stdout, err = self._run_command(
            build_command=build_command,
            unsafe_shell=True
        )

        os.umask(old_umask)

        if rc != 0:
            self.failure(
                err=err,
                rc=rc,
                msg='failed to create tar archive',
                command=' '.join(build_command)
            )

        return archive_name

    def _lvm_lv_remove(self, lv_name):
        """Remove an LV.

        :param lv_name: The name of the logical volume
        :type lv_name: ``str``
        """

        vg = self._get_lxc_vg()
        build_command = [
            self.module.get_bin_path('lvremove', True),
            "-f",
            "%s/%s" % (vg, lv_name),
        ]
        rc, stdout, err = self._run_command(build_command)
        if rc != 0:
            self.failure(
                err=err,
                rc=rc,
                msg='Failed to remove LVM LV %s/%s' % (vg, lv_name),
                command=' '.join(build_command)
            )

    def _rsync_data(self, container_path, temp_dir):
        """Sync the container directory to the temp directory.

        :param container_path: path to the container container
        :type container_path: ``str``
        :param temp_dir: path to the temporary local working directory
        :type temp_dir: ``str``
        """
        # This loop is created to support overlayfs archives. This should
        # squash all of the layers into a single archive.
        fs_paths = container_path.split(':')
        if 'overlayfs' in fs_paths:
            fs_paths.pop(fs_paths.index('overlayfs'))

        for fs_path in fs_paths:
            # Set the path to the container data
            fs_path = os.path.dirname(fs_path)

            # Run the sync command
            build_command = [
                self.module.get_bin_path('rsync', True),
                '-aHAX',
                fs_path,
                temp_dir
            ]
            rc, stdout, err = self._run_command(
                build_command,
                unsafe_shell=True
            )
            if rc != 0:
                self.failure(
                    err=err,
                    rc=rc,
                    msg='failed to perform archive',
                    command=' '.join(build_command)
                )

    def _unmount(self, mount_point):
        """Unmount a file system.

        :param mount_point: path on the file system that is mounted.
        :type mount_point: ``str``
        """

        build_command = [
            self.module.get_bin_path('umount', True),
            mount_point,
        ]
        rc, stdout, err = self._run_command(build_command)
        if rc != 0:
            self.failure(
                err=err,
                rc=rc,
                msg='failed to unmount [ %s ]' % mount_point,
                command=' '.join(build_command)
            )

    def _overlayfs_mount(self, lowerdir, upperdir, mount_point):
        """mount an lv.

        :param lowerdir: name/path of the lower directory
        :type lowerdir: ``str``
        :param upperdir: name/path of the upper directory
        :type upperdir: ``str``
        :param mount_point: path on the file system that is mounted.
        :type mount_point: ``str``
        """

        build_command = [
            self.module.get_bin_path('mount', True),
            '-t overlayfs',
            '-o lowerdir=%s,upperdir=%s' % (lowerdir, upperdir),
            'overlayfs',
            mount_point,
        ]
        rc, stdout, err = self._run_command(build_command)
        if rc != 0:
            self.failure(
                err=err,
                rc=rc,
                msg='failed to mount overlayfs:%s:%s to %s -- Command: %s'
                    % (lowerdir, upperdir, mount_point, build_command)
            )

    def _container_create_tar(self):
        """Create a tar archive from an LXC container.

        The process is as follows:
            * Stop or Freeze the container
            * Create temporary dir
            * Copy container and config to temporary directory
            * If LVM backed:
                * Create LVM snapshot of LV backing the container
                * Mount the snapshot to tmpdir/rootfs
            * Restore the state of the container
            * Create tar of tmpdir
            * Clean up
        """

        # Create a temp dir
        temp_dir = tempfile.mkdtemp()

        # Set the name of the working dir, temp + container_name
        work_dir = os.path.join(temp_dir, self.container_name)

        # LXC container rootfs
        lxc_rootfs = self.container.get_config_item('lxc.rootfs')

        # Test if the containers rootfs is a block device
        block_backed = lxc_rootfs.startswith(os.path.join(os.sep, 'dev'))

        # Test if the container is using overlayfs
        overlayfs_backed = lxc_rootfs.startswith('overlayfs')

        mount_point = os.path.join(work_dir, 'rootfs')

        # Set the snapshot name if needed
        snapshot_name = '%s_lxc_snapshot' % self.container_name

        container_state = self._get_state()
        try:
            # Ensure the original container is stopped or frozen
            if container_state not in ['stopped', 'frozen']:
                if container_state == 'running':
                    self.container.freeze()
                else:
                    self.container.stop()

            # Sync the container data from the container_path to work_dir
            self._rsync_data(lxc_rootfs, temp_dir)

            if block_backed:
                if snapshot_name not in self._lvm_lv_list():
                    if not os.path.exists(mount_point):
                        os.makedirs(mount_point)

                    # Take snapshot
                    size, measurement = self._get_lv_size(
                        lv_name=self.container_name
                    )
                    self._lvm_snapshot_create(
                        source_lv=self.container_name,
                        snapshot_name=snapshot_name,
                        snapshot_size_gb=size
                    )

                    # Mount snapshot
                    self._lvm_lv_mount(
                        lv_name=snapshot_name,
                        mount_point=mount_point
                    )
                else:
                    self.failure(
                        err='snapshot [ %s ] already exists' % snapshot_name,
                        rc=1,
                        msg='The snapshot [ %s ] already exists. Please clean'
                            ' up old snapshot of containers before continuing.'
                            % snapshot_name
                    )
            elif overlayfs_backed:
                lowerdir, upperdir = lxc_rootfs.split(':')[1:]
                self._overlayfs_mount(
                    lowerdir=lowerdir,
                    upperdir=upperdir,
                    mount_point=mount_point
                )

            # Set the state as changed and set a new fact
            self.state_change = True
            return self._create_tar(source_dir=work_dir)
        finally:
            if block_backed or overlayfs_backed:
                # unmount snapshot
                self._unmount(mount_point)

            if block_backed:
                # Remove snapshot
                self._lvm_lv_remove(snapshot_name)

            # Restore original state of container
            if container_state == 'running':
                if self._get_state() == 'frozen':
                    self.container.unfreeze()
                else:
                    self.container.start()

            # Remove tmpdir
            shutil.rmtree(temp_dir)

    def check_count(self, count, method):
        if count > 1:
            self.failure(
                error='Failed to %s container' % method,
                rc=1,
                msg='The container [ %s ] failed to %s. Check to lxc is'
                    ' available and that the container is in a functional'
                    ' state.' % (self.container_name, method)
            )

    def failure(self, **kwargs):
        """Return a Failure when running an Ansible command.

        :param error: ``str``  Error that occurred.
        :param rc: ``int``     Return code while executing an Ansible command.
        :param msg: ``str``    Message to report.
        """

        self.module.fail_json(**kwargs)

    def run(self):
        """Run the main method."""

        action = getattr(self, LXC_ANSIBLE_STATES[self.state])
        action()

        outcome = self._container_data()
        if self.archive_info:
            outcome.update(self.archive_info)

        if self.clone_info:
            outcome.update(self.clone_info)

        self.module.exit_json(
            changed=self.state_change,
            lxc_container=outcome
        )


def main():
    """Ansible Main module."""

    module = AnsibleModule(
        argument_spec=dict(
            name=dict(
                type='str',
                required=True
            ),
            template=dict(
                type='str',
                default='ubuntu'
            ),
            backing_store=dict(
                type='str',
                choices=LXC_BACKING_STORE.keys(),
                default='dir'
            ),
            template_options=dict(
                type='str'
            ),
            config=dict(
                type='path',
            ),
            vg_name=dict(
                type='str',
                default='lxc'
            ),
            thinpool=dict(
                type='str'
            ),
            fs_type=dict(
                type='str',
                default='ext4'
            ),
            fs_size=dict(
                type='str',
                default='5G'
            ),
            directory=dict(
                type='path'
            ),
            zfs_root=dict(
                type='str'
            ),
            lv_name=dict(
                type='str'
            ),
            lxc_path=dict(
                type='path'
            ),
            state=dict(
                choices=LXC_ANSIBLE_STATES.keys(),
                default='started'
            ),
            container_command=dict(
                type='str'
            ),
            container_config=dict(
                type='str'
            ),
            container_log=dict(
                type='bool',
                default='false'
            ),
            container_log_level=dict(
                choices=[n for i in LXC_LOGGING_LEVELS.values() for n in i],
                default='INFO'
            ),
            clone_name=dict(
                type='str',
                required=False
            ),
            clone_snapshot=dict(
                type='bool',
                default='false'
            ),
            archive=dict(
                type='bool',
                default='false'
            ),
            archive_path=dict(
                type='path',
            ),
            archive_compression=dict(
                choices=LXC_COMPRESSION_MAP.keys(),
                default='gzip'
            )
        ),
        supports_check_mode=False,
        required_if=([
            ('archive', True, ['archive_path'])
        ]),
    )

    if not HAS_LXC:
        module.fail_json(
            msg='The `lxc` module is not importable. Check the requirements.'
        )

    lv_name = module.params.get('lv_name')
    if not lv_name:
        module.params['lv_name'] = module.params.get('name')

    lxc_manage = LxcContainerManagement(module=module)
    lxc_manage.run()


if __name__ == '__main__':
    main()
