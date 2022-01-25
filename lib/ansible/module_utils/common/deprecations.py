# Copyright (c), Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import re

from ansible.module_utils._text import to_native
from ansible.module_utils.six import string_types

version_string = re.compile(r'^\d+\.\d+(?:\.\d+\w*)*$')
date_string = re.compile(r'^\d{4}-\d{2}-\d{2}$')


class Deprecation():
    ''' One deprecation class to rule em all '''

    def __init__(self, why, when=None, alternatives=None, collection_name=None, **kw):

        try:
            self.why = to_native(why).strip()
            if self.why[-1] not in ['!', '?', '.']:
                self.why += '.'
        except TypeError:
            raise Exception('Expected a string for "why" item is deprecated but got "{0}" instead: {1}'.format(type(why), why))

        # when to remove: date or version
        if when is None:
            for found in ('removed_in', 'removed_at_date', 'date', 'version', 'removal_version', 'removed_in_version'):
                if found in kw:
                    # TODO: evenetually deprecate
                    self.when = kw[found]
        else:
            self.when = when

        if not self.when:
            raise Exception('We required to know "when" something is deprecated but got no info')

        if not date_string.match(self.when) or version_string.match(self.when):
            raise Exception('We required "when" we deprecate to be a future version(semantic) or date(YYYY-MM-DD), but got: {0}'.format(self.when))

        # point out alternatives
        if alternatives is None:
            self.alternatives = kw.get('alternative', None)
            if self.alternatives is not None:
                # TODO: evenetually deprecate
                pass
        else:
            self.alternatives = alternatives

        if self.alternatives is not None and not isinstance(self.alternatives, string_types):
            raise Exception('Expected a string for deprecation "alternatives" but got "{0}" instead: {1}'.format(type(self.alternatives), self.alternatives))

        # collection
        if collection_name is None:
            if 'removed_from_collection' in kw:
                # TODO: evenetually deprecate
                self.collection_name = kw.get('removed_from_collection')
            else:
                self.collection_name = 'ansible-core'
        else:
            self.collection_name = collection_name

        # no ansible.builtin release
        if self.collection_name == 'ansible.builtin':
            self.collection_name = 'ansible-core'

    def __str__(self):

        msg = '{0}  This feature will be removed from {1}'.format(self.why, self.collection_name)

        if self.when is None:
            msg += 'in a future release.'
        if date_string.match(self.when):
            msg += 'in a release after {0}.'.format(self.when)
        elif version_string.match(self.when):
            msg += 'in version {0}.'.format(self.when)

        if self.alternatives:
            msg += '  For alternatives see {0}'.format(self.alternatives)

        return msg

    def __rpr__(self):
        return self.__str__()

    def __contains__(self, x):
        return self.why.__contains__(x)
