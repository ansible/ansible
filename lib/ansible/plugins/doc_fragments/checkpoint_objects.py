# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Or Soffer <orso@checkpoint.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # Standard files documentation fragment
    DOCUMENTATION = r'''
options:
  name:
    description:
      - Object name. Should be unique in the domain.
    type: str
  uid:
    description:
      Object unique identifier.
    type: str
  tags:
    description:
      - Collection of tag objects identified by the name or UID. How much details are returned depends on the
        details-level field of the request. This table shows the level of detail shown when details-level is set to
        standard.
    type: list
  color:
    description:
      - Color of the object. Should be one of existing colors.
    type: str
    choices: ['aquamarine', 'black', 'blue', 'crete blue', 'burlywood', 'cyan', 'dark green', 'khaki', 'orchid',
              'dark orange', 'dark sea green', 'pink', 'turquoise', 'dark blue', 'firebrick', 'brown', 'forest green',
              'gold', 'dark gold', 'gray', 'dark gray', 'light green', 'lemon chiffon', 'coral', 'sea green',
              'sky blue', 'magenta', 'purple', 'slate blue', 'violet red', 'navy blue', 'olive', 'orange', 'red',
              'sienna', 'yellow']
  comments:
    description:
      - Comments string.
    type: str
  details_level:
    description:
      - The level of detail for some of the fields in the response can vary from showing only the UID value of the
        object to a fully detailed representation of the object.
    type: str
    choices: ['uid', 'standard', 'full']
  groups:
    description:
      - Collection of group identifiers.
    type: list
  ignore_warnings:
    description:
      - Apply changes ignoring warnings.
    type: bool
  ignore_errors:
    description:
      - Apply changes ignoring errors. You won't be able to publish such a changes. If ignore-warnings flag was omitted
        - warnings will also be ignored.
    type: bool
  new_name:
    description:
      - New name of the object.
    type: str
  state:
    description:
      - State of the access rule (present or absent). Defaults to present.
    type: str
    required: True
    choices: ['present', 'absent']
  auto_publish_session:
    description:
      - Publish the current session if changes have been performed
        after task completes.
    type: bool
  wait_for_task:
    description:
      - Wait for the task to end. Such as publish task.
    type: bool
    default: true
  version:
    description:
      - Version of checkpoint. If not given one, the latest version taken.
    type: str
'''
