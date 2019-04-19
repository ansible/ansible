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

# Make coding more python3-ish
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import os
import sys
import pytest

from ansible.plugins.filter.genie import parse_genie, HAS_GENIE, HAS_PYATS


fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "network")

with open(os.path.join(fixture_path, "show_version.txt")) as f:
    show_version_text = f.read()

show_version_parsed = {
    "version": {
        "chassis": "CSR1000V",
        "chassis_sn": "9TKUWGKX5MO",
        "curr_config_register": "0x2102",
        "disks": {
            "bootflash:.": {
                "disk_size": "7774207",
                "type_of_disk": "virtual hard disk",
            },
            "webui:.": {"disk_size": "0", "type_of_disk": "WebUI ODM Files"},
        },
        "hostname": "host-172-16-1-96",
        "image_id": "X86_64_LINUX_IOSD-UNIVERSALK9-M",
        "image_type": "production image",
        "last_reload_reason": "Reload Command",
        "license_level": "ax",
        "license_type": "Default. No valid license found.",
        "main_mem": "1126522",
        "mem_size": {"non-volatile configuration": "32768", "physical": "3018840"},
        "next_reload_license_level": "ax",
        "number_of_intfs": {"Gigabit Ethernet": "2"},
        "os": "IOS-XE",
        "platform": "Virtual XE",
        "processor_type": "VXE",
        "rom": "IOS-XE ROMMON",
        "rtr_type": "CSR1000V",
        "system_image": "bootflash:packages.conf",
        "uptime": "2 minutes",
        "uptime_this_cp": "3 minutes",
        "version": "16.5.1b,",
        "version_short": "16.5",
    }
}

@pytest.mark.skipif(sys.version_info < (3, 4),
                    reason="Genie requires python3.4 or greater")
@pytest.mark.skipif(HAS_GENIE is False,
                    reason="Requires Genie package")
@pytest.mark.skipif(HAS_PYATS is False,
                    reason="Requires pyATS package")
def test_parse_genie():
    assert parse_genie(show_version_text, command="show version", os="iosxe") == show_version_parsed
