# -*- coding: utf-8 -*-

from __future__ import annotations

import pytest

from ansible.modules.cron import CronTab


class TestModule:
    def get_bin_path(self, args, required=False):
        """ do nothing, just avoid exception """
        pass


name = "hello"
job = "*/20 * * * * echo hello"
crontab = CronTab(TestModule(), cron_file="/etc/cron.d/crontab")


@pytest.mark.parametrize(
    ("lines", "expected"),
    [
        pytest.param(
            [],
            [
                crontab.do_comment(name),
                job
            ],
            id="empty-crontab",
        ),
        pytest.param(
            [
                job,
            ],
            [
                crontab.do_comment(name),
                job
            ],
            id="no-comment-with-single-job",
        ),
        pytest.param(
            [
                crontab.do_comment(name),
            ],
            [
                crontab.do_comment(name),
                job
            ],
            id="comment-with-no-job",
        ),
        pytest.param(
            [
                job,
                crontab.do_comment("")
            ],
            [
                crontab.do_comment(name),
                job
            ],
            id="fix-empty-comment-at-last",
        ),
        pytest.param(
            [
                job,
                crontab.do_comment("hhhh")
            ],
            [
                crontab.do_comment(name),
                job
            ],
            id="fix-last-comment",
        ),
        pytest.param(
            [
                job,
                crontab.do_comment("hhhh"),
                "*/10 * * * * echo hhhh"
            ],
            [
                crontab.do_comment(name),
                job,
                crontab.do_comment("hhhh"),
                "*/10 * * * * echo hhhh"
            ],
            id="first-job-with-no-comment",
        ),
        pytest.param(
            [
                crontab.do_comment("aaaa"),
                "*/10 * * * * echo aaaa",
                job,
                crontab.do_comment("hhhh"),
                "*/10 * * * * echo hhhh"
            ],
            [
                crontab.do_comment("aaaa"),
                "*/10 * * * * echo aaaa",
                crontab.do_comment(name),
                job,
                crontab.do_comment("hhhh"),
                "*/10 * * * * echo hhhh"
            ],
            id="middle-job-with-no-comment",
        ),
        pytest.param(
            [
                crontab.do_comment(name),
                crontab.do_comment("hhhh"),
                "*/10 * * * * echo hhhh"
            ],
            [
                crontab.do_comment(name),
                job,
                crontab.do_comment("hhhh"),
                "*/10 * * * * echo hhhh"
            ],
            id="first-comment-with-no-job",
        ),
        pytest.param(
            [
                crontab.do_comment("hhhh"),
                "*/10 * * * * echo hhhh",
                crontab.do_comment(name),
            ],
            [
                crontab.do_comment("hhhh"),
                "*/10 * * * * echo hhhh",
                crontab.do_comment(name),
                job,
            ],
            id="last-comment-with-no-job",
        ),
    ],
)
def test_crontab_add_job(lines, expected):
    crontab.lines = lines
    old_job = crontab.find_job(name, job)

    # update crontab, same as the code in cron.py
    if len(old_job) == 0:
        crontab.add_job(name, job)
        changed = True
    if len(old_job) > 0 and old_job[1] is None:
        crontab.insert_job(name, job)
        changed = True
    if len(old_job) > 0 and old_job[1] != job:
        crontab.update_job(name, job)
        changed = True
    if len(old_job) > 2:
        crontab.update_job(name, job)
        changed = True

    assert crontab.lines == expected


@pytest.mark.parametrize(
    ("lines", "expected"),
    [
        pytest.param(
            [],
            [],
            id="remove-empty-crontab",
        ),
        pytest.param(
            [
                crontab.do_comment(name),
                crontab.do_comment("hhhh"),
                "*/10 * * * * echo hhhh",
            ],
            [
                crontab.do_comment("hhhh"),
                "*/10 * * * * echo hhhh",
            ],
            id="remove-comment-with-no-job-at-first",
        ),
        pytest.param(
            [
                crontab.do_comment("hhhh"),
                "*/10 * * * * echo hhhh",
                crontab.do_comment(name)
            ],
            [
                crontab.do_comment("hhhh"),
                "*/10 * * * * echo hhhh",
            ],
            id="remove-comment-with-no-job-at-last",
        ),
        pytest.param(
            [
                crontab.do_comment("hhhh"),
                "*/10 * * * * echo hhhh",
                crontab.do_comment(name),
                crontab.do_comment("xyz"),
                "*/10 * * * * echo xyz"
            ],
            [
                crontab.do_comment("hhhh"),
                "*/10 * * * * echo hhhh",
                crontab.do_comment("xyz"),
                "*/10 * * * * echo xyz",
            ],
            id="remove-comment-with-no-job-in-middle",
        ),
    ]
)
def test_crontab_remove_job(lines, expected):
    crontab.lines = lines
    old_job = crontab.find_job(name)

    if len(old_job) > 0:
        crontab.remove_job(name)

    assert crontab.lines == expected
