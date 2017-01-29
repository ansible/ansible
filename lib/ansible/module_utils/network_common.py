# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# (c) 2016 Red Hat Inc.
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
from socket import inet_aton, inet_ntoa
from struct import pack

from ansible.module_utils.basic import AnsibleFallbackNotFound
from ansible.module_utils.six import iteritems
from ansible.module_utils.six.moves import zip


def to_list(val):
    if isinstance(val, (list, tuple, set)):
        return list(val)
    elif val is not None:
        return [val]
    else:
        return list()


class ComplexDict(object):
    """Transforms a dict to with an argument spec

    This class will take a dict and apply an Ansible argument spec to the
    values.  The resulting dict will contain all of the keys in the param
    with appropriate values set.

    Example::

        argument_spec = dict(
            command=dict(key=True),
            display=dict(default='text', choices=['text', 'json']),
            validate=dict(type='bool')
        )
        transform = ComplexDict(argument_spec, module)
        value = dict(command='foo')
        result = transform(value)
        print result
        {'command': 'foo', 'display': 'text', 'validate': None}

    Supported argument spec:
        * key - specifies how to map a single value to a dict
        * read_from - read and apply the argument_spec from the module
        * required - a value is required
        * type - type of value (uses AnsibleModule type checker)
        * fallback - implements fallback function
        * choices - set of valid options
        * default - default value

    """

    def __init__(self, attrs, module):
        self._attributes = attrs
        self._module = module
        self.attr_names = frozenset(self._attributes.keys())

        self._has_key = False
        for name, attr in iteritems(self._attributes):
            if attr.get('read_from'):
                spec = self._module.argument_spec.get(attr['read_from'])
                if not spec:
                    raise ValueError('argument_spec %s does not exist' %  attr['read_from'])
                for key, value in iteritems(spec):
                    if key not in attr:
                        attr[key] = value

            if attr.get('key'):
                if self._has_key:
                    raise ValueError('only one key value can be specified')
                self_has_key = True
                attr['required'] = True


    def _dict(self, value):
        obj = {}
        for name, attr in iteritems(self._attributes):
            if attr.get('key'):
                obj[name] = value
            else:
                obj[name] = attr.get('default')
        return obj

    def __call__(self, value):
        if not isinstance(value, dict):
            value = self._dict(value)

        unknown = set(value).difference(self.attr_names)
        if unknown:
            raise ValueError('invalid keys: %s' % ','.join(unknown))

        for name, attr in iteritems(self._attributes):
            if not value.get(name):
                value[name] = attr.get('default')

            if attr.get('fallback') and not value.get(name):
                fallback = attr.get('fallback', (None,))
                fallback_strategy = fallback[0]
                fallback_args = []
                fallback_kwargs = {}
                if fallback_strategy is not None:
                    for item in fallback[1:]:
                        if isinstance(item, dict):
                            fallback_kwargs = item
                        else:
                            fallback_args = item
                    try:
                        value[name] = fallback_strategy(*fallback_args, **fallback_kwargs)
                    except AnsibleFallbackNotFound:
                        continue

            if attr.get('required') and value.get(name) is None:
                raise ValueError('missing required attribute %s' % name)

            if 'choices' in attr:
                if value[name] not in attr['choices']:
                    raise ValueError('%s must be one of %s, got %s' % \
                            (name, ', '.join(attr['choices']), value[name]))

            if value[name] is not None:
                value_type = attr.get('type', 'str')
                type_checker = self._module._CHECK_ARGUMENT_TYPES_DISPATCHER[value_type]
                type_checker(value[name])

        return value

class ComplexList(ComplexDict):
    """Extends ```ComplexDict``` to handle a  list of dicts """

    def __call__(self, values):
        if not isinstance(values, (list, tuple)):
            raise TypeError('value must be an ordered iterable')
        return [(super(ComplexList, self).__call__(v)) for v in values]

valid_masks = [2**8-2**i for i in range(0, 9)]

def is_netmask(val):
    parts = str(val).split('.')
    if not len(parts) == 4:
        return False
    for part in parts:
        try:
            if int(part) not in valid_masks:
                raise ValueError
        except ValueError:
            return False
    return True

def is_masklen(val):
    try:
        return 0 <= int(val) <= 32
    except ValueError:
        return False

def to_bits(val):
    """ converts a netmask to bits """
    bits = ''
    for octet in val.split('.'):
        bits += bin(int(octet))[2:].zfill(8)
    return str

def to_netmask(val):
    """ converts a masklen to a netmask """
    if not is_masklen(val):
        raise ValueError('invalid value for masklen')

    bits = 0
    for i in range(32 - int(val), 32):
        bits |= (1 << i)

    return inet_ntoa(pack('>I', bits))

def to_masklen(val):
    """ converts a netmask to a masklen """
    if not is_netmask(val):
        raise ValueError('invalid value for netmask: %s' % val)

    bits = list()
    for x in val.split('.'):
        octet = bin(int(x)).count('1')
        bits.append(octet)

    return sum(bits)

def to_subnet(addr, mask, dotted_notation=False):
    """ coverts an addr / mask pair to a subnet in cidr notation """
    try:
        if not is_masklen(mask):
            raise ValueError
        cidr = int(mask)
        mask = to_netmask(mask)
    except ValueError:
        cidr = to_masklen(mask)

    addr = addr.split('.')
    mask = mask.split('.')

    network = list()
    for s_addr, s_mask in zip(addr, mask):
        network.append(str(int(s_addr) & int(s_mask)))

    if dotted_notation:
        return '%s %s' % ('.'.join(network), to_netmask(cidr))
    return '%s/%s' % ('.'.join(network), cidr)


