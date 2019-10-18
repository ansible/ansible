# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

"""
This file contains common code for building ansible. If you want to use code from here at runtime,
it needs to be moved out of this file and the implementation looked over to figure out whether API
should be changed before being made public.
"""

import os.path


def update_file_if_different(filename, b_data):
    '''
    Replace file content only if content is different.

    This preserves timestamps in case the file content has not changed.  It performs multiple
    operations on the file so it is not atomic and may be slower than simply writing to the file.

    :arg filename: The filename to write to
    :b_data: Byte string containing the data to write to the file
    '''
    try:
        with open(filename, 'rb') as f:
            b_data_old = f.read()
    except IOError as e:
        if e.errno != 2:
            raise
        # File did not exist, set b_data_old to a sentinel value so that
        # b_data gets written to the filename
        b_data_old = None

    if b_data_old != b_data:
        with open(filename, 'wb') as f:
            f.write(b_data)
        return True

    return False
