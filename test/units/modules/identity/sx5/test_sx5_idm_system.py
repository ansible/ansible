import collections
import os
import unittest
from ansible.modules.identity.sx5.sx5_idm_system import *

class Sx5SystemTestCase(unittest.TestCase):

    def test_create_system(self):
        toCreate = {}
#        toCreate["spUrl"] = "http://localhost:18081"
#        toCreate["spUsername"] = "admin"
#        toCreate["spPassword"] = "admin"
#        toCreate["spRealm"] = "master"
#        toCreate["idmClient_id"] = "admin-cli"
#        toCreate["idmClient_secret"] = ""
        toCreate["sx5IdmUrl"] = "http://localhost:18085/idm/config"
        toCreate["systemName"] = "FonctionsAllegeesDEV"
        toCreate["clients"] = [{"nom": "faiusdev"},{"nom": "faservicesdev"}]
        toCreate["sadu_principal"] = "http://sadu.dev.inspq.qc.ca"
        toCreate["sadu_secondary"] = [{"adresse": "http://sadu_secondary1"},{"adresse": "http://sadu_secondary2"}]
        toCreate["clientRoles_mapper"] = [{"spClientRole": "roleInSp11", "eq_sadu_role": "roleSadu11"},{"spClientRole": "roleInSp12", "eq_sadu_role": "roleSadu12"}]
        toCreate["state"] = "present"
        toCreate["force"] = False
    
        results = system(toCreate)
        #print str(results)
        self.assertTrue(results['changed'])
        self.assertEquals(results["ansible_facts"]["systemes"]["nom"], toCreate["systemName"], "systemName: " + results["ansible_facts"]["systemes"]["nom"] + " : " + toCreate["systemName"])
        

    def test_system_not_changed(self):
        toDoNotChange = {}
