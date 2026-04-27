#!/usr/bin/python
from __future__ import annotations


DOCUMENTATION = r"""
name: double_doc
description:
    - module also uses 'DOCUMENTATION' in class
"""


class Foo:

    # 2nd ref to documentation string, used to trip up tokinzer doc reader
    DOCUMENTATION = None

    def __init__(self):
        pass
