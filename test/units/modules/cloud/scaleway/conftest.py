from ansible.compat.tests.mock import patch, MagicMock

import json
import pytest


class FakeReader:
    def __init__(self, object):
        self.content = json.dumps(object, sort_keys=True)

    def read(self):
        return self.content


@pytest.fixture
def mock_fetch_url(request, mocker):
    responses = request.getfuncargvalue('testcase')['calls']
    module_name = request.module.TESTED_MODULE

    def fetch_url(module, url, data=None, headers=None, method=None, timeout=10):
        """Fake request"""

        data, info = responses.pop(0)
        excepted_url = info['url']
        if url == excepted_url:
            if isinstance(data, Exception):
                raise data(info)
            else:
                return [FakeReader(data), info]
        else:
            raise Exception('Expected call: %r, called with: %r' % (excepted_url, url))

    return mocker.patch('ansible.module_utils.scaleway.fetch_url', side_effect=fetch_url)
