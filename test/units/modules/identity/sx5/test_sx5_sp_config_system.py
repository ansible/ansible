import collections
import os
import unittest
from ansible.modules.identity.sx5.sx5_sp_config_system import *
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
                "roles": [{"name":"test31","description": "test31","composite": "False"},
                             {"name":"toChange","description": "toChange","composite": True,"composites": [{"id": "master-realm","name": "view-users","clientRole": True,"composite": True}]}
                             ]
                },
            {
                "clientId": "clientsystemChange31",
                "name": "clientsystemChange31",
                "roles": [{"name":"test31","description": "test31","composite": "False"},
                             {"name":"toChange","description": "toChange","composite": True,"composites": [{"id": "master-realm","name": "view-users","clientRole": True,"composite": True}]}
                             ]
                },
            {
                "clientId": "clientsystem32",
                "name": "clientsystem32",
                "roles": [{"name":"test32","description": "test32","composite": "False"},
                             {"name":"toChange","description": "toChange","composite": True,"composites": [{"id": "master-realm","name": "view-users","clientRole": True,"composite": True}]}
                             ]
                },
            {
                "clientId": "clientsystemChange32",
                "name": "clientsystemChange32",
                "roles": [{"name":"test32","description": "test32","composite": "False"},
                             {"name":"toChange","description": "toChange","composite": True,"composites": [{"id": "master-realm","name": "view-users","clientRole": True,"composite": True}]}
                             ]
                },
            {
                "clientId": "clientsystemNS1",
                "name": "clientsystemNS1",
                "roles": [{"name":"testNS1","description": "testNS1","composite": "False"},
                             {"name":"toCreate","description": "toCreate","composite": True,"composites": [{"id": "master-realm","name": "view-users","clientRole": True,"composite": True}]}
                             ]
                },
            
            {
                "clientId": "clientsystemNS21",
                "name": "clientsystemNS21",
                "roles": [{"name":"testNS2","description": "testNS2","composite": "False"},
                             {"name":"toDoNotChange","description": "toDoNotChange","composite": True,"composites": [{"id": "master-realm","name": "view-users","clientRole": True,"composite": True}]}
                             ]
                },
            {
                "clientId": "clientsystemNS31",
                "name": "clientsystemNS31",
                "roles": [{"name":"testNS31","description": "testNS31","composite": "False"},
                             {"name":"toChange","description": "toChange","composite": True,"composites": [{"id": "master-realm","name": "view-users","clientRole": True,"composite": True}]}
                             ]
                },
            {
                "clientId": "clientsystemChangeNS31",
                "name": "clientsystemChangeNS31",
                "roles": [{"name":"testNS31","description": "testNS31","composite": "False"},
                             {"name":"toChange","description": "toChange","composite": True,"composites": [{"id": "master-realm","name": "view-users","clientRole": True,"composite": True}]}
                             ]
                },
            {
                "clientId": "clientsystemNS32",
                "name": "clientsystemNS32",
                "roles": [{"name":"testNS32","description": "testNS32","composite": "False"},
                             {"name":"toChange","description": "toChange","composite": True,"composites": [{"id": "master-realm","name": "view-users","clientRole": True,"composite": True}]}
                             ]
                },
            {
                "clientId": "clientsystemChangeNS32",
                "name": "clientsystemChangeNS32",
                "roles": [{"name":"testNS32","description": "testNS32","composite": "False"},
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
        toCreate["spConfigClient_id"] = "admin-cli" 
        toCreate["spConfigClient_secret"] = ""
        toCreate["spConfigUrl"] = "http://localhost:18182/config"
        toCreate["systemName"] = "system1"
        toCreate["systemShortName"] = "S1"
        toCreate["clients"] = [{"clientId": "clientsystem11"}]
        toCreate["sadu_principal"] = "http://sadu.dev.inspq.qc.ca"
        toCreate["sadu_secondary"] = [{"adresse": "http://sadu_secondary1"},{"adresse": "http://sadu_secondary2"}]
        toCreate["clientRoles_mapper"] = [{"spClientRole": "roleInSp11", "eq_sadu_role": "roleSadu11"},{"spClientRole": "roleInSp12", "eq_sadu_role": "roleSadu12"}]
        toCreate["clientRoles"] = [{"spClientRoleId": "test1", "spClientRoleName": "test1", "spClientRoleDescription": "test1"},{"spClientRoleId": "toCreate", "spClientRoleName": "toCreate", "spClientRoleDescription": "toCreate"}]
        toCreate["state"] = "present"
        toCreate["force"] = False
    
        results = system(toCreate)
        #print str(results)
        self.assertTrue(results['changed'])
        self.assertEquals(results["ansible_facts"]["systemes"]["nom"], toCreate["systemName"], "systemName: " + results["ansible_facts"]["systemes"]["nom"] + " : " + toCreate["systemName"])

    def test_system_not_changed(self):
        toDoNotChange = {}
        toDoNotChange["spUrl"] = "http://localhost:18081"
        toDoNotChange["spUsername"] = "admin"
        toDoNotChange["spPassword"] = "admin"
        toDoNotChange["spRealm"] = "master"
        toDoNotChange["spConfigClient_id"] = "admin-cli" 
        toDoNotChange["spConfigClient_secret"] = ""
        toDoNotChange["spConfigUrl"] = "http://localhost:18182/config"
        toDoNotChange["systemName"] = "system2"
        toDoNotChange["systemShortName"] = "S2"
        toDoNotChange["clients"] = [{"clientId": "clientsystem21"}]
        toDoNotChange["sadu_principal"] = "http://sadu.dev.inspq.qc.ca"
        toDoNotChange["sadu_secondary"] = [{"adresse": "http://sadu_secondary1"},{"adresse": "http://sadu_secondary2"}]
        toDoNotChange["clientRoles_mapper"] = [{"spClientRole": "roleInSp11", "eq_sadu_role": "roleSadu11"},{"spClientRole": "roleInSp12", "eq_sadu_role": "roleSadu12"}]
        toDoNotChange["clientRoles"] = [{"spClientRoleId": "test2", "spClientRoleName": "test2", "spClientRoleDescription": "test2"},{"spClientRoleId": "toDoNotChange", "spClientRoleName": "toDoNotChange", "spClientRoleDescription": "toDoNotChange"}]
        toDoNotChange["state"] = "present"
        toDoNotChange["force"] = False

        system(toDoNotChange)
        #print str(results)
        results = system(toDoNotChange)
        #print str(results)
        self.assertFalse(results['changed'])

    def test_modify_system(self):
        toChange = {}
        toChange["spUrl"] = "http://localhost:18081"
        toChange["spUsername"] = "admin"
        toChange["spPassword"] = "admin"
        toChange["spRealm"] = "master"
        toChange["spConfigClient_id"] = "admin-cli" 
        toChange["spConfigClient_secret"] = ""
        toChange["spConfigUrl"] = "http://localhost:18182/config"
        toChange["systemName"] = "system3"
        toChange["systemShortName"] = "S3"
        toChange["clients"] = [{"clientId": "clientsystem31"}]
        toChange["sadu_principal"] = "http://sadu.dev.inspq.qc.ca"
        toChange["sadu_secondary"] = [{"adresse": "http://sadu_secondary1"},{"adresse": "http://sadu_secondary2"}]
        toChange["clientRoles_mapper"] = [{"spClientRole": "roleInSp11", "eq_sadu_role": "roleSadu11"},{"spClientRole": "roleInSp12", "eq_sadu_role": "roleSadu12"}]
        toChange["clientRoles"] = [{"spClientRoleId": "test31", "spClientRoleName": "test31", "spClientRoleDescription": "test31"},{"spClientRoleId": "toChange", "spClientRoleName": "toChange", "spClientRoleDescription": "toChange"}]
        toChange["state"] = "present"
        toChange["force"] = False

        results = system(toChange)
        #print str(results)
        toChange["sadu_principal"] = "http://localhost/test3"
        toChange["clients"] = [{"clientId": "clientsystemChange31"}]
        NnClient=len(toChange["clients"])+1
        results = system(toChange)
        #print str(results)
        self.assertTrue(results['changed'])
        for adressesApprovisionnement in results["ansible_facts"]["entreesAdressesApprovisionnement"]["entreesAdressesApprovisionnement"]:
            if adressesApprovisionnement["principale"]:
                self.assertEquals(adressesApprovisionnement["adresse"], toChange["sadu_principal"], "sadu_principal: " + adressesApprovisionnement["adresse"] + " : " + toChange["sadu_principal"])
        
        self.assertEquals(len(results["ansible_facts"]["systemes"]["composants"]), 
                          NnClient, 
                          str(len(results["ansible_facts"]["systemes"]["composants"])) + " : " + str(NnClient))


    def test_modify_system_add_clients(self):
        toChange = {}
        toChange["spUrl"] = "http://localhost:18081"
        toChange["spUsername"] = "admin"
        toChange["spPassword"] = "admin"
        toChange["spRealm"] = "master"
        toChange["spConfigClient_id"] = "admin-cli" 
        toChange["spConfigClient_secret"] = ""
        toChange["spConfigUrl"] = "http://localhost:18182/config"
        toChange["systemName"] = "test3"
        toChange["systemShortName"] = "T3"
        toChange["clients"] = [{"clientId": "clientsystem32"}]
        toChange["sadu_principal"] = "http://sadu.dev.inspq.qc.ca"
        toChange["sadu_secondary"] = [{"adresse": "http://sadu_secondary1"},{"adresse": "http://sadu_secondary2"}]
        toChange["clientRoles_mapper"] = [{"spClientRole": "roleInSp11", "eq_sadu_role": "roleSadu11"},{"spClientRole": "roleInSp12", "eq_sadu_role": "roleSadu12"}]
        toChange["clientRoles"] = [{"spClientRoleId": "test32", "spClientRoleName": "test32", "spClientRoleDescription": "test32"},{"spClientRoleId": "toChange", "spClientRoleName": "toChange", "spClientRoleDescription": "toChange"}]
        toChange["state"] = "present"
        toChange["force"] = False

        results = system(toChange)

        newToChange = {}
        newToChange["spUrl"] = "http://localhost:18081"
        newToChange["spUsername"] = "admin"
        newToChange["spPassword"] = "admin"
        newToChange["spRealm"] = "master"
        newToChange["spConfigClient_id"] = "admin-cli" 
        newToChange["spConfigClient_secret"] = ""
        newToChange["spConfigUrl"] = "http://localhost:18182/config"
        newToChange["systemName"] = "test3"
        newToChange["systemShortName"] = "T3"
        newToChange["clients"] = [{"clientId": "clientsystemChange32"}]
        newToChange["sadu_principal"] = "http://sadu_principal"
        newToChange["sadu_secondary"] = [{"adresse": "http://sadu_secondary1"},{"adresse": "http://sadu_secondary2"}]
        newToChange["clientRoles_mapper"] = [{"spClientRole": "roleInSp11", "eq_sadu_role": "roleSadu11"},{"spClientRole": "roleInSp12", "eq_sadu_role": "roleSadu12"}]
        newToChange["clientRoles"] = [{"spClientRoleId": "test32", "spClientRoleName": "test32", "spClientRoleDescription": "test32"},{"spClientRoleId": "toChange", "spClientRoleName": "toChange", "spClientRoleDescription": "toChange"}]
        newToChange["state"] = "present"
        newToChange["force"] = False

        results = system(newToChange)
        print str(results)
        self.assertTrue(results['changed'])
        systemClients = results["ansible_facts"]["systemes"]["composants"]
        print str(systemClients)
        for toChangeClient in toChange["clients"]:
            clientFound = False
            for systemClient in systemClients:
                if toChangeClient["clientId"] == systemClient["clientId"]:
                    clientFound = True
                    break
            self.assertTrue(clientFound, toChangeClient["clientId"] + " not found")
        for newToChangeClient in newToChange["clients"]:
            clientFound = False
            for systemClient in systemClients:
                if newToChangeClient["clientId"] == systemClient["clientId"]:
                    clientFound = True
                    break
            self.assertTrue(clientFound, newToChangeClient["clientId"] + " not found")
        
    def test_create_system_no_sadu(self):
        toCreate = {}
        toCreate["spUrl"] = "http://localhost:18081"
        toCreate["spUsername"] = "admin"
        toCreate["spPassword"] = "admin"
        toCreate["spRealm"] = "master"
        toCreate["spConfigClient_id"] = "admin-cli" 
        toCreate["spConfigClient_secret"] = ""
        toCreate["spConfigUrl"] = "http://localhost:18182/config"
        toCreate["systemName"] = "systemNS1"
        toCreate["systemShortName"] = "NS1"
        toCreate["clients"] = [{"clientId": "clientsystemNS1"}]
        toCreate["clientRoles"] = [{"spClientRoleId": "testNS1", "spClientRoleName": "testNS1", "spClientRoleDescription": "testNS1"},{"spClientRoleId": "toCreate", "spClientRoleName": "toCreate", "spClientRoleDescription": "toCreate"}]
        toCreate["state"] = "present"
        toCreate["force"] = False
    
        results = system(toCreate)
        #print str(results)
        self.assertTrue(results['changed'])
        self.assertEquals(results["ansible_facts"]["systemes"]["nom"], toCreate["systemName"], "systemName: " + results["ansible_facts"]["systemes"]["nom"] + " : " + toCreate["systemName"])

    def test_system_no_sadu_not_changed(self):
        toDoNotChange = {}
        toDoNotChange["spUrl"] = "http://localhost:18081"
        toDoNotChange["spUsername"] = "admin"
        toDoNotChange["spPassword"] = "admin"
        toDoNotChange["spRealm"] = "master"
        toDoNotChange["spConfigClient_id"] = "admin-cli" 
        toDoNotChange["spConfigClient_secret"] = ""
        toDoNotChange["spConfigUrl"] = "http://localhost:18182/config"
        toDoNotChange["systemName"] = "systemNS2"
        toDoNotChange["systemShortName"] = "SNS2"
        toDoNotChange["clients"] = [{"clientId": "clientsystemNS21"}]
        toDoNotChange["clientRoles"] = [{"spClientRoleId": "testNS2", "spClientRoleName": "testNS2", "spClientRoleDescription": "testNS2"},{"spClientRoleId": "toDoNotChange", "spClientRoleName": "toDoNotChange", "spClientRoleDescription": "toDoNotChange"}]
        toDoNotChange["state"] = "present"
        toDoNotChange["force"] = False

        system(toDoNotChange)
        #print str(results)
        results = system(toDoNotChange)
        #print str(results)
        self.assertFalse(results['changed'])

    def test_modify_system_no_sadu(self):
        toChange = {}
        toChange["spUrl"] = "http://localhost:18081"
        toChange["spUsername"] = "admin"
        toChange["spPassword"] = "admin"
        toChange["spRealm"] = "master"
        toChange["spConfigClient_id"] = "admin-cli" 
        toChange["spConfigClient_secret"] = ""
        toChange["spConfigUrl"] = "http://localhost:18182/config"
        toChange["systemName"] = "systemNS3"
        toChange["systemShortName"] = "SNS3"
        toChange["clients"] = [{"clientId": "clientsystemNS31"}]
        toChange["clientRoles"] = [{"spClientRoleId": "testNS31", "spClientRoleName": "testNS31", "spClientRoleDescription": "testNS31"},{"spClientRoleId": "toChange", "spClientRoleName": "toChange", "spClientRoleDescription": "toChange"}]
        toChange["state"] = "present"
        toChange["force"] = False

        results = system(toChange)
        #print str(results)
        toChange["clients"] = [{"clientId": "clientsystemChangeNS31"}]
        NnClient=len(toChange["clients"])+1
        results = system(toChange)
        #print str(results)
        self.assertTrue(results['changed'])
        self.assertEquals(len(results["ansible_facts"]["systemes"]["composants"]), 
                          NnClient, 
                          str(len(results["ansible_facts"]["systemes"]["composants"])) + " : " + str(NnClient))

    def test_modify_system_no_sadu_add_clients(self):
        toChange = {}
        toChange["spUrl"] = "http://localhost:18081"
        toChange["spUsername"] = "admin"
        toChange["spPassword"] = "admin"
        toChange["spRealm"] = "master"
        toChange["spConfigClient_id"] = "admin-cli" 
        toChange["spConfigClient_secret"] = ""
        toChange["spConfigUrl"] = "http://localhost:18182/config"
        toChange["systemName"] = "testNS3"
        toChange["systemShortName"] = "TNS3"
        toChange["clients"] = [{"clientId": "clientsystemNS32"}]
        toChange["clientRoles"] = [{"spClientRoleId": "testNS32", "spClientRoleName": "testNS32", "spClientRoleDescription": "testNS32"},{"spClientRoleId": "toChange", "spClientRoleName": "toChange", "spClientRoleDescription": "toChange"}]
        toChange["state"] = "present"
        toChange["force"] = False

        results = system(toChange)

        newToChange = {}
        newToChange["spUrl"] = "http://localhost:18081"
        newToChange["spUsername"] = "admin"
        newToChange["spPassword"] = "admin"
        newToChange["spRealm"] = "master"
        newToChange["spConfigClient_id"] = "admin-cli" 
        newToChange["spConfigClient_secret"] = ""
        newToChange["spConfigUrl"] = "http://localhost:18182/config"
        newToChange["systemName"] = "testNS3"
        newToChange["systemShortName"] = "TNS3"
        newToChange["clients"] = [{"clientId": "clientsystemChangeNS32"}]
        newToChange["clientRoles"] = [{"spClientRoleId": "testNS32", "spClientRoleName": "testNS32", "spClientRoleDescription": "testNS32"},{"spClientRoleId": "toChange", "spClientRoleName": "toChange", "spClientRoleDescription": "toChange"}]
        newToChange["state"] = "present"
        newToChange["force"] = False

        results = system(newToChange)
        print str(results)
        self.assertTrue(results['changed'])
        systemClients = results["ansible_facts"]["systemes"]["composants"]
        print str(systemClients)
        for toChangeClient in toChange["clients"]:
            clientFound = False
            for systemClient in systemClients:
                if toChangeClient["clientId"] == systemClient["clientId"]:
                    clientFound = True
                    break
            self.assertTrue(clientFound, toChangeClient["clientId"] + " not found")
        for newToChangeClient in newToChange["clients"]:
            clientFound = False
            for systemClient in systemClients:
                if newToChangeClient["clientId"] == systemClient["clientId"]:
                    clientFound = True
                    break
            self.assertTrue(clientFound, newToChangeClient["clientId"] + " not found")
    def test_delete_system(self):
        toDelete = {}
        toDelete["spUrl"] = "http://localhost:18081"
        toDelete["spUsername"] = "admin"
        toDelete["spPassword"] = "admin"
        toDelete["spRealm"] = "master"
        toDelete["spConfigClient_id"] = "admin-cli" 
        toDelete["spConfigClient_secret"] = ""
        toDelete["spConfigUrl"] = "http://localhost:18182/config"
        toDelete["systemName"] = "system4"
        toDelete["systemShortName"] = "S4"
        toDelete["clients"] = [{"clientId": "clientsystem41"}]
        toDelete["sadu_principal"] = "http://sadu.dev.inspq.qc.ca"
        toDelete["sadu_secondary"] = [{"adresse": "http://sadu_secondary1"},{"adresse": "http://sadu_secondary2"}]
        toDelete["clientRoles_mapper"] = [{"spClientRole": "roleInSp11", "eq_sadu_role": "roleSadu11"},{"spClientRole": "roleInSp12", "eq_sadu_role": "roleSadu12"}]
        toDelete["clientRoles"] = [{"spClientRoleId": "test4", "spClientRoleName": "test4", "spClientRoleDescription": "test4"},{"spClientRoleId": "toDelete", "spClientRoleName": "toDelete", "spClientRoleDescription": "toDelete"}]
        toDelete["state"] = "present"
        toDelete["force"] = False

        system(toDelete)
        toDelete["state"] = "absent"
        results = system(toDelete)
        #print str(results)
        self.assertTrue(results['changed'])
        self.assertEqual(results['stdout'], 'deleted', 'system has been deleted')
