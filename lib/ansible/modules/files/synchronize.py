#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2012-2013, Timothy Appnel <tim@appnel.com>
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'core'}


DOCUMENTATION = '''
---
module: synchronize
version_added: "1.4"
short_description: A wrapper around rsync to make common tasks in your playbooks quick and easy.
description:
    - C(synchronize) is a wrapper around rsync to make common tasks in your playbooks quick and easy. It is run and originates on the local host where
      Ansible is being run. Of course, you could just use the C(command) action to call rsync yourself, but you also have to add a fair number of
      boilerplate options and host facts. C(synchronize) is not intended to provide access to the full power of rsync, but does make the most common
      invocations easier to implement. You `still` may need to call rsync directly via C(command) or C(shell) depending on your use case.
options:
  src:
    description:
      - Path on the source host that will be synchronized to the destination; The path can be absolute or relative.
    required: true
  dest:
    description:
      - Path on the destination host that will be synchronized from the source; The path can be absolute or relative.
    required: true
  dest_port:
    description:
      - Port number for ssh on the destination host. Prior to ansible 2.0, the ansible_ssh_port inventory var took precedence over this value.
    default: Value of ansible_ssh_port for this host, remote_port config setting, or the value from ssh client configuration if none of those are set
    version_added: "1.5"
  direction:
    description:
      - Specify the direction of the synchronization. In push mode the localhost or delegate is the source; In pull mode the remote host in context
        is the source.
      - This option was previously called I(mode), but was renamed to improve consistency with other file modules.
      - The alias I(mode) is still available, but may go away in a future release.
    required: false
    choices: [ 'push', 'pull' ]
    default: 'push'
    aliases:
      - mode
  archive:
    description:
      - Mirrors the rsync archive flag, enables recursive, links, perms, times, owner, group flags and -D.
    choices: [ 'yes', 'no' ]
    default: 'yes'
    required: false
  checksum:
    description:
      - Skip based on checksum, rather than mod-time & size; Note that that "archive" option is still enabled by default - the "checksum" option will
        not disable it.
    choices: [ 'yes', 'no' ]
    default: 'no'
    required: false
    version_added: "1.6"
  compress:
    description:
      - Compress file data during the transfer. In most cases, leave this enabled unless it causes problems.
    choices: [ 'yes', 'no' ]
    default: 'yes'
    required: false
    version_added: "1.7"
  existing_only:
    description:
      - Skip creating new files on receiver.
    choices: [ 'yes', 'no' ]
    default: 'no'
    required: false
    version_added: "1.5"
  delete:
    description:
      - Delete files in C(dest) that don't exist (after transfer, not before) in the C(src) path. This option requires C(recursive=yes).
    choices: [ 'yes', 'no' ]
    default: 'no'
    required: false
  dirs:
    description:
      - Transfer directories without recursing
    choices: [ 'yes', 'no' ]
    default: 'no'
    required: false
  recursive:
    description:
      - Recurse into directories.
    choices: [ 'yes', 'no' ]
    default: the value of the archive option
    required: false
  preserve_links:
    description:
      - Copy symlinks as symlinks.
      - If both this and I(copy_links) are C(no), symlinks are ignored.
      - This option was previously called I(links), but was renamed to improve consistency.
      - The alias I(links) is still available, but may go away in a future release.
    choices: [ 'yes', 'no' ]
    default: the value of the archive option
    required: false
    aliases:
      - links
  copy_links:
    description:
      - Copy symlinks as the item that they point to (the referent) is copied, rather than the symlink.
      - This option is not the exact opposite of I(preserve_links)=C(no). If both I(copy_links) and I(preserve_links) or I(archive) are C(no),
        then nothing is created at the destination if a symlink is encountered.
    choices: [ 'yes', 'no' ]
    default: 'no'
    required: false
  preserve_mode:
    description:
      - Preserve permissions.
      - This option was previously called I(perms), but was renamed to improve consistency.
      - The alias I(perms) is still available, but may go away in a future release.
    choices: [ 'yes', 'no' ]
    default: the value of the archive option
    required: false
    aliases:
      - perms
  preserve_times:
    description:
      - Preserve modification times.
      - This option was previously called I(times), but was renamed to improve consistency.
      - The alias I(times) is still available, but may go away in a future release.
    choices: [ 'yes', 'no' ]
    default: the value of the archive option
    required: false
    aliases:
      - times
  preserve_owner:
    description:
      - Preserve owner. (super user only)
      - This option was previously called I(owner), but was renamed to improve consistency with other file modules.
      - The alias I(owner) is still available, but may go away in a future release.
    choices: [ 'yes', 'no' ]
    default: the value of the archive option
    required: false
    aliases:
      - owner
  preserve_group:
    description:
      - Preserve group.
      - This option was previously called I(group), but was renamed to improve consistency with other file modules.
      - The alias I(group) is still available, but may go away in a future release.
    choices: [ 'yes', 'no' ]
    default: the value of the archive option
    required: false
    aliases:
      - group
  rsync_path:
    description:
      - Specify the rsync command to run on the remote host. See C(--rsync-path) on the rsync man page.
    required: false
  rsync_timeout:
    description:
      - Specify a --timeout for the rsync command in seconds.
    default: 0
    required: false
  set_remote_user:
    description:
      - put user@ for the remote paths. If you have a custom ssh config to define the remote user for a host
        that does not match the inventory user, you should set this parameter to "no".
    default: yes
  use_ssh_args:
    description:
      - Use the ssh_args specified in ansible.cfg
    default: "no"
    choices:
      - "yes"
      - "no"
    version_added: "2.0"
  rsync_opts:
    description:
      - Specify additional rsync options by passing in an array.
    default:
    required: false
    version_added: "1.6"
  partial:
    description:
      - Tells rsync to keep the partial file which should make a subsequent transfer of the rest of the file much faster.
    default: no
    required: false
    version_added: "2.0"
  verify_host:
    description:
      - Verify destination host key.
    default: no
    required: false
    version_added: "2.0"
notes:
   - rsync must be installed on both the local and remote host.
   - For the C(synchronize) module, the "local host" is the host `the synchronize task originates on`, and the "destination host" is the host
     `synchronize is connecting to`.
   - The "local host" can be changed to a different host by using `delegate_to`.  This enables copying between two remote hosts or entirely on one
     remote machine.
   - >
     The user and permissions for the synchronize `src` are those of the user running the Ansible task on the local host (or the remote_user for a
     delegate_to host when delegate_to is used).
   - The user and permissions for the synchronize `dest` are those of the `remote_user` on the destination host or the `become_user` if `become=yes` is active.
   - In 2.0.0.0 a bug in the synchronize module made become occur on the "local host".  This was fixed in 2.0.1.
   - Currently, synchronize is limited to elevating permissions via passwordless sudo.  This is because rsync itself is connecting to the remote machine
     and rsync doesn't give us a way to pass sudo credentials in.
   - Currently there are only a few connection types which support synchronize (ssh, paramiko, local, and docker) because a sync strategy has been
     determined for those connection types.  Note that the connection for these must not need a password as rsync itself is making the connection and
     rsync does not provide us a way to pass a password to the connection.
   - Expect that dest=~/x will be ~<remote_user>/x even if using sudo.
   - Inspect the verbose output to validate the destination user/host/path
     are what was expected.
   - To exclude files and directories from being synchronized, you may add
     C(.rsync-filter) files to the source directory.
   - rsync daemon must be up and running with correct permission when using
     rsync protocol in source or destination path.
   - The C(synchronize) module forces `--delay-updates` to avoid leaving a destination in a broken in-between state if the underlying rsync process
     encounters an error. Those synchronizing large numbers of files that are willing to trade safety for performance should call rsync directly.

author: "Timothy Appnel (@tima)"
'''

