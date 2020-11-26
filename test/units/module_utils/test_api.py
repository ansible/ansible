# -*- coding: utf-8 -*-
# Copyright: (c) 2020, Abhijeet Kasurde <akasurde@redhat.com>
# Copyright: (c) 2020, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


from ansible.module_utils.api import rate_limit, retry

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
