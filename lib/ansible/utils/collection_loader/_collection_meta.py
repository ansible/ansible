# (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# CAUTION: There are two implementations of the collection loader.
#          They must be kept functionally identical, although their implementations may differ.
#
# 1) The controller implementation resides in the "lib/ansible/utils/collection_loader/" directory.
#    It must function on all Python versions supported on the controller.
# 2) The ansible-test implementation resides in the "test/lib/ansible_test/_data/legacy_collection_loader/" directory.
#    It must function on all Python versions supported on managed hosts which are not supported by the controller.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

try:
    from collections.abc import Mapping   # pylint: disable=ansible-bad-import-from
except ImportError:
    from collections import Mapping  # pylint: disable=ansible-bad-import-from

import ansible.constants as C
from ansible.module_utils.common.yaml import yaml_load
from ansible.utils.display import Display
from ansible.module_utils.six import string_types


display = Display()


def _meta_yml_to_dict(yaml_string_data, content_id):
    """
    Converts string YAML dictionary to a Python dictionary. This function may be monkeypatched to another implementation
    by some tools (eg the import sanity test).
    :param yaml_string_data: a bytes-ish YAML dictionary
    :param content_id: a unique ID representing the content to allow other implementations to cache the output
    :return: a Python dictionary representing the YAML dictionary content
    """
    # NB: content_id is passed in, but not used by this implementation
    routing_dict = yaml_load(yaml_string_data)
    if not routing_dict:
        routing_dict = {}
    if not isinstance(routing_dict, Mapping):
        raise ValueError('collection metadata must be an instance of Python Mapping')
    return routing_dict


def _validate_action_group_metadata(action, found_group_metadata, fq_group_name):
    valid_metadata = {
        'extend_group': {
            'types': (list, string_types,),
            'errortype': 'list',
        },
    }

    metadata_warnings = []

    validate = C.VALIDATE_ACTION_GROUP_METADATA
    metadata_only = isinstance(action, dict) and 'metadata' in action and len(action) == 1

    if validate and not metadata_only:
        found_keys = ', '.join(sorted(list(action)))
        metadata_warnings.append("The only expected key is metadata, but got keys: {keys}".format(keys=found_keys))
    elif validate:
        if found_group_metadata:
            metadata_warnings.append("The group contains multiple metadata entries.")
        if not isinstance(action['metadata'], dict):
            metadata_warnings.append("The metadata is not a dictionary. Got {metadata}".format(metadata=action['metadata']))
        else:
            unexpected_keys = set(action['metadata'].keys()) - set(valid_metadata.keys())
            if unexpected_keys:
                metadata_warnings.append("The metadata contains unexpected keys: {0}".format(', '.join(unexpected_keys)))
            unexpected_types = []
            for field, requirement in valid_metadata.items():
                if field not in action['metadata']:
                    continue
                value = action['metadata'][field]
                if not isinstance(value, requirement['types']):
                    unexpected_types.append("%s is %s (expected type %s)" % (field, value, requirement['errortype']))
            if unexpected_types:
                metadata_warnings.append("The metadata contains unexpected key types: {0}".format(', '.join(unexpected_types)))
    if metadata_warnings:
        metadata_warnings.insert(0, "Invalid metadata was found for action_group {0} while loading module_defaults.".format(fq_group_name))
        display.warning(" ".join(metadata_warnings))
