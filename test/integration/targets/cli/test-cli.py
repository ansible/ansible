#!/usr/bin/env python
# Copyright (c) 2019 Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import os

import pexpect

os.environ['ANSIBLE_NOCOLOR'] = '1'
out = pexpect.run(
    'ansible localhost -m debug -a msg="{{ ansible_password }}" -k',
    events={
        'SSH password:': '{{ 1 + 2 }}\n'
    }
)

assert b'{{ 1 + 2 }}' in out
