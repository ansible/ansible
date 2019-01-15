# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, Bojan Vitnik <bvitnik@mainstream.rs>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


import sys
import importlib
import pytest

sys.modules['XenAPI'] = importlib.import_module('units.modules.cloud.xenserver.FakeXenAPI')
import XenAPI
