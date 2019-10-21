# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.facts.network import fc_wwn
from units.compat.mock import Mock


# AIX lsdev
LSDEV_OUTPUT = """
fcs0 Defined   00-00 8Gb PCI Express Dual Port FC Adapter (df1000f114108a03)
fcs1 Available 04-00 8Gb PCI Express Dual Port FC Adapter (df1000f114108a03)
"""

# a bit cutted output of lscfg (from Z0 to ZC)
LSCFG_OUTPUT = """
  fcs1             U78CB.001.WZS00ZS-P1-C9-T1  8Gb PCI Express Dual Port FC Adapter (df1000f114108a03)

        Part Number.................00E0806
        Serial Number...............1C4090830F
        Manufacturer................001C
        EC Level.................... D77161
        Customer Card ID Number.....577D
        FRU Number..................00E0806
        Device Specific.(ZM)........3
        Network Address.............10000090FA551508
        ROS Level and ID............027820B7
        Device Specific.(Z0)........31004549
        Device Specific.(ZC)........00000000
        Hardware Location Code......U78CB.001.WZS00ZS-P1-C9-T1
"""

# Solaris
FCINFO_OUTPUT = """
HBA Port WWN: 10000090fa1658de
        Port Mode: Initiator
        Port ID: 30100
        OS Device Name: /dev/cfg/c13
        Manufacturer: Emulex
        Model: LPe12002-S
        Firmware Version: LPe12002-S 2.01a12
        FCode/BIOS Version: Boot:5.03a0 Fcode:3.01a1
        Serial Number: 4925381+13090001ER
        Driver Name: emlxs
        Driver Version: 3.3.00.1 (2018.01.05.16.30)
        Type: N-port
        State: online
        Supported Speeds: 2Gb 4Gb 8Gb
        Current Speed: 8Gb
        Node WWN: 20000090fa1658de
        NPIV Not Supported
"""


def mock_get_bin_path(cmd, required=False):
    result = None
    if cmd == 'lsdev':
        result = '/usr/sbin/lsdev'
    elif cmd == 'lscfg':
        result = '/usr/sbin/lscfg'
    elif cmd == 'fcinfo':
        result = '/usr/sbin/fcinfo'
    return result


def mock_run_command(cmd):
    rc = 0
    if 'lsdev' in cmd:
        result = LSDEV_OUTPUT
    elif 'lscfg' in cmd:
        result = LSCFG_OUTPUT
    elif 'fcinfo' in cmd:
        result = FCINFO_OUTPUT
    else:
        rc = 1
        result = 'Error'
    return (rc, result, '')


def test_get_fc_wwn_info(mocker):
    module = Mock()
    inst = fc_wwn.FcWwnInitiatorFactCollector()

    mocker.patch.object(module, 'get_bin_path', side_effect=mock_get_bin_path)
    mocker.patch.object(module, 'run_command', side_effect=mock_run_command)

    d = {'aix6': ['10000090FA551508'], 'sunos5': ['10000090fa1658de']}
    for key, value in d.items():
        mocker.patch('sys.platform', key)
        wwn_expected = {"fibre_channel_wwn": value}
        assert wwn_expected == inst.collect(module=module)
