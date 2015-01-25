#!/usr/bin/env python

import argparse
from collections import defaultdict
import ipalib
import json
import sys

def autovivify(levels=1, final=dict):
    '''
    This function builds a multidimensional dictionary of levels depth, with
    the final element being of final type.

    This function takes two arguments, levels an integer defining the 
    levels of depth, and final, an object representing the final (last) type.

    This function returns the dictionary.
    '''
    return (defaultdict(final) if levels < 2 else
            defaultdict(lambda: autovivify(levels -1, final)))

def build_ansible_variables(host):
    '''
    This function builds the variables to be returned for Ansible's use. This
    function takes one argument, a dictionary containing the LDIF return
    from FreeIPA/IPA.

    This function returns a properly formatted dictionary of variables for 
    the host. The main purpose here is to pick and choose variables to return.
    If an additional variable is needed for Ansible, simply add it here.
    '''

    variables = {}

    #Don't assume that the key exists.
    if 'sshpubkeyfp' in host:
        variables['sshpubkeyfp'] = host['sshpubkeyfp']
    
    return variables

def initialize():
    '''
    This function initializes the FreeIPA/IPA API. This function requires
    no arguments. A kerberos key must be present in the users keyring in 
    order for this to work.

    This function rturns the initialized FreeIPA/IPA object.
    '''

    ipalib.api.bootstrap(context='cli')
    ipalib.api.finalize()
    try:
        ipalib.api.Backend.xmlclient.connect()
    except ipalib.errors.CCacheError:
        sys.stderr.write('No Kerberos ticket found in the Credential Cache, '
                         'try running kinit, aborting!')
        sys.exit(1)
    return ipalib.api

def list_groups(api):
    '''
    This function retrieves the entries from FreeIPA/IPA and prints a list of 
    all host groups in JSON format. This function requires one argument, the 
    FreeIPA/IPA API object. 

    This function returns None.
    '''

    inventory = autovivify(2, list)
    hostvars={}

    result = api.Command.host_find()['result']
   
    for host in result:
       
        #Not all hosts are members of a group, so we check for the key.
        if 'memberof_hostgroup' in host:
            for hostgroup in host['memberof_hostgroup']:
                inventory[hostgroup]['hosts'].append(host['fqdn'][0])

        hostvars[host['fqdn'][0]] = build_ansible_variables(host)

    inventory['_meta'] = {'hostvars': hostvars}
    inv_string = json.dumps(inventory, indent=1, sort_keys=True)
    print inv_string
    
    return None

def parse_args():
    '''
    This function parses the arguments that were passed in via the command line.
    This function expects no arguments and returns the parsed arguments.
    '''

    parser = argparse.ArgumentParser(description='Ansible FreeIPA/IPA '
                                     'inventory module')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--list', action='store_true',
                       help='List active servers')
    group.add_argument('--host', help='List details about the specified host')

    return parser.parse_args()

def print_host(host, api):
    '''
    This function is really a stub, it could return variables to be used in 
    a playbook. However, at this point there are no variables stored in 
    FreeIPA/IPA.

    This function expects one string, this hostname to lookup variables for.

    This function prints the output of json.dumps to stdout and returns None.
    '''
    
    #The API only accepts unicode
    uhost = unicode(host)

    host_result = api.Command.host_find(uhost)['result'][0]
    
    variables = build_ansible_variables(host_result)

    print json.dumps(variables)

    return None

if __name__ == '__main__':
    args = parse_args()

    api = initialize()

    if args.host:
        print_host(args.host, api)
    elif args.list:
        list_groups(api)
