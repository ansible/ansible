#!/usr/bin/python
# Copyright (c) 2018 CloudGenix Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: cloudgenix_sites

short_description: "Create, Modify, Describe, or Delete CloudGenix Sites"

version_added: "2.6"

description:
    - "Create, Modify, Describe, or Delete a CloudGenix site object."

options:
    operation:
        description:
            - The operation you would like to perform on the site object
        choices: ['create', 'modify', 'describe', 'delete']
        required: True

    role:
        description:
            - The function and/or type of site this is. Default 'BRANCH' if creating new site.
        choices: ['HUB', 'BRANCH']

    admin_state:
        description:
            - Administrative state of the site. Default 'disabled' if creating new site.
        choices: ['active', 'monitor', 'disabled']

    name:
        description:
            - Name of the site. Required if operation set to "create".

    id:
        description:
            - Globally unique ID of the object. Required if operation set to "modify", "describe" or "delete".

    description:
        description:
            - Description of the site. Maximum 256 chars.

    network_policyset:
        description:
            - ID of the Network Policyset used at the site. If not specified, will use the "Default" policy.

    security_policyset:
        description:
            - ID of the Security Policyset to be applied the site. If not specified, site will operate in "default" mode.

    service_binding:
        description:
            - ID of the Service Binding policy to be applied at the site.

    address_street:
        description:
            - First street line of the site address.

    address_street2:
        description:
            - Second street line of the site address.

    address_city:
        description:
            - City that the site is in.

    address_state:
        description:
            - State/provence that the site is in.

    address_country:
        description:
            - Country that the site is in.

    address_post_code:
        description:
            - Postal code of the site.

    location_description:
        description:
            - Location specific description for the site.

    location_latitude:
        description:
            - Decimal latitude of the site

    location_longitude:
        description:
            - Decimal logitude of the site

extends_documentation_fragment:
    - cloudgenix

author:
    - Aaron Edwards (@ebob9)
'''

EXAMPLES = '''
# Create a site
- name: create site
  cloudgenix_sites:
    auth_token: "<AUTH_TOKEN>"
    operation: "create"
    name: "My Site Name"
  register: create_site_results

# Retrieve a site
- name: describe site
  cloudgenix_sites:
    auth_token: "<AUTH_TOKEN>"
    operation: "describe"
    id: "<SITE_ID>"
  register: describe_results

# Modify a site
- name: modify site
  cloudgenix_sites:
    auth_token: "<AUTH_TOKEN>"
    operation: "modify"
    id: "<SITE_ID>"
    description: "Shiny happy description holding hands"
  register: modify_results

# Delete a site
- name: delete site
  cloudgenix_sites:
    auth_token: "<AUTH_TOKEN>"
    operation: "delete"
    id: "<SITE_ID>"
  register: delete_results
'''

RETURN = '''
operation:
    description: Operation that was executed
    type: string
    returned: always

role:
    description: Role of the site.
    type: string
    returned: always

admin_state:
    description: Administrative State of the site.
    type: string
    returned: always

name:
    description: Name of the site
    type: string
    returned: always

id:
    description: Globally unique ID of the object
    type: string
    returned: always

description:
    description: Description of the site.
    type: string
    returned: always

network_policyset:
    description: Network Policy Set ID used by the site.
    type: string
    returned: always

security_policyset:
    description: Security Policy Set ID used by the site.
    type: string
    returned: always

service_binding:
    description: Service Binding Set ID used by the site.
    type: string
    returned: always

address_street:
    description: First street line of the site address.
    type: string
    returned: always

address_street2:
    description: Second street line of the site address.
    type: string
    returned: always

address_city:
    description: City that the site is in.
    type: string
    returned: always

address_state:
    description: State/provence that the site is in.
    type: string
    returned: always

address_country:
    description: Country that the site is in.
    type: string
    returned: always

address_post_code:
    description: Postal code of the site.
    type: string
    returned: always

location_description:
    description: Location specific description for the site.
    type: string
    returned: always

location_latitude:
    description: Decimal latitude of the site.
    type: string
    returned: always

