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

from __future__ import absolute_import

import sys
import base64
import json
import os.path
import types
import pipes
import glob
import re
import crypt
import hashlib
import string
from functools import partial
import operator as py_operator
from random import SystemRandom, shuffle
import uuid

import yaml
from jinja2.filters import environmentfilter
from distutils.version import LooseVersion, StrictVersion

from ansible import errors
from ansible.utils.hashing import md5s, checksum_s
from ansible.utils.unicode import unicode_wrap, to_unicode


UUID_NAMESPACE_ANSIBLE = uuid.UUID('361E6D51-FAEC-444A-9079-341386DA8E2E')


def to_nice_yaml(*a, **kw):
    '''Make verbose, human readable yaml'''
    transformed = yaml.safe_dump(*a, indent=4, allow_unicode=True, default_flow_style=False, **kw)
    return to_unicode(transformed)

def to_json(a, *args, **kw):
    ''' Convert the value to JSON '''
    return json.dumps(a, *args, **kw)

def to_nice_json(a, *args, **kw):
    '''Make verbose, human readable JSON'''
    # python-2.6's json encoder is buggy (can't encode hostvars)
    if sys.version_info < (2, 7):
        try:
            import simplejson
        except ImportError:
            pass
        else:
            try:
                major = int(simplejson.__version__.split('.')[0])
            except:
                pass
            else:
                if major >= 2:
                    return simplejson.dumps(a, indent=4, sort_keys=True, *args, **kw)
        # Fallback to the to_json filter
        return to_json(a, *args, **kw)
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

def ternary(value, true_val, false_val):
    '''  value ? true_val : false_val '''
    if value:
        return true_val
    else:
        return false_val


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

def randomize_list(mylist):
    try:
        mylist = list(mylist)
        shuffle(mylist)
    except:
        pass
    return mylist

def get_hash(data, hashtype='sha1'):

    try: # see if hash is supported
        h = hashlib.new(hashtype)
    except:
        return None

    h.update(data)
    return h.hexdigest()

def get_encrypted_password(password, hashtype='sha512', salt=None):

    # TODO: find a way to construct dynamically from system
    cryptmethod= {
        'md5':      '1',
        'blowfish': '2a',
        'sha256':   '5',
        'sha512':   '6',
    }

    hastype = hashtype.lower()
    if hashtype in cryptmethod:
        if salt is None:
            r = SystemRandom()
            salt = ''.join([r.choice(string.ascii_letters + string.digits) for _ in range(16)])

        saltstring =  "$%s$%s" % (cryptmethod[hashtype],salt)
        encrypted = crypt.crypt(password,saltstring)
        return encrypted

    return None

def to_uuid(string):
    return str(uuid.uuid5(UUID_NAMESPACE_ANSIBLE, str(string)))

class FilterModule(object):
    ''' Ansible core jinja2 filters '''

    def filters(self):
        return {
            # base 64
            'b64decode': partial(unicode_wrap, base64.b64decode),
            'b64encode': partial(unicode_wrap, base64.b64encode),

            # uuid
            'to_uuid': to_uuid,

            # json
            'to_json': to_json,
            'to_nice_json': to_nice_json,
            'from_json': json.loads,

            # yaml
            'to_yaml': yaml.safe_dump,
            'to_nice_yaml': to_nice_yaml,
            'from_yaml': yaml.safe_load,

            # path
            'basename': partial(unicode_wrap, os.path.basename),
            'dirname': partial(unicode_wrap, os.path.dirname),
            'expanduser': partial(unicode_wrap, os.path.expanduser),
            'realpath': partial(unicode_wrap, os.path.realpath),
            'relpath': partial(unicode_wrap, os.path.relpath),

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

            # hash filters
            # md5 hex digest of string
            'md5': md5s,
            # sha1 hex digeset of string
            'sha1': checksum_s,
            # checksum of string as used by ansible for checksuming files
            'checksum': checksum_s,
            # generic hashing
            'password_hash': get_encrypted_password,
            'hash': get_hash,

            # file glob
            'fileglob': fileglob,

            # regex
            'match': match,
            'search': search,
            'regex': regex,
            'regex_replace': regex_replace,

            # ? : ;
            'ternary': ternary,

            # list
            # version comparison
            'version_compare': version_compare,

            # random stuff
            'random': rand,
            'shuffle': randomize_list,
        }
