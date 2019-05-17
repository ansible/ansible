#!/usr/bin/python
#
# @author: Gaurav Rastogi (grastogi@avinetworks.com)
#          Eric Anderson (eanderson@avinetworks.com)
# module_check: supported
#
# Copyright: (c) 2017 Gaurav Rastogi, <grastogi@avinetworks.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: avi_backupconfiguration
author: Gaurav Rastogi (@grastogi23) <grastogi@avinetworks.com>

short_description: Module for setup of BackupConfiguration Avi RESTful Object
description:
    - This module is used to configure BackupConfiguration object
    - more examples at U(https://github.com/avinetworks/devops)
requirements: [ avisdk ]
version_added: "2.4"
options:
    state:
        description:
            - The state that should be applied on the entity.
        default: present
        choices: ["absent", "present"]
    avi_api_update_method:
        description:
            - Default method for object update is HTTP PUT.
            - Setting to patch will override that behavior to use HTTP PATCH.
        version_added: "2.5"
        default: put
        choices: ["put", "patch"]
    avi_api_patch_op:
        description:
            - Patch operation to use when using avi_api_update_method as patch.
        version_added: "2.5"
        choices: ["add", "replace", "delete"]
    aws_access_key:
        description:
            - Aws access key id.
            - Field introduced in 18.2.3.
        version_added: "2.9"
    aws_bucket_id:
        description:
            - Aws bucket.
            - Field introduced in 18.2.3.
        version_added: "2.9"
    aws_secret_access:
        description:
            - Aws secret access key.
            - Field introduced in 18.2.3.
        version_added: "2.9"
    backup_file_prefix:
        description:
            - Prefix of the exported configuration file.
            - Field introduced in 17.1.1.
    backup_passphrase:
        description:
            - Passphrase of backup configuration.
    maximum_backups_stored:
        description:
            - Rotate the backup files based on this count.
            - Allowed values are 1-20.
            - Default value when not specified in API or module is interpreted by Avi Controller as 4.
    name:
        description:
            - Name of backup configuration.
        required: true
    remote_directory:
        description:
            - Directory at remote destination with write permission for ssh user.
    remote_hostname:
        description:
            - Remote destination.
    save_local:
        description:
            - Local backup.
        type: bool
    ssh_user_ref:
        description:
            - Access credentials for remote destination.
            - It is a reference to an object of type cloudconnectoruser.
    tenant_ref:
        description:
            - It is a reference to an object of type tenant.
    upload_to_remote_host:
        description:
            - Remote backup.
        type: bool
    upload_to_s3:
        description:
            - Cloud backup.
            - Field introduced in 18.2.3.
        version_added: "2.9"
        type: bool
    url:
        description:
            - Avi controller URL of the object.
    uuid:
        description:
            - Unique object identifier of the object.
extends_documentation_fragment:
    - avi
'''

EXAMPLES = """
- name: Example to create BackupConfiguration object
  avi_backupconfiguration:
    controller: 10.10.25.42
    username: admin
    password: something
    state: present
    name: sample_backupconfiguration
"""

RETURN = '''
obj:
    description: BackupConfiguration (api/backupconfiguration) object
    returned: success, changed
    type: dict
'''

from ansible.module_utils.basic import AnsibleModule
try:
    from ansible.module_utils.network.avi.avi import (
        avi_common_argument_spec, avi_ansible_api, HAS_AVI)
except ImportError:
    HAS_AVI = False


def main():
    argument_specs = dict(
        state=dict(default='present',
                   choices=['absent', 'present']),
        avi_api_update_method=dict(default='put',
                                   choices=['put', 'patch']),
        avi_api_patch_op=dict(choices=['add', 'replace', 'delete']),
        aws_access_key=dict(type='str', no_log=True,),
        aws_bucket_id=dict(type='str',),
        aws_secret_access=dict(type='str', no_log=True,),
        backup_file_prefix=dict(type='str',),
        backup_passphrase=dict(type='str', no_log=True,),
        maximum_backups_stored=dict(type='int',),
        name=dict(type='str', required=True),
        remote_directory=dict(type='str',),
        remote_hostname=dict(type='str',),
        save_local=dict(type='bool',),
        ssh_user_ref=dict(type='str',),
        tenant_ref=dict(type='str',),
        upload_to_remote_host=dict(type='bool',),
        upload_to_s3=dict(type='bool',),
        url=dict(type='str',),
        uuid=dict(type='str',),
    )
    argument_specs.update(avi_common_argument_spec())
    module = AnsibleModule(
        argument_spec=argument_specs, supports_check_mode=True)
    if not HAS_AVI:
        return module.fail_json(msg=(
            'Avi python API SDK (avisdk>=17.1) or requests is not installed. '
            'For more details visit https://github.com/avinetworks/sdk.'))
    return avi_ansible_api(module, 'backupconfiguration',
                           set(['backup_passphrase', 'aws_access_key', 'aws_secret_access']))


if __name__ == '__main__':
    main()
