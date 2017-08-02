# -*- coding: utf-8 -*-
#
# Copyright (2016-2017) Hewlett Packard Enterprise Development LP
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


class ModuleDocFragment(object):

    # OneView doc fragment
    DOCUMENTATION = '''
options:
    config:
      description:
        - Path to a .json configuration file containing the OneView client configuration.
          The configuration file is optional and when used should be present in the host running the ansible commands.
          If the file path is not provided, the configuration will be loaded from environment variables.
          For links to example configuration files or how to use the environment variables verify the notes section.
      required: false

requirements:
  - "python >= 2.7.9"

notes:
    - "A sample configuration file for the config parameter can be found at:
       U(https://github.com/HewlettPackard/oneview-ansible/blob/master/examples/oneview_config-rename.json)"
    - "Check how to use environment variables for configuration at:
       U(https://github.com/HewlettPackard/oneview-ansible#environment-variables)"
    - "Additional Playbooks for the HPE OneView Ansible modules can be found at:
       U(https://github.com/HewlettPackard/oneview-ansible/tree/master/examples)"
    '''

    VALIDATEETAG = '''
options:
    validate_etag:
        description:
            - When the ETag Validation is enabled, the request will be conditionally processed only if the current ETag
                for the resource matches the ETag provided in the data.
        default: true
        choices: ['true', 'false']
'''

    FACTSPARAMS = '''
options:
    params:
        description:
        - List of params to delimit, filter and sort the list of resources.
        - "params allowed:
            C(start): The first item to return, using 0-based indexing.
            C(count): The number of resources to return.
            C(filter): A general filter/query string to narrow the list of items returned.
            C(sort): The sort order of the returned data set."
        required: false
'''
