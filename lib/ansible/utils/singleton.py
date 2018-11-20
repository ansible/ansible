# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class Singleton(type):
    """Metaclass for classes that wish to implement Singleton
    functionality.  If an instance of the class exists, it's returned,
    otherwise a single instance is instantiated and returned.
    """
    def __init__(self, name, bases, dct):
        super(Singleton, self).__init__(name, bases, dct)
        self.__instance = None

    def __call__(self, *args, **kw):
        if self.__instance is None:
            self.__instance = super(Singleton, self).__call__(*args, **kw)
        return self.__instance
