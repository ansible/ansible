# Copyright: (c) 2018, Pluribus Networks
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)
#

from __future__ import absolute_import, division, print_function
__metaclass__ = type


from ansible.module_utils.network.netvisor.netvisor import run_commands


def pn_cli(module, switch=None, username=None, password=None, switch_local=None):
    """
    Method to generate the cli portion to launch the Netvisor cli.
    :param module: The Ansible module to fetch username and password.
    :return: The cli string for further processing.
    """

    cli = ''

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

    result, out, err = run_commands(module, cli)

    results = dict(
        command=cli,
        msg="%s operation completed" % cli,
        changed=True
    )
    # Response in JSON format
    if result != 0:
        module.exit_json(
            command=cli,
            msg="%s operation failed" % cli,
            changed=False
        )

    module.exit_json(**results)
