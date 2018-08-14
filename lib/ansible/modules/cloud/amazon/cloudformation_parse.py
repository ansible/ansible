#!/usr/bin/python

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: cloudformation_parse

short_description: Parse cloudformation templates for information

version_added: "2.4"

requirements:
  - cfn-flip >= 1.0.3

description:
    - "Parse local cloudformation template files for information"

options:
    parse:
        description:
            - List of dicts in the form { save: 'var_name', path: path to parse }
        required: true
    file:
        description:
            - Path to the cloudformation template to parse
        required: true

author:
    - Steven Miller @sjmiller609
'''

EXAMPLES = '''
- name: Parse each cloudformation template for the required tags
  parse_cloudformation:
    file: /path/to/cft.json
    parse:
    - save: SupportedBy
      path:
      - Parameters
      - SupportedBy
      - Default
    - save: UAI
      path:
      - Parameters
      - UAI
      - Default
    - save: Name
      path:
      - Parameters
      - Name
      - Default
    - save: Env
      path:
      - Parameters
      - Env
      - Default
  register: result

'''

RETURN = '''
value:
    description: Dictionary with a key for each 'save' and the value as the parsed value
    type: dict
'''

from ansible.module_utils.basic import AnsibleModule
# This module allows us to parse cfn including special tags
from cfn_flip import load as cfn_load

def run_module():
    # define the available arguments/parameters that a user can pass to
    # the module
    module_args = dict(
        parse=dict(type='list', required=True),
        file=dict(type='str', required=True)
    )

    # changed is always False for this module
    result = dict(
        changed=False,
        value={}
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # Get the inputs
    parse = module.params['parse']
    filepath = module.params['file']

    # read file
    with open(filepath,"r") as f:
        data = f.read()
    # parse file into hash
    parsed = cfn_load(data)[0]
    for var in parse:
        name = var['save']
        path = var['path']
        value = parsed
        try:
          # follow path to get the value
          for key in path:
              value = value[key]
        except KeyError:
            message = "ERROR: Could not find expected path in the cloudformation template: "+str(path)
            result['failed'] = True
            module.fail_json(msg=message, **result)
            return
        # set result['value'] to what we have found
        result['value'][name] = str(value)

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
