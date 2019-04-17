<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> Sx5-868 Update the keycloak_client module documentation for support of
# -*- coding: utf-8 -*-
# This unit test class need a Keycloak server running on localhost using port 18081.
# An admin user must exist and his password need to be admin.
# Use the following command to run a Keycloak server with Docker:
# docker run -d --rm --name testkc -p 18081:8080 -e KEYCLOAK_USER=admin -e KEYCLOAK_PASSWORD=admin jboss/keycloak:latest

<<<<<<< HEAD
=======
>>>>>>> SX5-868 Manage client roles (add, delete update), remove protocolMappers
=======
>>>>>>> Sx5-868 Update the keycloak_client module documentation for support of
import collections
import os
import unittest

from ansible.modules.identity.keycloak import keycloak_client
from units.modules.utils import AnsibleExitJson, AnsibleFailJson, ModuleTestCase, set_module_args

class KeycloakClientTestCase(ModuleTestCase):
    testClientRoles = [
        {
            "name":"test1",
            "description": "test1",
            "composite": False
            },
        {
            "name":"test2",
            "description": "test2",
            "composite": False
        }
    ]
    testClient = {
        "url": "http://localhost:18081/auth",
        "username": "admin",
        "password": "admin",
        "realm": "master",
        "state": "present",
        "clientId": "basetest",
        "rootUrl": "http://test.com:8080",
        "name": "basetestname",
        "description": "Base testing",
        "publicClient": False,
        "force": False
    }
    toModifyClient = {
        "url": "http://localhost:18081/auth",
        "username": "admin",
        "password": "admin",
        "realm": "master",
        "state": "present",
        "clientId": "test_modify_client",
        "rootUrl": "http://test3.com:8080",
        "name": "Modify client test",
        "description": "This client will be modified",
        "adminUrl": "http://test3.com:8080/admin",
        "baseUrl": "http://test3.com:8080",
        "enabled": True,
        "clientAuthenticatorType": "client-secret",
        "redirectUris": ["http://test3.com:8080/secure"],
        "webOrigins": ["http://test3.com:8080/secure"],
        "consentRequired": False,   
        "standardFlowEnabled": True,
        "implicitFlowEnabled": True,
        "directAccessGrantsEnabled": True,
        "serviceAccountsEnabled": True,
        "fullScopeAllowed": True,
        "protocol": "openid-connect",
        "bearerOnly": False,
        "publicClient": False,
        "roles": [
            {
                "name":"test1",
                "description": "test1",
                "composite": False
            },
            {
                "name":"test2",
                "description": "test2",
                "composite": True,
                "composites": []
            }
        ],
        "protocolMappers": [
            {
                "name": "test1Mapper",
                "protocol": "openid-connect",
                "protocolMapper": "oidc-usermodel-attribute-mapper",
                "consentRequired": False,
                "config": { 
                    "multivalued": 'false',
                    "userinfo.token.claim": False,
                    "user.attribute": "test1",
                    "id.token.claim": 'true',
                    "access.token.claim": 'true',
                    "claim.name": "test1",
                    "jsonType.label": "String"
                    }
                },
                {
                    "name": "test2Mapper",
                    "protocol": "openid-connect",
                    "protocolMapper": "oidc-usermodel-attribute-mapper",
                    "consentRequired": False,
                    "config": { 
                        "multivalued": 'false',
                        "userinfo.token.claim": 'true',
                        "user.attribute": "test2",
                        "id.token.claim": 'true',
                        "access.token.claim": 'true',
                        "claim.name": "test2",
                        "jsonType.label": "String"
                    }
                }
            ]
        }
    
    toAddCompositesForClientRole = {
        "url": "http://localhost:18081/auth",
        "username": "admin",
        "password": "admin",
        "realm": "master",
        "state": "present",
        "clientId": "test_add_client_composite_roles",
        "rootUrl": "http://test5.com:8080",
        "name": "Add composites role to this client",
        "description": "Composites role should be added to this client",
        "adminUrl": "http://test5.com:8080/admin",
        "baseUrl": "http://test5.com:8080",
        "enabled": True,
        "clientAuthenticatorType": "client-secret",
        "redirectUris": ["http://test5.com:8080/secure"],
        "webOrigins": ["http://test5.com:8080/secure"],
        "consentRequired": False,   
        "standardFlowEnabled": True,
        "implicitFlowEnabled": True,
        "directAccessGrantsEnabled": True,
        "fullScopeAllowed": True,
        "serviceAccountsEnabled": True,
        "protocol": "openid-connect",
        "bearerOnly": False,
        "publicClient": False,
        "roles":  [
            {
                "name":"test1",
                "description": "test1",
                "composite": False
                },
            {
                "name":"test2",
                "description": "test2",
                "composite": True,
                "composites": []
            }
        ],
        "protocolMappers": [
            {
                "name": "test1Mapper",
                "protocol": "openid-connect",
                "protocolMapper": "oidc-usermodel-attribute-mapper",
                "consentRequired": False,
                "config": { 
                    "multivalued": 'false',
                    "userinfo.token.claim": False,
                    "user.attribute": "test1",
                    "id.token.claim": 'true',
                    "access.token.claim": 'true',
                    "claim.name": "test1",
                    "jsonType.label": "String"}
            },
            {
                "name": "test2Mapper",
                "protocol": "openid-connect",
                "protocolMapper": "oidc-usermodel-attribute-mapper",
                "consentRequired": False,
                "config": { 
                    "multivalued": 'false',
                    "userinfo.token.claim": 'true',
                    "user.attribute": "test2",
                    "id.token.claim": 'true',
                    "access.token.claim": 'true',
                    "claim.name": "test2",
                    "jsonType.label": "String"
                }
            }
        ]
    }
    toRemoveMapperFromClient = {
        "url": "http://localhost:18081/auth",
        "username": "admin",
        "password": "admin",
        "realm": "master",
        "state": "present",
        "clientId": "test_remove_mapper_from_client",
        "rootUrl": "http://test.com:8080",
        "name": "Test remove mapper",
        "description": "Client from which we remove a mapper",
        "publicClient": False,
        "protocolMappers": [
            {
                "name": "thismapperstays",
                "protocol": "openid-connect",
                "protocolMapper": "oidc-usermodel-attribute-mapper",
                "consentRequired": False,
                "config": { 
                    "multivalued": 'false',
                    "userinfo.token.claim": False,
                    "user.attribute": "test1",
                    "id.token.claim": 'true',
                    "access.token.claim": 'true',
                    "claim.name": "test1",
                    "jsonType.label": "String"}
            },
            {
                "name": "thismappermustbedeleted",
                "protocol": "openid-connect",
                "protocolMapper": "oidc-usermodel-attribute-mapper",
                "consentRequired": False,
                "config": { 
                    "multivalued": 'false',
                    "userinfo.token.claim": 'true',
                    "user.attribute": "test2",
                    "id.token.claim": 'true',
                    "access.token.claim": 'true',
                    "claim.name": "test2",
                    "jsonType.label": "String"
                }
            }
        ],
        "force": False
    }
    toRemoveRoleFromClient = {
        "url": "http://localhost:18081/auth",
        "username": "admin",
        "password": "admin",
        "realm": "master",
        "state": "present",
        "clientId": "test_remove_role_from_client",
        "rootUrl": "http://test.com:8080",
        "name": "Test remove role",
        "description": "Client from which we remove a role",
        "publicClient": False,
        "roles": [
            {
                "name":"thisrolestays",
                "description": "This role must stay after the test",
                "composite": False,
                "state": "present"
                },
            {
                "name":"thisrolemustbedeleted",
                "description": "This role mus be deleted by the module",
                "composite": False,
                "state": "present"
            }
        ],
        "force": False
    }
    toDeleteClient = {
        "url": "http://localhost:18081/auth",
        "username": "admin",
        "password": "admin",
        "realm": "master",
        "state": "present",
        "clientId": "test_delete_client",
        "name": "Client to delete",
        "description": "this client should have been deleted",
        "rootUrl": "http://test.com:8080",
        "name": "basetestname",
        "description": "Base testing",
        "publicClient": False,
        "force": False
    }

    def setUp(self):
        super(KeycloakClientTestCase, self).setUp()
        self.module = keycloak_client
        self.testClient["roles"] = self.testClientRoles
        set_module_args(self.testClient)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.toModifyClient['roles'][1]['composites'].append({'id': self.testClient['clientId'],"name": self.testClientRoles[0]['name']})
        set_module_args(self.toModifyClient)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.toAddCompositesForClientRole['roles'][1]['composites'].append({'id': self.testClient['clientId'],"name": self.testClientRoles[0]['name']})
        set_module_args(self.toAddCompositesForClientRole)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        set_module_args(self.toRemoveMapperFromClient)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        set_module_args(self.toRemoveRoleFromClient)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        set_module_args(self.toDeleteClient)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
                

 
    def test_create_client(self):
        toCreate = {}
        toCreate["url"] = "http://localhost:18081/auth"
        toCreate["username"] = "admin"
        toCreate["password"] = "admin"
        toCreate["realm"] = "master"
        toCreate["state"] = "present"
        toCreate["clientId"] = "test_create_client"
        toCreate["rootUrl"] = "http://test.com:8080"
        toCreate["name"] = "Create client test"
        toCreate["description"] = "This client should be created"
        toCreate["adminUrl"] = "http://test.com:8080/admin"
        toCreate["baseUrl"] = "http://test.com:8080"
        toCreate["enabled"] = True
        toCreate["clientAuthenticatorType"] = "client-secret"
        toCreate["redirectUris"] = ["http://test.com:8080/secure","http://test1.com:8080/secure"]
        toCreate["webOrigins"] = ["*"]
        toCreate["consentRequired"] = False   
        toCreate["standardFlowEnabled"] = True
        toCreate["implicitFlowEnabled"] = True
        toCreate["directAccessGrantsEnabled"] = True
        toCreate["serviceAccountsEnabled"] = True
        #toCreate["authorizationServicesEnabled"] = False
        toCreate["protocol"] = "openid-connect"
        toCreate["fullScopeAllowed"] = True
        toCreate["bearerOnly"] = False
        toCreate["roles"] = [
            {
                "name":"test1",
                "description": "test1",
                "composite": False
            },
            {
                "name":"toCreate",
                "description": "toCreate",
                "composite": True,
                "composites": [
                    {
                        "id": self.testClient['clientId'],
                        "name": self.testClientRoles[0]['name']
                    },
                    {
                        "name": "admin"
                    }
                ]
            }
        ]
        toCreate["protocolMappers"] = [{"name": "test1Mapper",
                                        "protocol": "openid-connect",
                                        "protocolMapper": "oidc-usermodel-attribute-mapper",
                                        "consentRequired": False,
                                        "config": { 
                                            "multivalued": 'false',
                                            "userinfo.token.claim": 'true',
                                            "user.attribute": "test1",
                                            "id.token.claim": 'true',
                                            "access.token.claim": 'true',
                                            "claim.name": "test1",
                                            "jsonType.label": "String"}},
                                       {"name": "test2Mapper",
                                        "protocol": "openid-connect",
                                        "protocolMapper": "oidc-usermodel-attribute-mapper",
                                        "consentRequired": False,
                                        "config": { 
                                            "multivalued": 'false',
                                            "userinfo.token.claim": 'true',
                                            "user.attribute": "test2",
                                            "id.token.claim": 'true',
                                            "access.token.claim": 'true',
                                            "claim.name": "test2",
                                            "jsonType.label": "String"}}]
        toCreate["publicClient"] = False
        toCreate["force"] = False
        set_module_args(toCreate)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.assertTrue(results.exception.args[0]['end_state']['enabled'])
        self.assertTrue(results.exception.args[0]['changed'])
        self.assertTrue('clientSecret' in results.exception.args[0])
        OrderdRoles = sorted(results.exception.args[0]['end_state']['clientRoles'], key=lambda k: k['name'])
        self.assertEqual(OrderdRoles[0]['name'], toCreate["roles"][0]['name'], "roles : " + OrderdRoles[0]['name'])
        self.assertEqual(OrderdRoles[1]['name'], toCreate["roles"][1]['name'], "roles : " + OrderdRoles[1]['name'])
        for newComposite in toCreate["roles"][1]['composites']:
            compositeFound = False
            for createdComposite in OrderdRoles[1]['composites']:
                if "id" in newComposite and newComposite["id"] == createdComposite['id'] and newComposite["name"] == createdComposite['name']:
                    compositeFound = True
                elif newComposite["name"] == createdComposite['name']:
                    compositeFound = True
            if "id" in newComposite:
                message = "Composite: id:" + newComposite["id"] + " name:" + newComposite["name"] + " not found"
            else:
                message = "Composite: name:" + newComposite["name"] + " not found"
            self.assertTrue(compositeFound, message)
            
        self.assertEqual(results.exception.args[0]['end_state']['redirectUris'].sort(),toCreate["redirectUris"].sort(),"redirectUris: " + str(results.exception.args[0]['end_state']['redirectUris'].sort()))
        for toCreateMapper in toCreate["protocolMappers"]:
            mapperFound = False
            for mapper in results.exception.args[0]['end_state']['protocolMappers']:
                if mapper["name"] == toCreateMapper["name"]:
                    mapperFound = True
                    break
            self.assertTrue(mapperFound, "no mapper found: " + toCreateMapper["name"])
            if mapperFound:
                self.assertEqual(mapper["config"]["claim.name"], toCreateMapper["config"]["claim.name"], "claim.name: " + toCreateMapper["config"]["claim.name"] + ": " + mapper["config"]["claim.name"])
                self.assertEqual(mapper["config"]["user.attribute"], toCreateMapper["config"]["user.attribute"], "user.attribute: " + mapper["config"]["user.attribute"] + ": " + mapper["config"]["user.attribute"])

    def test_client_not_changed(self):
        set_module_args(self.testClient)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.assertFalse(results.exception.args[0]['changed'])


    def test_modify_client(self):
       
        self.toModifyClient["name"] = "test_modify_client_modified"
        self.toModifyClient["description"] = "This client should have been modified"
        self.toModifyClient["protocolMappers"] = [{"name": "test1Mapper",
                                        "protocol": "openid-connect",
                                        "protocolMapper": "oidc-usermodel-attribute-mapper",
                                        "consentRequired": False,
                                        "config": { 
                                            "multivalued": 'false',
                                            "userinfo.token.claim": 'false',
                                            "user.attribute": "modifiedattribute",
                                            "id.token.claim": 'true',
                                            "access.token.claim": 'true',
                                            "claim.name": "modifiedclaim",
                                            "jsonType.label": "String"}}]
        set_module_args(self.toModifyClient)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.assertTrue(results.exception.args[0]['end_state']['enabled'])
        self.assertTrue(results.exception.args[0]['changed'])
        
        self.assertEqual(results.exception.args[0]['end_state']['name'], self.toModifyClient["name"], "name: " + results.exception.args[0]['end_state']['name'])
        self.assertEqual(results.exception.args[0]['end_state']['description'], self.toModifyClient["description"], 'description: ' + results.exception.args[0]['end_state']['description'])
        self.assertEqual(results.exception.args[0]['end_state']['redirectUris'].sort(),self.toModifyClient["redirectUris"].sort(),"redirectUris: " + str(results.exception.args[0]['end_state']['redirectUris'].sort()))
        for toChangeMapper in self.toModifyClient["protocolMappers"]:
            mapperFound = False
            for mapper in results.exception.args[0]['end_state']['protocolMappers']:
                if mapper["name"] == toChangeMapper["name"]:
                    mapperFound = True
                    break
            self.assertTrue(mapperFound, "no mapper found: " + toChangeMapper["name"])
            if mapperFound:
                self.assertEqual(mapper["config"]["claim.name"], toChangeMapper["config"]["claim.name"], "claim.name: " + toChangeMapper["config"]["claim.name"] + ": " + mapper["config"]["claim.name"])
                self.assertEqual(mapper["config"]["user.attribute"], toChangeMapper["config"]["user.attribute"], "user.attribute: " + toChangeMapper["config"]["user.attribute"] + ": " + mapper["config"]["user.attribute"])
        OrderdRoles = sorted(results.exception.args[0]['end_state']['clientRoles'], key=lambda k: k['name'])
        self.assertEqual(OrderdRoles[0]['name'], self.toModifyClient["roles"][0]['name'], "roles : " + OrderdRoles[0]['name'])
        self.assertEqual(OrderdRoles[1]['name'], self.toModifyClient["roles"][1]['name'], "roles : " + OrderdRoles[1]['name'])
 
    def test_add_client_composite_roles(self):
        newClientRoles = [
            {
                "name":"test1",
                "description": "test1",
                "composite": False
                },
            {
                "name":"test2",
                "description": "test2",
                "composite": True,
                "composites": [
                    {
                        "id": self.testClient['clientId'],
                        "name": self.testClientRoles[0]['name']
                    },
                    {
                        "id": self.testClient['clientId'],
                        "name": self.testClientRoles[1]['name']
                    },
                    {
                        "name": "admin"
                    }
                ]
            }
        ]
        self.toAddCompositesForClientRole["roles"] = newClientRoles
        set_module_args(self.toAddCompositesForClientRole)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.assertTrue(results.exception.args[0]['end_state']['enabled'])
        self.assertTrue(results.exception.args[0]['changed'])
        OrderdRoles = sorted(results.exception.args[0]['end_state']['clientRoles'], key=lambda k: k['name'])
        self.assertEqual(OrderdRoles[0]['name'], newClientRoles[0]['name'], "roles : " + OrderdRoles[0]['name'])
        self.assertEqual(OrderdRoles[1]['name'], newClientRoles[1]['name'], "roles : " + OrderdRoles[1]['name'])
        #self.assertEqual(len(OrderdRoles[1]['composites']), len(newClientRoles[1]['composites']), 'Composite length: ' + len(OrderdRoles[1]['composites']) + ' : ' + len(newClientRoles[1]['composites']))
        OrderedComposites = sorted(OrderdRoles[1]['composites'], key=lambda k:['name]'])
        for index, composite in enumerate(OrderedComposites):
            compositeFound = False
            for toChangeComposite in newClientRoles[1]['composites']:
                if toChangeComposite['name'] == composite['name']:
                    compositeFound = True
                    break
            self.assertTrue(compositeFound, 'Composite ' + composite['name'] + ' not found')
    
    def test_remove_mapper_from_client(self):
        self.toRemoveMapperFromClient["protocolMappers"][1]["state"] = "absent"
        set_module_args(self.toRemoveMapperFromClient)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.assertTrue(results.exception.args[0]['changed'])
        mapperFound = False
        for mapper in results.exception.args[0]['end_state']['protocolMappers']:
            if mapper["name"] == self.toRemoveMapperFromClient["protocolMappers"][1]["name"]:
                mapperFound = True
                break
        self.assertFalse(mapperFound, "Mapper " + self.toRemoveMapperFromClient["protocolMappers"][1]["name"] + " has not been deleted")
         
    def test_remove_role_from_client(self):
        self.toRemoveRoleFromClient["roles"][1]["state"] = "absent"
        set_module_args(self.toRemoveRoleFromClient)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.assertTrue(results.exception.args[0]['changed'])
        roleFound = False
        for role in results.exception.args[0]['end_state']['clientRoles']:
            if role["name"] == self.toRemoveRoleFromClient["roles"][1]["name"]:
                roleFound = True
                break
        self.assertFalse(roleFound, "Role " + self.toRemoveRoleFromClient["roles"][1]["name"] + " has not been deleted")

    def test_delete_client(self):
        self.toDeleteClient["state"] = "absent"
        set_module_args(self.toDeleteClient)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.assertTrue(results.exception.args[0]['changed'])
