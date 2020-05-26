# (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from yaml import safe_load


def _meta_yml_to_dict(yaml_string_data, content_id):
    routing_dict = safe_load(yaml_string_data)
    if not routing_dict:
        routing_dict = {}
    # TODO: change this to Mapping abc?
    if not isinstance(routing_dict, dict):
        raise ValueError('collection metadata must be a dictionary')
    return routing_dict
