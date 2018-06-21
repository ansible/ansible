#!/usr/bin/env python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# This script can create an Ansible Dynamic Inventory with either:
# - the FreeIPA API over HTTPS with the `python_freeipa` module
# - using kerberos authentication with the `ipalib` and `ipaclient` module
#
# DEPENDENCIES: before this script will work the python_freeipa or ipalib module has to be installed
#
# For Ansible AWX or Tower add this to your Docker image
# RUN pip install python_freeipa urllib3
# or
# RUN pip install ipalib ipaclient
#
# The script assumes Kerberos authentication mode, arguments passed to the scipt will override environment variables.
# Set the following variables in Inventory Source:
# - `ipahttps`: if True the script will attemt to use HTTPS and freeipa_python, if false the script will attemt to use Kerberos and ipalib. Default is False.
# - `ipaserver`: the FQDN of the FreeIPA/RHIdM server
# - `ipauser`: an unprivileged user account for connecting to the API
# - `ipapassword`: password for freeipauser
# - `ipaversion`: specifies the FreeIPA API version, default is 2.228

from argparse import ArgumentParser
from distutils.version import LooseVersion
from os import environ as env
import os
import sys
import json


# Parse command line arguments
def parse_args():
    parser = ArgumentParser(description="AWX FreeIPA API dynamic host inventory")
    parser.add_argument(
        '--list',
        default=False,
        dest="list",
        action="store_true",
        help="Produce a JSON consumable grouping of servers for Ansible"
    )
    parser.add_argument(
        '--host',
        default=None,
        dest="host",
        help="Generate additional host specific details for given host for Ansible"
    )
    parser.add_argument(
        '-a'
        '--api',
        default=False,
        dest="useapi",
        action="store_true",
        help="Use the FreeIPA API, otherwise use Kerberos"
    )
    parser.add_argument(
        '-u',
        '--user',
        default=None,
        dest="ipauser",
        help="username to log into FreeIPA API, ignored if --api or -a not set"
    )
    parser.add_argument(
        '-w',
        '--password',
        default=None,
        dest="ipapassword",
        help="password to log into FreeIPA API, ignored if --api or -a not set"
    )
    parser.add_argument(
        '-s',
        '--server',
        default=None,
        dest="ipaserver",
        help="hostname of FreeIPA server, ignored if --api or -a not set"
    )
    parser.add_argument(
        '--ipa-version',
        default=None,
        dest="ipaversion",
        help="version of FreeIPA server"
    )
    return parser.parse_args()


def initialize(
    use_kerberos=False
):

    # Use Kerberos authenication or use the FreeIPA API
    if use_kerberos:
        '''
        This function initializes the FreeIPA/IPA API. This function requires
        no arguments. A kerberos key must be present in the users keyring in
        order for this to work. IPA default configuration directory is /etc/ipa,
        this path could be overridden with IPA_CONFDIR environment variable.
        '''

        api.bootstrap(context='cli')

        if not os.path.isdir(api.env.confdir):
            print("WARNING: IPA configuration directory (%s) is missing. "
                  "Environment variable IPA_CONFDIR could be used to override "
                  "default path." % api.env.confdir)

        if LooseVersion(IPA_VERSION) < LooseVersion('4.6.2'):
            # With ipalib < 4.6.0 'server' and 'domain' have default values
            # ('localhost:8888', 'example.com'), newer versions don't and
            # DNS autodiscovery is broken, then one of jsonrpc_uri / xmlrpc_uri is
            # required.
            # ipalib 4.6.0 is unusable (https://pagure.io/freeipa/issue/7132)
            # that's why 4.6.2 is explicitely tested.
            sys.exit(
                "ERROR: ipalib version newer than 4.6.2 required, current version is %s" %
                IPA_VERSION
            )

        if 'server' not in api.env or 'domain' not in api.env:
            sys.exit(
                "ERROR: ('jsonrpc_uri' or 'xmlrpc_uri') or 'domain' are not "
                "defined in '[global]' section of '%s' nor in '%s'." %
                (api.env.conf, api.env.conf_default)
            )

        api.finalize()
        try:
            api.Backend.rpcclient.connect()
        except AttributeError:
            # FreeIPA < 4.0 compatibility
            api.Backend.xmlclient.connect()

        return api
    else:
        # We don't need warnings
        urllib3.disable_warnings()

        ipaserver = None
        if args.ipaserver:
            ipaserver = args.ipaserver
        elif 'ipaserver' in env:
            ipaserver = env['ipaserver']

        ipauser = None
        if args.ipauser:
            ipauser = args.ipauser
        elif 'ipauser' in env:
            ipauser = env['ipauser']

        ipapassword = None
        if args.ipapassword:
            ipapassword = args.ipapassword
        elif 'ipapassword' in env:
            ipapassword = env['ipapassword']

        ipaversion = '2.228'
        if args.ipaversion:
            ipaversion = args.ipaversion
        elif 'ipaversion' in env:
            ipaversion = env['ipaversion']

        if not ipaserver:
            sys.exit("ERROR: No IPA server given with -s/--server argument, or set with ipaserver environment variable")

        if not ipauser:
            sys.exit("ERROR: No IPA user given with -u/--user argument, or set with ipapassword environment variable")

        if not ipapassword:
            sys.exit("ERROR: No IPA password given with -w/--password argument, or set with ipapassword environment variable")

        client = Client(
            ipaserver,
            version=ipaversion,
            verify_ssl=False
        )
        client.login(
            ipauser,
            ipapassword
        )
        return client


