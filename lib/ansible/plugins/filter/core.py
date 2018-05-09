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

import base64
import crypt
import glob
import hashlib
import itertools
import json
import ntpath
import os.path
import re
import string
import sys
import time
import uuid
import yaml

from collections import MutableMapping, MutableSequence
import datetime
from functools import partial
from random import Random, SystemRandom, shuffle

from jinja2.filters import environmentfilter, do_groupby as _do_groupby

try:
    import passlib.hash
    HAS_PASSLIB = True
except ImportError:
    HAS_PASSLIB = False

from ansible.errors import AnsibleFilterError
from ansible.module_utils.six import iteritems, string_types, integer_types
from ansible.module_utils.six.moves import reduce, shlex_quote
from ansible.module_utils._text import to_bytes, to_text
from ansible.parsing.ajson import AnsibleJSONEncoder
from ansible.parsing.yaml.dumper import AnsibleDumper
from ansible.utils.hashing import md5s, checksum_s
from ansible.utils.unicode import unicode_wrap
from ansible.utils.vars import merge_hash

UUID_NAMESPACE_ANSIBLE = uuid.UUID('361E6D51-FAEC-444A-9079-341386DA8E2E')


def to_yaml(a, *args, **kw):
    '''Make verbose, human readable yaml'''
    transformed = yaml.dump(a, Dumper=AnsibleDumper, allow_unicode=True, **kw)
    return to_text(transformed)


def to_nice_yaml(a, indent=4, *args, **kw):
    '''Make verbose, human readable yaml'''
    transformed = yaml.dump(a, Dumper=AnsibleDumper, indent=indent, allow_unicode=True, default_flow_style=False, **kw)
    return to_text(transformed)


def to_json(a, *args, **kw):
    ''' Convert the value to JSON '''
    return json.dumps(a, cls=AnsibleJSONEncoder, *args, **kw)


def to_nice_json(a, indent=4, *args, **kw):
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
            except Exception:
                pass
            else:
                if major >= 2:
                    return simplejson.dumps(a, default=AnsibleJSONEncoder.default, indent=indent, sort_keys=True, *args, **kw)

    try:
        return json.dumps(a, indent=indent, sort_keys=True, cls=AnsibleJSONEncoder, *args, **kw)
    except Exception:
        # Fallback to the to_json filter
        return to_json(a, *args, **kw)


def to_bool(a):
    ''' return a bool for the arg '''
    if a is None or isinstance(a, bool):
        return a
    if isinstance(a, string_types):
        a = a.lower()
    if a in ('yes', 'on', '1', 'true', 1):
        return True
    return False


def to_datetime(string, format="%Y-%m-%d %H:%M:%S"):
    return datetime.datetime.strptime(string, format)


def strftime(string_format, second=None):
    ''' return a date string using string. See https://docs.python.org/2/library/time.html#time.strftime for format '''
    if second is not None:
        try:
            second = int(second)
        except Exception:
            raise AnsibleFilterError('Invalid value for epoch value (%s)' % second)
    return time.strftime(string_format, time.localtime(second))


def quote(a):
    ''' return its argument quoted for shell usage '''
    return shlex_quote(to_text(a))


def fileglob(pathname):
    ''' return list of matched regular files for glob '''
    return [g for g in glob.glob(pathname) if os.path.isfile(g)]


def regex_replace(value='', pattern='', replacement='', ignorecase=False):
    ''' Perform a `re.sub` returning a string '''

    value = to_text(value, errors='surrogate_or_strict', nonstring='simplerepr')

    if ignorecase:
        flags = re.I
    else:
        flags = 0
    _re = re.compile(pattern, flags=flags)
    return _re.sub(replacement, value)


def regex_findall(value, regex, multiline=False, ignorecase=False):
    ''' Perform re.findall and return the list of matches '''
    flags = 0
    if ignorecase:
        flags |= re.I
    if multiline:
        flags |= re.M
    return re.findall(regex, value, flags)


def regex_search(value, regex, *args, **kwargs):
    ''' Perform re.search and return the list of matches or a backref '''

    groups = list()
    for arg in args:
        if arg.startswith('\\g'):
            match = re.match(r'\\g<(\S+)>', arg).group(1)
            groups.append(match)
        elif arg.startswith('\\'):
            match = int(re.match(r'\\(\d+)', arg).group(1))
            groups.append(match)
        else:
            raise AnsibleFilterError('Unknown argument')

    flags = 0
    if kwargs.get('ignorecase'):
        flags |= re.I
    if kwargs.get('multiline'):
        flags |= re.M

    match = re.search(regex, value, flags)
    if match:
        if not groups:
            return match.group()
        else:
            items = list()
            for item in groups:
                items.append(match.group(item))
            return items


def ternary(value, true_val, false_val):
    '''  value ? true_val : false_val '''
    if bool(value):
        return true_val
    else:
        return false_val


def regex_escape(string):
    '''Escape all regular expressions special characters from STRING.'''
    return re.escape(string)


def from_yaml(data):
    if isinstance(data, string_types):
        return yaml.safe_load(data)
    return data


