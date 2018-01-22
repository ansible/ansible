#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2018, Ian Tewksbury <itewk@redhat.com>
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
module: manageiq_config

short_description: Module for managing ManageIQ configuration.
version_added: '2.6'
author: Ian Tewksbury (@itewk)
description:
    - "Module for managing ManageIQ or CloudForms Managment Engine (CFME) configuration via the local rails runner on the Appliance."

options:
    name:
        description:
            - Name of the ManageIQ config element to modify.
        required: True
    value:
        description: Dictionary to set as the value for the ManageIQ config option. Any values not given will be left at current value.
        required: False
        default: {}
    vmdb_path:
        description: Path to the VMDB directory.
        required: False
        default: /var/www/miq/vmdb
'''

EXAMPLES = '''
# set the smtp settings
- manageiq_config:
    name: smtp
    value:
      from: cfme@example.com
      host: postfix.example.com
      port: 25
      domain: example.com

# set generic worker memory threshold
- manageiq_config:
    name: workers
    value:
      worker_base:
        queue_worker_base:
          generic_worker:
            memory_threshold: '900.megabytes'
'''

RETURN = '''
name:
    description: Name of the ManageIQ config option that is being modified.
    type: str
    returned: always
original_value:
    description: The original value of the ManageIQ config option being modified before modification.
    type: dict
    returned: always
value:
    description: The value of the ManageIQ config option being modified after modification.
    type: dict
    returned: always
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import json
import time
import collections
import copy


# @source https://gist.github.com/angstwad/bf22d1822c38a92ec0a9
def dict_merge(dct, merge_dct):
    """ Recursive dict merge. Inspired by :meth:``dict.update()``, instead of
    updating only top-level keys, dict_merge recurses down into dicts nested
    to an arbitrary depth, updating keys. The ``merge_dct`` is merged into
    ``dct``.
    :param dct: dict onto which the merge is executed
    :param merge_dct: dct merged into dct
    :return: None
    """
    for k, v in merge_dct.items():
        if (k in dct and isinstance(dct[k], dict)
                and isinstance(merge_dct[k], collections.Mapping)):
            dict_merge(dct[k], merge_dct[k])
        else:
            dct[k] = merge_dct[k]


def get_manageiq_config_value(module, name):
    """ Gets the current value for the given config option.
    :param module: AnsibleModule making the call
    :param name: ManageIQ config option name
    :return: dict of value of the ManageIQ config option
    """
    returncode, out, err = module.run_command([
        "rails",
        "r",
        "puts MiqServer.my_server.get_config(:%s).config.to_json" % (name)
    ], cwd=module.params['vmdb_path'])
    if returncode != 0:
        raise Exception("Error getting existing value for ':%s' config: %s" % (name, err))

    return json.loads(out)


def create_expected_value(original_value, changes):
    """ Merges changes into original value to create a merged expected value.
    :param original_value: dict original value to merge changes into
    :param changes: dict of changes to merge into original_value to create the expected value
    :return: dict of the changes merged into the original_value to create an expected value
    """
    expected_value = copy.deepcopy(original_value)
    dict_merge(expected_value, changes)
    return expected_value


def main():
    # define the module
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            value=dict(type='dict', required=False, default={}),
            vmdb_path=dict(type='str', required=False, default='/var/www/miq/vmdb'),
        ),
        supports_check_mode=True
    )

    # seed the result dict in the object
    result = dict(
        changed=False,
        name='',
        original_value={},
        value={},
        diff={}
    )

    # get the original value for the given config option
    try:
        original_value = get_manageiq_config_value(module, module.params['name'])
    except Exception as err:
        module.fail_json(msg=str(err), **result)

    # update the result
    result['name'] = module.params['name']
    result['original_value'] = original_value

    # create updated value dictionary
    expected_value = create_expected_value(original_value, module.params['value'])

    # enable diff mode
    result['diff'] = {
        'before': {
            module.params['name']: original_value
        },
        'after': {
            module.params['name']: expected_value
        }
    }

    # if check_mode then stop here
    if module.check_mode:
        result['changed'] = original_value != expected_value
        module.exit_json(**result)

    # update config if difference
    # else no-op
    if original_value != expected_value:
        (update_value_rc, update_value_out, update_value_err) = module.run_command([
            "rails",
            "r",
            "MiqServer.my_server.set_config(:%s => JSON.parse('%s')); MiqServer.my_server.save!" % (module.params['name'], json.dumps(expected_value))
        ], cwd=module.params['vmdb_path'])
        result['changed'] = True
        if update_value_rc != 0:
            module.fail_json(msg="Error updating value for ':%s' config: %s" % (module.params['name'], update_value_err), **result)
    else:
        module.exit_json(**result)

    # get the updated current value and expected value
    # NOTE: needed to create new expected value because MangeIQ has been known
    #       to update other defaults on the first update of the configuration after
    #       and upgrade. Therefor, recreating the expected value from the updated current
    #       value protects against that.
    current_value = get_manageiq_config_value(module, module.params['name'])
    expected_value = create_expected_value(current_value, module.params['value'])

    # if current ManageIQ config value equals expected value then exit with success
    # else exit with error
    if current_value == expected_value:
        module.exit_json(**result)
    else:
        module.fail_json(
            msg="Error updating value for ':%s' config. After update configuration does not match expected value after update." % (module.params['name']),
            current_value=current_value,
            expected_value=expected_value
        )


if __name__ == '__main__':
    main()