EXAMPLES = '''
# Synchronization of src on the control machine to dest on the remote hosts
- synchronize:
    src: some/relative/path
    dest: /some/absolute/path

# Synchronization using rsync protocol (push)
- synchronize:
    src: some/relative/path/
    dest: rsync://somehost.com/path/

# Synchronization using rsync protocol (pull)
- synchronize:
    direction: pull
    src: rsync://somehost.com/path/
    dest: /some/absolute/path/

# Synchronization using rsync protocol on delegate host (push)
- synchronize:
    src: /some/absolute/path/
    dest: rsync://somehost.com/path/
  delegate_to: delegate.host

# Synchronization using rsync protocol on delegate host (pull)
- synchronize:
    direction: pull
    src: rsync://somehost.com/path/
    dest: /some/absolute/path/
  delegate_to: delegate.host

# Synchronization without any --archive options enabled
- synchronize:
    src: some/relative/path
    dest: /some/absolute/path
    archive: no

# Synchronization with --archive options enabled except for --recursive
- synchronize:
    src: some/relative/path
    dest: /some/absolute/path
    recursive: no

# Synchronization with --archive options enabled except for --times, with --checksum option enabled
- synchronize:
    src: some/relative/path
    dest: /some/absolute/path
    checksum: yes
    preserve_times: no

# Synchronization without --archive options enabled except use --links
- synchronize:
    src: some/relative/path
    dest: /some/absolute/path
    archive: no
    preserve_links: yes

# Synchronization of two paths both on the control machine
- synchronize:
    src: some/relative/path
    dest: /some/absolute/path
  delegate_to: localhost

# Synchronization of src on the inventory host to the dest on the localhost in pull mode
- synchronize:
    direction: pull
    src: some/relative/path
    dest: /some/absolute/path

# Synchronization of src on delegate host to dest on the current inventory host.
- synchronize:
    src: /first/absolute/path
    dest: /second/absolute/path
  delegate_to: delegate.host

# Synchronize two directories on one remote host.
- synchronize:
    src: /first/absolute/path
    dest: /second/absolute/path
  delegate_to: "{{ inventory_hostname }}"

# Synchronize and delete files in dest on the remote host that are not found in src of localhost.
- synchronize:
    src: some/relative/path
    dest: /some/absolute/path
    delete: yes
    recursive: yes

# Synchronize using an alternate rsync command
# This specific command is granted su privileges on the destination
- synchronize:
    src: some/relative/path
    dest: /some/absolute/path
    rsync_path: "su -c rsync"

# Example .rsync-filter file in the source directory
# - var       # exclude any path whose last part is 'var'
# - /var      # exclude any path starting with 'var' starting at the source directory
# + /var/conf # include /var/conf even though it was previously excluded

# Synchronize passing in extra rsync options
- synchronize:
    src: /tmp/helloworld
    dest: /var/www/helloworld
    rsync_opts:
      - "--no-motd"
      - "--exclude=.git"
'''


