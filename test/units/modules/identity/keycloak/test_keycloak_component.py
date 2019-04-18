import collections
import os
import unittest

from ansible.modules.identity.keycloak.keycloak_component import *

class KeycloakComponentTestCase(unittest.TestCase):
 
    def test_create_component_ldap_user_storage_provider(self):
        toCreate = {}
        toCreate["url"] = "http://localhost:18081"
        toCreate["username"] = "admin"
        toCreate["password"] = "admin"
        toCreate["realm"] = "master"
        toCreate["state"] = "present"
        toCreate["name"] = "test1"
        toCreate["parentId"] = "master"
        toCreate["providerId"] = "ldap"
        toCreate["providerType"] = "org.keycloak.storage.UserStorageProvider"
        toCreate["config"] = dict(
            vendor=["ad"],
            usernameLDAPAttribute=["sAMAccountName"],
            rdnLDAPAttribute=["cn"],
            uuidLDAPAttribute=["objectGUID"],
            userObjectClasses=["person, organizationalPerson, user"],
            connectionUrl=["ldap://ldap.server.com:389"],
            usersDn=["OU=users,DC=ldap,DC=server,DC=com"],
            authType=["simple"],
            bindDn=["CN=toto,OU=users,DC=ldap,DC=server,DC=com"],
            bindCredential=["LeTresLongMotDePasse"]
            )
        toCreate["subComponents"] = {
            "org.keycloak.storage.ldap.mappers.LDAPStorageMapper": [{
                    "name": "groupMapper",
                    "providerId": "group-ldap-mapper",
                    "config": {
                        "mode": ["READ_ONLY"],
                        "membership.attribute.type": ["DN"],
                        "user.roles.retrieve.strategy": ["LOAD_GROUPS_BY_MEMBER_ATTRIBUTE"],
                        "group.name.ldap.attribute": ["cn"],
                        "membership.ldap.attribute": ["member"],
                        "preserve.group.inheritance": ["true"],
                        "membership.user.ldap.attribute": ["uid"],
                        "group.object.classes": ["groupOfNames"],
                        "groups.dn": ["cn=newgroups,OU=SEC,DC=SANTEPUBLIQUE,DC=RTSS,DC=QC,DC=CA"],
                        "drop.non.existing.groups.during.sync": ["false"]
                    }
                },
                {
                    "name": "groupMapper2",
                    "providerId": "group-ldap-mapper",
                    "config": {
                        "mode": ["READ_ONLY"],
                        "membership.attribute.type": ["DN"],
                        "user.roles.retrieve.strategy": ["LOAD_GROUPS_BY_MEMBER_ATTRIBUTE"],
                        "group.name.ldap.attribute": ["cn"],
                        "membership.ldap.attribute": ["member"],
                        "preserve.group.inheritance": ["true"],
                        "membership.user.ldap.attribute": ["uid"],
                        "group.object.classes": ["groupOfNames"],
                        "groups.dn": ["cn=groups,OU=SEC,DC=SANTEPUBLIQUE,DC=RTSS,DC=QC,DC=CA"],
                        "drop.non.existing.groups.during.sync": ["false"]
                    }
                }
            ]
        }
        toCreate["force"] = False

        results = component(toCreate)
        #print str(results)
    
        self.assertTrue("component" in results['ansible_facts'] and results['ansible_facts']['component'] is not None)
        self.assertEquals(results['ansible_facts']['component']['name'],toCreate["name"],"name: " + results['ansible_facts']['component']['name'])
        self.assertTrue(results['changed'])
        self.assertEquals(results['ansible_facts']['component']['config']['vendor'][0],toCreate["config"]["vendor"][0],"vendor: " + results['ansible_facts']['component']['config']['vendor'][0])
        subComponentFound = False
        for subComponent in results['ansible_facts']['subComponents']:
            if subComponent["name"] == toCreate["subComponents"]["org.keycloak.storage.ldap.mappers.LDAPStorageMapper"][0]["name"]:
                subComponentFound = True
                break
        self.assertTrue(subComponentFound,"Sub component not found in the sub components")
        self.assertEquals(subComponent["config"]["groups.dn"][0], 
                     toCreate["subComponents"]["org.keycloak.storage.ldap.mappers.LDAPStorageMapper"][0]["config"]["groups.dn"][0],
                     "groups.dn: " + subComponent["config"]["groups.dn"][0] + ": " + toCreate["subComponents"]["org.keycloak.storage.ldap.mappers.LDAPStorageMapper"][0]["config"]["groups.dn"][0])
        subComponentFound = False
        for subComponent in results['ansible_facts']['subComponents']:
            if subComponent["name"] == toCreate["subComponents"]["org.keycloak.storage.ldap.mappers.LDAPStorageMapper"][1]["name"]:
                subComponentFound = True
                break
        self.assertTrue(subComponentFound,"Sub component not found in the sub components")
        self.assertEquals(subComponent["config"]["groups.dn"][0], 
                     toCreate["subComponents"]["org.keycloak.storage.ldap.mappers.LDAPStorageMapper"][1]["config"]["groups.dn"][0],
                     "groups.dn: " + subComponent["config"]["groups.dn"][0] + ": " + toCreate["subComponents"]["org.keycloak.storage.ldap.mappers.LDAPStorageMapper"][1]["config"]["groups.dn"][0])
        subComponentFound = False
        
    def test_modify_component_ldap_user_storage_provider(self):
        toModify = {}
        toModify["url"] = "http://localhost:18081"
        toModify["username"] = "admin"
        toModify["password"] = "admin"
        toModify["realm"] = "master"
        toModify["state"] = "present"
        toModify["name"] = "test2"
        toModify["providerId"] = "ldap"
        toModify["providerType"] = "org.keycloak.storage.UserStorageProvider"
        toModify["config"] = dict(
            vendor=["ad"],
            usernameLDAPAttribute=["sAMAccountName"],
            rdnLDAPAttribute=["cn"],
            uuidLDAPAttribute=["objectGUID"],
            userObjectClasses=["person, organizationalPerson, user"],
            connectionUrl=["ldap://ldap.server.com:389"],
            usersDn=["OU=users,DC=ldap,DC=server,DC=com"],
            authType=["simple"],
            bindDn=["CN=toto,OU=users,DC=ldap,DC=server,DC=com"],
            bindCredential=["LeTresLongMotDePasse"]
            )
        toModify["subComponents"] = {
                "org.keycloak.storage.ldap.mappers.LDAPStorageMapper": [{
                    "name": "groupMapper",
                    "providerId": "group-ldap-mapper",
                    "config": {
                        "mode": ["READ_ONLY"],
                        "membership.attribute.type": ["DN"],
                        "user.roles.retrieve.strategy": ["LOAD_GROUPS_BY_MEMBER_ATTRIBUTE"],
                        "group.name.ldap.attribute": ["cn"],
                        "membership.ldap.attribute": ["member"],
                        "preserve.group.inheritance": ["true"],
                        "membership.user.ldap.attribute": ["uid"],
                        "group.object.classes": ["groupOfNames"],
                        "groups.dn": ["cn=groups,OU=SEC,DC=SANTEPUBLIQUE,DC=RTSS,DC=QC,DC=CA"],
                        "drop.non.existing.groups.during.sync": ["false"]
                    }
                }]
            }
        toModify["force"] = False
        component(toModify)
        toModify["config"]["connectionUrl"][0] = "TestURL"
        toModify["subComponents"] = {
            "org.keycloak.storage.ldap.mappers.LDAPStorageMapper": [{
                    "name": "groupMapper",
                    "providerId": "group-ldap-mapper",
                    "config": {
                        "mode": ["READ_ONLY"],
                        "membership.attribute.type": ["DN"],
                        "user.roles.retrieve.strategy": ["LOAD_GROUPS_BY_MEMBER_ATTRIBUTE"],
                        "group.name.ldap.attribute": ["cn"],
                        "membership.ldap.attribute": ["member"],
                        "preserve.group.inheritance": ["true"],
                        "membership.user.ldap.attribute": ["uid"],
                        "group.object.classes": ["groupOfNames"],
                        "groups.dn": ["cn=newgroups,OU=SEC,DC=SANTEPUBLIQUE,DC=RTSS,DC=QC,DC=CA"],
                        "drop.non.existing.groups.during.sync": ["false"]
                    }
                },
                {
                    "name": "groupMapper2",
                    "providerId": "group-ldap-mapper",
                    "config": {
                        "mode": ["READ_ONLY"],
                        "membership.attribute.type": ["DN"],
                        "user.roles.retrieve.strategy": ["LOAD_GROUPS_BY_MEMBER_ATTRIBUTE"],
                        "group.name.ldap.attribute": ["cn"],
                        "membership.ldap.attribute": ["member"],
                        "preserve.group.inheritance": ["true"],
                        "membership.user.ldap.attribute": ["uid"],
                        "group.object.classes": ["groupOfNames"],
                        "groups.dn": ["cn=groups,OU=SEC,DC=SANTEPUBLIQUE,DC=RTSS,DC=QC,DC=CA"],
                        "drop.non.existing.groups.during.sync": ["false"]
                    }
                }
            ]
        }
        results = component(toModify)
        #print str(results)
    
        self.assertEquals(results['ansible_facts']['component']['name'],"test2","name: " + results['ansible_facts']['component']['name'])
        self.assertTrue(results['changed'])
        self.assertEquals(results['ansible_facts']['component']['config']['vendor'][0],"ad","vendor: " + results['ansible_facts']['component']['config']['vendor'][0])
        self.assertEquals(results['ansible_facts']['component']['config']['connectionUrl'][0],"TestURL","connectionUrl: " + results['ansible_facts']['component']['config']['connectionUrl'][0])
        subComponentFound = False
        for subComponent in results['ansible_facts']['subComponents']:
            if subComponent["name"] == toModify["subComponents"]["org.keycloak.storage.ldap.mappers.LDAPStorageMapper"][0]["name"]:
                subComponentFound = True
                break
        self.assertTrue(subComponentFound,"Sub component not found in the sub components")
        self.assertEquals(subComponent["config"]["groups.dn"][0], 
                     toModify["subComponents"]["org.keycloak.storage.ldap.mappers.LDAPStorageMapper"][0]["config"]["groups.dn"][0],
                     "groups.dn: " + subComponent["config"]["groups.dn"][0] + ": " + toModify["subComponents"]["org.keycloak.storage.ldap.mappers.LDAPStorageMapper"][0]["config"]["groups.dn"][0])
        subComponentFound = False
        for subComponent in results['ansible_facts']['subComponents']:
            if subComponent["name"] == toModify["subComponents"]["org.keycloak.storage.ldap.mappers.LDAPStorageMapper"][1]["name"]:
                subComponentFound = True
                break
        self.assertTrue(subComponentFound,"Sub component not found in the sub components")
        self.assertEquals(subComponent["config"]["groups.dn"][0], 
                     toModify["subComponents"]["org.keycloak.storage.ldap.mappers.LDAPStorageMapper"][1]["config"]["groups.dn"][0],
                     "groups.dn: " + subComponent["config"]["groups.dn"][0] + ": " + toModify["subComponents"]["org.keycloak.storage.ldap.mappers.LDAPStorageMapper"][1]["config"]["groups.dn"][0])

    def test_do_not_modify_component_ldap_user_storage_provider(self):
        toDoNotModify = {}
        toDoNotModify["url"] = "http://localhost:18081"
        toDoNotModify["username"] = "admin"
        toDoNotModify["password"] = "admin"
        toDoNotModify["realm"] = "master"
        toDoNotModify["state"] = "present"
        toDoNotModify["name"] = "test3"
        toDoNotModify["providerId"] = "ldap"
        toDoNotModify["providerType"] = "org.keycloak.storage.UserStorageProvider"
        toDoNotModify["config"] = dict(
            vendor=["ad"],
            usernameLDAPAttribute=["sAMAccountName"],
            rdnLDAPAttribute=["cn"],
            uuidLDAPAttribute=["objectGUID"],
            userObjectClasses=["person, organizationalPerson, user"],
            connectionUrl=["ldap://ldap.server.com:389"],
            usersDn=["OU=users,DC=ldap,DC=server,DC=com"],
            authType=["simple"],
            bindDn=["CN=toto,OU=users,DC=ldap,DC=server,DC=com"],
            bindCredential=["LeTresLongMotDePasse"]
            )
        toDoNotModify["subComponents"] = {
            "org.keycloak.storage.ldap.mappers.LDAPStorageMapper": [{
                    "name": "groupMapper",
                    "providerId": "group-ldap-mapper",
                    "config": {
                        "mode": ["READ_ONLY"],
                        "membership.attribute.type": ["DN"],
                        "user.roles.retrieve.strategy": ["LOAD_GROUPS_BY_MEMBER_ATTRIBUTE"],
                        "group.name.ldap.attribute": ["cn"],
                        "membership.ldap.attribute": ["member"],
                        "preserve.group.inheritance": ["true"],
                        "membership.user.ldap.attribute": ["uid"],
                        "group.object.classes": ["groupOfNames"],
                        "groups.dn": ["cn=newgroups,OU=SEC,DC=SANTEPUBLIQUE,DC=RTSS,DC=QC,DC=CA"],
                        "drop.non.existing.groups.during.sync": ["false"]
                    }
                },
                {
                    "name": "groupMapper2",
                    "providerId": "group-ldap-mapper",
                    "config": {
                        "mode": ["READ_ONLY"],
                        "membership.attribute.type": ["DN"],
                        "user.roles.retrieve.strategy": ["LOAD_GROUPS_BY_MEMBER_ATTRIBUTE"],
                        "group.name.ldap.attribute": ["cn"],
                        "membership.ldap.attribute": ["member"],
                        "preserve.group.inheritance": ["true"],
                        "membership.user.ldap.attribute": ["uid"],
                        "group.object.classes": ["groupOfNames"],
                        "groups.dn": ["cn=groups,OU=SEC,DC=SANTEPUBLIQUE,DC=RTSS,DC=QC,DC=CA"],
                        "drop.non.existing.groups.during.sync": ["false"]
                    }
                }
            ]
        }
        toDoNotModify["force"] = False
        component(toDoNotModify)
        results = component(toDoNotModify)
    
        self.assertEquals(results['ansible_facts']['component']['name'],"test3","name: " + results['ansible_facts']['component']['name'])
        self.assertFalse(results['changed'])
        self.assertEquals(results['ansible_facts']['component']['config']['vendor'][0],"ad","vendor: " + results['ansible_facts']['component']['config']['vendor'][0])
        self.assertEquals(results['ansible_facts']['component']['config']['connectionUrl'][0],"ldap://ldap.server.com:389","connectionUrl: " + results['ansible_facts']['component']['config']['connectionUrl'][0])
        subComponentFound = False
        for subComponent in results['ansible_facts']['subComponents']:
            if subComponent["name"] == toDoNotModify["subComponents"]["org.keycloak.storage.ldap.mappers.LDAPStorageMapper"][0]["name"]:
                subComponentFound = True
                break
        self.assertTrue(subComponentFound,"Sub component not found in the sub components")
        self.assertEquals(subComponent["config"]["groups.dn"][0], 
                     toDoNotModify["subComponents"]["org.keycloak.storage.ldap.mappers.LDAPStorageMapper"][0]["config"]["groups.dn"][0],
                     "groups.dn: " + subComponent["config"]["groups.dn"][0] + ": " + toDoNotModify["subComponents"]["org.keycloak.storage.ldap.mappers.LDAPStorageMapper"][0]["config"]["groups.dn"][0])
        subComponentFound = False
        for subComponent in results['ansible_facts']['subComponents']:
            if subComponent["name"] == toDoNotModify["subComponents"]["org.keycloak.storage.ldap.mappers.LDAPStorageMapper"][1]["name"]:
                subComponentFound = True
                break
        self.assertTrue(subComponentFound,"Sub component not found in the sub components")
        self.assertEquals(subComponent["config"]["groups.dn"][0], 
                     toDoNotModify["subComponents"]["org.keycloak.storage.ldap.mappers.LDAPStorageMapper"][1]["config"]["groups.dn"][0],
                     "groups.dn: " + subComponent["config"]["groups.dn"][0] + ": " + toDoNotModify["subComponents"]["org.keycloak.storage.ldap.mappers.LDAPStorageMapper"][1]["config"]["groups.dn"][0])

    def test_delete_component_ldap_user_storage_provider(self):
        toDelete = {}
        toDelete["url"] = "http://localhost:18081"
        toDelete["username"] = "admin"
        toDelete["password"] = "admin"
        toDelete["realm"] = "master"
        toDelete["state"] = "present"
        toDelete["name"] = "test4"
        toDelete["providerId"] = "ldap"
        toDelete["providerType"] = "org.keycloak.storage.UserStorageProvider"
        toDelete["config"] = dict(
            vendor=["ad"],
            usernameLDAPAttribute=["sAMAccountName"],
            rdnLDAPAttribute=["cn"],
            uuidLDAPAttribute=["objectGUID"],
            userObjectClasses=["person, organizationalPerson, user"],
            connectionUrl=["ldap://ldap.server.com:389"],
            usersDn=["OU=users,DC=ldap,DC=server,DC=com"],
            authType=["simple"],
            bindDn=["CN=toto,OU=users,DC=ldap,DC=server,DC=com"],
            bindCredential=["LeTresLongMotDePasse"]
            )
        toDelete["subComponents"] = {
            "org.keycloak.storage.ldap.mappers.LDAPStorageMapper": [{
                    "name": "groupMapper",
                    "providerId": "group-ldap-mapper",
                    "config": {
                        "mode": ["READ_ONLY"],
                        "membership.attribute.type": ["DN"],
                        "user.roles.retrieve.strategy": ["LOAD_GROUPS_BY_MEMBER_ATTRIBUTE"],
                        "group.name.ldap.attribute": ["cn"],
                        "membership.ldap.attribute": ["member"],
                        "preserve.group.inheritance": ["true"],
                        "membership.user.ldap.attribute": ["uid"],
                        "group.object.classes": ["groupOfNames"],
                        "groups.dn": ["cn=newgroups,OU=SEC,DC=SANTEPUBLIQUE,DC=RTSS,DC=QC,DC=CA"],
                        "drop.non.existing.groups.during.sync": ["false"]
                    }
                },
                {
                    "name": "groupMapper2",
                    "providerId": "group-ldap-mapper",
                    "config": {
                        "mode": ["READ_ONLY"],
                        "membership.attribute.type": ["DN"],
                        "user.roles.retrieve.strategy": ["LOAD_GROUPS_BY_MEMBER_ATTRIBUTE"],
                        "group.name.ldap.attribute": ["cn"],
                        "membership.ldap.attribute": ["member"],
                        "preserve.group.inheritance": ["true"],
                        "membership.user.ldap.attribute": ["uid"],
                        "group.object.classes": ["groupOfNames"],
                        "groups.dn": ["cn=groups,OU=SEC,DC=SANTEPUBLIQUE,DC=RTSS,DC=QC,DC=CA"],
                        "drop.non.existing.groups.during.sync": ["false"]
                    }
                }
            ]
        }
        toDelete["force"] = False
        component(toDelete)
        toDelete["state"] = "absent"
        results = component(toDelete)
    
        self.assertTrue(results['changed'])
        self.assertEqual(results['stdout'], 'deleted', 'client has been deleted')
