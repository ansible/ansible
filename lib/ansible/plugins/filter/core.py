# (c) 2012, Jeroen Hoekx <jeroen@hoekx.be>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import base64
import glob
import hashlib
import json
import ntpath
import os.path
import re
import sys
import time
import uuid
import yaml

import datetime
from functools import partial
from random import Random, SystemRandom, shuffle

from jinja2.filters import environmentfilter, do_groupby as _do_groupby

from ansible.errors import AnsibleError, AnsibleFilterError, AnsibleFilterTypeError
from ansible.module_utils.six import string_types, integer_types, reraise, text_type
from ansible.module_utils.six.moves import shlex_quote
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.module_utils.common.collections import is_sequence
from ansible.module_utils.common._collections_compat import Mapping
from ansible.module_utils.common.yaml import yaml_load, yaml_load_all
from ansible.parsing.ajson import AnsibleJSONEncoder
from ansible.parsing.yaml.dumper import AnsibleDumper
from ansible.template import AnsibleUndefined, recursive_check_defined
from ansible.utils.display import Display
from ansible.utils.encrypt import passlib_or_crypt
from ansible.utils.hashing import md5s, checksum_s
from ansible.utils.unicode import unicode_wrap
from ansible.utils.vars import merge_hash

display = Display()

UUID_NAMESPACE_ANSIBLE = uuid.UUID('361E6D51-FAEC-444A-9079-341386DA8E2E')


def to_yaml(a, *args, **kw):
    '''Make verbose, human readable yaml'''
    default_flow_style = kw.pop('default_flow_style', None)
    try:
        transformed = yaml.dump(a, Dumper=AnsibleDumper, allow_unicode=True, default_flow_style=default_flow_style, **kw)
    except Exception as e:
        raise AnsibleFilterError("to_yaml - %s" % to_native(e), orig_exc=e)
    return to_text(transformed)


def to_nice_yaml(a, indent=4, *args, **kw):
    '''Make verbose, human readable yaml'''
    try:
        transformed = yaml.dump(a, Dumper=AnsibleDumper, indent=indent, allow_unicode=True, default_flow_style=False, **kw)
    except Exception as e:
        raise AnsibleFilterError("to_nice_yaml - %s" % to_native(e), orig_exc=e)
    return to_text(transformed)


def to_json(a, *args, **kw):
    ''' Convert the value to JSON '''
    return json.dumps(a, cls=AnsibleJSONEncoder, *args, **kw)


def to_nice_json(a, indent=4, sort_keys=True, *args, **kw):
    '''Make verbose, human readable JSON'''
    return to_json(a, indent=indent, sort_keys=sort_keys, separators=(',', ': '), *args, **kw)


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
    ''' return a date string using string. See https://docs.python.org/3/library/time.html#time.strftime for format '''
    if second is not None:
        try:
            second = float(second)
        except Exception:
            raise AnsibleFilterError('Invalid value for epoch value (%s)' % second)
    return time.strftime(string_format, time.localtime(second))


def quote(a):
    ''' return its argument quoted for shell usage '''
    if a is None:
        a = u''
    return shlex_quote(to_text(a))


def fileglob(pathname):
    ''' return list of matched regular files for glob '''
    return [g for g in glob.glob(pathname) if os.path.isfile(g)]


def regex_replace(value='', pattern='', replacement='', ignorecase=False, multiline=False):
    ''' Perform a `re.sub` returning a string '''

    value = to_text(value, errors='surrogate_or_strict', nonstring='simplerepr')

    flags = 0
    if ignorecase:
        flags |= re.I
    if multiline:
        flags |= re.M
    _re = re.compile(pattern, flags=flags)
    return _re.sub(replacement, value)


def regex_findall(value, regex, multiline=False, ignorecase=False):
    ''' Perform re.findall and return the list of matches '''

    value = to_text(value, errors='surrogate_or_strict', nonstring='simplerepr')

    flags = 0
    if ignorecase:
        flags |= re.I
    if multiline:
        flags |= re.M
    return re.findall(regex, value, flags)


def regex_search(value, regex, *args, **kwargs):
    ''' Perform re.search and return the list of matches or a backref '''

    value = to_text(value, errors='surrogate_or_strict', nonstring='simplerepr')

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


def ternary(value, true_val, false_val, none_val=None):
    '''  value ? true_val : false_val '''
    if value is None and none_val is not None:
        return none_val
    elif bool(value):
        return true_val
    else:
        return false_val


