# Copyright (c) 2013-2023, Graham Dumpleton
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

# copied from https://github.com/GrahamDumpleton/wrapt/blob/1.17.2/src/wrapt/wrappers.py

# LOCAL PATCHES:
# - disabled optional relative import of the _wrappers C extension; we shouldn't need it

from __future__ import annotations

# The following makes it easier for us to script updates of the bundled code
_BUNDLED_METADATA = {"pypi_name": "wrapt", "version": "1.17.2"}

import sys
import operator
import inspect

PY2 = sys.version_info[0] == 2

if PY2:
    string_types = basestring,
else:
    string_types = str,

def with_metaclass(meta, *bases):
    """Create a base class with a metaclass."""
    return meta("NewBase", bases, {})

class _ObjectProxyMethods(object):

    # We use properties to override the values of __module__ and
    # __doc__. If we add these in ObjectProxy, the derived class
    # __dict__ will still be setup to have string variants of these
    # attributes and the rules of descriptors means that they appear to
    # take precedence over the properties in the base class. To avoid
    # that, we copy the properties into the derived class type itself
    # via a meta class. In that way the properties will always take
    # precedence.

    @property
    def __module__(self):
        return self.__wrapped__.__module__

    @__module__.setter
    def __module__(self, value):
        self.__wrapped__.__module__ = value

    @property
    def __doc__(self):
        return self.__wrapped__.__doc__

    @__doc__.setter
    def __doc__(self, value):
        self.__wrapped__.__doc__ = value

    # We similar use a property for __dict__. We need __dict__ to be
    # explicit to ensure that vars() works as expected.

    @property
    def __dict__(self):
        return self.__wrapped__.__dict__

    # Need to also propagate the special __weakref__ attribute for case
    # where decorating classes which will define this. If do not define
    # it and use a function like inspect.getmembers() on a decorator
    # class it will fail. This can't be in the derived classes.

    @property
    def __weakref__(self):
        return self.__wrapped__.__weakref__

class _ObjectProxyMetaType(type):
    def __new__(cls, name, bases, dictionary):
        # Copy our special properties into the class so that they
        # always take precedence over attributes of the same name added
        # during construction of a derived class. This is to save
        # duplicating the implementation for them in all derived classes.

        dictionary.update(vars(_ObjectProxyMethods))

        return type.__new__(cls, name, bases, dictionary)

