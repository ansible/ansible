# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Toshio Kuratomi <tkuratomi@ansible.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from ansible import context


class FakeOptions:
    pass


def test_set_global_context():
    options = FakeOptions()
    options.tags = ["production", "webservers"]
    options.check_mode = True
    options.start_at_task = "Start with くらとみ"

    expected = frozenset(
        (
            ("tags", ("production", "webservers")),
            ("check_mode", True),
            ("start_at_task", "Start with くらとみ"),
        )
    )

    context._init_global_context(options)
    assert frozenset(context.CLIARGS.items()) == expected