location_longitude:
    description: Decimal longitude of the site.
    type: string
    returned: always

meta:
    description: Raw CloudGenix API response.
    type: dictionary
    returned: always

'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudgenix_util import (HAS_CLOUDGENIX, cloudgenix_common_arguments,
                                                  setup_cloudgenix_connection)

try:
    import cloudgenix
except ImportError:
    pass  # caught by imported HAS_CLOUDGENIX


def run_module():
    # define the available arguments/parameters that a user can pass to
    # the module
    module_args = cloudgenix_common_arguments()
    module_args.update(dict(
        operation=dict(choices=['create', 'modify', 'describe', 'delete'], required=True),
        role=dict(choices=['BRANCH', 'HUB'], default=None),
        admin_state=dict(choices=['active', 'monitor', 'disabled'], required=False, default=None),
        name=dict(type='str', required=False, default=None),
        id=dict(type='str', required=False, default=None),
        description=dict(type='str', required=False, default=None),
        network_policyset=dict(type='str', required=False, default=None),
        security_policyset=dict(type='str', required=False, default=None),
        service_binding=dict(type='str', required=False, default=None),
        address_street=dict(type='str', required=False, default=None),
        address_street2=dict(type='str', required=False, default=None),
        address_city=dict(type='str', required=False, default=None),
        address_state=dict(type='str', required=False, default=None),
        address_country=dict(type='str', required=False, default=None),
        address_post_code=dict(type='str', required=False, default=None),
        location_description=dict(type='str', required=False, default=None),
        location_latitude=dict(type='float', required=False, default=None),
        location_longitude=dict(type='float', required=False, default=None),
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # check for Cloudgenix SDK (Required)
    if not HAS_CLOUDGENIX:
        module.fail_json(msg='The "cloudgenix" python module is required by this Ansible module.')

    # seed the result dict in the object
    # we primarily care about changed and state
    # change is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        operation='',
        role='',
        admin_state='',
        name='',
        id='',
        description='',
        network_policyset='',
        security_policyset='',
        service_binding='',
        address_street='',
        address_street2='',
        address_city='',
        address_state='',
        address_country='',
        address_post_code='',
        location_description='',
        location_latitude='',
        location_longitude='',
        meta={},
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        return result

    # extract the params to shorter named vars.
    operation = module.params.get('operation')
    role = module.params.get('role')
    admin_state = module.params.get('admin_state')
    name = module.params.get('name')
    id = module.params.get('id')
    description = module.params.get('description')
    network_policyset = module.params.get('network_policyset')
    security_policyset = module.params.get('security_policyset')
    service_binding = module.params.get('service_binding')
    address_street = module.params.get('address_street')
    address_street2 = module.params.get('address_street2')
    address_city = module.params.get('address_city')
    address_state = module.params.get('address_state')
    address_country = module.params.get('address_country')
    address_post_code = module.params.get('address_post_code')
    location_description = module.params.get('location_description')
    location_latitude = module.params.get('location_latitude')
    location_longitude = module.params.get('location_longitude')

    # get CloudGenix API connection details
    auth_token, controller, tenant_id, cgx_session = setup_cloudgenix_connection(module)

    # start logic.

    # check if site is new, changing, or being deleted.
    if operation == 'describe':

        # Check for id as required for new site.
        if id is None:
            module.fail_json(msg='"id" is a required to describe site.', **result)

        # Get the object.
        sites_describe_response = cgx_session.get.sites(id)

        # Check for API failure
        if not sites_describe_response.cgx_status:
            result['meta'] = sites_describe_response.cgx_content
            module.fail_json(msg='Site ID {0} DESCRIBE failed.'.format(id), **result)

        updated_site_result = sites_describe_response.cgx_content

        # sanity check nested dicts.
        if not updated_site_result.get('address'):
            updated_site_result['address'] = {
                "city": None,
                "country": None,
                "post_code": None,
                "state": None,
                "street": None,
                "street2": None
            }
        if not updated_site_result.get('location'):
            updated_site_result['location'] = {
                "description": None,
                "latitude": None,
                "longitude": None
            }

        # update result
        result = dict(
            changed=False,
            operation=operation,
            role=updated_site_result['element_cluster_role'],
            admin_state=updated_site_result['admin_state'],
            name=updated_site_result['name'],
            id=updated_site_result['id'],
            description=updated_site_result['description'],
            network_policyset=updated_site_result['policy_set_id'],
            security_policyset=updated_site_result['security_policyset_id'],
            service_binding=updated_site_result['service_binding'],
            address_street=updated_site_result['address']['street'],
            address_street2=updated_site_result['address']['street2'],
            address_city=updated_site_result['address']['city'],
            address_state=updated_site_result['address']['state'],
            address_country=updated_site_result['address']['country'],
            address_post_code=updated_site_result['address']['post_code'],
            location_description=updated_site_result['location']['description'],
            location_latitude=updated_site_result['location']['latitude'],
            location_longitude=updated_site_result['location']['longitude'],
            meta=sites_describe_response.cgx_content
        )

        # success
        module.exit_json(**result)

    elif operation == 'create':
        # new site request!

        # Check for name as required for new site.
        if name is None:
            module.fail_json(msg='name is a required value for site creation.', **result)

        # cgx site template
        new_site = {
            "address": {
                "city": None,
                "country": None,
                "post_code": None,
                "state": None,
                "street": None,
                "street2": None
            },
            "admin_state": 'disabled',
            "description": None,
            "element_cluster_role": "SPOKE",
            "location": {
                "description": None,
                "latitude": None,
                "longitude": None
            },
            "name": None,
            "policy_set_id": None,
            "security_policyset_id": None,
            "service_binding": None
        }

        if role is not None:
            new_site['element_cluster_role'] = role
        if admin_state is not None:
            new_site['admin_state'] = admin_state
        if name is not None:
            new_site['name'] = name
        if description is not None:
            new_site['description'] = description
        if network_policyset is not None:
            new_site['policy_set_id'] = network_policyset
        if security_policyset is not None:
            new_site['security_policyset_id'] = security_policyset
        if service_binding is not None:
            new_site['service_binding'] = service_binding
        if address_street is not None:
            new_site['address']['street'] = address_street
        if address_street2 is not None:
            new_site['address']['street2'] = address_street2
        if address_city is not None:
            new_site['address']['city'] = address_city
        if address_state is not None:
            new_site['address']['state'] = address_state
        if address_country is not None:
            new_site['address']['country'] = address_country
        if address_post_code is not None:
            new_site['address']['post_code'] = address_post_code
        if location_description is not None:
            new_site['location']['description'] = location_description
        if location_latitude is not None:
            new_site['location']['latitude'] = location_latitude
        if location_longitude is not None:
            new_site['location']['longitude'] = location_longitude

        # Attempt to create site
        sites_create_response = cgx_session.post.sites(new_site)

        if not sites_create_response.cgx_status:
            result['meta'] = sites_create_response.cgx_content
            module.fail_json(msg='Site CREATE failed.', **result)

        updated_site_result = sites_create_response.cgx_content

        # update result
        result = dict(
            changed=True,
            operation=operation,
            role=updated_site_result['element_cluster_role'],
            admin_state=updated_site_result['admin_state'],
            name=updated_site_result['name'],
            id=updated_site_result['id'],
            description=updated_site_result['description'],
            network_policyset=updated_site_result['policy_set_id'],
            security_policyset=updated_site_result['security_policyset_id'],
            service_binding=updated_site_result['service_binding'],
            address_street=updated_site_result['address']['street'],
            address_street2=updated_site_result['address']['street2'],
            address_city=updated_site_result['address']['city'],
            address_state=updated_site_result['address']['state'],
            address_country=updated_site_result['address']['country'],
            address_post_code=updated_site_result['address']['post_code'],
            location_description=updated_site_result['location']['description'],
            location_latitude=updated_site_result['location']['latitude'],
            location_longitude=updated_site_result['location']['longitude'],
            meta=sites_create_response.cgx_content
        )

        # success
        module.exit_json(**result)

    elif operation == 'modify':

        # Check for id as required for new site.
        if id is None:
            module.fail_json(msg='"id" is a required value for site modification.', **result)

        # Get the object.
        sites_response = cgx_session.get.sites(id)

        # if site get fails, fail module.
        if not sites_response.cgx_status:
            result['meta'] = sites_response.cgx_content
            module.fail_json(msg='Site ID {0} retrieval failed.'.format(id), **result)
        # pull the site out of the Response
        updated_site = sites_response.cgx_content

        # sanity check nested dicts.
        if not updated_site.get('address'):
            updated_site['address'] = {
                "city": None,
                "country": None,
                "post_code": None,
                "state": None,
                "street": None,
                "street2": None
            }
        if not updated_site.get('location'):
            updated_site['location'] = {
                "description": None,
                "latitude": None,
                "longitude": None
            }

        # modify the site
        if role is not None:
            updated_site['element_cluster_role'] = role
        if admin_state is not None:
            updated_site['admin_state'] = admin_state
        if name is not None:
            updated_site['name'] = name
        if description is not None:
            updated_site['description'] = description
        if network_policyset is not None:
            updated_site['policy_set_id'] = network_policyset
        if security_policyset is not None:
            updated_site['security_policyset_id'] = security_policyset
        if service_binding is not None:
            updated_site['service_binding'] = service_binding
        if address_street is not None:
            updated_site['address']['street'] = address_street
        if address_street2 is not None:
            updated_site['address']['street2'] = address_street2
        if address_city is not None:
            updated_site['address']['city'] = address_city
        if address_state is not None:
            updated_site['address']['state'] = address_state
        if address_country is not None:
            updated_site['address']['country'] = address_country
        if address_post_code is not None:
            updated_site['address']['post_code'] = address_post_code
        if location_description is not None:
            updated_site['location']['description'] = location_description
        if location_latitude is not None:
            updated_site['location']['latitude'] = location_latitude
        if location_longitude is not None:
            updated_site['location']['longitude'] = location_longitude

        # Attempt to modify site
        sites_update_response = cgx_session.put.sites(id, updated_site)

        if not sites_update_response.cgx_status:
            result['meta'] = sites_update_response.cgx_content
            module.fail_json(msg='Site ID {0} UPDATE failed.'.format(id), **result)

        updated_site_result = sites_update_response.cgx_content

        # update result
        result = dict(
            changed=True,
            operation=operation,
            role=updated_site_result['element_cluster_role'],
            admin_state=updated_site_result['admin_state'],
            name=updated_site_result['name'],
            id=updated_site_result['id'],
            description=updated_site_result['description'],
            network_policyset=updated_site_result['policy_set_id'],
            security_policyset=updated_site_result['security_policyset_id'],
            service_binding=updated_site_result['service_binding'],
            address_street=updated_site_result['address']['street'],
            address_street2=updated_site_result['address']['street2'],
            address_city=updated_site_result['address']['city'],
            address_state=updated_site_result['address']['state'],
            address_country=updated_site_result['address']['country'],
            address_post_code=updated_site_result['address']['post_code'],
            location_description=updated_site_result['location']['description'],
            location_latitude=updated_site_result['location']['latitude'],
            location_longitude=updated_site_result['location']['longitude'],
            meta=sites_update_response.cgx_content
        )

        # success
        module.exit_json(**result)

    elif operation == 'delete':
        # Delete site request. Verify ID was passed.
        if id is None:
            module.fail_json(msg='Site ID not set and required for delete site operation.')

        else:
            # Attempt to delete site
            sites_delete_response = cgx_session.delete.sites(id)

            if not sites_delete_response.cgx_status:
                result['meta'] = sites_delete_response.cgx_content
                module.fail_json(msg='Site DELETE failed.', **result)

            # update result
            result['changed'] = True
            result['meta'] = sites_delete_response.cgx_content

            # success
            module.exit_json(**result)

    else:
        module.fail_json(msg='Invalid operation for module: {0}'.format(operation), **result)

    # avoid Pylint R1710
    return result


def main():
    run_module()


if __name__ == '__main__':
    main()
