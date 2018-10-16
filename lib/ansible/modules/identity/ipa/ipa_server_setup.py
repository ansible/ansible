#!/usr/bin/python
""" Configure ipa-server """
# -*- coding: utf-8 -*-
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
import subprocess
import re
from ansible.module_utils.basic import AnsibleModule


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: ipa_server_setup

short_description: Setup an ipa_server

version_added: "2.4"

description:
    - "After installing the ipa-server package, use this module to ipa-server configured and running"

options:
  hostname:
    description:
      - Hostname of the ipa server you wish to configure.
    required: true
    type: string
  adminpass:
    description:
      - Kerberos admin user password
    required: true
    type: string
  dmpass:
    description:
      - Directory manager admin user password
    required: true
    type: string
  realmname:
    description:
      - Kerberos realm domain name
    required: true
    type: string
  domainname:
    description:
      - DNS domain name
    required: true
    type: string
  setupdns:
    description:
      - Setup a DNS server
      - True or False value
    required: true
    type: boolean
  forwarder:
    description:
      - Configure DNS forwarders
      - only required if setupdns is set to True
    required: false
    type: string

author:
    - Ben Lewis
'''

EXAMPLES = '''

# If possible, don't put passwords in playbooks, use variables encrypted with vault
# https://docs.ansible.com/ansible/latest/user_guide/playbooks_vault.html

# Configure an IPA server including setting up a dns server
- name: configure ipa server
  ipa_server_setup:
    hostname: ipa1.ben.home
    adminpass: "{{ admin_pass }}"
    dmpass: "{{ admin_pass }}"
    realmname: ben.home
    domainname: ben.home
    setupdns: True
    forwarder: 8.8.8.8
  no_log: true

# Configure an IPA server without a dns server
- name: configure ipa server
  ipa_server_setup:
    hostname: ipa1.ben.home
    adminpass: "{{ admin_pass }}"
    dmpass: "{{ admin_pass }}"
    realmname: ben.home
    domainname: ben.home
    setupdns: False
  no_log: true

'''

RETURN = '''
original_message:
    description: The original name param that was passed in
    type: str
message:
    description: The output message that the sample module generates
'''


def ipa_stuff(params):
    """ Run IPA server install using passed in params """
    #
    # get parameters from args dict
    #
    ipahostname = "--hostname=" + params["hostname"]
    adminpass = params["adminpass"]
    dmpass = params["dmpass"]
    domainname = params["domainname"]
    realmname = params["realmname"]
    setupdns = params["setupdns"]
    # define output dict with some sane defaults
    results = {
        "output": "",
        "rc": "0",
        "change": True,
    }

    config_array = [
        "/sbin/ipa-server-install",
        "-p",
        dmpass,
        "-a",
        adminpass,
        ipahostname,
        "-n",
        domainname,
        "-r",
        realmname,
        "-U"
    ]

    # check if DNS is being configured
    if setupdns:
        forwarder = "--forwarder=" + params["forwarder"]
        config_array.append("--setup-dns")
        config_array.append(forwarder)

    #
    # attempt to run the IPA install
    #
    try:
        #
        # set the values to reflect a successful run
        #
        results["output"] = subprocess.check_output(config_array, stderr=subprocess.STDOUT)
        results["rc"] = 0
        results["change"] = True
    #
    # catch any exceptions
    #
    except subprocess.CalledProcessError as error:
        #
        # place the error in the dict, set change to false and change return code to error (1)
        #
        results["output"] = error.output
        results["change"] = False
        results["rc"] = 1
        #
        # split the command output by newline
        #
        search_output = results["output"].split('\n')
        #
        # iterate through array
        #
        for line in search_output:
            #
            # check if error is due to ipa already being configured
            #
            regexpgroup = re.search(r'^.*already exists in DNS.*(server\(s\))\:\s(.+)\.$', line)
            regexpgroup2 = re.search(r'^.*IPA server is already configured.*$', line)
            #
            # if failure is due to zone already being managed by a DNS master do some more checks
            #
            if regexpgroup:
                #
                # check hostname of ipa server
                #
                hostname = subprocess.check_output("hostname").rstrip()
                #
                # get DNS server name hosting zone requested
                #
                dnshost = regexpgroup.group(2).rstrip()
                #
                # if hostnames match, change error to a non failure for idempotent
                #
                if hostname == dnshost:
                    results["output"] = "IPA already configured on server."
                    results["rc"] = 0
                    results["change"] = False
            if regexpgroup2:
                results["output"] = "IPA already configured on server."
                results["rc"] = 0
                results["change"] = False

    #
    # return result dict
    #
    return results


def run_module():
    """ Get arguments from input, verify parameters """
    # define the available arguments/parameters that a user can pass to
    # the module
    module_args = dict(
        hostname=dict(type='str', required=True),
        adminpass=dict(type='str', required=True),
        dmpass=dict(type='str', required=True),
        domainname=dict(type='str', required=True),
        realmname=dict(type='str', required=True),
        setupdns=dict(type='bool', required=True),
        forwarder=dict(type='str', required=False)
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # change is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        message=''
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        return result

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)

    ipa_params = {
        "hostname": module.params["hostname"],
        "adminpass": module.params["adminpass"],
        "dmpass": module.params["dmpass"],
        "domainname": module.params["domainname"],
        "realmname": module.params["realmname"],
        "setupdns": module.params["setupdns"]
    }

    # if dns configured, add forwarders to ipa_params dict.
    if module.params["setupdns"]:
        if module.params["forwarder"]:
            ipa_params["forwarder"] = module.params["forwarder"]
        # if no forwarder configured, throw a useful error and exit
        else:
            msg = "Error: no dns forwarder configured, required forwarder: XXX.XXX.XXX.XXX"
            result['message'] = msg
            result['rc'] = 1
            result['changed'] = False
            module.exit_json(**result)
            return result
    #
    # pass parameters to ipa_stuff and configure ipa server, capture output in dict
    #
    joinstate = ipa_stuff(ipa_params)

    result['message'] = joinstate["output"]
    result['rc'] = joinstate["rc"]
    result['changed'] = joinstate["change"]

    # during the execution of the module, if there is an exception or a
    # conditional state that effectively causes a failure, run
    # AnsibleModule.fail_json() to pass in the message and the result
    if module.params['hostname'] == 'fail me':
        module.fail_json(msg='You requested this to fail', **result)

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    """ main function """
    run_module()


if __name__ == '__main__':
    main()