def regex_escape(string, re_type='python'):
    string = to_text(string, errors='surrogate_or_strict', nonstring='simplerepr')
    '''Escape all regular expressions special characters from STRING.'''
    if re_type == 'python':
        return re.escape(string)
    elif re_type == 'posix_basic':
        # list of BRE special chars:
        # https://en.wikibooks.org/wiki/Regular_Expressions/POSIX_Basic_Regular_Expressions
        return regex_replace(string, r'([].[^$*\\])', r'\\\1')
    # TODO: implement posix_extended
    # It's similar to, but different from python regex, which is similar to,
    # but different from PCRE.  It's possible that re.escape would work here.
    # https://remram44.github.io/regex-cheatsheet/regex.html#programs
    elif re_type == 'posix_extended':
        raise AnsibleFilterError('Regex type (%s) not yet implemented' % re_type)
    else:
        raise AnsibleFilterError('Invalid regex type (%s)' % re_type)


def from_yaml(data):
    if isinstance(data, string_types):
        # The ``text_type`` call here strips any custom
        # string wrapper class, so that CSafeLoader can
        # read the data
        return yaml_load(text_type(to_text(data, errors='surrogate_or_strict')))
    return data


def from_yaml_all(data):
    if isinstance(data, string_types):
        # The ``text_type`` call here strips any custom
        # string wrapper class, so that CSafeLoader can
        # read the data
        return yaml_load_all(text_type(to_text(data, errors='surrogate_or_strict')))
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
        return r.randrange(start, end, step)
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
    try:
        h = hashlib.new(hashtype)
    except Exception as e:
        # hash is not supported?
        raise AnsibleFilterError(e)

    h.update(to_bytes(data, errors='surrogate_or_strict'))
    return h.hexdigest()


def get_encrypted_password(password, hashtype='sha512', salt=None, salt_size=None, rounds=None, ident=None):
    passlib_mapping = {
        'md5': 'md5_crypt',
        'blowfish': 'bcrypt',
        'sha256': 'sha256_crypt',
        'sha512': 'sha512_crypt',
    }

    hashtype = passlib_mapping.get(hashtype, hashtype)
    try:
        return passlib_or_crypt(password, hashtype, salt=salt, salt_size=salt_size, rounds=rounds, ident=ident)
    except AnsibleError as e:
        reraise(AnsibleFilterError, AnsibleFilterError(to_native(e), orig_exc=e), sys.exc_info()[2])


def to_uuid(string, namespace=UUID_NAMESPACE_ANSIBLE):
    uuid_namespace = namespace
    if not isinstance(uuid_namespace, uuid.UUID):
        try:
            uuid_namespace = uuid.UUID(namespace)
        except (AttributeError, ValueError) as e:
            raise AnsibleFilterError("Invalid value '%s' for 'namespace': %s" % (to_native(namespace), to_native(e)))
    # uuid.uuid5() requires bytes on Python 2 and bytes or text or Python 3
    return to_text(uuid.uuid5(uuid_namespace, to_native(string, errors='surrogate_or_strict')))


def mandatory(a, msg=None):
    from jinja2.runtime import Undefined

    ''' Make a variable mandatory '''
    if isinstance(a, Undefined):
        if a._undefined_name is not None:
            name = "'%s' " % to_text(a._undefined_name)
        else:
            name = ''

        if msg is not None:
            raise AnsibleFilterError(to_native(msg))
        else:
            raise AnsibleFilterError("Mandatory variable %s not defined." % name)

    return a


def combine(*terms, **kwargs):
    recursive = kwargs.pop('recursive', False)
    list_merge = kwargs.pop('list_merge', 'replace')
    if kwargs:
        raise AnsibleFilterError("'recursive' and 'list_merge' are the only valid keyword arguments")

    # allow the user to do `[dict1, dict2, ...] | combine`
    dictionaries = flatten(terms, levels=1)

    # recursively check that every elements are defined (for jinja2)
    recursive_check_defined(dictionaries)

    if not dictionaries:
        return {}

    if len(dictionaries) == 1:
        return dictionaries[0]

    # merge all the dicts so that the dict at the end of the array have precedence
    # over the dict at the beginning.
    # we merge the dicts from the highest to the lowest priority because there is
    # a huge probability that the lowest priority dict will be the biggest in size
    # (as the low prio dict will hold the "default" values and the others will be "patches")
    # and merge_hash create a copy of it's first argument.
    # so high/right -> low/left is more efficient than low/left -> high/right
    high_to_low_prio_dict_iterator = reversed(dictionaries)
    result = next(high_to_low_prio_dict_iterator)
    for dictionary in high_to_low_prio_dict_iterator:
        result = merge_hash(dictionary, result, recursive, list_merge)

    return result


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


