# -*- coding: utf-8 -*-
#
# (c) 2018, Toshio Kuratomi <a.badger@gmail.com>
# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import os

from ansible.utils.display import Display


display = Display()


def __getattr__(name):
    if name != 'environ':
        raise AttributeError(name)

    display.deprecated(
        msg='`ansible.utils.py3compat.environ` is deprecated.',
        version='2.20',
        help_text='Use `os.environ` from the Python standard library instead.',
    )

    return os.environ
