# Copyright: (c) 2018, Pluribus Networks
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)
#


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
