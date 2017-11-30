import pytest

import unittest

try:
    import ansible.modules.cloud.amazon.s3 as s3
except ImportError:
    pytestmark = pytest.mark.skip("This test requires the s3 Python libraries")

from ansible.module_utils.six.moves.urllib.parse import urlparse

boto3 = pytest.importorskip("boto3")


class TestUrlparse(unittest.TestCase):

    def test_urlparse(self):
        actual = urlparse("http://test.com/here")
        self.assertEqual("http", actual.scheme)
        self.assertEqual("test.com", actual.netloc)
        self.assertEqual("/here", actual.path)

    def test_is_fakes3(self):
        actual = s3.is_fakes3("fakes3://bla.blubb")
        self.assertEqual(True, actual)

    def test_is_walrus(self):
        actual = s3.is_walrus("trulywalrus_but_invalid_url")
        # I don't know if this makes sense, but this is the current behaviour...
        self.assertEqual(True, actual)
        actual = s3.is_walrus("http://notwalrus.amazonaws.com")
        self.assertEqual(False, actual)

    def test_get_s3_connection(self):
        aws_connect_kwargs = dict(aws_access_key_id="access_key",
                                  aws_secret_access_key="secret_key")
        location = None
        rgw = True
        s3_url = "http://bla.blubb"
        actual = s3.get_s3_connection(None, aws_connect_kwargs, location, rgw, s3_url)
        self.assertEqual(bool("bla.blubb" in str(actual._endpoint)), True)
