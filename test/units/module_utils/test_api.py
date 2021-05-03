# -*- coding: utf-8 -*-
# Copyright: (c) 2020, Abhijeet Kasurde <akasurde@redhat.com>
# Copyright: (c) 2020, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


from ansible.module_utils.api import rate_limit, retry, retry_with_delays_and_condition

import pytest


class TestRateLimit:

    def test_ratelimit(self):
        @rate_limit(rate=1, rate_limit=1)
        def login_database():
            return "success"
        r = login_database()

        assert r == 'success'


class TestRetry:

    def test_no_retry_required(self):
        self.counter = 0

        @retry(retries=4, retry_pause=2)
        def login_database():
            self.counter += 1
            return 'success'

        r = login_database()

        assert r == 'success'
        assert self.counter == 1

    def test_catch_exception(self):

        @retry(retries=1)
        def login_database():
            return 'success'

        with pytest.raises(Exception):
            login_database()

    def test_no_retries(self):

        @retry()
        def login_database():
            assert False, "Should not execute"

        login_database()


class TestRetryWithDelaysAndCondition:

    def test_empty_retry_iterator(self):
        self.counter = 0

        @retry_with_delays_and_condition(backoff_iterator=[])
        def login_database():
            self.counter += 1

        r = login_database()
        assert self.counter == 1

    def test_no_retry_exception(self):
        self.counter = 0

        @retry_with_delays_and_condition(
            backoff_iterator=[1],
            should_retry_error=lambda x: False,
        )
        def login_database():
            self.counter += 1
            if self.counter == 1:
                raise Exception("Error")

        with pytest.raises(Exception):
            login_database()
        assert self.counter == 1

    def test_no_retry_result(self):
        self.counter = 0

        @retry_with_delays_and_condition(
            backoff_iterator=[1],
            should_retry_result=lambda x: False,
        )
        def login_database():
            self.counter += 1
            if self.counter == 1:
                return 'retry'
            return 'success'

        assert login_database() == 'retry'
        assert self.counter == 1

    def test_retry_exception(self):
        self.counter = 0

        @retry_with_delays_and_condition(
            backoff_iterator=[1],
            should_retry_error=lambda x: isinstance(x, Exception),
        )
        def login_database():
            self.counter += 1
            if self.counter == 1:
                raise Exception("Retry")
            return 'success'

        assert login_database() == 'success'
        assert self.counter == 2

    def test_retry_result(self):
        self.counter = 0

        @retry_with_delays_and_condition(
            backoff_iterator=[1],
            should_retry_result=lambda x: x == 'retry',
        )
        def login_database():
            self.counter += 1
            if self.counter == 1:
                return 'retry'
            return 'success'

        assert login_database() == 'success'
        assert self.counter == 2

    def test_do_on_retry(self):
        self.counter = 0
        self.retry_counter = 0

        def handle_retry(delay, exception, result):
            self.retry_counter += 1
            if self.counter == 1:
                assert exception is not None
                assert result is None
            if self.counter == 2:
                assert exception is None
                assert result is not None

        @retry_with_delays_and_condition(
            backoff_iterator=[1, 1],
            do_on_retry=handle_retry,
            should_retry_error=lambda x: isinstance(x, Exception),
            should_retry_result=lambda x: x == 'retry',
        )
        def login_database():
            self.counter += 1
            if self.counter == 1:
                raise Exception("Retry")
            if self.counter == 2:
                return 'retry'
            return 'success'

        assert login_database() == 'success'
        assert self.counter == 3
        assert self.retry_counter == 2
