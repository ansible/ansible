import os
import json
from units.compat import unittest
from units.compat.mock import Mock
from units.modules.utils import set_module_args
from ansible.modules.network.avi import avi_api_fileservice

fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures')
with open(fixture_path +'/avi_api_fileservice.json') as json_file:
    data = json.load(json_file)

class TestAviApiFileservice(unittest.TestCase):
    def test_api_fileservice_upload(self):
        set_module_args({
            "avi_credentials": {
                "controller": "1.2.3.4",
                "username": "fakeusername",
                "password": "fakepassword",
                "api_version": "18.2.5"
            },
            "upload": True,
            "path": "hsmpackages?hsmtype=safenet",
            "file_path": "./safenet.tar"
        })
        avi_api_fileservice.upload_file = Mock(
            return_value=data['upload_successful'])
        response = avi_api_fileservice.main()
        assert response['changed']

    def test_api_fileservice_download(self):
        set_module_args({
            "avi_credentials": {
                "controller": "1.2.3.4",
                "username": "fakeusername",
                "password": "fakepassword",
                "api_version": "18.2.5"
             },
            "upload": False,
            "path": "seova",
            "file_path": "./test_se.qcow2",
            "params":
                {
                    "file_format": "qcow2"
                }
        })

        avi_api_fileservice.download_file = Mock(
            return_value = data['download_successful'])
        response = avi_api_fileservice.main()
        assert response['changed']
