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

from ansible.module_utils.common.yaml import yaml_load


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
