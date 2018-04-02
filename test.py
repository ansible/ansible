from __future__ import print_function

from collections import MutableMapping

try:
    from six import iteritems
except ImportError:
    iteritems = lambda d: d.iteritems()

def lift_methods(cls, abs_cls):
    bases = abs_cls.__bases__
    if 1 == len(bases):
        if not object == bases[0]:
            lift_methods(cls, bases[0])
    for k in vars(abs_cls):
        if hasattr(cls, k):
            continue
        v = getattr(abs_cls, k)
        if not callable(v):
            continue
        if v in getattr(abs_cls,'__abstractmethods__', ()):
            continue
        try:
            setattr(cls, k, v.__func__.__get__(None, cls))
            print("set %s" % k, v)
        except AttributeError:
            # method_descriptors: opaque objects
            pass


class DictMeta(MutableMapping.__metaclass__):
    def __new__(cls, name, bases, attrs):
        self = super(DictMeta, cls).__new__(
            cls, name, tuple(b for b in bases if b is not dict), attrs)
        return self

    # def __call__(cls, *args, **kwargs):
    #     self = super(DictMeta, cls).__call__(*args, **kwargs)
    #     self.__class__ = dict
    #     return self

class A_M(dict):
    __metaclass__ = DictMeta
    """
    Abstract immutable mapping that wraps a dict, transforming keys and values before
    returning them.

    Subclasses must provide a callable attribute `transform`, which will be called on
    values and keys before returning them. `transform` will NOT be called on keys that are
    passed in (i.e. We assume `hash(transform(key)) == hash(key)`)

    If an exception is raised in __getitem__, a KeyError is raised and KeyError.chained_from is set to the
    original exception.

    Exceptions raised in __iter__ propagate as is (you could conceivably use this to end iteration early).

    Implementations Details:
    - A cache is used to store transformed values (but not keys) on the assumption that value lookups
      are quite common (and that `transform` might be expensive for them). This means that `transform`
      should be idempotent and that you should not depend on it being called for every lookup.

    Known Uses:
    - AnsibleUnsafeDict: inherits from AnsibleUnsafe with `transform` set to `wrap_var`
    - template.AnsibleContext.dict_proxy: transform marks the Jinja Context as unsafe when an unsafe
                                          key or value is fetched. If the value is a dict, rewrap it.
    """
    __slots__ = ('wrapped_dict', '_cache')

    SENTINAL_NONE = object()
    @property
    def __class__(self):
        return self.wrapped_dict.__class__

    def __init__(self, d):
        if not self.transform:
            raise NotImplementedError('Subclasses of AnsibleDictProxy must specify a transform function.')
#
        if not isinstance(d, type(self)):
            self.wrapped_dict = d
        else:
            self.wrapped_dict = d.wrapped_dict
#
        self._cache = {}
#
    def __getitem__(self, key):
        # We expect a large number of misses, so use sentinel instead of try...except
        val = self._cache.get(key, self.SENTINAL_NONE)
        if val is not self.SENTINAL_NONE:
            return val
#
        try:
            print("Transform")
            val = self.transform(self.wrapped_dict[key])
            self._cache[key] = val
            print(val)
        except Exception as e:
            key_e = KeyError(key)
            key_e.chained_from = e
            raise key_e
        return val
#
    def __setitem__(self, key, val):
        self.wrapped_dict[key] = val
        self._cache[key] = val

    def __delitem__(self, key):
        del self.wrapped_dict[key]
        del self._cache[key]
#
    def __contains__(self, key):
        return self.wrapped_dict.__contains__(key)
#
    def __copy__(self):
        val = type(self)(self.wrapped_dict.copy())
        return val
#
    def copy(self):
        return self.__copy__()
#
    # WARNING: Resolve is potentially data-modifying
    def resolve(self):
        assert isinstance(self.wrapped_dict, dict)
        return self.transform(self.wrapped_dict, resolve=True)
#
    def __iter__(self):
        for k in iter(self.wrapped_dict):
            yield self.transform(k)
#
    def __len__(self):
        return len(self.wrapped_dict)
#
    def __str__(self):
        return '{{{contents}}}'.format(
            contents=', '.join('{key}: {val}'.format(key=repr(key), val=repr(val))
                               for key, val in iteritems(self)))
#
    def __unicode__(self):
        return text_type(self.__str__())

    def update(self, other):
        self._cache.update(other)
        self.wrapped_dict.update(other)
