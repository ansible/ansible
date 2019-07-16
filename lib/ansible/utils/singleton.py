# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from threading import RLock


class Singleton(type):
    """Metaclass for classes that wish to implement Singleton
    functionality.  If an instance of the class exists, it's returned,
    otherwise a single instance is instantiated and returned.
    """
    def __init__(cls, name, bases, dct):
        super(Singleton, cls).__init__(name, bases, dct)
        cls.__instance = None
        cls.__rlock = RLock()

    def __call__(cls, *args, **kw):
        if cls.__instance is not None:
            return cls.__instance

        with cls.__rlock:
            if cls.__instance is None:
                cls.__instance = super(Singleton, cls).__call__(*args, **kw)

        return cls.__instance

    """Reset a singleton instance (mainly for unit tests to avoid
    reaching into the classobj directly)"""
    @staticmethod
    def clear(singleton_class):
        Singleton.assert_is_singleton(singleton_class)
        singleton_class.__instance = None

    """Force a singleton to a specific instance (mainly for unit tests
    to avoid reaching into the classobj directly)"""
    @staticmethod
    def set(singleton_class, obj):
        Singleton.assert_is_singleton(singleton_class)
        singleton_class.__instance = obj

    """Directly sample the singleton state without creating an instance
    (mainly for unit tests to avoid reaching into the classobj directly)"""
    @staticmethod
    def get(singleton_class):
        Singleton.assert_is_singleton(singleton_class)
        return singleton_class.__instance

    @staticmethod
    def assert_is_singleton(singleton_class):
        if not isinstance(singleton_class, Singleton):
            raise TypeError("{0} must be a Singleton type object")
