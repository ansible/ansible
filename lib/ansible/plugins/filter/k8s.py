# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


try:
    from openshift.helper.hashes import generate_hash
    HAS_GENERATE_HASH = True
except ImportError:
    HAS_GENERATE_HASH = False

from ansible.errors import AnsibleFilterError


def k8s_config_resource_name(resource):
    if not HAS_GENERATE_HASH:
        raise AnsibleFilterError("k8s_config_resource_name requires openshift>=0.7.2")
    try:
        return resource['metadata']['name'] + '-' + generate_hash(resource)
    except KeyError:
        raise AnsibleFilterError("resource must have a metadata.name key to generate a resource name")


# ---- Ansible filters ----
class FilterModule(object):

    def filters(self):
        return {
            'k8s_config_resource_name': k8s_config_resource_name
        }