class ObjectProxy(with_metaclass(_ObjectProxyMetaType)):

    __slots__ = '__wrapped__'

    def __init__(self, wrapped):
        object.__setattr__(self, '__wrapped__', wrapped)

        # Python 3.2+ has the __qualname__ attribute, but it does not
        # allow it to be overridden using a property and it must instead
        # be an actual string object instead.

        try:
            object.__setattr__(self, '__qualname__', wrapped.__qualname__)
        except AttributeError:
            pass

        # Python 3.10 onwards also does not allow itself to be overridden
        # using a property and it must instead be set explicitly.

        try:
            object.__setattr__(self, '__annotations__', wrapped.__annotations__)
        except AttributeError:
            pass

    def __self_setattr__(self, name, value):
        object.__setattr__(self, name, value)

    @property
    def __name__(self):
        return self.__wrapped__.__name__

    @__name__.setter
    def __name__(self, value):
        self.__wrapped__.__name__ = value

    @property
    def __class__(self):
        return self.__wrapped__.__class__

    @__class__.setter
    def __class__(self, value):
        self.__wrapped__.__class__ = value

    def __dir__(self):
        return dir(self.__wrapped__)

    def __str__(self):
        return str(self.__wrapped__)

    if not PY2:
        def __bytes__(self):
            return bytes(self.__wrapped__)

    def __repr__(self):
        return '<{} at 0x{:x} for {} at 0x{:x}>'.format(
                type(self).__name__, id(self),
                type(self.__wrapped__).__name__,
                id(self.__wrapped__))

    def __format__(self, format_spec):
        return format(self.__wrapped__, format_spec)

    def __reversed__(self):
        return reversed(self.__wrapped__)

    if not PY2:
        def __round__(self, ndigits=None):
            return round(self.__wrapped__, ndigits)

    if sys.hexversion >= 0x03070000:
        def __mro_entries__(self, bases):
            return (self.__wrapped__,)

    def __lt__(self, other):
        return self.__wrapped__ < other

    def __le__(self, other):
        return self.__wrapped__ <= other

    def __eq__(self, other):
        return self.__wrapped__ == other

    def __ne__(self, other):
        return self.__wrapped__ != other

    def __gt__(self, other):
        return self.__wrapped__ > other

    def __ge__(self, other):
        return self.__wrapped__ >= other

    def __hash__(self):
        return hash(self.__wrapped__)

    def __nonzero__(self):
        return bool(self.__wrapped__)

    def __bool__(self):
        return bool(self.__wrapped__)

    def __setattr__(self, name, value):
        if name.startswith('_self_'):
            object.__setattr__(self, name, value)

        elif name == '__wrapped__':
            object.__setattr__(self, name, value)
            try:
                object.__delattr__(self, '__qualname__')
            except AttributeError:
                pass
            try:
                object.__setattr__(self, '__qualname__', value.__qualname__)
            except AttributeError:
                pass
            try:
                object.__delattr__(self, '__annotations__')
            except AttributeError:
                pass
            try:
                object.__setattr__(self, '__annotations__', value.__annotations__)
            except AttributeError:
                pass

        elif name == '__qualname__':
            setattr(self.__wrapped__, name, value)
            object.__setattr__(self, name, value)

        elif name == '__annotations__':
            setattr(self.__wrapped__, name, value)
            object.__setattr__(self, name, value)

        elif hasattr(type(self), name):
            object.__setattr__(self, name, value)

        else:
            setattr(self.__wrapped__, name, value)

    def __getattr__(self, name):
        # If we are being to lookup '__wrapped__' then the
        # '__init__()' method cannot have been called.

        if name == '__wrapped__':
            raise ValueError('wrapper has not been initialised')

        return getattr(self.__wrapped__, name)

    def __delattr__(self, name):
        if name.startswith('_self_'):
            object.__delattr__(self, name)

        elif name == '__wrapped__':
            raise TypeError('__wrapped__ must be an object')

        elif name == '__qualname__':
            object.__delattr__(self, name)
            delattr(self.__wrapped__, name)

        elif hasattr(type(self), name):
            object.__delattr__(self, name)

        else:
            delattr(self.__wrapped__, name)

    def __add__(self, other):
        return self.__wrapped__ + other

    def __sub__(self, other):
        return self.__wrapped__ - other

    def __mul__(self, other):
        return self.__wrapped__ * other

    def __div__(self, other):
        return operator.div(self.__wrapped__, other)

    def __truediv__(self, other):
        return operator.truediv(self.__wrapped__, other)

    def __floordiv__(self, other):
        return self.__wrapped__ // other

    def __mod__(self, other):
        return self.__wrapped__ % other

    def __divmod__(self, other):
        return divmod(self.__wrapped__, other)

    def __pow__(self, other, *args):
        return pow(self.__wrapped__, other, *args)

    def __lshift__(self, other):
        return self.__wrapped__ << other

    def __rshift__(self, other):
        return self.__wrapped__ >> other

    def __and__(self, other):
        return self.__wrapped__ & other

    def __xor__(self, other):
        return self.__wrapped__ ^ other

    def __or__(self, other):
        return self.__wrapped__ | other

    def __radd__(self, other):
        return other + self.__wrapped__

    def __rsub__(self, other):
        return other - self.__wrapped__

    def __rmul__(self, other):
        return other * self.__wrapped__

    def __rdiv__(self, other):
        return operator.div(other, self.__wrapped__)

    def __rtruediv__(self, other):
        return operator.truediv(other, self.__wrapped__)

    def __rfloordiv__(self, other):
        return other // self.__wrapped__

    def __rmod__(self, other):
        return other % self.__wrapped__

    def __rdivmod__(self, other):
        return divmod(other, self.__wrapped__)

    def __rpow__(self, other, *args):
        return pow(other, self.__wrapped__, *args)

    def __rlshift__(self, other):
        return other << self.__wrapped__

    def __rrshift__(self, other):
        return other >> self.__wrapped__

    def __rand__(self, other):
        return other & self.__wrapped__

    def __rxor__(self, other):
        return other ^ self.__wrapped__

    def __ror__(self, other):
        return other | self.__wrapped__

    def __iadd__(self, other):
        self.__wrapped__ += other
        return self

    def __isub__(self, other):
        self.__wrapped__ -= other
        return self

    def __imul__(self, other):
        self.__wrapped__ *= other
        return self

    def __idiv__(self, other):
        self.__wrapped__ = operator.idiv(self.__wrapped__, other)
        return self

    def __itruediv__(self, other):
        self.__wrapped__ = operator.itruediv(self.__wrapped__, other)
        return self

    def __ifloordiv__(self, other):
        self.__wrapped__ //= other
        return self

    def __imod__(self, other):
        self.__wrapped__ %= other
        return self

    def __ipow__(self, other):
        self.__wrapped__ **= other
        return self

    def __ilshift__(self, other):
        self.__wrapped__ <<= other
        return self

    def __irshift__(self, other):
        self.__wrapped__ >>= other
        return self

    def __iand__(self, other):
        self.__wrapped__ &= other
        return self

    def __ixor__(self, other):
        self.__wrapped__ ^= other
        return self

    def __ior__(self, other):
        self.__wrapped__ |= other
        return self

    def __neg__(self):
        return -self.__wrapped__

    def __pos__(self):
        return +self.__wrapped__

    def __abs__(self):
        return abs(self.__wrapped__)

    def __invert__(self):
        return ~self.__wrapped__

    def __int__(self):
        return int(self.__wrapped__)

    def __long__(self):
        return long(self.__wrapped__)

    def __float__(self):
        return float(self.__wrapped__)

    def __complex__(self):
        return complex(self.__wrapped__)

    def __oct__(self):
        return oct(self.__wrapped__)

    def __hex__(self):
        return hex(self.__wrapped__)

    def __index__(self):
        return operator.index(self.__wrapped__)

    def __len__(self):
        return len(self.__wrapped__)

    def __contains__(self, value):
        return value in self.__wrapped__

    def __getitem__(self, key):
        return self.__wrapped__[key]

    def __setitem__(self, key, value):
        self.__wrapped__[key] = value

    def __delitem__(self, key):
        del self.__wrapped__[key]

    def __getslice__(self, i, j):
        return self.__wrapped__[i:j]

    def __setslice__(self, i, j, value):
        self.__wrapped__[i:j] = value

    def __delslice__(self, i, j):
        del self.__wrapped__[i:j]

    def __enter__(self):
        return self.__wrapped__.__enter__()

    def __exit__(self, *args, **kwargs):
        return self.__wrapped__.__exit__(*args, **kwargs)

    def __iter__(self):
        return iter(self.__wrapped__)

    def __copy__(self):
        raise NotImplementedError('object proxy must define __copy__()')

    def __deepcopy__(self, memo):
        raise NotImplementedError('object proxy must define __deepcopy__()')

    def __reduce__(self):
        raise NotImplementedError(
                'object proxy must define __reduce__()')

    def __reduce_ex__(self, protocol):
        raise NotImplementedError(
                'object proxy must define __reduce_ex__()')

