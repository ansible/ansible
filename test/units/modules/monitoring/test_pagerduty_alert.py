from units.compat import unittest
from ansible.modules.monitoring import pagerduty_alert

from ansible.module_utils.six.moves.urllib.parse import urlparse, urlencode, urlunparse


class PagerDutyAlertsTest(unittest.TestCase):
    def _assert_incident_api(self, module, url, method, headers):
        self.assertTrue('https://api.pagerduty.com/incidents' in url, 'url must contain REST API v2 network path')
        self.assertTrue('service_ids%5B%5D=service_id' in url, 'url must contain service id to filter incidents')
        self.assertTrue('sort_by=incident_number%3Adesc' in url, 'url should contain sorting parameter')
        self.assertTrue('time_zone=UTC' in url, 'url should contain time zone parameter')
        return Response(), {'status': 200}

    def _assert_compatibility_header(self, module, url, method, headers):
        self.assertDictContainsSubset(
            {'Accept': 'application/vnd.pagerduty+json;version=2'},
            headers,
            'Accept:application/vnd.pagerduty+json;version=2 HTTP header not found'
        )
        return Response(), {'status': 200}

    def _assert_incident_key(self, module, url, method, headers):
        self.assertTrue('incident_key=incident_key_value' in url, 'url must contain incident key')
        return Response(), {'status': 200}

    def test_incident_url(self):
        pagerduty_alert.check(None, 'name', 'state', 'service_id', 'integration_key', 'api_key', http_call=self._assert_incident_api)

    def test_compatibility_header(self):
        pagerduty_alert.check(None, 'name', 'state', 'service_id', 'integration_key', 'api_key', http_call=self._assert_compatibility_header)

    def test_incident_key_in_url_when_it_is_given(self):
        pagerduty_alert.check(
            None, 'name', 'state', 'service_id', 'integration_key', 'api_key', incident_key='incident_key_value', http_call=self._assert_incident_key
        )


class Response(object):
    def read(self):
        return '{"incidents":[{"id": "incident_id", "status": "triggered"}]}'
