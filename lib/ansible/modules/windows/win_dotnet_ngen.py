#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Peter Mounce <public@neverrunwithscissors.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_dotnet_ngen
version_added: "2.0"
short_description: Runs ngen to recompile DLLs after .NET  updates
description:
    - After .NET framework is installed/updated, Windows will probably want to recompile things to optimise for the host.
    - This happens via scheduled task, usually at some inopportune time.
    - This module allows you to run this task on your own schedule, so you incur the CPU hit at some more convenient and controlled time.
    - U(http://blogs.msdn.com/b/dotnet/archive/2013/08/06/wondering-why-mscorsvw-exe-has-high-cpu-usage-you-can-speed-it-up.aspx)
notes:
    - There are in fact two scheduled tasks for ngen but they have no triggers so aren't a problem.
    - There's no way to test if they've been completed.
    - The stdout is quite likely to be several megabytes.
author:
- Peter Mounce (@petemounce)
options: {}
'''

EXAMPLES = r'''
- name: run ngen tasks
  win_dotnet_ngen:
'''

RETURN = r'''
dotnet_ngen_update_exit_code:
  description: The exit code after running the 32-bit ngen.exe update /force
    command.
  returned: 32-bit ngen executable exists
  type: int
  sample: 0
dotnet_ngen_update_output:
  description: The stdout after running the 32-bit ngen.exe update /force
    command.
  returned: 32-bit ngen executable exists
  type: str
  sample: sample output
dotnet_ngen_eqi_exit_code:
  description: The exit code after running the 32-bit ngen.exe
    executeQueuedItems command.
  returned: 32-bit ngen executable exists
  type: int
  sample: 0
dotnet_ngen_eqi_output:
  description: The stdout after running the 32-bit ngen.exe executeQueuedItems
    command.
  returned: 32-bit ngen executable exists
  type: str
  sample: sample output
dotnet_ngen64_update_exit_code:
  description: The exit code after running the 64-bit ngen.exe update /force
    command.
  returned: 64-bit ngen executable exists
  type: int
  sample: 0
dotnet_ngen64_update_output:
  description: The stdout after running the 64-bit ngen.exe update /force
    command.
  returned: 64-bit ngen executable exists
  type: str
  sample: sample output
dotnet_ngen64_eqi_exit_code:
  description: The exit code after running the 64-bit ngen.exe
    executeQueuedItems command.
  returned: 64-bit ngen executable exists
  type: int
  sample: 0
dotnet_ngen64_eqi_output:
  description: The stdout after running the 64-bit ngen.exe executeQueuedItems
    command.
  returned: 64-bit ngen executable exists
  type: str
  sample: sample output
'''
