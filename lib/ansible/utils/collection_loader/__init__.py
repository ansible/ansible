# (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# CAUTION: There are two implementations of the collection loader.
#          They must be kept functionally identical, although their implementations may differ.
#
# 1) The controller implementation resides in the "lib/ansible/utils/collection_loader/" directory.
#    It must function on all Python versions supported on the controller.
# 2) The ansible-test implementation resides in the "test/lib/ansible_test/_util/target/legacy_collection_loader/" directory.
#    It must function on all Python versions supported on managed hosts which are not supported by the controller.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

# FIXME: decide what of this we want to actually be public/toplevel, put other stuff on a utility class?
from ._collection_config import AnsibleCollectionConfig
from ._collection_finder import AnsibleCollectionRef
from ansible.module_utils.common.text.converters import to_text


def resource_from_fqcr(ref):
    """
    Return resource from a fully-qualified collection reference,
    or from a simple resource name.
    For fully-qualified collection references, this is equivalent to
    ``AnsibleCollectionRef.from_fqcr(ref).resource``.
    :param ref: collection reference to parse
    :return: the resource as a unicode string
    """
    ref = to_text(ref, errors='strict')
    return ref.split(u'.')[-1]
