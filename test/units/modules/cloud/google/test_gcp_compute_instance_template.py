import unittest
import copy

from ansible.modules.cloud.google.gcp_compute_instance_template import encode_request, decode_response

class TestTestGCPComputeInstanceTemplate(unittest.TestCase):
    """Unit tests for gcp_compute_instance_template module."""
    request_without_metadata = {
        u'kind': 'compute#instanceTemplate',
        u'description': 'instance template description',
        u'name': 'my-instance-template',
        u'properties': {
            u'machineType': 'n1-standard-1'
        }
    }
    request_with_metadata = {
        u'kind': 'compute#instanceTemplate',
        u'description': 'instance template description',
        u'name': 'my-instance-template',
        u'properties': {
            u'machineType': 'n1-standard-1', 
            u'metadata': {
                'startup-script': '#!/bin/bash\necho hello',
                'ssh-keys': 'not-an-ssh-key'
            }
        }
    }
    response_without_metadata = {
        u'kind': u'compute#instanceTemplate', 
        u'description': 'instance template description',
        u'properties': {
            u'machineType': u'n1-standard-1', 
            u'metadata': {
                u'kind': u'compute#metadata', 
                u'fingerprint': u'ZmluZ2VycHJpbnQK'
            }
        }, 
        u'creationTimestamp': u'2019-05-22T06:58:43.884-07:00', 
        u'id': u'0000000000000000001', 
        u'selfLink': u'https://www.googleapis.com/compute/v1/projects/my-fake-gcp-project/global/instanceTemplates/my-instance-template', 
        u'name': u'my-instance-template'
    }
    response_with_metadata = {
        u'kind': u'compute#instanceTemplate', 
        u'description': 'instance template description',
        u'properties': {
            u'machineType': u'n1-standard-1', 
            u'metadata': {
                u'items': [
                    {
                        u'value': u'#!/bin/bash\necho hello', 
                        u'key': u'startup-script'
                    }
                ], 
                u'kind': u'compute#metadata', 
                u'fingerprint': u'ZmluZ2VycHJpbnQK'
            }
        }, 
        u'creationTimestamp': u'2019-05-22T06:58:43.884-07:00', 
        u'id': u'0000000000000000001', 
        u'selfLink': u'https://www.googleapis.com/compute/v1/projects/my-fake-gcp-project/global/instanceTemplates/my-instance-template', 
        u'name': u'my-instance-template'
    }

    def test_encode_request(self):
        encoded_request_without_metadata = encode_request(copy.deepcopy(self.request_without_metadata), None)
        self.assertEqual(
            encoded_request_without_metadata,
            self.request_without_metadata
        )

        encoded_request_with_metadata = encode_request(copy.deepcopy(self.request_with_metadata), None)
        self.assertNotEqual(
            encoded_request_with_metadata,
            self.request_with_metadata
        )

        self.assertIn('properties', encoded_request_with_metadata)
        self.assertIn('metadata', encoded_request_with_metadata['properties'])
        self.assertIn('items', encoded_request_with_metadata['properties']['metadata'])
        for metadata_key, metadata_value in self.request_with_metadata['properties']['metadata'].items():
            self.assertIn(
                { 'key': metadata_key, 'value': metadata_value },
                encoded_request_with_metadata['properties']['metadata']['items']
            )

    def test_decode_request(self):
        self.maxDiff = None

        # Even if there's no metadata items, decode_response will clear out the other
        # stuff in the metadata object.
        response_without_metadata_cleared = copy.deepcopy(self.response_without_metadata)
        response_without_metadata_cleared['properties']['metadata'].pop('kind')
        response_without_metadata_cleared['properties']['metadata'].pop('fingerprint')
        response_with_metadata_cleared = copy.deepcopy(self.response_with_metadata)
        response_with_metadata_cleared['properties']['metadata'].pop('kind')
        response_with_metadata_cleared['properties']['metadata'].pop('fingerprint')

        decoded_response_without_metadata = decode_response(copy.deepcopy(self.response_without_metadata), None)
        self.assertEqual(
            decoded_response_without_metadata,
            response_without_metadata_cleared
        )

        decoded_response_with_metadata = decode_response(copy.deepcopy(self.response_with_metadata), None)
        self.assertNotEqual(
            decoded_response_with_metadata,
            response_with_metadata_cleared
        )

        self.assertIn('properties', decoded_response_with_metadata)
        self.assertIn('metadata', decoded_response_with_metadata['properties'])
        for metadata_object in self.response_with_metadata['properties']['metadata']['items']:
            self.assertIn(
                metadata_object['key'], 
                decoded_response_with_metadata['properties']['metadata']
            )
            self.assertEqual(
                metadata_object['value'],
                decoded_response_with_metadata['properties']['metadata'][metadata_object['key']]
            )

