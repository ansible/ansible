#!/usr/bin/python

# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

import json
import os
import pipes
import stat

DOCUMENTATION = '''
---
module: puppet
short_description: Runs puppet
description:
  - Runs I(puppet) agent or apply in a reliable manner
version_added: "2.0"
options:
  timeout:
    description:
      - How long to wait for I(puppet) to finish.
    required: false
    default: 30m
  puppetmaster:
    description:
      - The hostname of the puppetmaster to contact. Must have this or manifest
    required: false
    default: None
  manifest:
    desciption:
      - Path to the manifest file to run puppet apply on. Must have this or puppetmaster
    required: false
    default: None
  show_diff:
    description:
      - Should puppet return diffs of changes applied. Defaults to off to avoid leaking secret changes by default.
    required: false
    default: no
    choices: [ "yes", "no" ]
  facts:
    description:
      - A dict of values to pass in as persistent external facter facts
    required: false
    default: None
  facter_basename:
    desciption:
      - Basename of the facter output file
    required: false
    default: ansible
requirements: [ puppet ]
author: Monty Taylor
'''

EXAMPLES = '''
# Run puppet and fail if anything goes wrong
- puppet

# Run puppet and timeout in 5 minutes
- puppet: timeout=5m
'''


def _get_facter_dir():
    if os.getuid() == 0:
        return '/etc/facter/facts.d'
    else:
        return os.path.expanduser('~/.facter/facts.d')


def _write_structured_data(basedir, basename, data):
    if not os.path.exists(basedir):
        os.makedirs(basedir)
    file_path = os.path.join(basedir, "{0}.json".format(basename))
    # This is more complex than you might normally expect because we want to
    # open the file with only u+rw set. Also, we use the stat constants
    # because ansible still supports python 2.4 and the octal syntax changed
    out_file = os.fdopen(
        os.open(
            file_path, os.O_CREAT | os.O_WRONLY,
            stat.S_IRUSR | stat.S_IWUSR), 'w')
    out_file.write(json.dumps(data).encode('utf8'))
    out_file.close()


def main():
    module = AnsibleModule(
        argument_spec=dict(
            timeout=dict(default="30m"),
            puppetmaster=dict(required=False, default=None),
            manifest=dict(required=False, default=None),
            show_diff=dict(
                default=False, aliases=['show-diff'], type='bool'),
            facts=dict(default=None),
            facter_basename=dict(default='ansible'),
        ),
        supports_check_mode=True,
        required_one_of=[
            ('puppetmaster', 'manifest'),
        ],
    )
    p = module.params

    global PUPPET_CMD
    PUPPET_CMD = module.get_bin_path("puppet", False)

    if not PUPPET_CMD:
        module.fail_json(
            msg="Could not find puppet. Please ensure it is installed.")

    if p['manifest']:
        if not os.path.exists(p['manifest']):
            module.fail_json(
                msg="Manifest file %(manifest)s not found." % dict(
                    manifest=p['manifest']))

    # Check if puppet is disabled here
    if p['puppetmaster']:
        rc, stdout, stderr = module.run_command(
            PUPPET_CMD + " config print agent_disabled_lockfile")
        if os.path.exists(stdout.strip()):
            module.fail_json(
                msg="Puppet agent is administratively disabled.", disabled=True)
        elif rc != 0:
            module.fail_json(
                msg="Puppet agent state could not be determined.")

    if module.params['facts'] and not module.check_mode:
        _write_structured_data(
            _get_facter_dir(),
            module.params['facter_basename'],
            module.params['facts'])

    base_cmd = "timeout -s 9 %(timeout)s %(puppet_cmd)s" % dict(
        timeout=pipes.quote(p['timeout']), puppet_cmd=PUPPET_CMD)

    if p['puppetmaster']:
        cmd = ("%(base_cmd)s agent --onetime"
               " --server %(puppetmaster)s"
               " --ignorecache --no-daemonize --no-usecacheonfailure --no-splay"
               " --detailed-exitcodes --verbose") % dict(
                   base_cmd=base_cmd,
                   puppetmaster=pipes.quote(p['puppetmaster']))
        if p['show_diff']:
            cmd += " --show-diff"
        if module.check_mode:
            cmd += " --noop"
    else:
        cmd = "%s apply --detailed-exitcodes " % base_cmd
        if module.check_mode:
            cmd += "--noop "
        cmd += pipes.quote(p['manifest'])
    rc, stdout, stderr = module.run_command(cmd)

    if rc == 0:
        # success
        module.exit_json(rc=rc, changed=False, stdout=stdout)
    elif rc == 1:
        # rc==1 could be because it's disabled
        # rc==1 could also mean there was a compilation failure
        disabled = "administratively disabled" in stdout
        if disabled:
            msg = "puppet is disabled"
        else:
            msg = "puppet did not run"
        module.exit_json(
            rc=rc, disabled=disabled, msg=msg,
            error=True, stdout=stdout, stderr=stderr)
    elif rc == 2:
        # success with changes
        module.exit_json(rc=0, changed=True)
    elif rc == 124:
        # timeout
        module.exit_json(
            rc=rc, msg="%s timed out" % cmd, stdout=stdout, stderr=stderr)
    else:
        # failure
        module.fail_json(
            rc=rc, msg="%s failed with return code: %d" % (cmd, rc),
            stdout=stdout, stderr=stderr)

# import module snippets
from ansible.module_utils.basic import *

main()
