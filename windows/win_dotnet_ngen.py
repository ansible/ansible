#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Peter Mounce <public@neverrunwithscissors.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

DOCUMENTATION = '''
---
module: win_dotnet_ngen
version_added: "2.0"
short_description: Runs ngen to recompile DLLs after .NET  updates
description:
    - After .NET framework is installed/updated, Windows will probably want to recompile things to optimise for the host.
    - This happens via scheduled task, usually at some inopportune time.
    - This module allows you to run this task on your own schedule, so you incur the CPU hit at some more convenient and controlled time.
    - "http://blogs.msdn.com/b/dotnet/archive/2013/08/06/wondering-why-mscorsvw-exe-has-high-cpu-usage-you-can-speed-it-up.aspx"
notes:
    - there are in fact two scheduled tasks for ngen but they have no triggers so aren't a problem
    - there's no way to test if they've been completed (?)
    - the stdout is quite likely to be several megabytes
author: Peter Mounce
'''

EXAMPLES = '''
  # Run ngen tasks
  win_dotnet_ngen:
'''
