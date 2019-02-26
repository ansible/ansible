"""."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type


from ..six import BytesIO, PY2

if PY2:
    class BytesIO(BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.close()