class CallableObjectProxy(ObjectProxy):

    def __call__(*args, **kwargs):
        def _unpack_self(self, *args):
            return self, args

        self, args = _unpack_self(*args)

        return self.__wrapped__(*args, **kwargs)

class PartialCallableObjectProxy(ObjectProxy):

    def __init__(*args, **kwargs):
        def _unpack_self(self, *args):
            return self, args

        self, args = _unpack_self(*args)

        if len(args) < 1:
            raise TypeError('partial type takes at least one argument')

        wrapped, args = args[0], args[1:]

        if not callable(wrapped):
            raise TypeError('the first argument must be callable')

        super(PartialCallableObjectProxy, self).__init__(wrapped)

        self._self_args = args
        self._self_kwargs = kwargs

    def __call__(*args, **kwargs):
        def _unpack_self(self, *args):
            return self, args

        self, args = _unpack_self(*args)
    
        _args = self._self_args + args

        _kwargs = dict(self._self_kwargs)
        _kwargs.update(kwargs)

        return self.__wrapped__(*_args, **_kwargs)

class _FunctionWrapperBase(ObjectProxy):

    __slots__ = ('_self_instance', '_self_wrapper', '_self_enabled',
            '_self_binding', '_self_parent', '_self_owner')

    def __init__(self, wrapped, instance, wrapper, enabled=None,
            binding='callable', parent=None, owner=None):

        super(_FunctionWrapperBase, self).__init__(wrapped)

        object.__setattr__(self, '_self_instance', instance)
        object.__setattr__(self, '_self_wrapper', wrapper)
        object.__setattr__(self, '_self_enabled', enabled)
        object.__setattr__(self, '_self_binding', binding)
        object.__setattr__(self, '_self_parent', parent)
        object.__setattr__(self, '_self_owner', owner)

    def __get__(self, instance, owner):
        # This method is actually doing double duty for both unbound and bound
        # derived wrapper classes. It should possibly be broken up and the
        # distinct functionality moved into the derived classes. Can't do that
        # straight away due to some legacy code which is relying on it being
        # here in this base class.
        #
        # The distinguishing attribute which determines whether we are being
        # called in an unbound or bound wrapper is the parent attribute. If
        # binding has never occurred, then the parent will be None.
        #
        # First therefore, is if we are called in an unbound wrapper. In this
        # case we perform the binding.
        #
        # We have two special cases to worry about here. These are where we are
        # decorating a class or builtin function as neither provide a __get__()
        # method to call. In this case we simply return self.
        #
        # Note that we otherwise still do binding even if instance is None and
        # accessing an unbound instance method from a class. This is because we
        # need to be able to later detect that specific case as we will need to
        # extract the instance from the first argument of those passed in.

        if self._self_parent is None:
            # Technically can probably just check for existence of __get__ on
            # the wrapped object, but this is more explicit.

            if self._self_binding == 'builtin':
                return self

            if self._self_binding == "class":
                return self

            binder = getattr(self.__wrapped__, '__get__', None)

            if binder is None:
                return self

            descriptor =  binder(instance, owner)

            return self.__bound_function_wrapper__(descriptor, instance,
                    self._self_wrapper, self._self_enabled,
                    self._self_binding, self, owner)

        # Now we have the case of binding occurring a second time on what was
        # already a bound function. In this case we would usually return
        # ourselves again. This mirrors what Python does.
        #
        # The special case this time is where we were originally bound with an
        # instance of None and we were likely an instance method. In that case
        # we rebind against the original wrapped function from the parent again.

        if self._self_instance is None and self._self_binding in ('function', 'instancemethod', 'callable'):
            descriptor = self._self_parent.__wrapped__.__get__(
                    instance, owner)

            return self._self_parent.__bound_function_wrapper__(
                    descriptor, instance, self._self_wrapper,
                    self._self_enabled, self._self_binding,
                    self._self_parent, owner)

        return self

    def __call__(*args, **kwargs):
        def _unpack_self(self, *args):
            return self, args

        self, args = _unpack_self(*args)

        # If enabled has been specified, then evaluate it at this point
        # and if the wrapper is not to be executed, then simply return
        # the bound function rather than a bound wrapper for the bound
        # function. When evaluating enabled, if it is callable we call
        # it, otherwise we evaluate it as a boolean.

        if self._self_enabled is not None:
            if callable(self._self_enabled):
                if not self._self_enabled():
                    return self.__wrapped__(*args, **kwargs)
            elif not self._self_enabled:
                return self.__wrapped__(*args, **kwargs)

        # This can occur where initial function wrapper was applied to
        # a function that was already bound to an instance. In that case
        # we want to extract the instance from the function and use it.

        if self._self_binding in ('function', 'instancemethod', 'classmethod', 'callable'):
            if self._self_instance is None:
                instance = getattr(self.__wrapped__, '__self__', None)
                if instance is not None:
                    return self._self_wrapper(self.__wrapped__, instance,
                            args, kwargs)

        # This is generally invoked when the wrapped function is being
        # called as a normal function and is not bound to a class as an
        # instance method. This is also invoked in the case where the
        # wrapped function was a method, but this wrapper was in turn
        # wrapped using the staticmethod decorator.

        return self._self_wrapper(self.__wrapped__, self._self_instance,
                args, kwargs)

    def __set_name__(self, owner, name):
        # This is a special method use to supply information to
        # descriptors about what the name of variable in a class
        # definition is. Not wanting to add this to ObjectProxy as not
        # sure of broader implications of doing that. Thus restrict to
        # FunctionWrapper used by decorators.

        if hasattr(self.__wrapped__, "__set_name__"):
            self.__wrapped__.__set_name__(owner, name)

    def __instancecheck__(self, instance):
        # This is a special method used by isinstance() to make checks
        # instance of the `__wrapped__`.
        return isinstance(instance, self.__wrapped__)

    def __subclasscheck__(self, subclass):
        # This is a special method used by issubclass() to make checks
        # about inheritance of classes. We need to upwrap any object
        # proxy. Not wanting to add this to ObjectProxy as not sure of
        # broader implications of doing that. Thus restrict to
        # FunctionWrapper used by decorators.

        if hasattr(subclass, "__wrapped__"):
            return issubclass(subclass.__wrapped__, self.__wrapped__)
        else:
            return issubclass(subclass, self.__wrapped__)

