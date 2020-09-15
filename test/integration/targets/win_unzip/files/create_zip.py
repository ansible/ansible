#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys
import tempfile
import zipfile


def main():
    filename = b"caf\xc3\xa9.txt"

    with tempfile.NamedTemporaryFile() as temp:
        with open(temp.name, mode="wb") as fd:
            fd.write(filename)

        with open(sys.argv[1], mode="wb") as fd:
            with zipfile.ZipFile(fd, "w") as zip:
                zip.write(temp.name, filename.decode('utf-8'))


if __name__ == '__main__':
    main()
