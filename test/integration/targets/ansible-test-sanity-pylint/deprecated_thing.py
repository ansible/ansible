"""
This file is not used by the integration test, but serves a related purpose.
It triggers sanity test failures that can only occur for ansible-core, which need to be ignored to ensure the pylint plugin is functioning properly.
"""
from __future__ import annotations

from ansible.module_utils.datatag import deprecator_from_collection_name
from ansible.module_utils.common.warnings import deprecate


def do_stuff() -> None:
    deprecator = deprecator_from_collection_name('ansible.builtin')

    deprecate(msg='ansible-deprecated-version', version='2.18')
    deprecate(msg='ansible-deprecated-no-version')
    deprecate(msg='ansible-invalid-deprecated-version', version='not-a-version')
    # collection-deprecated-version - ansible-core cannot encounter this
    # collection-invalid-deprecated-version - ansible-core cannot encounter this
    # ansible-deprecated-no-collection-name - ansible-core cannot encounter this
    # wrong-collection-deprecated - ansible-core cannot encounter this
    # ansible-expired-deprecated-date - ansible-core cannot encounter this
    # ansible-invalid-deprecated-date - ansible-core cannot encounter this
    # ansible-deprecated-both-version-and-date - ansible-core cannot encounter this
    # removal-version-must-be-major - ansible-core cannot encounter this
    deprecate(msg='ansible-deprecated-date-not-permitted', date='2099-01-01')
    deprecate(msg='ansible-deprecated-unnecessary-collection-name', deprecator=deprecator, version='2.99')
    deprecate(msg='ansible-deprecated-collection-name-not-permitted', collection_name='ansible.builtin', version='2.99')
    # ansible-deprecated-both-collection-name-and-deprecator - ansible-core cannot encounter this
