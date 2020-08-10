#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020, Zainab Alsaffar <zanssa>
# GNU General Public License v3.0 (see 'https://github.com/zanssa/ansible-python/blob/master/LICENSE')

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: jenkins_user_role
short_description: Manage a user's permission on Jenkins server that has Role-based Authorization Strategy plugin installed.
description:
    - This is a custom module built to manage the assignment of a role on Jenkins server to a user account when state is defined as present. 
    - And the removal of an assigned role to a user account when state is defined as absent.
version_added: '1.0'
author: 'Zainab Alsaffar (@zanssa)'
requirments:
    - 'python >= 2.6'
    - Jenkins API Access
    - Role-based Authorization Strategy plugin on Jenkins Server
options:
    api_token:
        description:
            - An API access token to authenticate with the Jenkins Server.
        required: true
        type: str
    login_user:
        description:
            - A user account with admin privilages to authenticate with Jenkins server.
        required: true
        type: str
    server_url: 
        description:
            - URL of a Jenkins server.
        required: true
        type: str
    proxy_server: 
        description:
            - URL of a proxy server.
        required: false
        type: str
    jenkins_user:
        description:
            - Name of the user in Jenkins Server.
        required: true
        type: str
    role_type:
        description:
            - Type of the Role on Jenkins Server.
        choices: ['global role', 'item role']
        required: true
        type: str
    role_name:
        description:
            - Name of the Role on Jenkins Server.
        required: true
        type: str
    state:
        description:
            - State of the user's access to a role.
            - On C(present), it will assign a role to a user if the assignment doesn't exist.
            - On C(absent), will remove the assignment of a role from a user if it exists.
        choices: ['present', 'absent']
        default: 'present'
        type: str
notes: supports_check_mode is allowed in this module 
'''

EXAMPLES = '''
- name: Assign a Role to a Jenkins User
  jenkins_user_role:
    server_url: 'your_server_url:port_num'
    api_token: 'your_api_access_token'
    login_user: admin
    proxy_server: proxy_server_url:port_num
    jenkins_user: example1
    role_type: global role
    role_name: authenticated
    state: present

- name: Remove a Role from a Jenkins User
  jenkins_user_role:
    server_url: 'your_server_url:port_num'
    api_token: 'your_api_access_token'
    login_user: admin
    jenkins_user: example1
    role_type: global role
    role_name: authenticated
    state: absent
