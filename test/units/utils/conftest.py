# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest

from ansible.utils.display import Display


@pytest.fixture()
def display_resource(request):
    Display._Singleton__instance = None

    def teardown():
        Display._Singleton__instance = None

    request.addfinalizer(teardown)
