#!/usr/bin/python

# Copyright: (c) 2015, Hewlett-Packard Development Company, L.P.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: puppet
short_description: Runs puppet
description:
  - Runs I(puppet) agent or apply in a reliable manner.
version_added: "2.0"
options:
  timeout:
    description:
      - How long to wait for I(puppet) to finish.
    default: 30m
  puppetmaster:
    description:
      - The hostname of the puppetmaster to contact.
  modulepath:
    description:
      - Path to an alternate location for puppet modules.
    version_added: "2.4"
  manifest:
    description:
      - Path to the manifest file to run puppet apply on.
  facts:
    description:
      - A dict of values to pass in as persistent external facter facts.
  facter_basename:
    description:
      - Basename of the facter output file.
    default: ansible
  environment:
    description:
      - Puppet environment to be used.
  logdest:
    description: |
      Where the puppet logs should go, if puppet apply is being used. C(all)
      will go to both C(stdout) and C(syslog).
    choices: [ stdout, syslog, all ]
    default: stdout
    version_added: "2.1"
  certname:
    description:
      - The name to use when handling certificates.
    version_added: "2.1"
  tags:
    description:
      - A comma-separated list of puppet tags to be used.
    version_added: "2.1"
  execute:
    description:
      - Execute a specific piece of Puppet code.
      - It has no effect with a puppetmaster.
    version_added: "2.1"
  summarize:
    description:
      - Whether to print a transaction summary
    version_added: "2.7"
  verbose:
    description:
      - Print extra information
    version_added: "2.7"
  debug:
    description:
      - Enable full debugging
    version_added: "2.7"
requirements:
- puppet
author:
- Monty Taylor (@emonty)
'''

EXAMPLES = '''
- name: Run puppet agent and fail if anything goes wrong
  puppet:

- name: Run puppet and timeout in 5 minutes
  puppet:
    timeout: 5m

- name: Run puppet using a different environment
  puppet:
    environment: testing

- name: Run puppet using a specific certname
  puppet:
    certname: agent01.example.com

- name: Run puppet using a specific piece of Puppet code. Has no effect with a puppetmaster
  puppet:
    execute: include ::mymodule

- name: Run puppet using a specific tags
  puppet:
    tags: update,nginx

- name: Run a manifest with debug, log to both syslog and stdout, specify module path
  puppet:
    modulepath: /etc/puppet/modules:/opt/stack/puppet-modules:/usr/share/openstack-puppet/modules
    logdest: all
    manifest: /var/lib/example/puppet_step_config.pp
'''

import json
import os
import pipes
import stat

from ansible.module_utils.basic import AnsibleModule


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
            timeout=dict(type='str', default='30m'),
            puppetmaster=dict(type='str'),
            modulepath=dict(type='str'),
            manifest=dict(type='str'),
            logdest=dict(type='str', default='stdout', choices=['stdout',
                                                                'syslog',
                                                                'all']),
            # internal code to work with --diff, do not use
            show_diff=dict(type='bool', default=False, aliases=['show-diff']),
            facts=dict(type='dict'),
            facter_basename=dict(type='str', default='ansible'),
            environment=dict(type='str'),
            certname=dict(type='str'),
            tags=dict(type='list'),
            execute=dict(type='str'),
            summarize=dict(type='bool', default=False),
            debug=dict(type='bool', default=False),
            verbose=dict(type='bool', default=False),
        ),
        supports_check_mode=True,
        mutually_exclusive=[
            ('puppetmaster', 'manifest'),
            ('puppetmaster', 'manifest', 'execute'),
            ('puppetmaster', 'modulepath')
        ],
    )
    p = module.params

    global PUPPET_CMD
    PUPPET_CMD = module.get_bin_path("puppet", False, ['/opt/puppetlabs/bin'])

    if not PUPPET_CMD:
        module.fail_json(
            msg="Could not find puppet. Please ensure it is installed.")

    global TIMEOUT_CMD
    TIMEOUT_CMD = module.get_bin_path("timeout", False)

    if p['manifest']:
        if not os.path.exists(p['manifest']):
            module.fail_json(
                msg="Manifest file %(manifest)s not found." % dict(
                    manifest=p['manifest']))

    # Check if puppet is disabled here
    if not p['manifest']:
        rc, stdout, stderr = module.run_command(
            PUPPET_CMD + " config print agent_disabled_lockfile")
        if os.path.exists(stdout.strip()):
            module.fail_json(
                msg="Puppet agent is administratively disabled.",
                disabled=True)
        elif rc != 0:
            module.fail_json(
                msg="Puppet agent state could not be determined.")

    if module.params['facts'] and not module.check_mode:
        _write_structured_data(
            _get_facter_dir(),
            module.params['facter_basename'],
            module.params['facts'])

    if TIMEOUT_CMD:
        base_cmd = "%(timeout_cmd)s -s 9 %(timeout)s %(puppet_cmd)s" % dict(
            timeout_cmd=TIMEOUT_CMD,
            timeout=pipes.quote(p['timeout']),
            puppet_cmd=PUPPET_CMD)
    else:
        base_cmd = PUPPET_CMD

    if not p['manifest'] and not p['execute']:
        cmd = ("%(base_cmd)s agent --onetime"
               " --ignorecache --no-daemonize --no-usecacheonfailure --no-splay"
               " --detailed-exitcodes --verbose --color 0") % dict(base_cmd=base_cmd)
        if p['puppetmaster']:
            cmd += " --server %s" % pipes.quote(p['puppetmaster'])
        if p['show_diff']:
            cmd += " --show_diff"
        if p['environment']:
            cmd += " --environment '%s'" % p['environment']
        if p['tags']:
            cmd += " --tags '%s'" % ','.join(p['tags'])
        if p['certname']:
            cmd += " --certname='%s'" % p['certname']
        if module.check_mode:
            cmd += " --noop"
        else:
            cmd += " --no-noop"
    else:
        cmd = "%s apply --detailed-exitcodes " % base_cmd
        if p['logdest'] == 'syslog':
            cmd += "--logdest syslog "
        if p['logdest'] == 'all':
            cmd += " --logdest syslog --logdest stdout"
        if p['modulepath']:
            cmd += "--modulepath='%s'" % p['modulepath']
        if p['environment']:
            cmd += "--environment '%s' " % p['environment']
        if p['certname']:
            cmd += " --certname='%s'" % p['certname']
        if p['tags']:
            cmd += " --tags '%s'" % ','.join(p['tags'])
        if module.check_mode:
            cmd += "--noop "
        else:
            cmd += "--no-noop "
        if p['execute']:
            cmd += " --execute '%s'" % p['execute']
        else:
            cmd += pipes.quote(p['manifest'])
        if p['summarize']:
            cmd += " --summarize"
        if p['debug']:
            cmd += " --debug"
        if p['verbose']:
            cmd += " --verbose"
    rc, stdout, stderr = module.run_command(cmd)

    if rc == 0:
        # success
        module.exit_json(rc=rc, changed=False, stdout=stdout, stderr=stderr)
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
        module.exit_json(rc=0, changed=True, stdout=stdout, stderr=stderr)
    elif rc == 124:
        # timeout
        module.exit_json(
            rc=rc, msg="%s timed out" % cmd, stdout=stdout, stderr=stderr)
    else:
        # failure
        module.fail_json(
            rc=rc, msg="%s failed with return code: %d" % (cmd, rc),
            stdout=stdout, stderr=stderr)


if __name__ == '__main__':
    main()
