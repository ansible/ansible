import json

from ansible.module_utils.urls import fetch_url


class Response(object):

    def __init__(self, resp, info):
        self.body = None
        if resp:
            self.body = resp.read()
        self.info = info

    @property
    def json(self):
        if not self.body:
            if "body" in self.info:
                return json.loads(self.info["body"])
            return None
        try:
            return json.loads(self.body)
        except ValueError:
            return None

    @property
    def status_code(self):
        return self.info["status"]

    @property
    def ok(self):
        return self.status_code in (200, 201, 202, 204)


class ScalewayAPI(object):

    def __init__(self, module, headers, base_url):
        self.module = module
        self.headers = headers
        self.base_url = base_url

    def _url_builder(self, path):
        if path[0] == '/':
            path = path[1:]
        return '%s/%s' % (self.base_url, path)

    def send(self, method, path, data=None, headers=None):
        url = self._url_builder(path)
        data = self.module.jsonify(data)
        timeout = self.module.params['timeout']

        if headers is not None:
            self.headers.update(headers)

        resp, info = fetch_url(self.module, url, data=data, headers=self.headers, method=method, timeout=timeout)

        # Exceptions in fetch_url may result in a status -1, the ensures a proper error to the user in all cases
        if info['status'] == -1:
            self.module.fail_json(msg=info['msg'])

        return Response(resp, info)

    def get(self, path, data=None, headers=None):
        return self.send('GET', path, data, headers)

    def put(self, path, data=None, headers=None):
        return self.send('PUT', path, data, headers)

    def post(self, path, data=None, headers=None):
        return self.send('POST', path, data, headers)

    def delete(self, path, data=None, headers=None):
        return self.send('DELETE', path, data, headers)

    def patch(self, path, data=None, headers=None):
        return self.send("PATCH", path, data, headers)

    def update(self, path, data=None, headers=None):
        return self.send("UPDATE", path, data, headers)
