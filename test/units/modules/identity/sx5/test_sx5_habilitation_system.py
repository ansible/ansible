import collections
import os
import unittest
from ansible.modules.identity.sx5.sx5_habilitation_system import *
from ansible.modules.identity.keycloak.keycloak_client import *

class Sx5SystemTestCase(unittest.TestCase):
    def setUp(self):
        unittest.TestCase.setUp(self)
        clientsToCreate = [
            {
                "clientId": "clientsystem11",
                "name": "clientsystem11",
                "roles": [{"name":"test1","description": "test1","composite": "False"},
                             {"name":"toCreate","description": "toCreate","composite": True,"composites": [{"id": "master-realm","name": "view-users","clientRole": True,"composite": True}]}
                             ]
                },
            {
                "clientId": "clientsystem21",
                "name": "clientsystem21",
                "roles": [{"name":"test2","description": "test2","composite": "False"},
                             {"name":"toDoNotChange","description": "toDoNotChange","composite": True,"composites": [{"id": "master-realm","name": "view-users","clientRole": True,"composite": True}]}
                             ]
                },
            {
                "clientId": "clientsystem31",
                "name": "clientsystem31",
                "roles": [{"name":"test3","description": "test3","composite": "False"},
                             {"name":"toChange","description": "toChange","composite": True,"composites": [{"id": "master-realm","name": "view-users","clientRole": True,"composite": True}]}
                             ]
                },
            {
                "clientId": "clientsystemChange31",
                "name": "clientsystemChange31",
                "roles": [{"name":"test3","description": "test3","composite": "False"},
                             {"name":"toChange","description": "toChange","composite": True,"composites": [{"id": "master-realm","name": "view-users","clientRole": True,"composite": True}]}
                             ]
                },
            {
                "clientId": "clientsystem41",
                "name": "clientsystem41",
                "roles": [{"name":"test4","description": "test4","composite": "False"},
                             {"name":"toDelete","description": "toDelete","composite": True,"composites": [{"id": "master-realm","name": "view-users","clientRole": True,"composite": True}]}
                             ]
                }
            ]
        toCreateClient = {}
        toCreateClient["url"] = "http://localhost:18081"
        toCreateClient["username"] = "admin"
        toCreateClient["password"] = "admin"
        toCreateClient["realm"] = "master"
        toCreateClient["state"] = "present"
        toCreateClient["rootUrl"] = "http://test.com:18182"
        toCreateClient["description"] = "Ceci est un test"
        toCreateClient["adminUrl"] = "http://test.com:18182/admin"
        toCreateClient["enabled"] = True
        toCreateClient["clientAuthenticatorType"] = "client-secret"
        toCreateClient["redirectUris"] = ["http://test.com:18182/secure","http://test1.com:18182/secure"]
        toCreateClient["webOrigins"] = ["*"]
        toCreateClient["bearerOnly"] = False
        toCreateClient["publicClient"] = False
        toCreateClient["force"] = False
        for theClient in clientsToCreate:
            toCreateClient["clientId"] = theClient["clientId"]
            toCreateClient["name"] = theClient["name"]
            toCreateClient["roles"] = theClient["roles"]
            client(toCreateClient)
        
    def test_create_system(self):
        toCreate = {}
        toCreate["spUrl"] = "http://localhost:18081"
        toCreate["spUsername"] = "admin"
        toCreate["spPassword"] = "admin"
        toCreate["spRealm"] = "master"
        toCreate["habilitationClient_id"] = "admin-cli"
        toCreate["habilitationClient_secret"] = ""
        toCreate["habilitationUrl"] = "http://localhost:18182/config"
        toCreate["systemName"] = "system1"
        toCreate["clientKeycloak"] = [{"spClient": "clientsystem11"}]
        toCreate["clientRoles"] = [{"spClientRoleId": "test1", "spClientRoleName": "test1", "spClientRoleDescription": "test1"},{"spClientRoleId": "toCreate", "spClientRoleName": "toCreate", "spClientRoleDescription": "toCreate"}]
        toCreate["state"] = "present"
        toCreate["force"] = False
    
        results = system(toCreate)
        #print str(results)
        self.assertTrue(results['changed'])

    def test_system_not_changed(self):
        toDoNotChange = {}
        toDoNotChange["spUrl"] = "http://localhost:18081"
        toDoNotChange["spUsername"] = "admin"
        toDoNotChange["spPassword"] = "admin"
        toDoNotChange["spRealm"] = "master"
        toDoNotChange["habilitationClient_id"] = "admin-cli"
        toDoNotChange["habilitationClient_secret"] = ""
        toDoNotChange["habilitationUrl"] = "http://localhost:18182/config"
        toDoNotChange["systemName"] = "system2"
        toDoNotChange["clientKeycloak"] = [{"spClient": "clientsystem21"}]
        toDoNotChange["clientRoles"] = [{"spClientRoleId": "test2", "spClientRoleName": "test2", "spClientRoleDescription": "test2"},{"spClientRoleId": "toDoNotChange", "spClientRoleName": "toDoNotChange", "spClientRoleDescription": "toDoNotChange"}]
        toDoNotChange["state"] = "present"
        toDoNotChange["force"] = False

        results = system(toDoNotChange)
        print str(results)
        results = system(toDoNotChange)
        print str(results)
        self.assertFalse(results['changed'])

    def test_modify_system(self):
        toChange = {}
        toChange["spUrl"] = "http://localhost:18081"
        toChange["spUsername"] = "admin"
        toChange["spPassword"] = "admin"
        toChange["spRealm"] = "master"
        toChange["habilitationClient_id"] = "admin-cli"
        toChange["habilitationClient_secret"] = ""
        toChange["habilitationUrl"] = "http://localhost:18182/config"
        toChange["systemName"] = "system3"
        toChange["clientKeycloak"] = [{"spClient": "clientsystem31"}]
        toChange["clientRoles"] = [{"spClientRoleId": "test3", "spClientRoleName": "test3", "spClientRoleDescription": "test3"},{"spClientRoleId": "toChange", "spClientRoleName": "toChange", "spClientRoleDescription": "toChange"}]
        toChange["state"] = "present"
        toChange["force"] = False

        results = system(toChange)
        print str(results)
        toChange["clientKeycloak"] = [{"spClient": "clientsystemChange31"}]
        results = system(toChange)
        print str(results)
        self.assertTrue(results['changed'])
        
        
    def test_delete_system(self):
        toDelete = {}
        toDelete["spUrl"] = "http://localhost:18081"
        toDelete["spUsername"] = "admin"
        toDelete["spPassword"] = "admin"
        toDelete["spRealm"] = "master"
        toDelete["habilitationClient_id"] = "admin-cli"
        toDelete["habilitationClient_secret"] = ""
        toDelete["habilitationUrl"] = "http://localhost:18182/config"
        toDelete["systemName"] = "system4"
        toDelete["clientKeycloak"] = [{"spClient": "clientsystem41"}]
        toDelete["clientRoles"] = [{"spClientRoleId": "test4", "spClientRoleName": "test4", "spClientRoleDescription": "test4"},{"spClientRoleId": "toDelete", "spClientRoleName": "toDelete", "spClientRoleDescription": "toDelete"}]
        toDelete["state"] = "present"
        toDelete["force"] = False

        system(toDelete)
        toDelete["state"] = "absent"
        results = system(toDelete)
        #print str(results)
        self.assertTrue(results['changed'])
        self.assertEqual(results['stdout'], 'deleted', 'system has been deleted')
