#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2015 Nandaja Varma <nvarma@redhat.com>
# Copyright 2018 Red Hat, Inc.
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''

---
module: gluster_georep
short_description: Create/Delete/Start/Stop GlusterFS Geo-Replicatoin sessions
description:
  - The gluster_georep module creates/deletes/starts/stops/reconfigures the
    Geo-Replication sessions. Module expects master and slave GlusterFS volumes
    to be already created, with these parameters it establishes a
    Geo-Replication sessions between them. Once the session is created, the
    sessions can be configured using the module. Existing Geo-Replication
    sessions can be maintained using this module.
version_added: "2.6"
author: Sachidananda Urs (@sac)
options:
    state:
       choices: ["present", "absent", "started", "stopped", "paused", "resumed"]
       description:
          - Determines whether the Geo-Replication session should be created,
            deleted, started, stopped, paused, or resumed.
       required: true
    mastervol:
       description:
          - GlusterFS volume which has to be used as master volume for creating
            Geo-Replication session.
       required: true
    slavevol:
       description:
          - GlusterFS volume which has to be used as slave volume for creating
            Geo-Replication session.
       required: true
    force:
       type: bool
       default: "false"
       description:
          - Applicable only with states started, stopped, and while creating a
            Geo-Replication session. If force is set to yes, the volume will be
            started/stopped/created despite the client verification failure.
    georepuser:
       default: "root"
       description:
          - The Geo-Replication user to be used while performing any of
            Geo-Replication's administrative tasks. If no user is specified
            "root" is used.
    gluster_log_file:
       description:
          - The path to the Geo-Replication glusterfs log file.
    gluster_log_level:
       choices: ["INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL", "NONE",
                 "TRACE"]
       default: "INFO"
       description:
          - The log level for glusterfs processes.
    log_file:
       description:
          - The path to the geo-replication log file.
    log_level:
       choices: ["INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL", "NONE",
                 "TRACE"]
       default: "INFO"
       description:
          - The log level for geo-replication.
    changelog_log_level:
       choices: ["INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL", "NONE",
                 "TRACE"]
       default: "INFO"
       description:
          - The log level for the changelog.
    ssh_command:
       default: "ssh"
       description:
          - The SSH command to connect to the remote machine.
    rsync_command:
       default: "rsync"
       description:
          - The rsync command to use for synchronizing the files.
    use_tarssh:
       choices: ["true", "false"]
       default: "false"
       description:
          - The use-tarssh command allows tar over Secure Shell protocol. Use
            this option to handle workloads of files that have not undergone
            edits.
    volume_id:
       description:
          - The command to delete the existing master UID for the
            intermediate/slave node.
    timeout:
       description:
          - The timeout period in seconds.
    sync_jobs:
       description:
          - The number of sync-jobs represents the maximum number of syncer
            threads (rsync processes or tar over ssh processes for syncing)
            inside each worker.
    ignore_deletes:
       description:
          - If this option is set to 1, a file deleted on the master will not
            trigger a delete operation on the slave. As a result, the slave will
            remain as a superset of the master and can be used to recover the
            master in the event of a crash and/or accidental delete.
    checkpoint:
       description:
          - Sets a checkpoint with the given option LABEL. If the option is set
            as `now', then the current time will be used as the label.
    sync_acls:
       choices: ["true", "false"]
       default: "true"
       description:
          - Syncs acls to the Slave cluster. By default, this option is enabled.
            Geo-replication can sync acls only with rsync as the sync engine and
            not with tarssh as the sync engine.
    sync_xattrs:
       choices: ["true", "false"]
       default: "true"
       description:
          - Syncs extended attributes to the Slave cluster. By default, this
            option is enabled.
    log_rsync_performance:
       choices: ["true", "false"]
       default: "false"
       description:
          - If this option is set to enable, geo-replication starts recording
            the rsync performance in log files. By default, this option is
            disabled.
    rsync_options:
       description:
          - Additional options to rsync. For example, you can limit the rsync
            bandwidth usage "--bwlimit=<value>".
    use_meta_volume:
       choices: ["true", "false"]
       default: "false"
       description:
          - Set this option to enable, to use meta volume in Geo-replicaiton. By
            default, this option is disabled.
    meta_volume_mnt:
       description:
          - The path of the meta volume mount point.

requirements:
  - GlusterFS > 3.2
notes:
  - This module does not support check mode.
'''

EXAMPLES = '''
- name: Create a Geo-Replication session
  gluster_georep:
         state: present
         mastervol: master
         slavevol: 10.70.41.224:slave
         force: true

- name: Delete a Geo-Replication session
  gluster_georep:
          state: absent
          mastervol: master
          slavevol: 10.70.41.224:slave
          force: true

- name: Start a Geo-Replication session
  gluster_georep:
          state: started
          mastervol: master
          slavevol: 10.70.41.224:slave
          force: false

- name: Pause a Geo-Replication session
  gluster_georep:
          state: paused
          mastervol: master
          slavevol: 10.70.41.224:slave

- name: Resume a paused Geo-Replication session
  gluster_georep:
          state: resumed
          mastervol: master
          slavevol: 10.70.41.224:slave

- name: Configure a Geo-Replication session
  gluster_georep:
          state: started
          mastervol: master
          slavevol: 10.70.41.224:slave
          use_tarssh: true
          rsync_command: sync
'''

RETURN = '''
'''

from ansible.module_utils.basic import AnsibleModule
import re
from distutils.version import LooseVersion


class GeoRep(object):
    def __init__(self, module):
        self.module = module
        self.state = self.module.params['state']
        # Convert the state to respective geo-replication volume actions
        if self.state == 'present':
            self.action = 'create'
        elif self.state == 'absent':
            self.action = 'delete'
        elif self.state == 'started':
            self.action = 'start'
        elif self.state == 'stopped':
            self.action = 'stop'
        elif self.state == 'paused':
            self.action = 'pause'
        elif self.state == 'resumed':
            self.action = 'resume'
        self.options = ['gluster_log_file', 'gluster_log_level', 'log_file',
                        'log_level', 'changelog_log_level', 'ssh_command',
                        'rsync_command', 'use_tarssh', 'volume_id', 'timeout',
                        'sync_jobs', 'ignore_deletes', 'checkpoint',
                        'sync_acls', 'sync_xattrs', 'log_rsync_performance',
                        'rsync_options', 'use_meta_volume', 'meta_volume_mnt']

        self.gluster_georep_ops()

    def gluster_georep_ops(self):
        mastervol = self.module.params['mastervol']
        slavevol = self.module.params['slavevol']
        slavevol = self.check_pool_exclusiveness(mastervol, slavevol)
        if self.action in ['delete']:
            force = ''
        else:
            force = 'force' if self.module.params.get('force') else ''

        # If options are set, then `state' has to be set to started
        options = self.config_georep()
        if options:
            if self.state != 'started':
                self.module.fail_json(msg="Option(s) %s can be used only "
                                      "with state=started" % options)
            else:
                # state is set to started, set the options
                self.action = 'config'
                for opt in options:
                    rc, output, err = self.call_gluster_cmd('volume',
                                                            'geo-replication',
                                                            mastervol, slavevol,
                                                            self.action, opt)
        if self.action in ['stop', 'delete'] and self.user == 'root':
            self.user = 'geoaccount'
            rc, output, err = self.call_gluster_cmd('volume', 'geo-replication',
                                                    mastervol, slavevol.replace
                                                    ('root', 'geoaccount'),
                                                    self.action, force)
        else:
            rc, output, err = self.call_gluster_cmd('volume',
                                                    'geo-replication',
                                                    mastervol, slavevol,
                                                    self.action, force)
        self._get_output(rc, output, err)

    def config_georep(self):
        configs = []
        for opt in self.options:
            value = self.module.params[opt]
            if value:
                if value == 'reset':
                    configs.append("'!" + opt.replace('_', '-') + "'")
                configs.append(opt.replace('_', '-') + ' ' + value)
        return configs

    def check_pool_exclusiveness(self, mastervol, slavevol):
        rc, output, err = self.module.run_command("gluster pool list")
        peers_in_cluster = [line.split('\t')[1].strip() for
                            line in filter(None, output.split('\n')[1:])]
        val_group = re.search("(.*):(.*)", slavevol)
        if not val_group:
            self.module.fail_json(msg="Slave volume in unknown format. "
                                  "Correct format: <hostname>:<volume name>")
        if val_group.group(1) in peers_in_cluster:
            self.module.fail_json(msg="slave volume is in the trusted "
                                  "storage pool of master")
        self.user = 'root' if self.module.params['georepuser'] is None \
            else self.module.params['georepuser']
        return self.user + '@' + val_group.group(1) + '::' + val_group.group(2)

    def call_gluster_cmd(self, *args):
        params = ' '.join(opt for opt in args)
        return self._run_command('gluster', ' ' + params + ' ')

    def _get_output(self, rc, output, err):
        carryon = True if self.action in ['stop', 'delete',
                                          'resume'] else False
        changed = False if (carryon and rc) else True
        if self.action in ['stop', 'delete'] and (
                self.user == 'root' and changed == 0):
            return
        if not rc or carryon:
            self.module.exit_json(stdout=output, changed=changed)
        else:
            self.module.fail_json(msg=err)

    def _run_command(self, op, opts):
        cmd = self.module.get_bin_path(op, True) + opts
        return self.module.run_command(cmd)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str',
                       choices=['present', 'absent', 'started', 'stopped',
                                'paused', 'resumed']),
            # resume', 'config'
            mastervol=dict(),
            slavevol=dict(),
            force=dict(type='bool', required=False),
            georepuser=dict(),
            gluster_log_file=dict(),
            gluster_log_level=dict(required=False,
                                   choices=['INFO', 'DEBUG', 'WARNING', 'ERROR',
                                            'CRITICAL', 'NONE', 'TRACE']),
            log_file=dict(),
            log_level=dict(required=False,
                           choices=['INFO', 'DEBUG', 'WARNING', 'ERROR',
                                    'CRITICAL', 'NONE', 'TRACE']),
            changelog_log_level=dict(required=False,
                                     choices=['INFO', 'DEBUG', 'WARNING',
                                              'ERROR', 'CRITICAL', 'NONE',
                                              'TRACE']),
            ssh_command=dict(),
            rsync_command=dict(),
            use_tarssh=dict(required=False, choices=['true', 'false']),
            volume_id=dict(),
            timeout=dict(),
            sync_jobs=dict(),
            ignore_deletes=dict(),
            checkpoint=dict(),
            sync_acls=dict(required=False, choices=['true', 'false']),
            sync_xattrs=dict(required=False, choices=['true', 'false']),
            log_rsync_performance=dict(required=False,
                                       choices=['true', 'false']),
            rsync_options=dict(),
            use_meta_volume=dict(required=False, choices=['true', 'false']),
            meta_volume_mnt=dict()
        ),
        supports_check_mode=False,
    )
    # Verify if GlusterFS 3.2 or over is installed
    required_version = "3.2"
    if is_invalid_gluster_version(module, required_version):
        module.fail_json(msg="GlusterFS version > %s is required" %
                         required_version)
    GeoRep(module)


def is_invalid_gluster_version(module, required_version):
    cmd = module.get_bin_path('gluster', True) + ' --version'
    result = module.run_command(cmd)
    ver_line = result[1].split('\n')[0]
    version = ver_line.split(' ')[1]
    # If the installed version is less than 3.2, it is an invalid version
    # return True
    return LooseVersion(version) < LooseVersion(required_version)


if __name__ == '__main__':
    main()
