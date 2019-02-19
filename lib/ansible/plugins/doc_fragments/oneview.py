# -*- coding: utf-8 -*-
#
# Copyright: (c) 2016-2017, Hewlett Packard Enterprise Development LP
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # OneView doc fragment
    DOCUMENTATION = r'''
options:
    config:
      description:
        - Path to a .json configuration file containing the OneView client configuration.
          The configuration file is optional and when used should be present in the host running the ansible commands.
          If the file path is not provided, the configuration will be loaded from environment variables.
          For links to example configuration files or how to use the environment variables verify the notes section.
      type: path

requirements:
  - python >= 2.7.9

notes:
    - "A sample configuration file for the config parameter can be found at:
       U(https://github.com/HewlettPackard/oneview-ansible/blob/master/examples/oneview_config-rename.json)"
    - "Check how to use environment variables for configuration at:
       U(https://github.com/HewlettPackard/oneview-ansible#environment-variables)"
    - "Additional Playbooks for the HPE OneView Ansible modules can be found at:
       U(https://github.com/HewlettPackard/oneview-ansible/tree/master/examples)"
    - "The OneView API version used will directly affect returned and expected fields in resources.
       Information on setting the desired API version and can be found at:
       U(https://github.com/HewlettPackard/oneview-ansible#setting-your-oneview-version)"
    '''

    VALIDATEETAG = r'''
options:
    validate_etag:
        description:
            - When the ETag Validation is enabled, the request will be conditionally processed only if the current ETag
                for the resource matches the ETag provided in the data.
        type: bool
        default: yes
'''

    FACTSPARAMS = r'''
options:
    params:
        description:
        - List of params to delimit, filter and sort the list of resources.
        - "params allowed:
            - C(start): The first item to return, using 0-based indexing.
            - C(count): The number of resources to return.
            - C(filter): A general filter/query string to narrow the list of items returned.
            - C(sort): The sort order of the returned data set."
        type: dict
'''
