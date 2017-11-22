import json

from ansible.compat.tests.mock import patch
from ansible.compat.tests.unittest import TestCase
from ansible.module_utils import artifactory as ar_base
from ansible.modules.packaging import artifactory_repo as ar

from contextlib import contextmanager

from units.modules.utils import set_module_args, AnsibleExitJson, AnsibleFailJson, ModuleTestCase


class TestArtifactoryRepoManagement(TestCase):

    def setUp(self):
        self.fake_url = "http://www.fake.com/api/repositories"
        self.base_update_conf = dict(repoLayoutRef="standard-default",
                                     url="fake2.com")
        self.repo_uri_map = ar.URI_CONFIG_MAP

    @contextmanager
    def _stubs(self, url=None, repo=None, test_config=None, responses=None):
        with patch("ansible.module_utils.artifactory.ArtifactoryBase."
                   "query_artifactory") as query_resp:
            if not url:
                temp_url = self.fake_url
            else:
                temp_url = url
            if not test_config:
                temp_test_config = self.base_update_conf
            else:
                temp_test_config = self.base_update_conf
                self.base_update_conf.update(test_config)
            temp_test_config = json.dumps(temp_test_config)
            self.build_out_test_contruct(temp_url, repo, temp_test_config)
            if responses:
                http_responses = []
                for resp in responses:
                    http_responses.append(resp)
                query_resp.side_effect = http_responses
            yield query_resp

    def build_out_test_contruct(self, url, repo, test_config):
        self.arm = ar.ArtifactoryRepoManagement(
            artifactory_url=url,
            repo=repo,
            repo_config=test_config,
            config_map=self.repo_uri_map)

    def test_get_valid_conf_valid_conf_post(self):
        with self._stubs():
            self.arm.get_valid_conf("POST")

    def test_get_valid_conf_invalid_conf_is_none_on_post(self):
        self.base_update_conf = None
        with self.assertRaises(ar_base.ConfigValueTypeMismatch):
            with self._stubs():
                self.arm.get_valid_conf("POST")

    def test_get_valid_conf_valid_conf_put(self):
        with self._stubs(test_config=dict(rclass='local')):
            self.arm.get_valid_conf("PUT")

    def test_get_valid_conf_invalid_conf_is_none_on_put(self):
        self.base_update_conf = None
        with self.assertRaises(ar_base.ConfigValueTypeMismatch):
            with self._stubs():
                self.arm.get_valid_conf("PUT")

    def test_get_valid_conf_invalid_conf_is_missing_req_key_put(self):
        with self.assertRaises(ar_base.InvalidConfigurationData):
            with self._stubs():
                self.arm.get_valid_conf("PUT")

    def test_get_valid_conf_valid_remote_conf(self):
        # rclass>remote requires url key exists
        # url already exists within the base_update_conf dict
        with self._stubs(test_config=dict(rclass='remote')):
            self.arm.get_valid_conf("PUT")

    def test_get_valid_conf_invalid_conf_is_missing_req_key_remote(self):
        # rclass>remote requires url key exists
        # Pop url key to verify map is working
        self.base_update_conf.pop('url', None)
        with self.assertRaises(ar_base.InvalidConfigurationData):
            with self._stubs(test_config=dict(rclass='remote')):
                self.arm.get_valid_conf("PUT")

    def test_get_valid_conf_valid_virtual_conf(self):
        with self._stubs(test_config=dict(rclass='virtual',
                                          packageType='bower')):
            self.arm.get_valid_conf("PUT")

    def test_get_valid_conf_invalid_conf_is_missing_req_key_virtual(self):
        # rclass>virtual requires packageType key exists
        with self.assertRaises(ar_base.InvalidConfigurationData):
            with self._stubs(test_config=dict(rclass='virtual')):
                self.arm.get_valid_conf("PUT")

    def test_get_valid_conf_invalid_conf_bad_packageType_virtual(self):
        # rclass>virtual requires packageType key exists
        with self.assertRaises(ar_base.InvalidConfigurationData):
            with self._stubs(test_config=dict(rclass='virtual',
                                              packageType='bad_type')):
                self.arm.get_valid_conf("PUT")

    def test_get_valid_conf_invalid_rclass_put(self):
        with self.assertRaises(ar_base.InvalidConfigurationData):
            with self._stubs(test_config=dict(rclass='bad_rclass')):
                self.arm.get_valid_conf("PUT")

    def test_get_valid_conf_invalid_rclass_post(self):
        with self.assertRaises(ar_base.InvalidConfigurationData):
            with self._stubs(test_config=dict(rclass='bad_rclass')):
                self.arm.get_valid_conf("POST")

    def test_get_valid_conf_invalid_artifactory_url(self):
        self.fake_url = "bad.url.com"
        with self.assertRaises(ar_base.InvalidArtifactoryURL):
            with self._stubs(test_config=dict(rclass='local')):
                self.arm.get_valid_conf("PUT")


