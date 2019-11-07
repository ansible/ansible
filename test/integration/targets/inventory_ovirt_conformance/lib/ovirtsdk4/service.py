from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class Service(object):
    def __init__(self, connection, path):
        """
        Creates a new service that will use the given connection and path.
        """
        self._connection = connection
        self._path = path
