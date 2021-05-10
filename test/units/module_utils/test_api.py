# -*- coding: utf-8 -*-
# Copyright: (c) 2020, Abhijeet Kasurde <akasurde@redhat.com>
# Copyright: (c) 2020, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


from ansible.module_utils.api import rate_limit, retry, retry_with_delays_and_condition

import pytest


class CustomException(Exception):
    pass


class CustomBaseException(BaseException):
    pass


class TestRateLimit:

    def test_ratelimit(self):
        @rate_limit(rate=1, rate_limit=1)
        def login_database():
            return "success"
        r = login_database()

        assert r == 'success'


class TestRetry:

    def test_no_retry_required(self):
        @retry(retries=4, retry_pause=2)
        def login_database():
            login_database.counter += 1
            return 'success'

        login_database.counter = 0
        r = login_database()

        assert r == 'success'
        assert login_database.counter == 1

    def test_catch_exception(self):

        @retry(retries=1)
        def login_database():
            return 'success'

        with pytest.raises(Exception, match="Retry"):
            login_database()

    def test_no_retries(self):

        @retry()
        def login_database():
            assert False, "Should not execute"

        login_database()


class TestRetryWithDelaysAndCondition:

    def test_empty_retry_iterator(self):
        @retry_with_delays_and_condition(backoff_iterator=[])
        def login_database():
            login_database.counter += 1

        login_database.counter = 0
        r = login_database()
        assert login_database.counter == 1

    def test_no_retry_exception(self):
        @retry_with_delays_and_condition(
            backoff_iterator=[1],
            should_retry_error=lambda x: False,
        )
        def login_database():
            login_database.counter += 1
            if login_database.counter == 1:
                raise CustomException("Error")

        login_database.counter = 0
        with pytest.raises(CustomException, match="Error"):
            login_database()
        assert login_database.counter == 1

    def test_no_retry_baseexception(self):
        @retry_with_delays_and_condition(
            backoff_iterator=[1],
            should_retry_error=lambda x: True,  # Retry all exceptions inheriting from Exception
        )
        def login_database():
            login_database.counter += 1
            if login_database.counter == 1:
                # Raise an exception inheriting from BaseException
                raise CustomBaseException("Error")

        login_database.counter = 0
        with pytest.raises(CustomBaseException, match="Error"):
            login_database()
        assert login_database.counter == 1

    def test_retry_exception(self):
        @retry_with_delays_and_condition(
            backoff_iterator=[1],
            should_retry_error=lambda x: isinstance(x, CustomException),
        )
        def login_database():
            login_database.counter += 1
            if login_database.counter == 1:
                raise CustomException("Retry")
            return 'success'

        login_database.counter = 0
        assert login_database() == 'success'
        assert login_database.counter == 2
