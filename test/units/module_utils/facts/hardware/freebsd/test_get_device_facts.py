# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import json
import os
import pathlib

from ansible.module_utils.facts.hardware import freebsd


def test_get_device_facts(monkeypatch):
    fixtures = pathlib.Path(__file__).parent / 'fixtures'
    dev_dir = (fixtures / 'devices').read_text().split()
    expected_dev_dir = json.load(open(fixtures / 'expected_devices', 'r'))

    monkeypatch.setattr(os.path, 'isdir', lambda x: True)
    monkeypatch.setattr(os, 'listdir', lambda x: dev_dir)

    freebsd_hardware = freebsd.FreeBSDHardware(None)
    facts = freebsd_hardware.get_device_facts()
    assert facts == expected_dev_dir
