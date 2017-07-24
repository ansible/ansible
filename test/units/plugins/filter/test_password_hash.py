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
from __future__ import (absolute_import, division, print_function)

import pytest


__metaclass__ = type

from ansible.plugins.filter.core import get_encrypted_password
from ansible import errors


def test_md5():
    expected_result = '$1$12345678$o2n/JiO/h5VviOInWJ4OQ/'
    assert get_encrypted_password('password', 'md5', salt='12345678') == expected_result
    assert get_encrypted_password('password', 'md5', salt='xxxxxxxx') != expected_result
    assert get_encrypted_password('aaaaaaaa', 'md5', salt='12345678') != expected_result


def test_sha1():
    expected_result = '$sha1$480000$1234567890abcdef$0dqtrHQD1d054xh6KlthCRribz6D'
    assert get_encrypted_password('password', 'sha1', salt='1234567890abcdef') == expected_result


def test_sha256():
    expected_result = '$5$rounds=535000$1234567890abcdef$.0h4aOwY/VLi7JZgHMpT4nnUnM9fblM0W76l0aOcc.7'
    assert get_encrypted_password('password', 'sha256', salt='1234567890abcdef') == expected_result


def test_sha512():
    expected_result = '$6$rounds=656000$1234567890abcdef$zwZMM.vpCtgYA/7VF/gOjasxcF04UkjJBKv0/pcUHBSb0S8mb46dO71cu/YM9wFPqgRMW8B24JjedYk6hHlWs1'
    assert get_encrypted_password('password', 'sha512', salt='1234567890abcdef') == expected_result


def test_bcrypt():
    expected_result = '$2b$12$12345678901234567890aOpVxCaEL7mB6vCKwsWEmst5i10B6c.z.'
    assert get_encrypted_password('password', 'bcrypt', salt='12345678901234567890ab') == expected_result


def test_unknown():
    with pytest.raises(errors.AnsibleFilterError):
        get_encrypted_password('password', 'unknown')