@environmentfilter
def rand(environment, end, start=None, step=None, seed=None):
    if seed is None:
        r = SystemRandom()
    else:
        r = Random(seed)
    if isinstance(end, integer_types):
        if not start:
            start = 0
        if not step:
            step = 1
        return r.randrange(start, end + 1, step)
    elif hasattr(end, '__iter__'):
        if start or step:
            raise AnsibleFilterError('start and step can only be used with integer values')
        return r.choice(end)
    else:
        raise AnsibleFilterError('random can only be used on sequences and integers')


def randomize_list(mylist, seed=None):
    try:
        mylist = list(mylist)
        if seed:
            r = Random(seed)
            r.shuffle(mylist)
        else:
            shuffle(mylist)
    except Exception:
        pass
    return mylist


def get_hash(data, hashtype='sha1'):

    try:  # see if hash is supported
        h = hashlib.new(hashtype)
    except Exception:
        return None

    h.update(to_bytes(data, errors='surrogate_or_strict'))
    return h.hexdigest()


def get_encrypted_password(password, hashtype='sha512', salt=None):

    # TODO: find a way to construct dynamically from system
    cryptmethod = {
        'md5': '1',
        'blowfish': '2a',
        'sha256': '5',
        'sha512': '6',
    }

    if hashtype in cryptmethod:
        if salt is None:
            r = SystemRandom()
            if hashtype in ['md5']:
                saltsize = 8
            else:
                saltsize = 16
            saltcharset = string.ascii_letters + string.digits + '/.'
            salt = ''.join([r.choice(saltcharset) for _ in range(saltsize)])

        if not HAS_PASSLIB:
            if sys.platform.startswith('darwin'):
                raise AnsibleFilterError('|password_hash requires the passlib python module to generate password hashes on Mac OS X/Darwin')
            saltstring = "$%s$%s" % (cryptmethod[hashtype], salt)
            encrypted = crypt.crypt(password, saltstring)
        else:
            if hashtype == 'blowfish':
                cls = passlib.hash.bcrypt
            else:
                cls = getattr(passlib.hash, '%s_crypt' % hashtype)

            encrypted = cls.encrypt(password, salt=salt)

        return encrypted

    return None


def to_uuid(string):
    return str(uuid.uuid5(UUID_NAMESPACE_ANSIBLE, str(string)))


def mandatory(a):
    from jinja2.runtime import Undefined

    ''' Make a variable mandatory '''
    if isinstance(a, Undefined):
        raise AnsibleFilterError('Mandatory variable not defined.')
    return a


def combine(*terms, **kwargs):
    recursive = kwargs.get('recursive', False)
    if len(kwargs) > 1 or (len(kwargs) == 1 and 'recursive' not in kwargs):
        raise AnsibleFilterError("'recursive' is the only valid keyword argument")

    dicts = []
    for t in terms:
        if isinstance(t, MutableMapping):
            dicts.append(t)
        elif isinstance(t, list):
            dicts.append(combine(*t, **kwargs))
        else:
            raise AnsibleFilterError("|combine expects dictionaries, got " + repr(t))

    if recursive:
        return reduce(merge_hash, dicts)
    else:
        return dict(itertools.chain(*map(iteritems, dicts)))


def comment(text, style='plain', **kw):
    # Predefined comment types
    comment_styles = {
        'plain': {
            'decoration': '# '
        },
        'erlang': {
            'decoration': '% '
        },
        'c': {
            'decoration': '// '
        },
        'cblock': {
            'beginning': '/*',
            'decoration': ' * ',
            'end': ' */'
        },
        'xml': {
            'beginning': '<!--',
            'decoration': ' - ',
            'end': '-->'
        }
    }

    # Pointer to the right comment type
    style_params = comment_styles[style]

    if 'decoration' in kw:
        prepostfix = kw['decoration']
    else:
        prepostfix = style_params['decoration']

    # Default params
    p = {
        'newline': '\n',
        'beginning': '',
        'prefix': (prepostfix).rstrip(),
        'prefix_count': 1,
        'decoration': '',
        'postfix': (prepostfix).rstrip(),
        'postfix_count': 1,
        'end': ''
    }

    # Update default params
    p.update(style_params)
    p.update(kw)

    # Compose substrings for the final string
    str_beginning = ''
    if p['beginning']:
        str_beginning = "%s%s" % (p['beginning'], p['newline'])
    str_prefix = ''
    if p['prefix']:
        if p['prefix'] != p['newline']:
            str_prefix = str(
                "%s%s" % (p['prefix'], p['newline'])) * int(p['prefix_count'])
        else:
            str_prefix = str(
                "%s" % (p['newline'])) * int(p['prefix_count'])
    str_text = ("%s%s" % (
        p['decoration'],
        # Prepend each line of the text with the decorator
        text.replace(
            p['newline'], "%s%s" % (p['newline'], p['decoration'])))).replace(
                # Remove trailing spaces when only decorator is on the line
                "%s%s" % (p['decoration'], p['newline']),
                "%s%s" % (p['decoration'].rstrip(), p['newline']))
    str_postfix = p['newline'].join(
        [''] + [p['postfix'] for x in range(p['postfix_count'])])
    str_end = ''
    if p['end']:
        str_end = "%s%s" % (p['newline'], p['end'])

    # Return the final string
    return "%s%s%s%s%s" % (
        str_beginning,
        str_prefix,
        str_text,
        str_postfix,
        str_end)


