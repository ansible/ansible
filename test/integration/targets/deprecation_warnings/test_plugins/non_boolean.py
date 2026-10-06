# Copyright (c) 2026 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


def passthru(value):
    """Return the value as-is, which allows returning a non-boolean result."""
    return value


class TestModule:
    def tests(self):
        return {
            'passthru': passthru,
        }
