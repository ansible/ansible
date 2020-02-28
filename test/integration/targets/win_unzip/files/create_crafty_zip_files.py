#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import os
import shutil
import sys
import zipfile

# Each key is a zip file and the vaule is the list of files that will be created
# and placed in the archive
zip_files = {
    'hat1': [r'hat/..\rabbit.txt'],
    'hat2': [r'hat/..\..\rabbit.txt'],
    'handcuffs': [r'..\..\houidini.txt'],
    'prison': [r'..\houidini.txt'],
}

# Accept an argument of where to create the files, defaulting to
# the current working directory.
try:
    output_dir = sys.argv[1]
except IndexError:
    output_dir = os.getcwd()

if not os.path.isdir(output_dir):
    os.mkdir(output_dir)

os.chdir(output_dir)

for name, files in zip_files.items():
    # Create the files to go in the zip archive
    for entry in files:
        dirname = os.path.dirname(entry)
        if dirname:
            if os.path.isdir(dirname):
                shutil.rmtree(dirname)
            os.mkdir(dirname)

        with open(entry, 'w') as e:
            e.write('escape!\n')

    # Create the zip archive with the files
    filename = '%s.zip' % name
    if os.path.isfile(filename):
        os.unlink(filename)

    with zipfile.ZipFile(filename, 'w') as zf:
        for entry in files:
            zf.write(entry)

    # Cleanup
    if dirname:
        shutil.rmtree(dirname)

    for entry in files:
        try:
            os.unlink(entry)
        except OSError:
            pass
