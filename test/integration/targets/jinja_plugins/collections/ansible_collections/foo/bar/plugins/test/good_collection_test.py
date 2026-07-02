# Copyright (c) 2021 Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


class TestModule:
    def tests(self):
        return {
            'world': lambda x: x.lower() == 'world',
        }
