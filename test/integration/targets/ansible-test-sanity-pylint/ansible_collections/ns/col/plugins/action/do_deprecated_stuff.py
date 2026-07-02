from __future__ import annotations

from ansible.module_utils.datatag import deprecator_from_collection_name
from ansible.plugins.action import ActionBase
from ansible.utils.display import _display

# extra lines below to allow for adding more imports without shifting the line numbers of the code that follows
#
#
#
#
#


class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        result = super(ActionModule, self).run(tmp, task_vars)
        deprecator = deprecator_from_collection_name('ns.col')

        # ansible-deprecated-version - only ansible-core can encounter this
        _display.deprecated(msg='ansible-deprecated-no-version')
        # ansible-invalid-deprecated-version - only ansible-core can encounter this
        _display.deprecated(msg='collection-deprecated-version', version='1.0.0')
        _display.deprecated(msg='collection-invalid-deprecated-version', version='not-a-version')
        # ansible-deprecated-no-collection-name - only a module_utils can encounter this
        _display.deprecated(msg='wrong-collection-deprecated', collection_name='ns.wrong', version='3.0.0')
        _display.deprecated(msg='ansible-expired-deprecated-date', date='2000-01-01')
        _display.deprecated(msg='ansible-invalid-deprecated-date', date='not-a-date')
        _display.deprecated(msg='ansible-deprecated-both-version-and-date', version='3.0.0', date='2099-01-01')
        _display.deprecated(msg='removal-version-must-be-major', version='3.1.0')
        # ansible-deprecated-date-not-permitted - only ansible-core can encounter this
        _display.deprecated(msg='ansible-deprecated-unnecessary-collection-name', deprecator=deprecator, version='3.0.0')
        # ansible-deprecated-collection-name-not-permitted - only ansible-core can encounter this
        _display.deprecated(msg='ansible-deprecated-both-collection-name-and-deprecator', collection_name='ns.col', deprecator=deprecator, version='3.0.0')

        return result
