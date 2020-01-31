#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

