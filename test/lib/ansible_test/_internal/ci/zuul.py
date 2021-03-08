"""Support code for working without a supported CI provider."""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import getpass
import hashlib
import random
import platform


from . import (
    CIProvider,
)

from .local import Local


CODE = "zuul"


class Zuul(Local):
    """CI provider implementation for Zuul-CI."""
    priority = CIProvider.priority

    @staticmethod
    def is_supported():  # type: () -> bool
        """Return True if this provider is supported in the current running environment."""
        return getpass.getuser() == "zuul"

    @property
    def code(self):  # type: () -> str
        """Return a unique code representing this provider."""
        return CODE

    @property
    def name(self):  # type: () -> str
        """Return descriptive name for this provider."""
        return "Zuul"

    def generate_resource_prefix(self):  # type: () -> str
        """Return a resource prefix specific to this CI provider."""
        node = hashlib.md5(platform.node().encode()).hexdigest()

        prefix = "ansible-test-%s-%d" % (node, random.randint(10000000, 99999999))

        return prefix