def extract(item, container, morekeys=None):
    from jinja2.runtime import Undefined

    value = container[item]

    if value is not Undefined and morekeys is not None:
        if not isinstance(morekeys, list):
            morekeys = [morekeys]

        try:
            value = reduce(lambda d, k: d[k], morekeys, value)
        except KeyError:
            value = Undefined()

    return value


@environmentfilter
def do_groupby(environment, value, attribute):
    """Overridden groupby filter for jinja2, to address an issue with
    jinja2>=2.9.0,<2.9.5 where a namedtuple was returned which
    has repr that prevents ansible.template.safe_eval.safe_eval from being
    able to parse and eval the data.

    jinja2<2.9.0,>=2.9.5 is not affected, as <2.9.0 uses a tuple, and
    >=2.9.5 uses a standard tuple repr on the namedtuple.

    The adaptation here, is to run the jinja2 `do_groupby` function, and
    cast all of the namedtuples to a regular tuple.

    See https://github.com/ansible/ansible/issues/20098

    We may be able to remove this in the future.
    """
    return [tuple(t) for t in _do_groupby(environment, value, attribute)]


def b64encode(string, encoding='utf-8'):
    return to_text(base64.b64encode(to_bytes(string, encoding=encoding, errors='surrogate_or_strict')))


def b64decode(string, encoding='utf-8'):
    return to_text(base64.b64decode(to_bytes(string, errors='surrogate_or_strict')), encoding=encoding)


def flatten(mylist, levels=None):

    ret = []
    for element in mylist:
        if element in (None, 'None', 'null'):
            # ignore undefined items
            break
        elif isinstance(element, MutableSequence):
            if levels is None:
                ret.extend(flatten(element))
            elif levels >= 1:
                levels = int(levels) - 1
                ret.extend(flatten(element, levels=levels))
            else:
                ret.append(element)
        else:
            ret.append(element)

    return ret


def dict_to_list_of_dict_key_value_elements(mydict):
    ''' takes a dictionary and transforms it into a list of dictionaries,
        with each having a 'key' and 'value' keys that correspond to the keys and values of the original '''

    if not isinstance(mydict, MutableMapping):
        raise AnsibleFilterError("dict2items requires a dictionary, got %s instead." % type(mydict))

    ret = []
    for key in mydict:
        ret.append({'key': key, 'value': mydict[key]})
    return ret


class FilterModule(object):
    ''' Ansible core jinja2 filters '''

    def filters(self):
        return {
            # jinja2 overrides
            'groupby': do_groupby,

            # base 64
            'b64decode': b64decode,
            'b64encode': b64encode,

            # uuid
            'to_uuid': to_uuid,

            # json
            'to_json': to_json,
            'to_nice_json': to_nice_json,
            'from_json': json.loads,

            # yaml
            'to_yaml': to_yaml,
            'to_nice_yaml': to_nice_yaml,
            'from_yaml': from_yaml,

            # path
            'basename': partial(unicode_wrap, os.path.basename),
            'dirname': partial(unicode_wrap, os.path.dirname),
            'expanduser': partial(unicode_wrap, os.path.expanduser),
            'expandvars': partial(unicode_wrap, os.path.expandvars),
            'realpath': partial(unicode_wrap, os.path.realpath),
            'relpath': partial(unicode_wrap, os.path.relpath),
            'splitext': partial(unicode_wrap, os.path.splitext),
            'win_basename': partial(unicode_wrap, ntpath.basename),
            'win_dirname': partial(unicode_wrap, ntpath.dirname),
            'win_splitdrive': partial(unicode_wrap, ntpath.splitdrive),

            # file glob
            'fileglob': fileglob,

            # types
            'bool': to_bool,
            'to_datetime': to_datetime,

            # date formating
            'strftime': strftime,

            # quote string for shell usage
            'quote': quote,

            # hash filters
            # md5 hex digest of string
            'md5': md5s,
            # sha1 hex digeset of string
            'sha1': checksum_s,
            # checksum of string as used by ansible for checksumming files
            'checksum': checksum_s,
            # generic hashing
            'password_hash': get_encrypted_password,
            'hash': get_hash,

            # regex
            'regex_replace': regex_replace,
            'regex_escape': regex_escape,
            'regex_search': regex_search,
            'regex_findall': regex_findall,

            # ? : ;
            'ternary': ternary,

            # random stuff
            'random': rand,
            'shuffle': randomize_list,

            # undefined
            'mandatory': mandatory,

            # comment-style decoration
            'comment': comment,

            # debug
            'type_debug': lambda o: o.__class__.__name__,

            # Data structures
            'combine': combine,
            'extract': extract,
            'flatten': flatten,
            'dict2items': dict_to_list_of_dict_key_value_elements,
        }
