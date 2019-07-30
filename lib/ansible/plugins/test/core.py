# (c) 2012, Jeroen Hoekx <jeroen@hoekx.be>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re
import operator as py_operator
from distutils.version import LooseVersion, StrictVersion

from ansible import errors
from ansible.module_utils._text import to_text
from ansible.module_utils.common._collections_compat import MutableMapping, MutableSequence
from ansible.utils.display import Display

display = Display()


def failed(result):
    ''' Test if task result yields failed '''
    if not isinstance(result, MutableMapping):
        raise errors.AnsibleFilterError("The 'failed' test expects a dictionary")
    return result.get('failed', False)


def success(result):
    ''' Test if task result yields success '''
    return not failed(result)


def unreachable(result):
    ''' Test if task result yields unreachable '''
    if not isinstance(result, MutableMapping):
        raise errors.AnsibleFilterError("The 'unreachable' test expects a dictionary")
    return result.get('unreachable', False)


def reachable(result):
    ''' Test if task result yields reachable '''
    return not unreachable(result)


def changed(result):
    ''' Test if task result yields changed '''
    if not isinstance(result, MutableMapping):
        raise errors.AnsibleFilterError("The 'changed' test expects a dictionary")
    if 'changed' not in result:
        changed = False
        if (
            'results' in result and   # some modules return a 'results' key
            isinstance(result['results'], MutableSequence) and
            isinstance(result['results'][0], MutableMapping)
        ):
            for res in result['results']:
                if res.get('changed', False):
                    changed = True
                    break
    else:
        changed = result.get('changed', False)
    return changed


def skipped(result):
    ''' Test if task result yields skipped '''
    if not isinstance(result, MutableMapping):
        raise errors.AnsibleFilterError("The 'skipped' test expects a dictionary")
    return result.get('skipped', False)


def started(result):
    ''' Test if async task has started '''
    if not isinstance(result, MutableMapping):
        raise errors.AnsibleFilterError("The 'started' test expects a dictionary")
    if 'started' in result:
        # For async tasks, return status
        # NOTE: The value of started is 0 or 1, not False or True :-/
        return result.get('started', 0) == 1
    else:
        # For non-async tasks, warn user, but return as if started
        display.warning("The 'started' test expects an async task, but a non-async task was tested")
        return True


def finished(result):
    ''' Test if async task has finished '''
    if not isinstance(result, MutableMapping):
        raise errors.AnsibleFilterError("The 'finished' test expects a dictionary")
    if 'finished' in result:
        # For async tasks, return status
        # NOTE: The value of finished is 0 or 1, not False or True :-/
        return result.get('finished', 0) == 1
    else:
        # For non-async tasks, warn user, but return as if finished
        display.warning("The 'finished' test expects an async task, but a non-async task was tested")
        return True


def regex(value='', pattern='', ignorecase=False, multiline=False, match_type='search'):
    ''' Expose `re` as a boolean filter using the `search` method by default.
        This is likely only useful for `search` and `match` which already
        have their own filters.
    '''
    # In addition to ensuring the correct type, to_text here will ensure
    # _fail_with_undefined_error happens if the value is Undefined
    value = to_text(value, errors='surrogate_or_strict')
    flags = 0
    if ignorecase:
        flags |= re.I
    if multiline:
        flags |= re.M
    _re = re.compile(pattern, flags=flags)
    return bool(getattr(_re, match_type, 'search')(value))


def match(value, pattern='', ignorecase=False, multiline=False):
    ''' Perform a `re.match` returning a boolean '''
    return regex(value, pattern, ignorecase, multiline, 'match')


def search(value, pattern='', ignorecase=False, multiline=False):
    ''' Perform a `re.search` returning a boolean '''
    return regex(value, pattern, ignorecase, multiline, 'search')


def version_compare(value, version, operator='eq', strict=False):
    ''' Perform a version comparison on a value '''
    op_map = {
        '==': 'eq', '=': 'eq', 'eq': 'eq',
        '<': 'lt', 'lt': 'lt',
        '<=': 'le', 'le': 'le',
        '>': 'gt', 'gt': 'gt',
        '>=': 'ge', 'ge': 'ge',
        '!=': 'ne', '<>': 'ne', 'ne': 'ne'
    }

    if strict:
        Version = StrictVersion
    else:
        Version = LooseVersion

    if operator in op_map:
        operator = op_map[operator]
    else:
        raise errors.AnsibleFilterError('Invalid operator type')

    try:
        method = getattr(py_operator, operator)
        return method(Version(str(value)), Version(str(version)))
    except Exception as e:
        raise errors.AnsibleFilterError('Version comparison: %s' % e)


class TestModule(object):
    ''' Ansible core jinja2 tests '''

    def tests(self):
        return {
            # failure testing
            'failed': failed,
            'failure': failed,
            'succeeded': success,
            'success': success,
            'successful': success,
            'reachable': reachable,
            'unreachable': unreachable,

            # changed testing
            'changed': changed,
            'change': changed,

            # skip testing
            'skipped': skipped,
            'skip': skipped,

            # async testing
            'finished': finished,
            'started': started,

            # regex
            'match': match,
            'search': search,
            'regex': regex,

            # version comparison
            'version_compare': version_compare,
            'version': version_compare,

            # lists
            'any': any,
            'all': all,
        }