#        toDoNotChange["spUrl"] = "http://localhost:18081"
#        toDoNotChange["spUsername"] = "admin"
#        toDoNotChange["spPassword"] = "admin"
#        toDoNotChange["spRealm"] = "master"
#        toDoNotChange["idmClient_id"] = "admin-cli"
#        toDoNotChange["idmClient_secret"] = ""
        toDoNotChange["sx5IdmUrl"] = "http://localhost:18085/idm/config"
        toDoNotChange["systemName"] = "test2"
        toDoNotChange["clients"] = [{"nom": "client1"},{"nom": "client2"}]
        toDoNotChange["sadu_principal"] = "http://sadu_principal"
        toDoNotChange["sadu_secondary"] = [{"adresse": "http://sadu_secondary1"},{"adresse": "http://sadu_secondary2"}]
        toDoNotChange["clientRoles_mapper"] = [{"spClientRole": "roleInSp21", "eq_sadu_role": "roleSadu21"},{"spClientRole": "roleInSp12", "eq_sadu_role": "roleSadu12"}]
        toDoNotChange["state"] = "present"
        toDoNotChange["force"] = False

        system(toDoNotChange)
        #print str(results)
        results = system(toDoNotChange)
        #print str(results)
        self.assertFalse(results['changed'])

    def test_modify_system(self):
        toChange = {}
 #       toChange["spUrl"] = "http://localhost:18081"
 #       toChange["spUsername"] = "admin"
 #       toChange["spPassword"] = "admin"
 #       toChange["spRealm"] = "master"
 #       toChange["idmClient_id"] = "admin-cli"
 #       toChange["idmClient_secret"] = ""
        toChange["sx5IdmUrl"] = "http://localhost:18085/idm/config"
        toChange["systemName"] = "test3"
        toChange["clients"] = [{"nom": "client1"},{"nom": "client2"}]
        toChange["sadu_principal"] = "http://sadu_principal"
        toChange["sadu_secondary"] = [{"adresse": "http://sadu_secondary1"},{"adresse": "http://sadu_secondary2"}]
        toChange["clientRoles_mapper"] = [{"spClientRole": "roleInSp11", "eq_sadu_role": "roleSadu11"},{"spClientRole": "roleInSp12", "eq_sadu_role": "roleSadu12"}]
        toChange["state"] = "present"
        toChange["force"] = False

        results = system(toChange)
        #print str(results)
        toChange["sadu_principal"] = "http://localhost/test3"
        results = system(toChange)
        #print str(results)
        self.assertTrue(results['changed'])
        for adressesApprovisionnement in results["ansible_facts"]["systemes"]["adressesApprovisionnement"]:
            if adressesApprovisionnement["principal"]:
                self.assertEquals(adressesApprovisionnement["adresse"], toChange["sadu_principal"], "sadu_principal: " + adressesApprovisionnement["adresse"] + " : " + toChange["sadu_principal"])
        
        self.assertEquals(len(results["ansible_facts"]["systemes"]["clientsKeycloak"]), 
                          len(toChange["clients"]), 
                          str(len(results["ansible_facts"]["systemes"]["clientsKeycloak"])) + " : " + str(len(toChange["clients"])))


    def test_modify_system_add_clients(self):
        toChange = {}
 #       toChange["spUrl"] = "http://localhost:18081"
 #       toChange["spUsername"] = "admin"
 #       toChange["spPassword"] = "admin"
 #       toChange["spRealm"] = "master"
 #       toChange["idmClient_id"] = "admin-cli"
 #       toChange["idmClient_secret"] = ""
        toChange["sx5IdmUrl"] = "http://localhost:18085/idm/config"
        toChange["systemName"] = "test3"
        toChange["clients"] = [{"nom": "client1"},{"nom": "client2"}]
        toChange["sadu_principal"] = "http://sadu_principal"
        toChange["sadu_secondary"] = [{"adresse": "http://sadu_secondary1"},{"adresse": "http://sadu_secondary2"}]
        toChange["clientRoles_mapper"] = [{"spClientRole": "roleInSp11", "eq_sadu_role": "roleSadu11"},{"spClientRole": "roleInSp12", "eq_sadu_role": "roleSadu12"}]
        toChange["state"] = "present"
        toChange["force"] = False

        results = system(toChange)
        newToChange = {}
        newToChange["sx5IdmUrl"] = "http://localhost:18085/idm/config"
        newToChange["systemName"] = "test3"
        newToChange["clients"] = [{"nom": "client3"},{"nom": "client4"}]
        newToChange["sadu_principal"] = "http://sadu_principal"
        newToChange["sadu_secondary"] = [{"adresse": "http://sadu_secondary1"},{"adresse": "http://sadu_secondary2"}]
        newToChange["clientRoles_mapper"] = [{"spClientRole": "roleInSp11", "eq_sadu_role": "roleSadu11"},{"spClientRole": "roleInSp12", "eq_sadu_role": "roleSadu12"}]
        newToChange["state"] = "present"
        newToChange["force"] = False

        results = system(newToChange)
        #print str(results)
        self.assertTrue(results['changed'])
        systemClients = results["ansible_facts"]["systemes"]["clientsKeycloak"]
        for toChangeClient in toChange["clients"]:
            clientFound = False
            for systemClient in systemClients:
                if toChangeClient["nom"] == systemClient["nom"]:
                    clientFound = True
                    break
            self.assertTrue(clientFound, toChangeClient["nom"] + " not found")
        for newToChangeClient in newToChange["clients"]:
            clientFound = False
            for systemClient in systemClients:
                if newToChangeClient["nom"] == systemClient["nom"]:
                    clientFound = True
                    break
            self.assertTrue(clientFound, newToChangeClient["nom"] + " not found")
        
        
    def test_delete_system(self):
        toDelete = {}
#        toDelete["spUrl"] = "http://localhost:18081"
#        toDelete["spUsername"] = "admin"
#        toDelete["spPassword"] = "admin"
#        toDelete["spRealm"] = "master"
#        toDelete["idmClient_id"] = "admin-cli"
#        toDelete["idmClient_secret"] = ""
        toDelete["sx5IdmUrl"] = "http://localhost:18085/idm/config"
        toDelete["systemName"] = "system01"
        toDelete["clients"] = [{"nom": "client1"},{"nom": "client2"}]
        toDelete["sadu_principal"] = "http://sadu_principal"
        toDelete["sadu_secondary"] = [{"adresse": "http://sadu_secondary1"},{"adresse": "http://sadu_secondary2"}]
        toDelete["clientRoles_mapper"] = [{"spClientRole": "roleInSp11", "eq_sadu_role": "roleSadu11"},{"spClientRole": "roleInSp12", "eq_sadu_role": "roleSadu12"}]
        toDelete["state"] = "present"
        toDelete["force"] = False

        system(toDelete)
        toDelete["state"] = "absent"
        results = system(toDelete)
        #print str(results)
        self.assertTrue(results['changed'])
        self.assertEqual(results['stdout'], 'deleted', 'system has been deleted')