#
    def __repr__(self):
        return self.__str__()

    def __reduce_ex__(self, protocol):
        # for pickling; state is passed to __getstate__
        # -> (constructor, args, state)
        return (type(self), (self.wrapped_dict,), self._cache)

    def __setstate__(self, state):
        self._cache = state

    def __eq__(self, other):
        import operator
        if not isinstance(other, type(self)):
            # This makes the proxy mostly transparent
            # We might not always want this; perhaps a class-level flag?
            # AnsibleContext.dict_proxy should be transparent
            # AnsibleUnsafeDict probably shouldn't be (though this involves
            # fixing a few places that test for emptiness by comparing with `{}`)
            # Here's a quick list (mostly tests):
            #  - ./contrib/inventory/ec2.py
            #  - ./lib/ansible/module_utils/netscaler.py
            #  - ./lib/ansible/modules/network/netscaler/netscaler_lb_monitor.py
            #  - ./lib/ansible/utils/vars.py
            #  - ./test/integration/roles/test_consul_acl/tasks/create-acl-without-rules.yml
            #  - ./test/integration/roles/test_consul_acl/tasks/update-acl.yml
            #  - ./test/integration/roles/test_rax_facts/tasks/main.yml
            #  - ./test/integration/roles/test_rax_facts/tasks/main.yml
            #  - ./test/integration/roles/test_rax_facts/tasks/main.yml
            #  - ./test/integration/roles/test_rax_meta/tasks/main.yml
            #  - ./test/integration/roles/test_rax_meta/tasks/main.yml
            #  - ./test/integration/roles/test_rax_meta/tasks/main.yml
            #  - ./test/integration/roles/test_rax_meta/tasks/main.yml
            #  - ./test/integration/roles/test_rax_meta/tasks/main.yml
            #  - ./test/integration/roles/test_rax_meta/tasks/main.yml
            #  - ./test/integration/roles/test_rax_scaling_group/tasks/main.yml
            #  - ./test/integration/roles/test_rax_scaling_group/tasks/main.yml
            #  - ./test/integration/targets/rds_param_group/tasks/main.yml
            #  - ./test/integration/targets/xattr/tasks/test.yml
            #  - ./test/runner/import/lib/ansible/module_utils/netscaler.py
            #  - ./test/units/executor/module_common/test_recursive_finder.py
            #  - ./test/units/executor/module_common/test_recursive_finder.py
            #  - ./test/units/executor/module_common/test_recursive_finder.py
            #  - ./test/units/executor/module_common/test_recursive_finder.py
            #  - ./test/units/executor/module_common/test_recursive_finder.py
            #  - ./test/units/executor/module_common/test_recursive_finder.py
            #  - ./test/units/modules/cloud/amazon/test_ec2_vpc_vpn.py
            #  - ./test/units/modules/cloud/amazon/test_ec2_vpc_vpn.py
            if self.wrapped_dict == other:
                return True
            return False
        try:
            if self.wrapped_dict == other.wrapped_dict:
                return True

            if self.__slots__ == other.__slots__:
                for cls in self.mro():
                    attr_getters = (operator.attrgetter(attr) for attr in cls.__slots__)
                    if any(not getter(self) == getter(other) for getter in attr_getters):
                        return False
                return True
        except AttributeError:
            pass

        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    # def __setstate__(self):
    #     return self.__dict__
    #def __getstate__(self, state):

MutableMapping.register(A_M)
#lift_methods(A_M, dict)
lift_methods(A_M, MutableMapping)

class M(A_M):
    __slots__ = ()
    transform = staticmethod(lambda val: 7 if isinstance(val, int) else val)

m = M({'a': 1, 'b': 2, 'c': 3})
n = M(m)
k = m.copy()

d = {'a': 1, 'b': 2, 'c': 3}
print(d)
print(repr(d))
print(d.__str__())

print("Copy: %s" % (n == m))
print("Copy 2: %s" % (k == m))

print("Is Dict: %s" % isinstance(m, dict))

print("m: %s" % m)

print(m)

d_of_m = dict(m)
print("dict of m: %s" % d_of_m)
print(d_of_m == m)
print(m==d_of_m)
print(d_of_m == {'a': 7, 'b': 7, 'c': 7})

d = {'a': 'boop', 'boop': 3}
print("d: %s" % d)


d.update(m)
print("Updated %s" % d)
del d['boop']
del m['a']
print("Del a %s" % m)

#m.__class__ = MutableMapping
#print(A_M.__slots__, "\n\n\n")
# print(dir(m))
# print((A_M.__dict__))
# print(m.__class__)
# print(type(m))
# print(m.__class__.__bases__)
print(type(m).mro())

import pickle
p = pickle.dumps(m)
n = pickle.loads(p)
print(n == m)
print(n)
print(n.__class__)

#print(n.__dict__)

print(bool(m))
print(bool(M({})))
