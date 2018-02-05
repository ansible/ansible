import json

from ansible.compat.tests.mock import patch
from ansible.compat.tests.unittest import TestCase
from ansible.module_utils import artifactory as ar_base
from ansible.modules.packaging import artifactory_security as art_s

from contextlib import contextmanager

from units.modules.utils import set_module_args, AnsibleExitJson, AnsibleFailJson, ModuleTestCase


class TestArtifactorySecurity(TestCase):

    def setUp(self):
        self.fake_url = "http://www.fake.com/api/security/groups"
        self.base_update_conf = dict(placeholder='whatever')
        self.repo_uri_map = art_s.URI_CONFIG_MAP

    @contextmanager
    def _stubs(self, url=None, name=None, test_config=None, responses=None):
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
            self.build_out_test_contruct(temp_url, name, temp_test_config)
            if responses:
                http_responses = []
                for resp in responses:
                    http_responses.append(resp)
                query_resp.side_effect = http_responses
            yield query_resp

    def build_out_test_contruct(self, url, name, test_config):
        self.arm = art_s.ArtifactorySecurity(
            artifactory_url=url,
            name=name,
            sec_config=test_config,
            config_map=self.repo_uri_map)

    def test_get_valid_conf_invalid_post_bad_url(self):
        temp_url = "bad.url.com"
        with self.assertRaises(ar_base.InvalidArtifactoryURL):
            with self._stubs(url=temp_url):
                self.arm.get_valid_conf("POST")

    def test_get_valid_conf_invalid_put_bad_url(self):
        temp_url = "bad.url.com"
        with self.assertRaises(ar_base.InvalidArtifactoryURL):
            with self._stubs(url=temp_url):
                self.arm.get_valid_conf("PUT")

    def test_get_valid_conf_valid_conf_post_groups(self):
        with self._stubs():
            self.arm.get_valid_conf("POST")

    def test_get_valid_conf_valid_conf_put_groups(self):
        with self._stubs():
            self.arm.get_valid_conf("PUT")

    def test_get_valid_conf_valid_conf_put_permissions(self):
        test_config = {"repositories": ['whatever']}
        temp_url = "api/security/permissions"
        with self._stubs(url=temp_url, test_config=test_config):
            self.arm.get_valid_conf("PUT")

    def test_get_valid_conf_invalid_conf_put_permissions(self):
        temp_url = "api/security/permissions"
        test_config = {"not_repositories": ['whatever']}
        with self.assertRaises(ar_base.InvalidConfigurationData):
            with self._stubs(url=temp_url, test_config=test_config):
                self.arm.get_valid_conf("PUT")

    def test_get_valid_conf_valid_conf_post_permissions(self):
        temp_url = "api/security/permissions"
        test_config = {"not_repositories": ['whatever']}
        with self._stubs(url=temp_url, test_config=test_config):
            self.arm.get_valid_conf("POST")

    def test_get_valid_conf_valid_conf_post_users(self):
        test_config = {"email": 'test@email.com', "password": "pass"}
        temp_url = "api/security/users"
        with self._stubs(url=temp_url, test_config=test_config):
            self.arm.get_valid_conf("PUT")

    def test_get_valid_conf_invalid_conf_put_users_noemail(self):
        test_config = {"not_email": 'test@email.com', "password": "pass"}
        temp_url = "api/security/users"
        with self.assertRaises(ar_base.InvalidConfigurationData):
            with self._stubs(url=temp_url, test_config=test_config):
                self.arm.get_valid_conf("PUT")

    def test_get_valid_conf_invalid_conf_put_users_nopassword(self):
        test_config = {"email": 'test@email.com', "no_password": "pass"}
        temp_url = "api/security/users"
        with self.assertRaises(ar_base.InvalidConfigurationData):
            with self._stubs(url=temp_url, test_config=test_config):
                self.arm.get_valid_conf("PUT")

    def test_get_valid_conf_invalid_conf_put_users_nopassword_or_email(self):
        test_config = {"no_email": 'test@email.com', "no_password": "pass"}
        temp_url = "api/security/users"
        with self.assertRaises(ar_base.InvalidConfigurationData):
            with self._stubs(url=temp_url, test_config=test_config):
                self.arm.get_valid_conf("PUT")

    def test_get_valid_conf_valid_conf_post_users_nopassword_or_email(self):
        test_config = {"no_email": 'test@email.com', "no_password": "pass"}
        temp_url = "api/security/users"
        with self._stubs(url=temp_url, test_config=test_config):
            self.arm.get_valid_conf("POST")


class TestArtifactorySecurityModule(ModuleTestCase):
    def setUp(self):
        super(TestArtifactorySecurityModule, self).setUp()
        self.module = art_s
        self.fake_url = "http://www.fake.com/api/security/users"

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

    def test_missing_artifactory_url_and_name(self):
        set_module_args(dict())
        result = self.failed()
        self.assertTrue("missing required arguments" in result["msg"])
        self.assertTrue("name" in result["msg"])
        self.assertTrue("artifactory_url" in result["msg"])

    def test_missing_name(self):
        set_module_args(dict(artifactory_url=self.fake_url))
        result = self.failed()
        self.assertTrue("missing required arguments" in result["msg"])
        self.assertTrue("name" in result["msg"])

    def test_missing_artifactory_url(self):
        set_module_args(dict(name='test'))
        result = self.failed()
        self.assertTrue("missing required arguments" in result["msg"])
        self.assertTrue("artifactory_url" in result["msg"])

    def test_with_artifactory_url_and_name(self):
        set_module_args(dict(artifactory_url=self.fake_url, name='test'))
        result = self.failed()
        self.assertTrue("one of the following is required" in result["msg"])
        self.assertTrue("password" in result["msg"])
        self.assertTrue("auth_token" in result["msg"])

    def test_with_artifactory_url_name_auth_token(self):
        repo = 'test'
        set_module_args(dict(artifactory_url=self.fake_url, name=repo,
                             auth_token='derp', state='read'))
        http_resp = '[{"key": "%s"}]' % repo
        fake_http1 = self.FakeHttpResp(http_resp)
        fake_http2 = self.FakeHttpResp(http_resp)
        responses = [fake_http1, fake_http2]
        with self._stubs(responses) as query:
            result = self.changed(changed=True)
            succ_msg = "Successfully read config on target '%s'." % repo
            self.assertEqual(result['message'], succ_msg)
            self.assertEqual(query.call_count, 2)

    def test_with_artifactory_url_repo_auth_token_state_present(self):
        repo = 'test'
        set_module_args(dict(artifactory_url=self.fake_url, name=repo,
                             auth_token='derp', state='present'))
        http_resp = '{"key": "%s"}' % repo
        fake_http1 = self.FakeHttpResp("[%s]" % http_resp)
        fake_http2 = self.FakeHttpResp(http_resp)
        fake_http3 = self.FakeHttpResp(http_resp)
        responses = [fake_http1, fake_http2, fake_http3]
        with self._stubs(responses) as query:
            result = self.changed()
            succ_msg = ("Target '%s' was not updated because config was "
                        "identical." % repo)
            self.assertEqual(result['message'], succ_msg)
            self.assertEqual(query.call_count, 3)
