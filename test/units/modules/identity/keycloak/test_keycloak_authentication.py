import collections
import os

from ansible.modules.identity.keycloak import keycloak_authentication
from units.modules.utils import AnsibleExitJson, AnsibleFailJson, ModuleTestCase, set_module_args

class KeycloakAuthenticationTestCase(ModuleTestCase):
    addExecutionToAuthenticationFlowWithoutCopy = {
        "url":  "http://localhost:18081/auth",
        "username": "admin",
        "password": "admin",
        "realm": "master",
        "alias": "Test add execution to authentication flow without copy",
        "providerId": "basic-flow",
        "authenticationExecutions": [
            {
                "providerId": "identity-provider-redirector",
                "requirement": "ALTERNATIVE",
                "authenticationConfig": {
                    "alias": "name",
                    "config": {
                        "defaultProvider": "value"
                    }
                }
            }
        ], 
        "state":"present",
        "force":False
    }
    authenticationFlowNotChanged = {
        "url":  "http://localhost:18081/auth",
        "username": "admin",
        "password": "admin",
        "realm": "master",
        "alias": "Test authentication flow not changed",
        "copyFrom": "first broker login",
        "authenticationExecutions": [
            {
                "providerId": "identity-provider-redirector",
                "requirement": "ALTERNATIVE",
                "authenticationConfig": {
                    "alias": "name",
                    "config": {
                        "defaultProvider": "value"
                    }
                }
            }
        ], 
        "state":"present",
        "force":False
    }
    modifyAuthenticationFlow = {
        "url":  "http://localhost:18081/auth",
        "username": "admin",
        "password": "admin",
        "realm": "master",
        "alias": "Test modify authentication flow",
        "copyFrom": "first broker login",
        "authenticationExecutions": [
            {
                "providerId": "identity-provider-redirector",
                "requirement": "ALTERNATIVE",
                "authenticationConfig": {
                    "alias": "name",
                    "config": {
                        "defaultProvider": "value"
                    }
                }
            }
        ],
        "state":"present",
        "force":False
    }
    deleteAuthenticationFlow = {
        "url":  "http://localhost:18081/auth",
        "username": "admin",
        "password": "admin",
        "realm": "master",
        "alias": "Test delete authentication flow",
        "copyFrom": "first broker login",
        "authenticationExecutions": [
            {
                "providerId": "identity-provider-redirector",
                "requirement": "ALTERNATIVE",
                "authenticationConfig": {
                    "alias": "name",
                    "config": {
                        "defaultProvider": "value"
                    }
                }
            }
        ], 
        "state":"present",
        "force":False
    }
    def setUp(self):
        super(KeycloakAuthenticationTestCase, self).setUp()
        self.module = keycloak_authentication
        set_module_args(self.addExecutionToAuthenticationFlowWithoutCopy)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        set_module_args(self.authenticationFlowNotChanged)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        set_module_args(self.modifyAuthenticationFlow)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        set_module_args(self.deleteAuthenticationFlow)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
 
    def tearDown(self):
        super(KeycloakAuthenticationTestCase, self).tearDown()
                
    def test_create_authentication_flow_copy(self):
        toCreate = {
            "url":  "http://localhost:18081/auth",
            "username": "admin",
            "password": "admin",
            "realm": "master",
            "alias": "Test create authentication flow copy",
            "copyFrom": "first broker login",
            "authenticationExecutions":[
                {
                    "providerId": "identity-provider-redirector",
                    "requirement": "ALTERNATIVE",
                    "authenticationConfig": {
                        "alias": "name",
                        "config": {
                            "defaultProvider": "value"
                        }
                    }
                },
            ], 
            "state":"present",
            "force":False
        }

        set_module_args(toCreate)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.assertTrue(results.exception.args[0]['changed'])
        self.assertEquals(results.exception.args[0]["flow"]["alias"], toCreate["alias"], results.exception.args[0]["flow"]["alias"] + "is not" + toCreate["alias"] )
        for expectedExecutions in toCreate["authenticationExecutions"]:
            executionFound = False
            for execution in results.exception.args[0]["flow"]["authenticationExecutions"]:
                if "providerId" in execution and execution["providerId"] == expectedExecutions["providerId"]:
                    executionFound = True
                    break
            self.assertTrue(executionFound, "Execution " + expectedExecutions["providerId"] + " not found")
            self.assertEquals(execution["requirement"], expectedExecutions["requirement"], execution["requirement"] + " is not equals to " + expectedExecutions["requirement"])
            for key in expectedExecutions["authenticationConfig"]["config"]:
                self.assertEquals(expectedExecutions["authenticationConfig"]["config"][key], execution["authenticationConfig"]["config"][key], execution["authenticationConfig"]["config"][key] + " is not equals to " + expectedExecutions["authenticationConfig"]["config"][key])

    def test_create_authentication_flow_set_update_profile_on_first_login_to_on(self):
        toCreate = {
            "url":  "http://localhost:18081/auth",
            "username": "admin",
            "password": "admin",
            "realm": "master",
            "alias": "Test create authentication flow set update profile on first login to on",
            "copyFrom": "first broker login",
            "authenticationExecutions": [
                {
                    "providerId": "idp-review-profile",
                    "requirement": "REQUIRED",
                    "authenticationConfig": {
                        "alias": "New review profile config",
                        "config": {
                            "update.profile.on.first.login": "on"
                        }
                    } 
                },
            ], 
            "state":"present",
            "force":False
        }

        set_module_args(toCreate)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.assertTrue(results.exception.args[0]['changed'])
        self.assertEquals(results.exception.args[0]["flow"]["alias"], toCreate["alias"], results.exception.args[0]["flow"]["alias"] + "is not" + toCreate["alias"] )
        for expectedExecutions in toCreate["authenticationExecutions"]:
            executionFound = False
            for execution in results.exception.args[0]["flow"]["authenticationExecutions"]:
                if "providerId" in execution and execution["providerId"] == expectedExecutions["providerId"]:
                    executionFound = True
                    break
            self.assertTrue(executionFound, "Execution " + expectedExecutions["providerId"] + " not found")
            self.assertEquals(execution["requirement"], expectedExecutions["requirement"], execution["requirement"] + " is not equals to " + expectedExecutions["requirement"])
            for key in expectedExecutions["authenticationConfig"]["config"]:
                self.assertEquals(expectedExecutions["authenticationConfig"]["config"][key], execution["authenticationConfig"]["config"][key], execution["authenticationConfig"]["config"][key] + " is not equals to " + expectedExecutions["authenticationConfig"]["config"][key])
        
    def test_create_authentication_flow_without_copy(self):
        toCreate = {
            "url":  "http://localhost:18081/auth",
            "username": "admin",
            "password": "admin",
            "realm": "master",
            "alias": "Test create authentication flow without copy",
            "providerId": "basic-flow",
            "authenticationExecutions": [
                {
                    "providerId": "identity-provider-redirector",
                    "requirement": "ALTERNATIVE",
                    "authenticationConfig": {
                        "alias": "name",
                        "config": {
                            "defaultProvider": "value"
                        }
                    }
                }
            ], 
            "state":"present",
            "force":False
        }

        set_module_args(toCreate)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.assertTrue(results.exception.args[0]['changed'])
        self.assertEquals(results.exception.args[0]["flow"]["alias"], toCreate["alias"], results.exception.args[0]["flow"]["alias"] + "is not" + toCreate["alias"] )
        for expectedExecutions in toCreate["authenticationExecutions"]:
            executionFound = False
            for execution in results.exception.args[0]["flow"]["authenticationExecutions"]:
                if "providerId" in execution and execution["providerId"] == expectedExecutions["providerId"]:
                    executionFound = True
                    break
            self.assertTrue(executionFound, "Execution " + expectedExecutions["providerId"] + " not found")
            self.assertEquals(execution["requirement"], expectedExecutions["requirement"], execution["requirement"] + " is not equals to " + expectedExecutions["requirement"])
            for key in expectedExecutions["authenticationConfig"]["config"]:
                self.assertEquals(expectedExecutions["authenticationConfig"]["config"][key], execution["authenticationConfig"]["config"][key], execution["authenticationConfig"]["config"][key] + " is not equals to " + expectedExecutions["authenticationConfig"]["config"][key])

    def test_create_authentication_flow_with_two_executions_without_copy(self):
        toCreate = {
            "url":  "http://localhost:18081/auth",
            "username": "admin",
            "password": "admin",
            "realm": "master",
            "alias": "Test create authentication flow with two executions without copy",
            "providerId": "basic-flow",
            "authenticationExecutions": [
                {
                    "providerId": "identity-provider-redirector",
                    "requirement": "ALTERNATIVE",
                    "authenticationConfig": {
                        "alias": "name",
                        "config": {
                            "defaultProvider": "value"
                        }
                    }
                },
                {
                    "providerId": "auth-conditional-otp-form",
                    "requirement": "REQUIRED",
                    "authenticationConfig": {
                        "alias": "test-conditional-otp",
                        "config": {
                            "skipOtpRole": "admin",
                            "forceOtpRole": "broker.read-token",
                            "defaultOtpOutcome": "skip"
                        }
                    }
                }
            ], 
            "state":"present",
            "force":False
        }

        set_module_args(toCreate)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.assertTrue(results.exception.args[0]['changed'])
        self.assertEquals(results.exception.args[0]["flow"]["alias"], toCreate["alias"], results.exception.args[0]["flow"]["alias"] + "is not" + toCreate["alias"] )
        for expectedExecutions in toCreate["authenticationExecutions"]:
            executionFound = False
            for execution in results.exception.args[0]["flow"]["authenticationExecutions"]:
                if "providerId" in execution and execution["providerId"] == expectedExecutions["providerId"]:
                    executionFound = True
                    break
            self.assertTrue(executionFound, "Execution " + expectedExecutions["providerId"] + " not found")
            self.assertEquals(execution["requirement"], expectedExecutions["requirement"], execution["requirement"] + " is not equals to " + expectedExecutions["requirement"])
            for key in expectedExecutions["authenticationConfig"]["config"]:
                self.assertEquals(expectedExecutions["authenticationConfig"]["config"][key], execution["authenticationConfig"]["config"][key], execution["authenticationConfig"]["config"][key] + " is not equals to " + expectedExecutions["authenticationConfig"]["config"][key])
                
    def test_add_execution_to_authentication_flow_without_copy(self):
        executionToAdd = {
            "providerId": "auth-conditional-otp-form",
            "requirement": "ALTERNATIVE",
            "authenticationConfig": {
                "alias": "test-conditional-otp",
                "config": {
                    "skipOtpRole": "admin",
                    "forceOtpRole": "broker.read-token",
                    "defaultOtpOutcome": "skip"
                }
            }
        }
        self.addExecutionToAuthenticationFlowWithoutCopy["authenticationExecutions"].append(executionToAdd)
        set_module_args(self.addExecutionToAuthenticationFlowWithoutCopy)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.assertTrue(results.exception.args[0]['changed'])
        self.assertEquals(results.exception.args[0]["flow"]["alias"], self.addExecutionToAuthenticationFlowWithoutCopy["alias"], results.exception.args[0]["flow"]["alias"] + "is not" + self.addExecutionToAuthenticationFlowWithoutCopy["alias"] )
        for expectedExecutions in self.addExecutionToAuthenticationFlowWithoutCopy["authenticationExecutions"]:
            executionFound = False
            for execution in results.exception.args[0]["flow"]["authenticationExecutions"]:
                if "providerId" in execution and execution["providerId"] == expectedExecutions["providerId"]:
                    executionFound = True
                    break
            self.assertTrue(executionFound, "Execution " + expectedExecutions["providerId"] + " not found")
            self.assertEquals(execution["requirement"], expectedExecutions["requirement"], execution["requirement"] + " is not equals to " + expectedExecutions["requirement"])
            for key in expectedExecutions["authenticationConfig"]["config"]:
                self.assertEquals(expectedExecutions["authenticationConfig"]["config"][key], execution["authenticationConfig"]["config"][key], execution["authenticationConfig"]["config"][key] + " is not equals to " + expectedExecutions["authenticationConfig"]["config"][key])

    def test_authentication_flow_not_changed(self):
        set_module_args(self.authenticationFlowNotChanged)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.assertFalse(results.exception.args[0]['changed'])

    def test_modify_authentication_flow(self):
        self.modifyAuthenticationFlow["authenticationExecutions"][0]["authenticationConfig"]["config"]["defaultProvider"] = "modified value"
        set_module_args(self.modifyAuthenticationFlow)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.assertTrue(results.exception.args[0]['changed'])
        self.assertEquals(results.exception.args[0]["flow"]["alias"], self.modifyAuthenticationFlow["alias"], results.exception.args[0]["flow"]["alias"] + "is not" + self.modifyAuthenticationFlow["alias"] )
        for expectedExecutions in self.modifyAuthenticationFlow["authenticationExecutions"]:
            executionFound = False
            for execution in results.exception.args[0]["flow"]["authenticationExecutions"]:
                if "providerId" in execution and execution["providerId"] == expectedExecutions["providerId"]:
                    executionFound = True
                    break
            self.assertTrue(executionFound, "Execution " + expectedExecutions["providerId"] + " not found")
            self.assertEquals(execution["requirement"], expectedExecutions["requirement"], execution["requirement"] + " is not equals to " + expectedExecutions["requirement"])
            for key in expectedExecutions["authenticationConfig"]["config"]:
                self.assertEquals(expectedExecutions["authenticationConfig"]["config"][key], execution["authenticationConfig"]["config"][key], execution["authenticationConfig"]["config"][key] + " is not equals to " + expectedExecutions["authenticationConfig"]["config"][key])
        
    def test_delete_authentication_flow(self):
        self.deleteAuthenticationFlow['state'] = 'absent'
        set_module_args(self.deleteAuthenticationFlow)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.assertTrue(results.exception.args[0]['changed'])
        self.assertRegexpMatches(results.exception.args[0]['msg'], 'deleted', 'authentication flow not deleted')

    def test_delete_inexisting_authentication_flow(self):
        toDelete = {
            "url":  "http://localhost:18081/auth",
            "username": "admin",
            "password": "admin",
            "realm": "master",
            "alias": "Test delete inexisting authentication flow",
            "state":"absent",
            "force":False
        }
        set_module_args(toDelete)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.assertFalse(results.exception.args[0]['changed'])
        self.assertRegexpMatches(results.exception.args[0]['msg'], 'absent', 'authentication flow is not absent')