@environmentfilter
def extract(environment, item, container, morekeys=None):
    if morekeys is None:
        keys = [item]
    elif isinstance(morekeys, list):
        keys = [item] + morekeys
    else:
        keys = [item, morekeys]

    value = container
    for key in keys:
        value = environment.getitem(value, key)

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


def flatten(mylist, levels=None, skip_nulls=True):

    ret = []
    for element in mylist:
        if skip_nulls and element in (None, 'None', 'null'):
            # ignore null items
            continue
        elif is_sequence(element):
            if levels is None:
                ret.extend(flatten(element, skip_nulls=skip_nulls))
            elif levels >= 1:
                # decrement as we go down the stack
                ret.extend(flatten(element, levels=(int(levels) - 1), skip_nulls=skip_nulls))
            else:
                ret.append(element)
        else:
            ret.append(element)

    return ret


def subelements(obj, subelements, skip_missing=False):
    '''Accepts a dict or list of dicts, and a dotted accessor and produces a product
    of the element and the results of the dotted accessor

    >>> obj = [{"name": "alice", "groups": ["wheel"], "authorized": ["/tmp/alice/onekey.pub"]}]
    >>> subelements(obj, 'groups')
    [({'name': 'alice', 'groups': ['wheel'], 'authorized': ['/tmp/alice/onekey.pub']}, 'wheel')]

    '''
    if isinstance(obj, dict):
        element_list = list(obj.values())
    elif isinstance(obj, list):
        element_list = obj[:]
    else:
        raise AnsibleFilterError('obj must be a list of dicts or a nested dict')

    if isinstance(subelements, list):
        subelement_list = subelements[:]
    elif isinstance(subelements, string_types):
        subelement_list = subelements.split('.')
    else:
        raise AnsibleFilterTypeError('subelements must be a list or a string')

    results = []

    for element in element_list:
        values = element
        for subelement in subelement_list:
            try:
                values = values[subelement]
            except KeyError:
                if skip_missing:
                    values = []
                    break
                raise AnsibleFilterError("could not find %r key in iterated item %r" % (subelement, values))
            except TypeError:
                raise AnsibleFilterTypeError("the key %s should point to a dictionary, got '%s'" % (subelement, values))
        if not isinstance(values, list):
            raise AnsibleFilterTypeError("the key %r should point to a list, got %r" % (subelement, values))

        for value in values:
            results.append((element, value))

    return results


def dict_to_list_of_dict_key_value_elements(mydict, key_name='key', value_name='value'):
    ''' takes a dictionary and transforms it into a list of dictionaries,
        with each having a 'key' and 'value' keys that correspond to the keys and values of the original '''

    if not isinstance(mydict, Mapping):
        raise AnsibleFilterTypeError("dict2items requires a dictionary, got %s instead." % type(mydict))

    ret = []
    for key in mydict:
        ret.append({key_name: key, value_name: mydict[key]})
    return ret


def list_of_dict_key_value_elements_to_dict(mylist, key_name='key', value_name='value'):
    ''' takes a list of dicts with each having a 'key' and 'value' keys, and transforms the list into a dictionary,
        effectively as the reverse of dict2items '''

    if not is_sequence(mylist):
        raise AnsibleFilterTypeError("items2dict requires a list, got %s instead." % type(mylist))

    return dict((item[key_name], item[value_name]) for item in mylist)


def path_join(paths):
    ''' takes a sequence or a string, and return a concatenation
        of the different members '''
    if isinstance(paths, string_types):
        return os.path.join(paths)
    elif is_sequence(paths):
        return os.path.join(*paths)
    else:
        raise AnsibleFilterTypeError("|path_join expects string or sequence, got %s instead." % type(paths))


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
            'from_yaml_all': from_yaml_all,

            # path
            'basename': partial(unicode_wrap, os.path.basename),
            'dirname': partial(unicode_wrap, os.path.dirname),
            'expanduser': partial(unicode_wrap, os.path.expanduser),
            'expandvars': partial(unicode_wrap, os.path.expandvars),
            'path_join': path_join,
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

            # date formatting
            'strftime': strftime,

            # quote string for shell usage
            'quote': quote,

            # hash filters
            # md5 hex digest of string
            'md5': md5s,
            # sha1 hex digest of string
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
            'items2dict': list_of_dict_key_value_elements_to_dict,
            'subelements': subelements,
            'split': partial(unicode_wrap, text_type.split),
        }