def get_host(
    ipaconnection,
    host,
    use_kerberos=False
):
    """
    This function expects one string, this hostname to lookup variables for.
    Args:
        ipaconnection: FreeIPA API Object
        host: Name of Hostname
        use_kerberos: if True Kerberos authentication with ipalib is used, if False HTTPS auth with python_freeipa is used

    Returns: Dict of Host vars if found else None
    """
    if use_kerberos:
        try:
            result = ipaconnection.Command.host_show(host)['result']
            if 'usercertificate' in result:
                del result['usercertificate']
        except errors.NotFound as e:
            result = {}
    else:
        # We don't need warnings
        urllib3.disable_warnings()
        result = ipaconnection._request(
            'host_show',
            host,
            {'all': True, 'raw': False}
        )['result']
        if 'usercertificate' in result:
            del result['usercertificate']

    return result


def get_hostgroups(
    ipaconnection,
    use_kerberos=False
):
    '''
    This function prints a list of all host groups. This function requires
    one argument, the FreeIPA/IPA API object.
    '''
    inventory = {}
    hostvars = {}
    result = {}

    if use_kerberos:
        result = ipaconnection.Command.hostgroup_find(all=True)['result']
    else:
        # We don't need warnings
        urllib3.disable_warnings()
        result = ipaconnection._request(
            'hostgroup_find',
            '',
            {'all': True, 'raw': False}
        )['result']

    for hostgroup in result:
        members = []
        children = []

        if 'member_host' in hostgroup:
            members = [host for host in hostgroup['member_host']]
        if 'member_hostgroup' in hostgroup:
            children = hostgroup['member_hostgroup']
        inventory[hostgroup['cn'][0]] = {
            'hosts': [host for host in members],
            'children': children
        }

        for member in members:
            # This should actually grab the hostvars for the hosts
            hostvars[member] = get_host(ipaconnection, member, use_kerberos)

    inventory['_meta'] = {'hostvars': hostvars}
    return inventory


if __name__ == '__main__':
    args = parse_args()

    use_kerberos = True
    if 'ipahttps' in env:
        if env['ipahttps'].strip() in ['True', 'true']:
            use_kerberos = False
    if args.useapi:
        use_kerberos = False

    # Load the correct module
    if use_kerberos:
        try:
            from ipalib import api, errors, __version__ as IPA_VERSION
        except ImportError:
            print('The ipa dynamic inventory script requires ipalib for Kerberos authentication')
    else:
        try:
            from python_freeipa import Client
            import urllib3
        except ImportError:
            print(
                'The ipa dynamic inventory script requires python_freeipa'
                'to use the FreeIPA API with HTTPS authentication'
            )

    ipaconnection = initialize(use_kerberos)

    if args.host:
        hostvars = get_host(ipaconnection, args.host, use_kerberos)
        print(json.dumps(hostvars, indent=1, sort_keys=True))
    elif args.list:
        inventory = get_hostgroups(ipaconnection, use_kerberos)
        print(json.dumps(inventory, indent=1, sort_keys=True))
