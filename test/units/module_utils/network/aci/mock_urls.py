class fetch_url_mock(object):
    def __init__(self):

        self.items = {
            "status": None,
            "msg": None,
            "body": None,
        }

        self.headers = None

    def read(self):

        return self.items["body"]


def fetch_url(
    module,
    url,
    data=None,
    headers=None,
    method=None,
    use_proxy=True,
    force=False,
    last_mod_time=None,
    timeout=10,
):

    module.mock.items['request_url'] = url
    module.mock.items['request_data'] = data
    module.mock.items['request_headers'] = headers
    module.mock.items['request_method'] = method
    module.mock.items['request_use_proxy'] = use_proxy
    module.mock.items['request_force'] = force
    module.mock.items['request_last_mod_time'] = last_mod_time
    module.mock.items['request_timeout'] = timeout

    return module.mock, module.mock.items
