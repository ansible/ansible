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
import pipes
import glob
import re
from ansible import errors
from ansible.utils import md5s
# TODO: hack to make tests pass; update tests instead
from ansible.runner.test_plugins.core import *
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

def mandatory(a):
    ''' Make a variable mandatory '''
    try:
        a
    except NameError:
        raise errors.AnsibleFilterError('Mandatory variable not defined.')
    else:
        return a

def quote(a):
    ''' return its argument quoted for shell usage '''
    return pipes.quote(a)

def fileglob(pathname):
    ''' return list of matched files for glob '''
    return glob.glob(pathname)

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

            # variable existence
            'mandatory': mandatory,

            # quote string for shell usage
            'quote': quote,

            # md5 hex digest of string
            'md5': md5s,

            # file glob
            'fileglob': fileglob,

            # regex
            'regex_replace': regex_replace,

            # list
            'unique' : unique,
            'intersect': intersect,
            'difference': difference,
            'symmetric_difference': symmetric_difference,
            'union': union,

            # random numbers
            'random': rand,
        }

