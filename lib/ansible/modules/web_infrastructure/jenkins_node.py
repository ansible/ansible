#!/usr/bin/python
#
# Copyright: (c) Ansible Project
#
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: jenkins_node
short_description: Jenkins Node/Executor Operation.
description:
 - Uses Jenkins REST API to manage jenkins node/Executor operations.
 - Change node label via append/replace.
 - Bring node online or offline with message.
 - Wait for node to become idle and then proceed with the ansible tasks.

version_added: "2.8.0"
requirements:
    - "python-jenkins >= 1.4.0"
options:
    host:
        description:
            - Jenkins node/Executor name.
        type: str
        required: true
    jenkins_server:
        description:
            - Jenkins server url(incl http/https, port).
        type: str
        required: true
    jenkins_username:
        description:
            - Authenticated username with Jenkins server.
        type: str
        required: true
    jenkins_token:
        description:
            - Authenticated token with Jenkins server.
        type: str
        required: true
    wait_until_free:
        description:
            - Check and halt play execution if node/Executor is running jenkins job.
            - halt makes present task sleep for 60 seconds.
        type: bool
        required: false
    online:
        description:
            - state tells whether to bring node offline or online
            - msg message on Jenkins UI when node is bought offline.
        type: dict
        required: false
    label:
        description:
            - Modify jenkins node label name.
            - Provides ability to add new label, add suffix or prefix label, remove label,
              remove suffix or prefix label.
        type: dict
        required: false
    delete:
        description:
            - Delete  node from jenkins master.
seealso:
    - module: jenkins_job
    - module: jenkins_plugin
requirements:
    - "python-jenkins >= 1.4.0"
author: "Nalin Garg (@nalingarg2)"
'''

EXAMPLES = '''

-   name: Add new label.
    jenkins_node:
        host: myhost
        jenkins_server: https://jenkins.example.com
        jenkins_username: test_username
        jenkins_token: test_token
        label:
            new: "Maintenance"

-   name: Delete suffix and prefix from existing labels. Delete standalone label
    jenkins_node:
        host: myhost
        jenkins_server: https://jenkins.example.com
        jenkins_username: test_username
        jenkins_token: test_token
        label:
            delete_suffix: "-Maintenance"
            delete_prefix: "Maintenance-"
            delete: "Maintenance"

-   name: Bring Node offline.
    jenkins_node:
        host: myhost
        jenkins_server: https://jenkins.example.com
        jenkins_username: test_username
        jenkins_token: test_token
        online:
            state: no
            msg: "Bringing node offline."

-   name: Bring Node online.
    jenkins_node: 
        host: myhost
        jenkins_server: https://jenkins.example.com
        jenkins_username: test_username
        jenkins_token: test_token
        online:
            state: yes

-   name: Halt play execution is Jenkins node is busy.
    jenkins_node:
        host: myhost
        jenkins_server: https://jenkins.example.com
        jenkins_username: test_username
        jenkins_token: test_token
        wait_until_free: yes

-   name: Change node label. Halt is node is running jenkins job. Bring node offline.
    jenkins_node:
        host: myhost
        jenkins_server: https://jenkins.example.com
        jenkins_username: test_username
        jenkins_token: test_token
        wait_until_free: yes
        label:
            new: "Maintenance"
        online:
            state: no
            msg: "Bringing node offline."

'''
RETURN = '''
---
host:
    description: Name of jenkins node/Executor where task ran.
    returned: always
    sample: myhost
    type: str
jenkins_username:
    description: Whether node is online/offline.
    returned: always
    sample: test_ansible
    type: str
jenkins_server:
    description: name of jenkins master.
    sample: https://jenkins.example.com
    type: str
    returned: always
online:
    description: Indicate the status of node.
    sample: true
    returned: success
    type: bool
