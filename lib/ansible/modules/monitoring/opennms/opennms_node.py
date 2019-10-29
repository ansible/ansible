#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: opennms_node
short_description: Manage nodes in OpenNMS
version_added: "2.8"
description:
  - "An ansible module to manage nodes in OpenNMS"
author:
    - "Vincent Van Ouytsel (@vvanouytsel)"

options:
  server:
    description:
      - The path to the OpenNMS API endpoint
    required: true
    type: str
  username:
    description:
      - The username to authenticate the API calls
    required: true
    type: str
  password:
    description:
      - The password to authenticate the API calls
    required: true
    type: str
  name:
    description:
        - The name of the node
    required: true
    type: str
  requisition:
    description:
      - The requisition to add the node to
    required: true
    type: str
  building:
    description:
      - The building where the node is located
    required: false
    type: str
  city:
    description:
      - The city where the node is located
    required: false
    type: str
  state:
    description:
      - The state of the node
    required: false
    type: str
    default: present
    choices: [ "present", "absent"]
  rescan:
    description:
      - Rescan the requisition when a node is added
    required: no
    type: bool
    default: no
  ipaddr:
    description:
        - "The ip address of the node, required when using 'state: present'"
    required: false
    type: str
  categories:
    description:
        - Comma seperated list of categories to add
    required: false
    type: str
  assets:
    description:
        - Assets to add to the node
    required: false
    type: list
'''

EXAMPLES = '''
# Add a node

- name: Add a node to the 'Generic' requisition and perform a rescan on the requisition
  opennms_node:
    server: http://my_opennms_server:8980/opennms/rest
    username: admin
    password: secret_password
    name: my_node
    building: datacenter_1
    ipaddr: 192.168.0.1
    requisition: Generic
    rescan: yes

- name: Add a node to the 'Generic' requisition, providing some metadate and not rescanning the requisition
  opennms_node:
    server: http://my_opennms_server:8980/opennms/rest
    username: admin
    password: secret_password
    name: my_node
    building: datacenter_1
    ipaddr: 192.168.0.1
    city: Brussels
    state: present
    requisition: Generic
    rescan: no
    categories: linux,production,minimal
    assets:
       - name: operatingSystem
         value: Ubuntu 16.04 LTS
       - name: responsible
         value: vvanouytsel

- name: Delete a node
  opennms_node:
    server: http://my_opennms_server:8980/opennms/rest
    username: admin
    password: secret_password
    name: my_node
    state: absent
    requisition: Generic
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import open_url
import json
import xml.etree.ElementTree as ET


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        server=dict(type='str', required=True),
        username=dict(type='str', required=True),
        password=dict(type='str', required=True, no_log=True),
        name=dict(type='str', required=True),
        requisition=dict(type='str', required=True),
        building=dict(type='str', required=False),
        ipaddr=dict(type='str', required=False),
        state=dict(type='str', required=False, default='present', choices=["present", "absent"]),
        categories=dict(type='str', required=False),
        assets=dict(type='list', required=False),
        city=dict(type='str', required=False),
        rescan=dict(type='bool', required=False, default=False)
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # change is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        server='',
        username='',
        password='',
        name='',
        response='',
        requisition='',
        ipaddr='',
        categories='',
        assets='',
        city='',
        building='',
        rescan=''
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
        module.exit_json(**result)

    # Pass the arguments into variables
    server = module.params['server']
    username = module.params['username']
    password = module.params['password']
    name = module.params['name']
    state = module.params['state']
    requisition = module.params['requisition']
    ipaddr = module.params['ipaddr']
    categories = module.params['categories']
    assets = module.params['assets']
    city = module.params['city']
    building = module.params['building']
    rescan = module.params['rescan']

    # Set the result dictionary
    result['server'] = server
    result['username'] = username
    result['password'] = password
    result['name'] = name
    result['state'] = state
    result['requisition'] = requisition
    result['ipaddr'] = ipaddr
    result['categories'] = categories
    result['assets'] = assets
    result['city'] = city
    result['building'] = building
    result['rescan'] = rescan

    if state == "present":
        # Some variables are required when adding a node, but not required when deleting a node, check if the required variables are set for adding a node
        variables = [ipaddr]
        for var in variables:
            if var is None:
                module.fail_json(msg="The variable " + "'" + var + "' has to be defined when adding a node.", **result)

        # We need to add a node to OpenNMS
        # Generate the XML content to send to OpenNMS
        # Create the '<node>' element
        node_element = ET.Element('node', {'foreign-id': name, 'node-label': name})

        # Add the 'building' attribute when city is specified
        if building is not None:
            node_element.set('building', building)

        # Add the 'city' attribute when city is specified
        if city is not None:
            node_element.set('city', city)

        # Create the 'interface' element
        interface_element = ET.SubElement(node_element, 'interface', {'status': '1', 'ip-addr': ipaddr, 'snmp-primary': 'P'})

        if categories is not None:
            # Loop over all the categories and them add as children of 'node'
            for category in categories.split(','):
                category_element = ET.SubElement(node_element, 'category')
                category_element.set('name', category)

        if assets is not None:
            # Loop over all the assets and add them as children of 'node'
            for asset in assets:
                asset_element = ET.SubElement(node_element, 'asset')
                asset_element.set('name', asset['name'])
                asset_element.set('value', asset['value'])

        # Perform the REST call to add the node to the requisition
        data = ET.tostring(node_element, method="html")
        headers = {'Content-Type': 'application/xml'}
        try:
            response = open_url(server + "/requisitions/" + requisition + "/nodes", method="POST",
                                url_username=username, url_password=password, headers=headers, data=data)
        except Exception as e:
            module.fail_json(msg=e, **result)

        # Pass the payload and response code to the result
        result['data'] = data

        # Check if the user wants to rescan/reload the requisition
        if rescan:
            try:
                response = open_url(server + "/requisitions/" + requisition + "/import?rescanExisting=false",
                                    method="PUT", url_username=username, url_password=password, headers=headers)
                result['changed'] = True
            except Exception as e:
                module.fail_json(msg=e, **result)

        result['response'] = response.status

    elif state == "absent":
        # We need to delete a node from OpenNMS
        # Get all the nodes
        headers = {'Accept': 'application/json'}
        # ?limit=0
        response = open_url(server + "/nodes?limit=0", method="GET", url_username=username, url_password=password, headers=headers)

        response = response.read().decode('utf-8')
        nodes_object = json.loads(response)

        # Loop through nodes
        for node in nodes_object['node']:
            if node['label'] == name:
                # The node we want to delete is found in the node list returned by OpenNMS
                # Delete the node
                result['id'] = node['id']
                try:
                    response = open_url(server + "/nodes/" + node["id"], method="DELETE", url_username=username, url_password=password)
                    result['response'] = response.status
                    result['message'] = response.msg
                    if response.status == 202:
                        # The node was succesfully deleted
                        result['changed'] = True
                    else:
                        module.fail_json(msg="Unable to delete node '" + node['label'] + "' with id '" + node['id'] + "'", **result)
                except Exception as e:
                    module.fail_json(msg=e, **result)
    else:
        module.fail_json(msg="Only 'present' and 'absent' is supported as value for 'state'", **result)

    # in the event of a successful module execution
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
