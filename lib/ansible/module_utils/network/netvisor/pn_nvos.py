# Copyright: (c) 2018, Pluribus Networks
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)
#

from __future__ import absolute_import, division, print_function
__metaclass__ = type


import shlex


def pn_cli(module, switch=None, username=None, password=None, switch_local=None):
    """
    Method to generate the cli portion to launch the Netvisor cli.
    :param module: The Ansible module to fetch username and password.
    :return: The cli string for further processing.
    """

    cli = '/usr/bin/cli --quiet -e --no-login-prompt '

    if username and password:
        cli += '--user "%s":"%s" ' % (username, password)
    if switch:
        cli += ' switch ' + switch
    if switch_local:
        cli += ' switch-local '

    return cli


def booleanArgs(arg, trueString, falseString):
    if arg is True:
        return " %s " % trueString
    elif arg is False:
        return " %s " % falseString
    else:
        return ""


def run_cli(module, cli, state_map):
    """
    This method executes the cli command on the target node(s) and returns the
    output. The module then exits based on the output.
    :param cli: the complete cli string to be executed on the target node(s).
    :param state_map: Provides state of the command.
    :param module: The Ansible module to fetch command
    """
    state = module.params['state']
    command = state_map[state]

    cmd = shlex.split(cli)
    result, out, err = module.run_command(cmd)

    remove_cmd = '/usr/bin/cli --quiet -e --no-login-prompt'

    results = dict(
        command=' '.join(cmd).replace(remove_cmd, ''),
        msg="%s operation completed" % command,
        changed=True
    )
    # Response in JSON format
    if result != 0:
        module.exit_json(
            command=' '.join(cmd).replace(remove_cmd, ''),
            stderr=err.strip(),
            msg="%s operation failed" % command,
            changed=False
        )

    if out:
        results['stdout'] = out.strip()
    module.exit_json(**results)