import os

# Python3 compat. six.moves.shlex_quote will be available once we're free to
# upgrade beyond six-1.4 module-side.
try:
    from shlex import quote as shlex_quote
except ImportError:
    from pipes import quote as shlex_quote

from ansible.module_utils.basic import AnsibleModule


client_addr = None


def substitute_controller(path):
    global client_addr
    if not client_addr:
        ssh_env_string = os.environ.get('SSH_CLIENT', None)
        try:
            client_addr, _ = ssh_env_string.split(None, 1)
        except AttributeError:
            ssh_env_string = os.environ.get('SSH_CONNECTION', None)
            try:
                client_addr, _ = ssh_env_string.split(None, 1)
            except AttributeError:
                pass
        if not client_addr:
            raise ValueError

    if path.startswith('localhost:'):
        path = path.replace('localhost', client_addr, 1)
    return path


def is_rsh_needed(source, dest):
    if source.startswith('rsync://') or dest.startswith('rsync://'):
        return False
    if ':' in source or ':' in dest:
        return True
    return False


def main():
    module = AnsibleModule(
        argument_spec = dict(
            src = dict(required=True),
            dest = dict(required=True),
            dest_port = dict(default=None, type='int'),
            delete = dict(default='no', type='bool'),
            private_key = dict(type='path', default=None),
            rsync_path = dict(default=None),
            _local_rsync_path = dict(default='rsync', type='path'),
            _substitute_controller = dict(default='no', type='bool'),
            archive = dict(default='yes', type='bool'),
            checksum = dict(default='no', type='bool'),
            compress = dict(default='yes', type='bool'),
            existing_only = dict(default='no', type='bool'),
            dirs  = dict(default='no', type='bool'),
            recursive = dict(type='bool'),
            preserve_links = dict(type='bool', aliases=['links']),
            copy_links = dict(default='no', type='bool'),
            preserve_mode = dict(type='bool', aliases=['perms']),
            preserve_times = dict(type='bool', aliases=['times']),
            preserve_owner = dict(type='bool', aliases=['owner']),
            preserve_group = dict(type='bool', aliases=['group']),
            set_remote_user = dict(default='yes', type='bool'),
            rsync_timeout = dict(type='int', default=0),
            rsync_opts = dict(type='list'),
            ssh_args = dict(type='str'),
            partial = dict(default='no', type='bool'),
            verify_host = dict(default='no', type='bool'),
            direction = dict(default='push', choices=['push', 'pull'], aliases=['mode']),
        ),
        supports_check_mode = True
    )

    if module.params['_substitute_controller']:
        try:
            source = substitute_controller(module.params['src'])
            dest = substitute_controller(module.params['dest'])
        except ValueError:
            module.fail_json(msg='Could not determine controller hostname for rsync to send to')
    else:
        source = module.params['src']
        dest = module.params['dest']
    dest_port = module.params['dest_port']
    delete = module.params['delete']
    private_key = module.params['private_key']
    rsync_path = module.params['rsync_path']
    rsync = module.params.get('_local_rsync_path', 'rsync')
    rsync_timeout = module.params.get('rsync_timeout', 'rsync_timeout')
    archive = module.params['archive']
    checksum = module.params['checksum']
    compress = module.params['compress']
    existing_only = module.params['existing_only']
    dirs = module.params['dirs']
    partial = module.params['partial']
    # the default of these params depends on the value of archive
    recursive = module.params['recursive']
    preserve_links = module.params['preserve_links']
    copy_links = module.params['copy_links']
    preserve_mode = module.params['preserve_mode']
    preserve_times = module.params['preserve_times']
    preserve_owner = module.params['preserve_owner']
    preserve_group = module.params['preserve_group']
    rsync_opts = module.params['rsync_opts']
    ssh_args = module.params['ssh_args']
    verify_host = module.params['verify_host']

    # Notify the user of deprecated parameters
    for param in (('links', 'preserve_links'), ('perms', 'preserve_mode'),
                  ('times', 'preserve_times'), ('owner', 'preserve_owner'),
                  ('group', 'preserve_group'), ('mode', 'direction')):
        if param[0] in module.params:
            module.deprecate(msg="Please use parameter " + param[1] + " instead of " + param[0])

    if '/' not in rsync:
        rsync = module.get_bin_path(rsync, required=True)

    cmd = [rsync, '--delay-updates', '-F']
    if compress:
        cmd.append('--compress')
    if rsync_timeout:
        cmd.append('--timeout=%s' % rsync_timeout)
    if module.check_mode:
        cmd.append('--dry-run')
    if delete:
        cmd.append('--delete-after')
    if existing_only:
        cmd.append('--existing')
    if checksum:
        cmd.append('--checksum')
    if copy_links:
        cmd.append('--copy-links')
    if archive:
        cmd.append('--archive')
        if recursive is False:
            cmd.append('--no-recursive')
        if preserve_links is False:
            cmd.append('--no-links')
        if preserve_mode is False:
            cmd.append('--no-perms')
        if preserve_times is False:
            cmd.append('--no-times')
        if preserve_owner is False:
            cmd.append('--no-owner')
        if preserve_group is False:
            cmd.append('--no-group')
    else:
        if recursive is True:
            cmd.append('--recursive')
        if preserve_links is True:
            cmd.append('--links')
        if preserve_mode is True:
            cmd.append('--perms')
        if preserve_times is True:
            cmd.append('--times')
        if preserve_owner is True:
            cmd.append('--owner')
        if preserve_group is True:
            cmd.append('--group')
    if dirs:
        cmd.append('--dirs')

    if source.startswith('rsync://') and dest.startswith('rsync://'):
        module.fail_json(msg='either src or dest must be a localhost', rc=1)

    if is_rsh_needed(source, dest):
        ssh_cmd = [module.get_bin_path('ssh', required=True), '-S', 'none']
        if private_key is not None:
            ssh_cmd.extend(['-i', private_key])
        # If the user specified a port value
        # Note:  The action plugin takes care of setting this to a port from
        # inventory if the user didn't specify an explicit dest_port
        if dest_port is not None:
            ssh_cmd.extend(['-o', 'Port=%s' % dest_port])
        if not verify_host:
            ssh_cmd.extend(['-o', 'StrictHostKeyChecking=no', '-o', 'UserKnownHostsFile=/dev/null'])
        ssh_cmd_str = ' '.join(shlex_quote(arg) for arg in ssh_cmd)
        if ssh_args:
            ssh_cmd_str += ' %s' % ssh_args
        cmd.append('--rsh=%s' % ssh_cmd_str)

    if rsync_path:
        cmd.append('--rsync-path=%s' % rsync_path)

    if rsync_opts:
        cmd.extend(rsync_opts)

    if partial:
        cmd.append('--partial')

    changed_marker = '<<CHANGED>>'
    cmd.append('--out-format=' + changed_marker + '%i %n%L')

    # expand the paths
    if '@' not in source:
        source = os.path.expanduser(source)
    if '@' not in dest:
        dest = os.path.expanduser(dest)

    cmd.append(source)
    cmd.append(dest)
    cmdstr = ' '.join(cmd)
    (rc, out, err) = module.run_command(cmd)
    if rc:
        return module.fail_json(msg=err, rc=rc, cmd=cmdstr)
    else:
        changed = changed_marker in out
        out_clean = out.replace(changed_marker, '')
        out_lines = out_clean.split('\n')
        while '' in out_lines:
            out_lines.remove('')
        if module._diff:
            diff = {'prepared': out_clean}
            return module.exit_json(changed=changed, msg=out_clean,
                                    rc=rc, cmd=cmdstr, stdout_lines=out_lines,
                                    diff=diff)
        else:
            return module.exit_json(changed=changed, msg=out_clean,
                                    rc=rc, cmd=cmdstr, stdout_lines=out_lines)


if __name__ == '__main__':
    main()
