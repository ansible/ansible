from __future__ import absolute_import, division, print_function
__metaclass__ = type
ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}
DOCUMENTATION = '''
---
module: my_sample_module

short_description: This is my sample module

version_added: "2.4"

description:
    - "This is my longer description explaining my sample module"

options:
    name:
        description:
            - This is the message to send to the sample module
        required: true
    new:
        description:
            - Control to demo if the result of this module is changed or not
        required: false
'''

EXAMPLES = '''

# Pass in a message
- name: Test with a message
  my_new_test_module:
    name: hello world

'''

RETURN = '''

  original_message:
      description: The original name param that was passed in
      type: str
  message:
      description: The output message that the sample module generates
'''
foo = 'apple'
