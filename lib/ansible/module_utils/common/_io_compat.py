"""Compat shim for BytesIO."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type


from ansible.module_utils.six import BytesIO


if not hasattr(BytesIO, '__enter__') or not hasattr(BytesIO, '__exit__'):
    class BytesIO(BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.close()
