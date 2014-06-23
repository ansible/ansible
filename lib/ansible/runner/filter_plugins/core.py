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

import base64
import json
import os.path
import yaml
import types
import pipes
import glob
import re
import operator as py_operator
from ansible import errors
from ansible.utils import md5s
from distutils.version import LooseVersion, StrictVersion
from random import SystemRandom
from jinja2.filters import environmentfilter

def to_nice_yaml(*a, **kw):
    '''Make verbose, human readable yaml'''
    return yaml.safe_dump(*a, indent=4, allow_unicode=True, default_flow_style=False, **kw)

def to_json(a, *args, **kw):
    ''' Convert the value to JSON '''
    return json.dumps(a, *args, **kw)

def to_nice_json(a, *args, **kw):
    '''Make verbose, human readable JSON'''
    return json.dumps(a, indent=4, sort_keys=True, *args, **kw)

def failed(*a, **kw):
    ''' Test if task result yields failed '''
    item = a[0]
    if type(item) != dict:
        raise errors.AnsibleFilterError("|failed expects a dictionary")
    rc = item.get('rc',0)
    failed = item.get('failed',False)
    if rc != 0 or failed:
        return True
    else:
        return False

def success(*a, **kw):
    ''' Test if task result yields success '''
    return not failed(*a, **kw)

def changed(*a, **kw):
    ''' Test if task result yields changed '''
    item = a[0]
    if type(item) != dict:
        raise errors.AnsibleFilterError("|changed expects a dictionary")
    if not 'changed' in item:
        changed = False
        if ('results' in item    # some modules return a 'results' key
                and type(item['results']) == list
                and type(item['results'][0]) == dict):
            for result in item['results']:
                changed = changed or result.get('changed', False)
    else:
        changed = item.get('changed', False)
    return changed

def skipped(*a, **kw):
    ''' Test if task result yields skipped '''
    item = a[0]
    if type(item) != dict:
        raise errors.AnsibleFilterError("|skipped expects a dictionary")
    skipped = item.get('skipped', False)
    return skipped

def mandatory(a):
    ''' Make a variable mandatory '''
    try:
        a
    except NameError:
        raise errors.AnsibleFilterError('Mandatory variable not defined.')
    else:
        return a

def bool(a):
    ''' return a bool for the arg '''
    if a is None or type(a) == bool:
        return a
    if type(a) in types.StringTypes:
        a = a.lower()
    if a in ['yes', 'on', '1', 'true', 1]:
        return True
    else:
        return False

def quote(a):
    ''' return its argument quoted for shell usage '''
    return pipes.quote(a)

def fileglob(pathname):
    ''' return list of matched files for glob '''
    return glob.glob(pathname)

def regex(value='', pattern='', ignorecase=False, match_type='search'):
    ''' Expose `re` as a boolean filter using the `search` method by default.
        This is likely only useful for `search` and `match` which already
        have their own filters.
    '''
    if ignorecase:
        flags = re.I
    else:
        flags = 0
    _re = re.compile(pattern, flags=flags)
    _bool = __builtins__.get('bool')
    return _bool(getattr(_re, match_type, 'search')(value))

def match(value, pattern='', ignorecase=False):
    ''' Perform a `re.match` returning a boolean '''
    return regex(value, pattern, ignorecase, 'match')

def search(value, pattern='', ignorecase=False):
    ''' Perform a `re.search` returning a boolean '''
    return regex(value, pattern, ignorecase, 'search')

def regex_replace(value='', pattern='', replacement='', ignorecase=False):
    ''' Perform a `re.sub` returning a string '''

    if not isinstance(value, basestring):
        value = str(value)

    if ignorecase:
        flags = re.I
    else:
        flags = 0
    _re = re.compile(pattern, flags=flags)
    return _re.sub(replacement, value)

def unique(a):
    return set(a)

def intersect(a, b):
    return set(a).intersection(b)

def difference(a, b):
    return set(a).difference(b)

def symmetric_difference(a, b):
    return set(a).symmetric_difference(b)

def union(a, b):
    return set(a).union(b)

def version_compare(value, version, operator='eq', strict=False):
    ''' Perform a version comparison on a value '''
    op_map = {
        '==': 'eq', '=':  'eq', 'eq': 'eq',
        '<':  'lt', 'lt': 'lt',
        '<=': 'le', 'le': 'le',
        '>':  'gt', 'gt': 'gt',
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
    except Exception, e:
        raise errors.AnsibleFilterError('Version comparison: %s' % e)

@environmentfilter
def rand(environment, end, start=None, step=None):
    r = SystemRandom()
    if isinstance(end, (int, long)):
        if not start:
            start = 0
        if not step:
            step = 1
        return r.randrange(start, end, step)
    elif hasattr(end, '__iter__'):
        if start or step:
            raise errors.AnsibleFilterError('start and step can only be used with integer values')
        return r.choice(end)
    else:
        raise errors.AnsibleFilterError('random can only be used on sequences and integers')

class FilterModule(object):
    ''' Ansible core jinja2 filters '''

    def filters(self):
        return {
            # base 64
            'b64decode': base64.b64decode,
            'b64encode': base64.b64encode,

            # json
            'to_json': to_json,
            'to_nice_json': to_nice_json,
            'from_json': json.loads,

            # yaml
            'to_yaml': yaml.safe_dump,
            'to_nice_yaml': to_nice_yaml,
            'from_yaml': yaml.safe_load,

            # path
            'basename': os.path.basename,
            'dirname': os.path.dirname,
            'expanduser': os.path.expanduser,
            'realpath': os.path.realpath,
            'relpath': os.path.relpath,

            # failure testing
            'failed'  : failed,
            'success' : success,

            # changed testing
            'changed' : changed,

            # skip testing
            'skipped' : skipped,

            # variable existence
            'mandatory': mandatory,

            # value as boolean
            'bool': bool,

            # quote string for shell usage
            'quote': quote,

            # md5 hex digest of string
            'md5': md5s,

            # file glob
            'fileglob': fileglob,

            # regex
            'match': match,
            'search': search,
            'regex': regex,
            'regex_replace': regex_replace,

            # list
            'unique' : unique,
            'intersect': intersect,
            'difference': difference,
            'symmetric_difference': symmetric_difference,
            'union': union,

            # version comparison
            'version_compare': version_compare,

            # random numbers
            'random': rand,
        }

