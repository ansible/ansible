from units.compat import unittest
from ansible.modules.monitoring import pagerduty

import json


class PagerDutyTest(unittest.TestCase):
    def setUp(self):
        self.pd = pagerduty.PagerDutyRequest(module=pagerduty, name='name', user='user', token='token')

    def _assert_ongoing_maintenance_windows(self, module, url, headers):
        self.assertEquals('https://api.pagerduty.com/maintenance_windows?filter=ongoing', url)
        return object(), {'status': 200}

    def _assert_ongoing_window_with_v1_compatible_header(self, module, url, headers, data=None, method=None):
        self.assertDictContainsSubset(
            {'Accept': 'application/vnd.pagerduty+json;version=2'},
            headers,
            'Accept:application/vnd.pagerduty+json;version=2 HTTP header not found'
        )
        return object(), {'status': 200}

    def _assert_create_a_maintenance_window_url(self, module, url, headers, data=None, method=None):
        self.assertEquals('https://api.pagerduty.com/maintenance_windows', url)
        return object(), {'status': 201}

    def _assert_create_a_maintenance_window_http_method(self, module, url, headers, data=None, method=None):
        self.assertEquals('POST', method)
        return object(), {'status': 201}

    def _assert_create_a_maintenance_window_from_header(self, module, url, headers, data=None, method=None):
        self.assertDictContainsSubset(
            {'From': 'requester_id'},
            headers,
            'From:requester_id HTTP header not found'
        )
        return object(), {'status': 201}

    def _assert_create_window_with_v1_compatible_header(self, module, url, headers, data=None, method=None):
        self.assertDictContainsSubset(
            {'Accept': 'application/vnd.pagerduty+json;version=2'},
            headers,
            'Accept:application/vnd.pagerduty+json;version=2 HTTP header not found'
        )
        return object(), {'status': 201}

    def _assert_create_window_payload(self, module, url, headers, data=None, method=None):
        payload = json.loads(data)
        window_data = payload['maintenance_window']
        self.assertTrue('start_time' in window_data, '"start_time" is requiered attribute')
        self.assertTrue('end_time' in window_data, '"end_time" is requiered attribute')
        self.assertTrue('services' in window_data, '"services" is requiered attribute')
        return object(), {'status': 201}

    def _assert_create_window_single_service(self, module, url, headers, data=None, method=None):
        payload = json.loads(data)
        window_data = payload['maintenance_window']
        services = window_data['services']
        self.assertEquals(
            [{'id': 'service_id', 'type': 'service_reference'}],
            services
        )
        return object(), {'status': 201}

    def _assert_create_window_multiple_service(self, module, url, headers, data=None, method=None):
        payload = json.loads(data)
        window_data = payload['maintenance_window']
        services = window_data['services']
        print(services)
        self.assertEquals(
            [
                {'id': 'service_id_1', 'type': 'service_reference'},
                {'id': 'service_id_2', 'type': 'service_reference'},
                {'id': 'service_id_3', 'type': 'service_reference'},
            ],
            services
        )
        return object(), {'status': 201}

    def _assert_absent_maintenance_window_url(self, module, url, headers, method=None):
        self.assertEquals('https://api.pagerduty.com/maintenance_windows/window_id', url)
        return object(), {'status': 204}

    def _assert_absent_window_with_v1_compatible_header(self, module, url, headers, method=None):
        self.assertDictContainsSubset(
            {'Accept': 'application/vnd.pagerduty+json;version=2'},
            headers,
            'Accept:application/vnd.pagerduty+json;version=2 HTTP header not found'
        )
        return object(), {'status': 204}

    def test_ongoing_maintenance_windos_url(self):
        self.pd.ongoing(http_call=self._assert_ongoing_maintenance_windows)

    def test_ongoing_maintenance_windos_compatibility_header(self):
        self.pd.ongoing(http_call=self._assert_ongoing_window_with_v1_compatible_header)

    def test_create_maintenance_window_url(self):
        self.pd.create('requester_id', 'service', 1, 0, 'desc', http_call=self._assert_create_a_maintenance_window_url)

    def test_create_maintenance_window_http_method(self):
        self.pd.create('requester_id', 'service', 1, 0, 'desc', http_call=self._assert_create_a_maintenance_window_http_method)

    def test_create_maintenance_from_header(self):
        self.pd.create('requester_id', 'service', 1, 0, 'desc', http_call=self._assert_create_a_maintenance_window_from_header)

    def test_create_maintenance_compatibility_header(self):
        self.pd.create('requester_id', 'service', 1, 0, 'desc', http_call=self._assert_create_window_with_v1_compatible_header)

    def test_create_maintenance_request_payload(self):
        self.pd.create('requester_id', 'service', 1, 0, 'desc', http_call=self._assert_create_window_payload)

    def test_create_maintenance_for_single_service(self):
        self.pd.create('requester_id', 'service_id', 1, 0, 'desc', http_call=self._assert_create_window_single_service)

    def test_create_maintenance_for_multiple_services(self):
        self.pd.create('requester_id', ['service_id_1', 'service_id_2', 'service_id_3'], 1, 0, 'desc', http_call=self._assert_create_window_multiple_service)

    def test_absent_maintenance_window_url(self):
        self.pd.absent('window_id', http_call=self._assert_absent_maintenance_window_url)

    def test_absent_maintenance_compatibility_header(self):
        self.pd.absent('window_id', http_call=self._assert_absent_window_with_v1_compatible_header)
