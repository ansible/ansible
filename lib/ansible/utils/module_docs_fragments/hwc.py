# Copyright: (c) 2018, Huawei Inc.
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):
        # HWC doc fragment.
        DOCUMENTATION = '''
options:
    identity_endpoint:
        description:
            - The Identity authentication URL..
        required: true
    user_name:
        description:
            - The user name to login with.
        required: true
    password:
        description:
            - The password to login with.
        required: true
    domain_name:
        description:
            - The name of the Domain to scope to (Identity v3).
        required: true
    project_name:
        description:
            - The name of the Tenant (Identity v2) or Project (Identity v3).
        required: true
    region:
        description:
            - The region to which the project belongs.
        required: true
    timeouts:
        description:
            - The timeouts for create/update/delete operation.
        suboptions:
            create:
                description:
                    - The timeouts for create operation.
                default: '10m'
            update:
                description:
                    - The timeouts for update operation.
                default: '10m'
            delete:
                description:
                    - The timeouts for delete operation.
                default: '10m'
    id:
        description:
            - The id of resource to be managed.
notes:
  - For authentication, you can set identity_endpoint using the
    C(IDENTITY_ENDPOINT) env variable.
  - For authentication, you can set user_name using the
    C(USER_NAME) env variable.
  - For authentication, you can set password using the C(PASSWORD) env
    variable.
  - For authentication, you can set domain_name using the C(DOMAIN_NAME) env
    variable.
  - For authentication, you can set project_name using the C(PROJECT_NAME) env
    variable.
  - For authentication, you can set region using the C(REGION) env variable.
  - Environment variables values will only be used if the playbook values are
    not set.
'''
