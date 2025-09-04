# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from os import environ as _e

if 'ANSIBLE_DEV_DEBUG' not in _e and 'ANSIBLE_TEST_ANSIBLE_LIB_ROOT' not in _e:
    raise ImportError('_d')


from ansible.utils.display import Display as _Display

_d = _Display()
_p = _d.display
