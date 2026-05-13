# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

import pytest

from ansible.modules.apt_repository import SourcesList


@pytest.mark.parametrize(
    "line, expected", [
        pytest.param("deb http://deb.debian.org/debian stable main contrib non-free", True, id="valid_line"),
        pytest.param("# This is a commented line that should be ignored", False, id="commented_line"),
        pytest.param("deb http://ftp.us.debian.org/debian sid main", True, id="no_options_line"),
        pytest.param("deb-src http://ftp.debian.org/debian/ experimental/", True, id="suite_with_slash"),
        pytest.param("deb-src http://ftp.debian.org/debian/ experimental/ main", False, id="suite_with_slash_and_component"),
        pytest.param("deb [arch=amd64,i386] http://ftp.us.debian.org/debian sid main", True, id="multi_arch_option_line"),
        pytest.param("deb [trusted=yes arch=amd64] https://example.com/debian focal", False, id="invalid_line"),
        pytest.param("deb [trusted=yes arch=amd64] https://example.com/debian focal main", True, id="trusted_option_line"),
        pytest.param("deb [trusted=yes signed-by=/etc/apt/key.gpg] http://my.repo.com/ubuntu focal-updates main", True, id="signed_by_option_line"),
        pytest.param("deb-src [arch=amd64 trusted=yes] http://my.repo.com/ubuntu focal main universe", True, id="multiple_components_line"),
        pytest.param("deb [arch=amd64,i386 trusted=yes] http://my.repo.com/ubuntu focal main", True, id="multiple_arch_trusted_option_line"),
        pytest.param(
            "deb [arch=amd64,i386] http://archive.ubuntu.com/ubuntu/ xenial-updates main restricted # a comment at the end",
            True,
            id="comment_at_end_line"
        ),
    ]
)
def test_validate(line, expected):
    assert SourcesList._validate_source(line) == expected