maintenance:
    description: Indicate status of maintenance flag.
    sample: true`
    returned: success
    type: bool
label:
    description: Name of maintenance label.
    type: str
    returned: success
    sample: maintenance
changed:
    description: indicates if task ran to change the state.
    returned: success
    sample: true
    type: bool
'''

import time
import re
import traceback
try:
    import jenkins
    python_jenkins_installed = True
except ImportError:
    JENKINS_IMP_ERR = traceback.format_exc()
    python_jenkins_installed = False

import xml.etree.ElementTree as ET
from ansible.module_utils.basic import AnsibleModule, missing_required_lib


def test_dependencies(module):
    # Test if python-jenkins python package is present.
    if not python_jenkins_installed:
        module.fail_json(
            msg=missing_required_lib("python-jenkins",
                                     url="https://python-jenkins.readthedocs.io/en/latest/install.html"),
            exception=JENKINS_IMP_ERR)


def host_config(module, jenkins_server, jenkins_username, jenkins_token):
    # Create jenkins server object.
    try:
        server = jenkins.Jenkins(jenkins_server,
                                 username=jenkins_username,
                                 password=jenkins_token)
    except Exception as e:
        module.fail_json(msg="Unable to contact jenkins server: {}".format(e))
    return server


def jenkins_node_info(host, server_node, module):
    # Get jenkins nodes information.
    try:
        node_info = server_node.get_node_info(host)
    except Exception as e:
        module.fail_json(msg="Unable to contact jenkins node {}: {},".format(host, e))
    return node_info


def delete_node(server_node, host, module):
    # Delete jenkins node from jenkins server.
    try:
        server_node.delete_node(host)
    except jenkins.JenkinsException:
        module.fail_json(msg="Could not delete {}'.format(host)".format(host))


def set_node_status(server_node, host, dict_online):
    # Disconnect jenkins node with message from jenkins server.
    if dict_online['state'] in ['no', False, 'false']:
        server_node.disable_node(host, dict_online['msg'])
    else:
        server_node.enable_node(host)


def node_config_change(host, server_node, dict_label,
                       result, module):
    try:
        tree = ET.fromstring(server_node.get_node_config(host))
        root = ET.ElementTree(element=tree).getroot()
    except Exception as e:
        module.fail_json(msg="Unable to contact jenkins node {}: (get_node_config): {}".format(host, e))
    try:
        for child in root:
            if child.tag == 'label':
                current_label = child.text
                # list with unique elements and not extra spaces.
                current_label_list = list(set(list(filter(None, current_label.split(" ")))))
                # replace all existing label with new label.
                if 'replace' in dict_label.keys():
                    current_label_list = dict_label['replace']
                # add new label to existing list.
                if 'new' in dict_label.keys():
                    if not dict_label['new'] in current_label_list:
                        current_label_list.append(dict_label['new'])
                # add prefix to existing label.
                # First remove prefix and then add to avoid duplicate.
                if 'new_prefix' in dict_label.keys():
                    current_label_list = list(map(lambda x: re.sub('^%s' % dict_label['new_prefix'], "", x),
                                                  current_label_list))
                    current_label_list = list(map(lambda x: dict_label['new_prefix'] + x, current_label_list))
                # add suffix to existing label.
                # First remove prefix and then add to avoid duplicate.
                if 'new_suffix' in dict_label.keys():
                    current_label_list = list(map(lambda x: re.sub('%s$' % dict_label['new_suffix'], "", x),
                                                  current_label_list))
                    current_label_list = list(map(lambda x: x + dict_label['new_suffix'], current_label_list))
                # delete existing label.
                if 'delete' in dict_label.keys():
                    current_label_list = list(map(lambda x:  re.sub('^%s$' % dict_label['delete'], "", x),
                                             current_label_list))
                # delete existing prefix label.
                if 'delete_prefix' in dict_label.keys():
                    current_label_list = list(map(lambda x: re.sub('^%s' % dict_label['delete_prefix'], "", x),
                                             current_label_list))
                # delete existing suffix label.
                if 'delete_suffix' in dict_label.keys():
                    current_label_list = list(map(lambda x: re.sub('%s$' % dict_label['delete_suffix'], "", x),
                                             current_label_list))
                child.text = " ".join(list(set(list(filter(None, current_label_list)))))
        if not set(list(filter(None, current_label_list))) == set(list(filter(None, current_label.split(" ")))):
            server_node.reconfig_node(host, ET.tostring(tree, encoding='utf8', method='xml').decode("utf-8"))
            result['changed'] = True
        else:
            result['changed'] = False
        result['label'] = current_label_list
    except Exception as e:
        module.fail_json(msg="Unable to reconfigure jenkins node with desired label: {}".format(e))
    return result


def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(required=True, type='str'),
            jenkins_server=dict(required=True, type='str'),
            jenkins_username=dict(required=True, type="str"),
            jenkins_token=dict(required=True, type="str", no_log=True),
            wait_until_free=dict(required=False, type='bool', default=False),
            label=dict(required=False, type='dict', default={}),
            online=dict(required=False, type='dict', default={}),
            delete=dict(required=False, type='bool', default=False)
        )
    )
    host = module.params['host']
    jenkins_server = module.params['jenkins_server']
    jenkins_username = module.params['jenkins_username']
    jenkins_token = module.params['jenkins_token']
    wait_until_free = module.params['wait_until_free']
    delete = module.params['delete']

    # child params: append, name, state
    dict_label = module.params['label']
    # child params: state, msg
    online = module.params['online']

    result = dict(
        changed=False,
        host=None,
        jenkins_server=None,
        jenkins_username=None,
        label=None,
        online=None,
        delete=False,
        maintenance=False
    )

    # initializing return values
    result['host'] = host.strip()
    result['jenkins_server'] = jenkins_server.strip()
    result['jenkins_username'] = jenkins_username.strip()

    test_dependencies(module)

    # jenkins server object.
    server_node = host_config(module, jenkins_server,
                              jenkins_username, jenkins_token)
    # change label.
    if dict_label:
        node_config_result = node_config_change(host, server_node, dict_label,
                                                result, module)

    # sleep if node is busy
    if wait_until_free:
        while not (jenkins_node_info(host, server_node, module)['idle']):
            time.sleep(60)

    # mark node as offline
    if online:
       set_node_status(server_node, host, online)

    # delete node
    if delete:
        delete_node(server_node, host, module)

    # Success exit procedure.
    if (dict_label and not node_config_result['changed']) and not wait_until_free and not online and not delete:
        module.exit_json(changed=True, msg="Changed node label")
    elif dict_label and wait_until_free and not online and not delete:
        module.exit_json(changed=True, msg="Changed node label and Node is Idle now.")
    elif dict_label and wait_until_free and not online and  delete:
        module.exit_json(changed=True, msg="Node is deleted from jenkins server.")
    else:
        module.exit_json(changed=True, msg="Node Status: {}".format(online))


if __name__ == '__main__':
    main()