class BoundFunctionWrapper(_FunctionWrapperBase):

    def __call__(*args, **kwargs):
        def _unpack_self(self, *args):
            return self, args

        self, args = _unpack_self(*args)

        # If enabled has been specified, then evaluate it at this point and if
        # the wrapper is not to be executed, then simply return the bound
        # function rather than a bound wrapper for the bound function. When
        # evaluating enabled, if it is callable we call it, otherwise we
        # evaluate it as a boolean.

        if self._self_enabled is not None:
            if callable(self._self_enabled):
                if not self._self_enabled():
                    return self.__wrapped__(*args, **kwargs)
            elif not self._self_enabled:
                return self.__wrapped__(*args, **kwargs)

        # We need to do things different depending on whether we are likely
        # wrapping an instance method vs a static method or class method.

        if self._self_binding == 'function':
            if self._self_instance is None and args:
                instance, newargs = args[0], args[1:]
                if isinstance(instance, self._self_owner):
                    wrapped = PartialCallableObjectProxy(self.__wrapped__, instance)
                    return self._self_wrapper(wrapped, instance, newargs, kwargs)

            return self._self_wrapper(self.__wrapped__, self._self_instance,
                    args, kwargs)

        elif self._self_binding == 'callable':
            if self._self_instance is None:
                # This situation can occur where someone is calling the
                # instancemethod via the class type and passing the instance as
                # the first argument. We need to shift the args before making
                # the call to the wrapper and effectively bind the instance to
                # the wrapped function using a partial so the wrapper doesn't
                # see anything as being different.

                if not args:
                    raise TypeError('missing 1 required positional argument')

                instance, args = args[0], args[1:]
                wrapped = PartialCallableObjectProxy(self.__wrapped__, instance)
                return self._self_wrapper(wrapped, instance, args, kwargs)

            return self._self_wrapper(self.__wrapped__, self._self_instance,
                    args, kwargs)

        else:
            # As in this case we would be dealing with a classmethod or
            # staticmethod, then _self_instance will only tell us whether
            # when calling the classmethod or staticmethod they did it via an
            # instance of the class it is bound to and not the case where
            # done by the class type itself. We thus ignore _self_instance
            # and use the __self__ attribute of the bound function instead.
            # For a classmethod, this means instance will be the class type
            # and for a staticmethod it will be None. This is probably the
            # more useful thing we can pass through even though we loose
            # knowledge of whether they were called on the instance vs the
            # class type, as it reflects what they have available in the
            # decoratored function.

            instance = getattr(self.__wrapped__, '__self__', None)

            return self._self_wrapper(self.__wrapped__, instance, args,
                    kwargs)

