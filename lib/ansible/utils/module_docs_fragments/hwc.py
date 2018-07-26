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
            update:
                description:
                    - The timeouts for update operation.
            delete:
                description:
                    - The timeouts for delete operation.
    id:
        description:
            - The id of resource to be managed.
'''
