#!/usr/bin/env python

import json
import os

try:
    from http.server import HTTPServer
    from http.server import SimpleHTTPRequestHandler
except ImportError:
    from BaseHTTPServer import HTTPServer
    from SimpleHTTPServer import SimpleHTTPRequestHandler

from threading import Thread

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse


class TestHandler(SimpleHTTPRequestHandler):
    # Path handlers:
    handlers = {}

    def log_message(self, format, *args):
        """
        Empty method, so we don't mix output of HTTP server with tests
        """
        pass

    def do_GET(self):
        params = urlparse(self.path)

        if params.path in self.handlers:
            self.handlers[params.path](self)
        else:
            SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        params = urlparse(self.path)

        if params.path in self.handlers:
            self.handlers[params.path](self)
        else:
            SimpleHTTPRequestHandler.do_POST(self)


class TestServer(object):
    # The host and port and path used by the embedded tests web server:
    PORT = None

    # The embedded web server:
    _httpd = None
    # Thread for http server:
    _thread = None

    def set_json_response(self, path, code, body):
        def _handle_request(handler):
            handler.send_response(code)
            handler.send_header('Content-Type', 'application/json')
            handler.end_headers()

            data = json.dumps(body, ensure_ascii=False).encode('utf-8')
            handler.wfile.write(data)

        TestHandler.handlers[path] = _handle_request

    def start_server(self, host='localhost'):
        self._httpd = HTTPServer((host, 12345), TestHandler)
        self._thread = Thread(target=self._httpd.serve_forever)
        self._thread.start()

    def stop_server(self):
        self._httpd.shutdown()
        self._thread.join()


if __name__ == '__main__':
    print(os.getpid())
    server = TestServer()
    server.start_server()
    server.set_json_response(path="/version", code=200, body={})
    server.set_json_response(path="/api", code=200, body={
        "kind": "APIVersions", "versions": ["v1"], "serverAddressByClientCIDRs": [{"clientCIDR": "0.0.0.0/0", "serverAddress": "localhost:12345"}]
    })
    server.set_json_response(path="/api/v1", code=200, body={'resources': {}})
    server.set_json_response(path="/apis", code=200, body={
        "kind": "APIGroupList", "apiVersion": "v1",
        "groups": [{
            "name": "kubevirt.io", "versions": [{"groupVersion": "kubevirt.io/v1alpha3", "version": "v1alpha3"}],
            "preferredVersion": {"groupVersion": "kubevirt.io/v1alpha3", "version": "v1alpha3"}
        }]
    })
    server.set_json_response(
        path="/apis/kubevirt.io/v1alpha3",
        code=200,
        body={
            "kind": "APIResourceList", "apiVersion": "v1", "groupVersion": "kubevirt.io/v1alpha3",
            "resources": [{
                "name": "virtualmachineinstances", "singularName": "virtualmachineinstance",
                "namespaced": True, "kind": "VirtualMachineInstance",
                "verbs": ["delete", "deletecollection", "get", "list", "patch", "create", "update", "watch"],
                "shortNames":["vmi", "vmis"]
            }]
        }
    )
    server.set_json_response(
        path="/apis/kubevirt.io/v1alpha3/namespaces/default/virtualmachineinstances",
        code=200,
        body={'apiVersion': 'kubevirt.io/v1alpha3',
              'items': [{'apiVersion': 'kubevirt.io/v1alpha3',
                         'kind': 'VirtualMachineInstance',
                         'metadata': {'annotations': {'ansible': '{"data1": "yes", "data2": "no"}'},
                                      'creationTimestamp': '2019-04-05T14:17:02Z',
                                      'generateName': 'myvm',
                                      'generation': 1,
                                      'labels': {'kubevirt.io/nodeName': 'localhost',
                                                 'label': 'x',
                                                 'vm.cnv.io/name': 'myvm'},
                                      'name': 'myvm',
                                      'namespace': 'default',
                                      'ownerReferences': [{'apiVersion': 'kubevirt.io/v1alpha3',
                                                           'blockOwnerDeletion': True,
                                                           'controller': True,
                                                           'kind': 'VirtualMachine',
                                                           'name': 'myvm',
                                                           'uid': 'f78ebe62-5666-11e9-a214-0800279ffc6b'}],
                                      'resourceVersion': '1614085',
                                      'selfLink': '/apis/kubevirt.io/v1alpha3/namespaces/default/virtualmachineinstances/myvm',
                                      'uid': '7ba1b196-57ad-11e9-9e2e-0800279ffc6b'},
                         'spec': {'domain': {'devices': {'disks': [{'disk': {'bus': 'virtio'},
                                                                    'name': 'containerdisk'},
                                                                   {'disk': {'bus': 'virtio'}, 'name': 'ansiblecloudinitdisk'}],
                                                         'interfaces': [{'bridge': {}, 'name': 'default'}]},
                                             'firmware': {'uuid': 'cdf77e9e-871b-5acb-a707-80ef3d4b9849'},
                                             'machine': {'type': ''},
                                             'resources': {'requests': {'memory': '64M'}}},
                                  'networks': [{'name': 'default', 'pod': {}}],
                                  'volumes': [{'containerDisk': {'image': 'kubevirt/cirros-container-disk-demo:v0.11.0'},
                                               'name': 'containerdisk'},
                                              {'cloudInitNoCloud': {'userData': '#cloud-config\npassword: password\nchpasswd: { expire: False }'},
                                               'name': 'ansiblecloudinitdisk'}]},
                         'status': {'conditions': [{'lastProbeTime': None,
                                                    'lastTransitionTime': None,
                                                    'status': 'True',
                                                    'type': 'LiveMigratable'},
                                                   {'lastProbeTime': None,
                                                    'lastTransitionTime': '2019-04-05T14:17:27Z',
                                                    'status': 'True',
                                                    'type': 'Ready'}],
                                    'interfaces': [{'ipAddress': '172.17.0.19',
                                                    'mac': '02:42:ac:11:00:13',
                                                    'name': 'default'}],
                                    'migrationMethod': 'BlockMigration',
                                    'nodeName': 'localhost',
                                    'phase': 'Running'}}],
              'kind': 'VirtualMachineInstanceList',
              'metadata': {'continue': '',
                           'resourceVersion': '1614862',
                           'selfLink': '/apis/kubevirt.io/v1alpha3/namespaces/default/virtualmachineinstances'}}
    )
