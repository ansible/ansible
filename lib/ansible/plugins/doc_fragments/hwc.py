# Copyright: (c) 2018, Huawei Inc.
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # HWC doc fragment.
    DOCUMENTATION = '''
options:
    identity_endpoint:
        description:
            - The Identity authentication URL.
        type: str
        required: true
    user:
        description:
            - The user name to login with (currently only user names are
              supported, and not user IDs).
        type: str
        required: true
    password:
        description:
            - The password to login with.
        type: str
        required: true
    domain:
        description:
            - The name of the Domain to scope to (Identity v3, currently only
              domain names are supported, and not domain IDs).
        type: str
        required: true
    project:
        description:
            - The name of the Tenant (Identity v2) or Project (Identity v3).
              (currently only project names are supported, and not
               project IDs).
        type: str
        required: true
    region:
        description:
            - The region to which the project belongs.
        type: str
        required: true
    timeouts:
        description:
            - The timeouts for create/update/delete operation.
        type: dict
        suboptions:
            create:
                description:
                    - The timeouts for create operation.
                type: str
                default: '10m'
            update:
                description:
                    - The timeouts for update operation.
                type: str
                default: '10m'
            delete:
                description:
                    - The timeouts for delete operation.
                type: str
    id:
        description:
            - The id of resource to be managed.
        type: str
notes:
  - For authentication, you can set identity_endpoint using the
    C(ANSIBLE_HWC_IDENTITY_ENDPOINT) env variable.
  - For authentication, you can set user using the
    C(ANSIBLE_HWC_USER) env variable.
  - For authentication, you can set password using the C(ANSIBLE_HWC_PASSWORD) env
    variable.
  - For authentication, you can set domain using the C(ANSIBLE_HWC_DOMAIN) env
    variable.
  - For authentication, you can set project using the C(ANSIBLE_HWC_PROJECT) env
    variable.
  - For authentication, you can set region using the C(ANSIBLE_HWC_REGION) env variable.
  - Environment variables values will only be used if the playbook values are
    not set.
'''
