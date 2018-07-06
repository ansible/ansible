from ansible.compat.tests import unittest
from ansible.modules.monitoring import pagerduty

import json

class PagerDutyTest(unittest.TestCase):
    def setUp(self):
        self.module = pagerduty

    def _retrieve_ongoing_maintenance_windows(self, module, url, headers):
        self.assertEquals(url, 'https://api.pagerduty.com/maintenance_windows?filter=ongoing')
        return object(), {'status': 200}

    def _with_v1_v2_backward_compatible_header(self, module, url, headers):
        self.assertDictContainsSubset(
          {'Accept': 'application/vnd.pagerduty+json;version=2'},
          headers,
          'No Accept:application/vnd.pagerduty+json;version=2 HTTP header'
        )
        return object(), {'status': 200}

    def test_ongoing_maintenance_windos_urls(self):
        pd = pagerduty.PagerDutyRequest(module=self.module, name='name', user='user', passwd='password', token='token')
        pd.ongoing(http_call=self._retrieve_ongoing_maintenance_windows)

    def test_compatibility_header(self):
        pd = pagerduty.PagerDutyRequest(module=self.module, name='name', user='user', passwd='password', token='token')
        pd.ongoing(http_call=self._with_v1_v2_backward_compatible_header)
