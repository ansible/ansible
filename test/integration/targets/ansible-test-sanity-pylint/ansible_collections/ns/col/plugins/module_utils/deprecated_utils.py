from __future__ import annotations

from ansible.module_utils.datatag import deprecator_from_collection_name
from ansible.module_utils.common.warnings import deprecate

# extra lines below to allow for adding more imports without shifting the line numbers of the code that follows
#
#
#
#
#
#
#
#


def do_stuff() -> None:
    deprecator = deprecator_from_collection_name('ns.col')

    # ansible-deprecated-version - only ansible-core can encounter this
    deprecate(msg='ansible-deprecated-no-version', collection_name='ns.col')
    # ansible-invalid-deprecated-version - only ansible-core can encounter this
    deprecate(msg='collection-deprecated-version', collection_name='ns.col', version='1.0.0')
    deprecate(msg='collection-invalid-deprecated-version', collection_name='ns.col', version='not-a-version')
    # ansible-deprecated-no-collection-name - module_utils cannot encounter this
    deprecate(msg='wrong-collection-deprecated', collection_name='ns.wrong', version='3.0.0')
    deprecate(msg='ansible-expired-deprecated-date', collection_name='ns.col', date='2000-01-01')
    deprecate(msg='ansible-invalid-deprecated-date', collection_name='ns.col', date='not-a-date')
    deprecate(msg='ansible-deprecated-both-version-and-date', collection_name='ns.col', version='3.0.0', date='2099-01-01')
    deprecate(msg='removal-version-must-be-major', collection_name='ns.col', version='3.1.0')
    # ansible-deprecated-date-not-permitted - only ansible-core can encounter this
    # ansible-deprecated-unnecessary-collection-name - module_utils cannot encounter this
    # ansible-deprecated-collection-name-not-permitted - only ansible-core can encounter this
    deprecate(msg='ansible-deprecated-both-collection-name-and-deprecator', collection_name='ns.col', deprecator=deprecator, version='3.0.0')