'''

RETURN = '''
'''

from ansible.module_utils.basic import AnsibleModule
import requests, json, re

class JenkinsUserRole(object):
    def __init__(self, module, header, proxy):
        self._module = module
        self._jheader = header
        self._proxy = proxy

    # check if the role name exists 
    def check_role_exists(self, server_url, login_user, access_token, role_type, role_name):
        roles_name = requests.get(server_url+'/role-strategy/strategy/getAllRoles?type='+role_type, auth=(login_user,access_token),
            headers=self._jheader, proxies=self._proxy, verify=False)
        if roles_name.status_code == 200:
            roles_name = roles_name.json()
            for role in roles_name:
                if role == role_name:
                    return True
        return False
    
    # assign a role to a user
    def assign_role_to_user(self, server_url, login_user, access_token, role_type, role_name, jenkins_user_id):
        try:
            if self._module.check_mode:
                self._module.exit_json(changed=True)

            data = {
                'type':role_type,
                'roleName':role_name,
                'sid':jenkins_user_id
            }
            requests.post(server_url+'/role-strategy/strategy/assignRole',
                auth=(login_user, access_token), headers=self._jheader, proxies=self._proxy, verify=False, data=data)

        except Exception as e:
            self._module.fail_json(msg="Failed to assign a role to the user %s: %s" % (jenkins_user_id, e))

    # check if the role is assigned to the user
    def check_user_role_assignment(self, server_url, login_user, access_token, role_name, role_type, jenkins_user_id):
        get_user_list = requests.get(server_url+'/role-strategy/strategy/getRole?type='+role_type+'&roleName='+role_name,
            auth=(login_user,access_token), headers=self._jheader, proxies=self._proxy, verify=False)
        
        user_list = get_user_list.json()
        if user_list:
            for user in user_list['sids']:
                if user == jenkins_user_id:
                    return True
        return False

    # remove a role from a user
    def unassign_role_from_user(self, server_url, login_user, access_token, role_name, role_type, jenkins_user_id):
        try:
            if self._module.check_mode:
                self._module.exit_json(changed=True)

            data = {
                'type':role_type,
                'roleName':role_name,
                'sid':jenkins_user_id
            }
            requests.post(server_url+'/role-strategy/strategy/unassignRole', auth=(login_user,access_token),
                headers=self._jheader, proxies=self._proxy, verify=False, data=data)

        except Exception as e:
            self._module.fail_json(msg="Failed to remove the assignment of the role from the user: %s: %s" % (jenkins_user_id, e))

def main():
    module = AnsibleModule(
        argument_spec=dict(
            api_token=dict(type='str', required=True, no_log=True),
            login_user=dict(type='str', required=True),
            server_url=dict(type='str', required=True),
            proxy_server=dict(type='str', required=False),
            jenkins_user=dict(type='str', required=True),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            role_type=dict(typr='str', required=True, choices=['global role', 'item role']),
            role_name=dict(type='str', required=True)
            ),
        supports_check_mode=True )

    api_token = module.params['api_token']
    login_user = module.params['login_user']
    server_url = module.params['server_url']
    proxy_server = module.params['proxy_server']
    jenkins_user = module.params['jenkins_user']
    state = module.params['state']
    role_type = module.params['role_type']
    role_name = module.params['role_name']

    # convert the gui value to its corresponding value in api
    jenkins_role_type = {
        'global role': 'globalRoles',
        'item role': 'projectRoles'
    }
    role_type = jenkins_role_type[role_type]
    
    proxy = {}

    if proxy_server:
        proxy = {
            'https': proxy_server
        }

    header = {}
    # generate a crumb token
    try:
        crumb_info = requests.get(server_url+'/crumbIssuer/api/xml?xpath=concat(//crumbRequestField,":",//crumb)',
            auth=(login_user,api_token), proxies=proxy, verify=False)
        
        # store the issued crumb and session for the user in header dict to be used in API calls
        # session key & value
        cookie = str(crumb_info.cookies)
        cookie_key = re.findall('(Cookie) .*/',cookie )
        cookie_key = ''.join(cookie_key)
        cookie_value = re.findall('Cookie (.*)/',cookie)
        cookie_value = ''.join(cookie_value)
        
        # crumb token key & value
        crumb_token_key = crumb_info.text.split(':')[0]
        crumb_token_value = crumb_info.text.split(':')[1]

        header = {
            cookie_key: cookie_value,
            crumb_token_key: crumb_token_value
        }
    except Exception as e:
        module.fail_json(msg="Failed to generate a CRUMB token to be used besides API token to authenticate and make the requested changes on Jenkins server  %s" % e)

    roles = JenkinsUserRole(module, header, proxy)

    does_role_exist = roles.check_role_exists(server_url, login_user, api_token, role_type, role_name)
    is_role_assigned_to_user = roles.check_user_role_assignment(server_url, login_user, api_token, role_name, role_type, jenkins_user)

    if does_role_exist:
        # check if the role is already assigned to the user
        if not is_role_assigned_to_user:
            
            # if state is specified as present
            if state == "present":
                # assign role to user
                roles.assign_role_to_user(server_url, login_user, api_token, role_type, role_name, jenkins_user)
                module.exit_json(changed=True, result="Successfully assigned the role to the user %s: %s" % (jenkins_user, role_name))
            # in case state is set to be absent
            else:
                module.exit_json(changed=False, result="Role is not assigned to the user. No change to report %s: %s" % (jenkins_user, role_name))
        # in case that the role is assigned
        else:
            if state == "present":
                module.exit_json(changed=False, result="Role is already assigned to the user. No change to report %s: %s" % (jenkins_user, role_name))
                
            # in case state is set to be absent
            else:
                # unassign role from user
                roles.unassign_role_from_user(server_url, login_user, api_token, role_name, role_type, jenkins_user)
                module.exit_json(changed=True, result="Successfully removed the assignment of the role from the user %s: %s" % (jenkins_user, role_name))

    # if role name is not found on Jenkins
    else:
        module.fail_json(msg="Role name not found: %s" % role_name)

if __name__=="__main__":
    main()