class TestArtifactoryRepoModule(ModuleTestCase):
    def setUp(self):
        super(TestArtifactoryRepoModule, self).setUp()
        self.module = ar
        self.fake_url = "http://www.fake.com/api/repositories"

    def failed(self):
        with self.assertRaises(AnsibleFailJson) as exc:
            self.module.main()

        result = exc.exception.args[0]
        self.assertTrue(result['failed'], result)
        return result

    def changed(self, changed=False):
        with self.assertRaises(AnsibleExitJson) as exc:
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], changed, result)
        return result

    class FakeHttpResp:
        def __init__(self, resp):
            self.resp = resp

        def read(self):
            return self.resp

    @contextmanager
    def _stubs(self, responses=None):
        with patch("ansible.module_utils.artifactory.ArtifactoryBase."
                   "query_artifactory") as query_resp:
            if responses:
                http_responses = []
                for resp in responses:
                    http_responses.append(resp)
                query_resp.side_effect = http_responses
            yield query_resp

    def test_missing_artifactory_url_and_repo(self):
        set_module_args(dict())
        result = self.failed()
        self.assertTrue("missing required arguments" in result["msg"])
        self.assertTrue("name" in result["msg"])
        self.assertTrue("artifactory_url" in result["msg"])

    def test_missing_repo(self):
        set_module_args(dict(artifactory_url=self.fake_url))
        result = self.failed()
        self.assertTrue("missing required arguments" in result["msg"])
        self.assertTrue("name" in result["msg"])

    def test_missing_artifactory_url(self):
        set_module_args(dict(name='test'))
        result = self.failed()
        self.assertTrue("missing required arguments" in result["msg"])
        self.assertTrue("artifactory_url" in result["msg"])

    def test_with_artifactory_url_and_repo(self):
        set_module_args(dict(artifactory_url=self.fake_url, name='test'))
        result = self.failed()
        self.assertTrue("one of the following is required" in result["msg"])
        self.assertTrue("password" in result["msg"])
        self.assertTrue("auth_token" in result["msg"])

    def test_with_invalid_rclass(self):
        set_module_args(dict(artifactory_url=self.fake_url, name='test',
                             auth_token='derp', rclass='blech'))
        result = self.failed()
        fail_msg = ("value of rclass must be one of: local, remote, "
                    "virtual, got: blech")
        self.assertEqual(result['msg'], fail_msg)
        self.assertTrue("value of rclass must be one of" in result["msg"])
        self.assertTrue("local" in result["msg"])
        self.assertTrue("remote" in result["msg"])
        self.assertTrue("virtual" in result["msg"])

    def test_with_invalid_packageType(self):
        set_module_args(dict(artifactory_url=self.fake_url, name='test',
                             auth_token='derp', packageType='blech'))
        result = self.failed()
        self.assertTrue("value of packageType must be one of" in result["msg"])
        for valid_pack in ar.VALID_PACKAGETYPES:
            self.assertTrue(valid_pack in result["msg"])

    def test_with_artifactory_url_repo_auth_token(self):
        repo = 'test'
        set_module_args(dict(artifactory_url=self.fake_url, name=repo,
                             auth_token='derp', state='read'))
        http_resp = '[{"key": "%s"}]' % repo
        fake_http1 = self.FakeHttpResp(http_resp)
        fake_http2 = self.FakeHttpResp(http_resp)
        responses = [fake_http1, fake_http2]
        with self._stubs(responses) as query:
            result = self.changed(changed=True)
            succ_msg = "Successfully read config on repo '%s'." % repo
            self.assertEqual(result['message'], succ_msg)
            self.assertEqual(query.call_count, 2)

    def test_with_artifactory_url_repo_auth_token_state_present(self):
        repo = 'test'
        set_module_args(dict(artifactory_url=self.fake_url, name=repo,
                             auth_token='derp', state='present',
                             rclass='local'))
        http_resp = '{"key": "%s"}' % repo
        fake_http1 = self.FakeHttpResp("[%s]" % http_resp)
        fake_http2 = self.FakeHttpResp(http_resp)
        fake_http3 = self.FakeHttpResp(http_resp)
        responses = [fake_http1, fake_http2, fake_http3]
        with self._stubs(responses) as query:
            result = self.changed()
            succ_msg = ("Repo '%s' was not updated because config was "
                        "identical." % repo)
            self.assertEqual(result['message'], succ_msg)
            self.assertEqual(query.call_count, 3)
