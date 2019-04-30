import collections
import os
import copy
from ansible.modules.identity.keycloak import keycloak_identity_provider
from units.modules.utils import AnsibleExitJson, AnsibleFailJson, ModuleTestCase, set_module_args

class KeycloakIdentityProviderTestCase(ModuleTestCase):

    toCreateIdP = {
        "auth_username": "admin", 
        "auth_password": "admin",
        "realm": "master",
        "auth_keycloak_url": "http://localhost:18081/auth",
        "alias": "test_create_idp",
        "providerId": "oidc",
        "displayName": "test_create_idp",
        "enabled": True,
        "updateProfileFirstLoginMode": "on",
        "trustEmail": False,
        "storeToken": True,
        "addReadTokenRoleOnCreate": True,
        "authenticateByDefault": False,
        "linkOnly": False,
        "firstBrokerLoginFlowAlias": "first broker login",
        "config": {
            "openIdConfigurationUrl": "http://localhost:18081/auth/realms/master/.well-known/openid-configuration",
            "clientId": "test",
            "defaultScope": "openid email profile",
            "disableUserInfo": "false",
            "guiOrder": "1",
            "backchannelSupported": "false"
        },
        "mappers": [ 
            {
                "name": "test",
                "identityProviderMapper": "oidc-user-attribute-idp-mapper", 
                "config" : {
                    "claim" : "test",
                    "user.attribute": "lastname"
                    }
            }, 
            {
                "name" : "test2",
                "identityProviderMapper": "oidc-user-attribute-idp-mapper", 
                "config" : {
                    "claim": "test2",
                    "user.attribute":"firstname"
                }
            },
            {
                "name" : "test3",
                "identityProviderMapper": "oidc-role-idp-mapper", 
                "config" : {
                    "claim": "claimName",
                    "claim.value": "valueThatGiveRole",
                    "role": "roleName"
                }
            }

        ],
        "state": "absent",
        "force": False
    }

    toDoNotChange = {
        "auth_username": "admin", 
        "auth_password": "admin",
        "realm": "master",
        "auth_keycloak_url": "http://localhost:18081/auth",
        "alias": "test_idp_not_changed",
        "providerId": "oidc",
        "displayName": "test idp not changed",
        "enabled": True,
        "updateProfileFirstLoginMode": "on",
        "trustEmail": False,
        "storeToken": True,
        "addReadTokenRoleOnCreate": True,
        "authenticateByDefault": False,
        "linkOnly": False,
        "firstBrokerLoginFlowAlias": "first broker login",
        "config": { 
            "openIdConfigurationUrl": "http://localhost:18081/auth/realms/master/.well-known/openid-configuration",
            "clientId": "test1",
            "defaultScope": "openid email profile",
            "disableUserInfo": "false",
            "guiOrder": "1",
            "backchannelSupported": "true"
            },
        "mappers": [ 
                {
                    "name": "test11",
                    "identityProviderMapper": "oidc-user-attribute-idp-mapper", 
                    "config" : {
                        "claim" : "test",
                        "user.attribute": "lastname"
                        }
                }, 
                {
                    "name" : "test12",
                    "identityProviderMapper": "oidc-user-attribute-idp-mapper", 
                    "config" : {
                        "claim": "test2",
                        "user.attribute":"firstname"
                    }
                },
                {
                    "name" : "test13",
                    "identityProviderMapper": "oidc-role-idp-mapper", 
                    "config" : {
                        "claim": "claimName",
                        "claim.value": "valueThatGiveRole",
                        "role": "roleName"
                    }
                }

            ],
        "state": "present",
        "force": False
    }
    toModifyIdp = {
        "auth_username": "admin", 
        "auth_password": "admin",
        "realm": "master",
        "auth_keycloak_url": "http://localhost:18081/auth",
        "alias": "test_modify_idp",
        "providerId": "oidc",
        "displayName": "test modify idp",
        "enabled": True,
        "updateProfileFirstLoginMode": "on",
        "trustEmail": False,
        "storeToken": True,
        "addReadTokenRoleOnCreate": True,
        "authenticateByDefault": False,
        "linkOnly": False,
        "firstBrokerLoginFlowAlias": "first broker login",
        "config": {
            "openIdConfigurationUrl": "http://localhost:18081/auth/realms/master/.well-known/openid-configuration",
            "clientId": "test2",
            "defaultScope": "openid email profile",
            "disableUserInfo": "false",
            "guiOrder": "1",
            "backchannelSupported": "true"
        },
        "mappers": [ 
            {
                "name": "test21",
                "identityProviderMapper": "oidc-user-attribute-idp-mapper", 
                "config" : {
                    "claim" : "test",
                    "user.attribute": "lastname"
                }
            }, 
            {
                "name" : "test22",
                "identityProviderMapper": "oidc-user-attribute-idp-mapper", 
                "config" : {
                    "claim": "test2",
                    "user.attribute":"firstname"
                }
            },
            {
                "name" : "test23",
                "identityProviderMapper": "oidc-role-idp-mapper", 
                "config" : {
                    "claim": "claimName",
                    "claim.value": "valueThatGiveRole",
                    "role": "roleName"
                }
            }

        ],
        "state": "present",
        "force": False
    }
    toModifyIdpForce = {
        "auth_username": "admin", 
        "auth_password": "admin",
        "realm": "master",
        "auth_keycloak_url": "http://localhost:18081/auth",
        "alias": "test_modify_idp_force",
        "providerId": "oidc",
        "displayName": "Test the force option for modify",
        "enabled": True,
        "updateProfileFirstLoginMode": "on",
        "trustEmail": False,
        "storeToken": False,
        "addReadTokenRoleOnCreate": True,
        "authenticateByDefault": False,
        "linkOnly": False,
        "firstBrokerLoginFlowAlias": "first broker login",
        "config": {
            "openIdConfigurationUrl": "http://localhost:18081/auth/realms/master/.well-known/openid-configuration",
            "clientId": "test2",
            "defaultScope": "openid email profile",
            "disableUserInfo": "false",
            "guiOrder": "1",
            "backchannelSupported": "true"
        },
        "mappers": [ 
            {
                "name": "test21",
                "identityProviderMapper": "oidc-user-attribute-idp-mapper", 
                "config" : {
                    "claim" : "test",
                    "user.attribute": "lastname"
                    }
            }, 
            {
                "name" : "test22",
                "identityProviderMapper": "oidc-user-attribute-idp-mapper", 
                "config" : {
                    "claim": "test2",
                    "user.attribute":"firstname"
                }
            },
            {
                "name" : "test23",
                "identityProviderMapper": "oidc-role-idp-mapper", 
                "config" : {
                    "claim": "claimName",
                    "claim.value": "valueThatGiveRole",
                    "role": "roleName"
                }
            }

        ],
        "state": "present",
        "force": False
    }
    toModifyIdpMappers = {
        "auth_username": "admin", 
        "auth_password": "admin",
        "realm": "master",
        "auth_keycloak_url": "http://localhost:18081/auth",
        "alias": "test_modify_idp_mappers",
        "providerId": "oidc",
        "displayName": "test modify idp mappers",
        "enabled": True,
        "updateProfileFirstLoginMode": "on",
        "trustEmail": False,
        "storeToken": True,
        "addReadTokenRoleOnCreate": True,
        "authenticateByDefault": False,
        "linkOnly": False,
        "firstBrokerLoginFlowAlias": "first broker login",
        "config": {
            "openIdConfigurationUrl": "http://localhost:18081/auth/realms/master/.well-known/openid-configuration",
            "clientId": "test2",
            "defaultScope": "openid email profile",
            "disableUserInfo": "false"
        },
        "mappers": [ 
            {
                "name": "test21",
                "identityProviderMapper": "oidc-user-attribute-idp-mapper", 
                "config" : {
                    "claim" : "test",
                    "user.attribute": "lastname"
                    }
            }, 
            {
                "name" : "test22",
                "identityProviderMapper": "oidc-user-attribute-idp-mapper", 
                "config" : {
                    "claim": "test2",
                    "user.attribute":"firstname"
                }
            },
            {
                "name" : "test23",
                "identityProviderMapper": "oidc-role-idp-mapper", 
                "config" : {
                    "claim": "claimName",
                    "claim.value": "valueThatGiveRole",
                    "role": "roleName"
                }
            }

        ],
        "state": "present",
        "force": False
    }

    toModifyIdpRemoveMappers = {
        "auth_username": "admin",
        "auth_password":"admin",
        "realm": "master",
        "auth_keycloak_url": "http://localhost:18081/auth",
        "alias": "test_modify_idp_remove_mappers",
        "providerId": "oidc",
        "displayName": "Test removal of mappers",
        "enabled": True,
        "updateProfileFirstLoginMode": "on",
        "trustEmail": False,
        "storeToken": True,
        "addReadTokenRoleOnCreate": True,
        "authenticateByDefault": False,
        "linkOnly": False,
        "firstBrokerLoginFlowAlias": "first broker login",
        "config": {
            "openIdConfigurationUrl": "http://localhost:18081/auth/realms/master/.well-known/openid-configuration",
            "clientId": "test2",
            "defaultScope": "openid email profile",
            "disableUserInfo": "false"
        },
        "mappers": [
            {
                "name": "thismapperissupposedtostay",
                "identityProviderMapper": "oidc-user-attribute-idp-mapper", 
                "config" : {
                    "claim" : "newTest",
                    "user.attribute": "lastname"
                    },
                "state": "present"
            },
            {
                "name" : "thismapperissupposedtobedeleted",
                "identityProviderMapper": "oidc-role-idp-mapper", 
                "config" : {
                    "claim": "claimName",
                    "claim.value": "valueThatGiveRole",
                    "role": "roleName"
                    },
                "state": "present"
                }
             ],
            "state": "present",
            "force": False
        }
    
    toDeleteIdp = {
        "auth_username": "admin", 
        "auth_password": "admin",
        "realm": "master",
        "auth_keycloak_url": "http://localhost:18081/auth",
        "alias": "test_delete_idp",
        "providerId": "oidc",
        "displayName": "Test delete IdP",
        "enabled": True,
        "updateProfileFirstLoginMode": "on",
        "trustEmail": False,
        "storeToken": True,
        "addReadTokenRoleOnCreate": True,
        "authenticateByDefault": False,
        "linkOnly": False,
        "firstBrokerLoginFlowAlias": "first broker login",
        "config": {
            "openIdConfigurationUrl": "http://localhost:18081/auth/realms/master/.well-known/openid-configuration",
            "clientId": "test2",
            "defaultScope": "openid email profile",
            "disableUserInfo": "false",
            "guiOrder": "1",
            "backchannelSupported": "true"
        },
        "mappers": [ 
            {
                "name": "test21",
                "identityProviderMapper": "oidc-user-attribute-idp-mapper", 
                "config" : {
                    "claim" : "test",
                    "user.attribute": "lastname"
                    }
            }, 
            {
                "name" : "test22",
                "identityProviderMapper": "oidc-user-attribute-idp-mapper", 
                "config" : {
                    "claim": "test2",
                    "user.attribute":"firstname"
                }
            },
            {
                "name" : "test23",
                "identityProviderMapper": "oidc-role-idp-mapper", 
                "config" : {
                    "claim": "claimName",
                    "claim.value": "valueThatGiveRole",
                    "role": "roleName"
                }
            }

        ],
        "state": "present",
        "force": False
    }
    toChangeIdPClientSecret = {
        "auth_username": "admin", 
        "auth_password": "admin",
        "realm": "master",
        "auth_keycloak_url": "http://localhost:18081/auth",
        "alias": "test_change_client_secret",
        "providerId": "oidc",
        "displayName": "Test change IdP client secret",
        "config": {
            "openIdConfigurationUrl": "http://localhost:18081/auth/realms/master/.well-known/openid-configuration",
            "clientId": "test2",
            "defaultScope": "openid email profile",
            "disableUserInfo": "false",
            "guiOrder": "1",
            "backchannelSupported": "true"
        },
        "state": "present",
        "force": False
    }

    def setUp(self):
        super(KeycloakIdentityProviderTestCase, self).setUp()
        self.module = keycloak_identity_provider
        set_module_args(self.toCreateIdP)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        set_module_args(self.toDoNotChange)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        set_module_args(self.toModifyIdp)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        set_module_args(self.toModifyIdpForce)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        set_module_args(self.toModifyIdpMappers)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        set_module_args(self.toModifyIdpRemoveMappers)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        set_module_args(self.toDeleteIdp)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        set_module_args(self.toChangeIdPClientSecret)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
 
    def tearDown(self):
        super(KeycloakIdentityProviderTestCase, self).tearDown()
 
    def test_create_idp(self):
        toCreate = self.toCreateIdP.copy()
        toCreate["state"] = "present"
        set_module_args(toCreate)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.assertTrue(results.exception.args[0]['changed'])
        self.assertTrue(results.exception.args[0]['idp']['enabled'])
        self.assertEquals(results.exception.args[0]['idp']['alias'],toCreate["alias"], 'Alias = ' + results.exception.args[0]['idp']['alias'])
        self.assertEquals(results.exception.args[0]['idp']['config']['clientId'],toCreate["config"]["clientId"],"ClientId: " + results.exception.args[0]['idp']['config']['clientId'])
        self.assertEquals(results.exception.args[0]['idp']['config']['guiOrder'], toCreate["config"]["guiOrder"],"GuiOrder: " + results.exception.args[0]['idp']['config']['guiOrder'] + ": " + toCreate["config"]["guiOrder"])
        for mapperToCreate in toCreate["mappers"]:
            mapperFound = False
            for mapper in results.exception.args[0]['mappers']:
                if mapper["name"] == mapperToCreate["name"]:
                    mapperFound = True
                    self.assertEquals(mapper["identityProviderMapper"], mapperToCreate["identityProviderMapper"], "identityProviderMapper: " + mapper["identityProviderMapper"] + "not equal " + mapperToCreate["identityProviderMapper"])
                    self.assertDictEqual(mapper["config"], mapperToCreate["config"], "config: " + str(mapper["config"]) + "not equal " + str(mapperToCreate["config"]))
            self.assertTrue(mapperFound, "mapper " + mapperToCreate["name"] + " not found")                                          
        
    def test_idp_not_changed(self):
        set_module_args(self.toDoNotChange)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.assertFalse(results.exception.args[0]['changed'])
        self.assertEquals(results.exception.args[0]['idp']['alias'],self.toDoNotChange['alias'], 'Alias = ' + results.exception.args[0]['idp']['alias'])
        for mapperToDoNotChange in self.toDoNotChange["mappers"]:
            mapperFound = False
            for mapper in results.exception.args[0]['mappers']:
                if mapper["name"] == mapperToDoNotChange["name"]:
                    mapperFound = True
                    self.assertEquals(mapper["identityProviderMapper"], mapperToDoNotChange["identityProviderMapper"], "identityProviderMapper: " + mapper["identityProviderMapper"] + "not equal " + mapperToDoNotChange["identityProviderMapper"])
                    self.assertDictEqual(mapper["config"], mapperToDoNotChange["config"], "config: " + str(mapper["config"]) + "not equal " + str(mapperToDoNotChange["config"]))
            self.assertTrue(mapperFound, "mapper " + mapperToDoNotChange["name"] + " not found")                                          

    def test_modify_idp(self):
        newToChange = {
            "auth_username": "admin",
            "auth_password":"admin",
            "realm": "master",
            "auth_keycloak_url": "http://localhost:18081/auth",
            "alias": "test_modify_idp",
            "providerId": "oidc",
            "storeToken": False,
            "firstBrokerLoginFlowAlias": "registration",
            "config": { 
                "openIdConfigurationUrl": "http://localhost:18081/auth/realms/master/.well-known/openid-configuration",
                "clientId": "test2",
                "defaultScope": "openid email profile",
                "disableUserInfo": "false",
                "guiOrder": "2"
                },
            "state": "present",
            "force": False
        }
        
        set_module_args(newToChange)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.assertTrue(results.exception.args[0]['changed'])
        self.assertEquals(results.exception.args[0]['idp']['alias'],newToChange["alias"], 'Alias = ' + results.exception.args[0]['idp']['alias'])
        self.assertFalse(results.exception.args[0]['idp']['storeToken'], 'storeToken should be false : ' + str(results.exception.args[0]['idp']['storeToken']))
        self.assertEquals(results.exception.args[0]['idp']['firstBrokerLoginFlowAlias'], newToChange["firstBrokerLoginFlowAlias"], "firstBrokerLoginFlowAlias: " + results.exception.args[0]['idp']['firstBrokerLoginFlowAlias'])
        self.assertEquals(results.exception.args[0]['idp']['config']['guiOrder'],newToChange["config"]["guiOrder"],"GuiOrder: " + results.exception.args[0]['idp']['config']['guiOrder'])

    def test_modify_idp_force(self):
        newToChange = self.toModifyIdpForce.copy()
        newToChange["force"] = True
        set_module_args(newToChange)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.assertTrue(results.exception.args[0]['changed'])
        
        self.assertEquals(results.exception.args[0]['idp']['alias'],newToChange["alias"], 'Alias = ' + results.exception.args[0]['idp']['alias'])
        self.assertFalse(results.exception.args[0]['idp']['storeToken'], 'storeToken should be false : ' + str(results.exception.args[0]['idp']['storeToken']))
        self.assertEquals(results.exception.args[0]['idp']['firstBrokerLoginFlowAlias'], newToChange["firstBrokerLoginFlowAlias"], "firstBrokerLoginFlowAlias: " + results.exception.args[0]['idp']['firstBrokerLoginFlowAlias'])
        self.assertEquals(results.exception.args[0]['idp']['config']['guiOrder'],newToChange["config"]["guiOrder"],"GuiOrder: " + results.exception.args[0]['idp']['config']['guiOrder'])

    def test_modify_idp_mappers(self):
        newToChange = {
            "auth_username": "admin",
            "auth_password":"admin",
            "realm": "master",
            "auth_keycloak_url": "http://localhost:18081/auth",
            "alias": "test_modify_idp_mappers",
            "providerId": "oidc",
            "mappers": [
                {
                    "name": "test24",
                    "identityProviderMapper": "oidc-user-attribute-idp-mapper", 
                    "config" : {
                        "claim" : "newTest",
                        "user.attribute": "lastname"
                        }
                 },
                {
                    "name" : "test25",
                    "identityProviderMapper": "oidc-role-idp-mapper", 
                    "config" : {
                        "claim": "claimName",
                        "claim.value": "valueThatGiveRole",
                        "role": "roleName"
                        }
                    }
                 ],
                "state": "present",
                "force": False
            }
        set_module_args(newToChange)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.assertTrue(results.exception.args[0]['changed'])        
        self.assertEquals(results.exception.args[0]['idp']['alias'], newToChange["alias"], 'Alias = ' + results.exception.args[0]['idp']['alias'])
        for mapperToChange in newToChange["mappers"]:
            mapperFound = False
            for mapper in results.exception.args[0]['mappers']:
                if mapper["name"] == mapperToChange["name"]:
                    mapperFound = True
                    self.assertEquals(mapper["identityProviderMapper"], mapperToChange["identityProviderMapper"], "identityProviderMapper: " + mapper["identityProviderMapper"] + "not equal " + mapperToChange["identityProviderMapper"])
                    self.assertDictEqual(mapper["config"], mapperToChange["config"], "config: " + str(mapper["config"]) + "not equal " + str(mapperToChange["config"]))
            self.assertTrue(mapperFound, "mapper " + mapperToChange["name"] + " not found")  

    def test_modify_idp_remove_mappers(self):
        toChange = self.toModifyIdpRemoveMappers.copy()
        toChange["mappers"][1]["state"] = "absent"
        set_module_args(toChange)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.assertTrue(results.exception.args[0]['changed'])        
        mapperFound = False
        for mapper in results.exception.args[0]['mappers']:
            if mapper["name"] == toChange['mappers'][1]["name"]:
                mapperFound = True
                break
        self.assertFalse(mapperFound, "mapper " + toChange['mappers'][1]["name"] + " has not been deleted")  

    def test_delete_idp(self):
        toDelete = self.toDeleteIdp.copy()         
        toDelete['state'] = "absent"
        set_module_args(toDelete)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.assertTrue(results.exception.args[0]['changed'])        
        self.assertRegexpMatches(results.exception.args[0]['msg'], 'deleted', 'IdP not deleted')

    def test_change_client_secret(self):
        toChangeSecret = dict(
            auth_username = "admin", 
            auth_password = "admin",
            realm = "master",
            auth_keycloak_url = "http://localhost:18081/auth",
            alias = "test_change_client_secret",
            config = dict(
                clientId = "test4",
                clientSecret = "CeciEstMonSecret"
                ),
            state="present",
            force=False
            )
        set_module_args(toChangeSecret)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.assertTrue(results.exception.args[0]['changed'])
        
    def test_change_client_secret_without_alias(self):
        toChangeSecret = dict(
            auth_username = "admin", 
            auth_password = "admin",
            realm = "master",
            auth_keycloak_url = "http://localhost:18081/auth",
            config = dict(
                clientId = "test4",
                clientSecret = "CeciEstMonSecret"
                ),
            state="present",
            force=False
            )
    
        set_module_args(toChangeSecret)
        with self.assertRaises(AnsibleFailJson) as results:
            self.module.main()
        self.assertTrue(results.exception.args[0]['failed'], 'Test has not failed has it is supposed to.')
        self.assertRegexpMatches(results.exception.args[0]['msg'], 'missing required arguments', 'Wrong error message: ' + results.exception.args[0]['msg'])

