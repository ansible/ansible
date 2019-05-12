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
      - Object unique identifier.
    type: str
  details_level:
    description:
      - The level of detail for some of the fields in the response can vary from showing only the UID value of the
        object to a fully detailed representation of the object.
    type: str
    choices: ['uid', 'standard', 'full']
  limit:
    description:
      - No more than that many results will be returned (1-500).
    type: int
  offset:
    description:
      - Skip that many results before beginning to return them.
    type: int
  order:
    description:
      - Sorts results by the given field. By default the results are sorted in the ascending order by name.
    type: list
  show_membership:
    description:
      - Indicates whether to calculate and show "groups" field for every object in reply.
    type: bool
  version:
    description:
      - Version of checkpoint. If not given one, the latest version taken.
    type: str
'''