class FunctionWrapper(_FunctionWrapperBase):

    __bound_function_wrapper__ = BoundFunctionWrapper

    def __init__(self, wrapped, wrapper, enabled=None):
        # What it is we are wrapping here could be anything. We need to
        # try and detect specific cases though. In particular, we need
        # to detect when we are given something that is a method of a
        # class. Further, we need to know when it is likely an instance
        # method, as opposed to a class or static method. This can
        # become problematic though as there isn't strictly a fool proof
        # method of knowing.
        #
        # The situations we could encounter when wrapping a method are:
        #
        # 1. The wrapper is being applied as part of a decorator which
        # is a part of the class definition. In this case what we are
        # given is the raw unbound function, classmethod or staticmethod
        # wrapper objects.
        #
        # The problem here is that we will not know we are being applied
        # in the context of the class being set up. This becomes
        # important later for the case of an instance method, because in
        # that case we just see it as a raw function and can't
        # distinguish it from wrapping a normal function outside of
        # a class context.
        #
        # 2. The wrapper is being applied when performing monkey
        # patching of the class type afterwards and the method to be
        # wrapped was retrieved direct from the __dict__ of the class
        # type. This is effectively the same as (1) above.
        #
        # 3. The wrapper is being applied when performing monkey
        # patching of the class type afterwards and the method to be
        # wrapped was retrieved from the class type. In this case
        # binding will have been performed where the instance against
        # which the method is bound will be None at that point.
        #
        # This case is a problem because we can no longer tell if the
        # method was a static method, plus if using Python3, we cannot
        # tell if it was an instance method as the concept of an
        # unnbound method no longer exists.
        #
        # 4. The wrapper is being applied when performing monkey
        # patching of an instance of a class. In this case binding will
        # have been perfomed where the instance was not None.
        #
        # This case is a problem because we can no longer tell if the
        # method was a static method.
        #
        # Overall, the best we can do is look at the original type of the
        # object which was wrapped prior to any binding being done and
        # see if it is an instance of classmethod or staticmethod. In
        # the case where other decorators are between us and them, if
        # they do not propagate the __class__  attribute so that the
        # isinstance() checks works, then likely this will do the wrong
        # thing where classmethod and staticmethod are used.
        #
        # Since it is likely to be very rare that anyone even puts
        # decorators around classmethod and staticmethod, likelihood of
        # that being an issue is very small, so we accept it and suggest
        # that those other decorators be fixed. It is also only an issue
        # if a decorator wants to actually do things with the arguments.
        #
        # As to not being able to identify static methods properly, we
        # just hope that that isn't something people are going to want
        # to wrap, or if they do suggest they do it the correct way by
        # ensuring that it is decorated in the class definition itself,
        # or patch it in the __dict__ of the class type.
        #
        # So to get the best outcome we can, whenever we aren't sure what
        # it is, we label it as a 'callable'. If it was already bound and
        # that is rebound later, we assume that it will be an instance
        # method and try and cope with the possibility that the 'self'
        # argument it being passed as an explicit argument and shuffle
        # the arguments around to extract 'self' for use as the instance.

        binding = None

        if isinstance(wrapped, _FunctionWrapperBase):
            binding = wrapped._self_binding

        if not binding:
            if inspect.isbuiltin(wrapped):
                binding = 'builtin'

            elif inspect.isfunction(wrapped):
                binding = 'function'

            elif inspect.isclass(wrapped):
                binding = 'class'

            elif isinstance(wrapped, classmethod):
                binding = 'classmethod'

            elif isinstance(wrapped, staticmethod):
                binding = 'staticmethod'

            elif hasattr(wrapped, '__self__'):
                if inspect.isclass(wrapped.__self__):
                    binding = 'classmethod'
                elif inspect.ismethod(wrapped):
                    binding = 'instancemethod'
                else:
                    binding = 'callable'

            else:
                binding = 'callable'

        super(FunctionWrapper, self).__init__(wrapped, None, wrapper,
                enabled, binding)
