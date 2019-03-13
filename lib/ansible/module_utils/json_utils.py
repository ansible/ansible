# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

import datetime
from itertools import repeat
import json

from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.module_utils.common._collections_compat import Set
from ansible.module_utils.six import (
    binary_type,
    iteritems,
    text_type,
)


# NB: a copy of this function exists in ../../modules/core/async_wrapper.py. Ensure any
# changes are propagated there.
def _filter_non_json_lines(data):
    '''
    Used to filter unrelated output around module JSON output, like messages from
    tcagetattr, or where dropbear spews MOTD on every single command (which is nuts).

    Filters leading lines before first line-starting occurrence of '{' or '[', and filter all
    trailing lines after matching close character (working from the bottom of output).
    '''
    warnings = []

    # Filter initial junk
    lines = data.splitlines()

    for start, line in enumerate(lines):
        line = line.strip()
        if line.startswith(u'{'):
            endchar = u'}'
            break
        elif line.startswith(u'['):
            endchar = u']'
            break
    else:
        raise ValueError('No start of json char found')

    # Filter trailing junk
    lines = lines[start:]

    for reverse_end_offset, line in enumerate(reversed(lines)):
        if line.strip().endswith(endchar):
            break
    else:
        raise ValueError('No end of json char found')

    if reverse_end_offset > 0:
        # Trailing junk is uncommon and can point to things the user might
        # want to change.  So print a warning if we find any
        trailing_junk = lines[len(lines) - reverse_end_offset:]
        for line in trailing_junk:
            if line.strip():
                warnings.append('Module invocation had junk after the JSON data: %s' % '\n'.join(trailing_junk))
                break

    lines = lines[:(len(lines) - reverse_end_offset)]

    return ('\n'.join(lines), warnings)


def _json_encode_fallback(obj):
    if isinstance(obj, Set):
        return list(obj)
    elif isinstance(obj, datetime.datetime):
        return obj.isoformat()
    raise TypeError("Cannot json serialize %s" % to_native(obj))


def jsonify(data, **kwargs):
    for encoding in ("utf-8", "latin-1"):
        try:
            return json.dumps(data, encoding=encoding, default=_json_encode_fallback, **kwargs)
        # Old systems using old simplejson module does not support encoding keyword.
        except TypeError:
            try:
                new_data = json_dict_bytes_to_unicode(data, encoding=encoding)
            except UnicodeDecodeError:
                continue
            return json.dumps(new_data, default=_json_encode_fallback, **kwargs)
        except UnicodeDecodeError:
            continue
    raise UnicodeError('Invalid unicode encoding encountered')


def json_dict_unicode_to_bytes(d, encoding='utf-8', errors='surrogate_or_strict'):
    ''' Recursively convert dict keys and values to byte str

        Specialized for json return because this only handles, lists, tuples,
        and dict container types (the containers that the json module returns)
    '''

    if isinstance(d, text_type):
        return to_bytes(d, encoding=encoding, errors=errors)
    elif isinstance(d, dict):
        return dict(map(json_dict_unicode_to_bytes, iteritems(d), repeat(encoding), repeat(errors)))
    elif isinstance(d, list):
        return list(map(json_dict_unicode_to_bytes, d, repeat(encoding), repeat(errors)))
    elif isinstance(d, tuple):
        return tuple(map(json_dict_unicode_to_bytes, d, repeat(encoding), repeat(errors)))
    else:
        return d


def json_dict_bytes_to_unicode(d, encoding='utf-8', errors='surrogate_or_strict'):
    """Recursively convert dict keys and values to byte str

    Specialized for json return because this only handles, lists, tuples,
    and dict container types (the containers that the json module returns)
    """

    if isinstance(d, binary_type):
        # Warning, can traceback
        return to_text(d, encoding=encoding, errors=errors)
    elif isinstance(d, dict):
        return dict(map(json_dict_bytes_to_unicode, iteritems(d), repeat(encoding), repeat(errors)))
    elif isinstance(d, list):
        return list(map(json_dict_bytes_to_unicode, d, repeat(encoding), repeat(errors)))
    elif isinstance(d, tuple):
        return tuple(map(json_dict_bytes_to_unicode, d, repeat(encoding), repeat(errors)))
    else:
        return d
