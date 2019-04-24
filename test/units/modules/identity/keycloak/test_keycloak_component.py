import collections
import os

from ansible.modules.identity.keycloak import keycloak_component
from units.modules.utils import AnsibleExitJson, AnsibleFailJson, ModuleTestCase, set_module_args

class KeycloakComponentTestCase(ModuleTestCase):

    modifyComponentLdapUserStorageProvider = {
        "url": "http://localhost:18081/auth",
        "username": "admin",
        "password": "admin",
        "realm": "master",
        "state": "present",
        "name": "test_modify_component_ldap_user_storage_provider",
        "providerId": "ldap",
        "providerType": "org.keycloak.storage.UserStorageProvider",
        "config": {
            "vendor": ["ad"],
            "usernameLDAPAttribute": ["sAMAccountName"],
            "rdnLDAPAttribute": ["cn"],
            "uuidLDAPAttribute": ["objectGUID"],
            "userObjectClasses": ["person, organizationalPerson, user"],
            "connectionUrl": ["ldap://ldap.server.com:389"],
            "usersDn": ["OU=users,DC=ldap,DC=server,DC=com"],
            "authType":["simple"],
            "bindDn":["CN=toto,OU=users,DC=ldap,DC=server,DC=com"],
            "bindCredential": ["LeTresLongMotDePasse"]
        },
        "subComponents": {
            "org.keycloak.storage.ldap.mappers.LDAPStorageMapper": [
                {
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
                }
            ]
        },
        "force": False
    }
    doNotModifyComponentLdapUserStorageProvider = {
        "url": "http://localhost:18081/auth",
        "username": "admin",
        "password": "admin",
        "realm": "master",
        "state": "present",
        "name":"test_do_not_modify_component_ldap_user_storage_provider",
        "providerId": "ldap",
        "providerType": "org.keycloak.storage.UserStorageProvider",
        "config": {
            "vendor": ["ad"],
            "usernameLDAPAttribute": ["sAMAccountName"],
            "rdnLDAPAttribute": ["cn"],
            "uuidLDAPAttribute": ["objectGUID"],
            "userObjectClasses": ["person, organizationalPerson, user"],
            "connectionUrl": ["ldap://ldap.server.com:389"],
            "usersDn": ["OU=users,DC=ldap,DC=server,DC=com"],
            "authType": ["simple"],
            "bindDn": ["CN=toto,OU=users,DC=ldap,DC=server,DC=com"],
            "bindCredential": ["LeTresLongMotDePasse"]
        },
        "subComponents": {
            "org.keycloak.storage.ldap.mappers.LDAPStorageMapper": [
                {
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
        },
        "force": False
    }
    
    modifyComponentLdapUserStorageProviderForce = {
        "url": "http://localhost:18081/auth",
        "username": "admin",
        "password": "admin",
        "realm": "master",
        "state": "present",
        "name":"test_modify_component_ldap_user_storage_provider_force",
        "providerId": "ldap",
        "providerType": "org.keycloak.storage.UserStorageProvider",
        "config": {
            "vendor": ["ad"],
            "usernameLDAPAttribute": ["sAMAccountName"],
            "rdnLDAPAttribute": ["cn"],
            "uuidLDAPAttribute": ["objectGUID"],
            "userObjectClasses": ["person, organizationalPerson, user"],
            "connectionUrl": ["ldap://ldap.server.com:389"],
            "usersDn": ["OU=users,DC=ldap,DC=server,DC=com"],
            "authType": ["simple"],
            "bindDn": ["CN=toto,OU=users,DC=ldap,DC=server,DC=com"],
            "bindCredential": ["LeTresLongMotDePasse"]
        },
        "subComponents": {
            "org.keycloak.storage.ldap.mappers.LDAPStorageMapper": [
                {
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
        },
        "force": False
    }

    deleteComponentLdapUserStorageProvider = {
        "url": "http://localhost:18081/auth",
        "username": "admin",
        "password": "admin",
        "realm": "master",
        "state": "present",
        "name": "test_delete_component_ldap_user_storage_provider",
        "providerId": "ldap",
        "providerType": "org.keycloak.storage.UserStorageProvider",
        "config": {
            "vendor": ["ad"],
            "usernameLDAPAttribute": ["sAMAccountName"],
            "rdnLDAPAttribute": ["cn"],
            "uuidLDAPAttribute": ["objectGUID"],
            "userObjectClasses": ["person, organizationalPerson, user"],
            "connectionUrl": ["ldap://ldap.server.com:389"],
            "usersDn": ["OU=users,DC=ldap,DC=server,DC=com"],
            "authType": ["simple"],
            "bindDn": ["CN=toto,OU=users,DC=ldap,DC=server,DC=com"],
            "bindCredential": ["LeTresLongMotDePasse"]
        },
        "subComponents": {
            "org.keycloak.storage.ldap.mappers.LDAPStorageMapper": [
                {
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
        },
        "force": False
    }

    def setUp(self):
        super(KeycloakComponentTestCase, self).setUp()
        self.module = keycloak_component
        set_module_args(self.modifyComponentLdapUserStorageProvider)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        set_module_args(self.modifyComponentLdapUserStorageProviderForce)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        set_module_args(self.doNotModifyComponentLdapUserStorageProvider)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        set_module_args(self.deleteComponentLdapUserStorageProvider)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
 
    def tearDown(self):
        super(KeycloakComponentTestCase, self).tearDown()
 
    def test_create_component_ldap_user_storage_provider(self):
        toCreate = {}
        toCreate["url"] = "http://localhost:18081/auth"
        toCreate["username"] = "admin"
        toCreate["password"] = "admin"
        toCreate["realm"] = "master"
        toCreate["state"] = "present"
        toCreate["name"] = "test_create_component_ldap_user_storage_provider"
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

        set_module_args(toCreate)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.assertTrue(results.exception.args[0]['changed'])
        self.assertTrue("component" in results.exception.args[0] and results.exception.args[0]['component'] is not None)
        self.assertEquals(results.exception.args[0]['component']['name'],toCreate["name"],"name: " + results.exception.args[0]['component']['name'])
        
        self.assertEquals(results.exception.args[0]['component']['config']['vendor'][0],toCreate["config"]["vendor"][0],"vendor: " + results.exception.args[0]['component']['config']['vendor'][0])
        subComponentFound = False
        for subComponent in results.exception.args[0]['subComponents']:
            if subComponent["name"] == toCreate["subComponents"]["org.keycloak.storage.ldap.mappers.LDAPStorageMapper"][0]["name"]:
                subComponentFound = True
                break
        self.assertTrue(subComponentFound,"Sub component not found in the sub components")
        self.assertEquals(subComponent["config"]["groups.dn"][0], 
                     toCreate["subComponents"]["org.keycloak.storage.ldap.mappers.LDAPStorageMapper"][0]["config"]["groups.dn"][0],
                     "groups.dn: " + subComponent["config"]["groups.dn"][0] + ": " + toCreate["subComponents"]["org.keycloak.storage.ldap.mappers.LDAPStorageMapper"][0]["config"]["groups.dn"][0])
        subComponentFound = False
        for subComponent in results.exception.args[0]['subComponents']:
            if subComponent["name"] == toCreate["subComponents"]["org.keycloak.storage.ldap.mappers.LDAPStorageMapper"][1]["name"]:
                subComponentFound = True
                break
        self.assertTrue(subComponentFound,"Sub component not found in the sub components")
        self.assertEquals(subComponent["config"]["groups.dn"][0], 
                     toCreate["subComponents"]["org.keycloak.storage.ldap.mappers.LDAPStorageMapper"][1]["config"]["groups.dn"][0],
                     "groups.dn: " + subComponent["config"]["groups.dn"][0] + ": " + toCreate["subComponents"]["org.keycloak.storage.ldap.mappers.LDAPStorageMapper"][1]["config"]["groups.dn"][0])
        subComponentFound = False
        
    def test_modify_component_ldap_user_storage_provider(self):
        self.modifyComponentLdapUserStorageProvider["config"]["connectionUrl"][0] = "TestURL"
        self.modifyComponentLdapUserStorageProvider["subComponents"] = {
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
        set_module_args(self.modifyComponentLdapUserStorageProvider)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.assertTrue(results.exception.args[0]['changed'])
    
        self.assertEquals(results.exception.args[0]['component']['name'], self.modifyComponentLdapUserStorageProvider["name"] ,"name: " + results.exception.args[0]['component']['name'])
        self.assertEquals(results.exception.args[0]['component']['config']['vendor'][0], self.modifyComponentLdapUserStorageProvider['config']['vendor'][0] ,"vendor: " + results.exception.args[0]['component']['config']['vendor'][0])
        self.assertEquals(results.exception.args[0]['component']['config']['connectionUrl'][0],self.modifyComponentLdapUserStorageProvider['config']['connectionUrl'][0], "connectionUrl: " + results.exception.args[0]['component']['config']['connectionUrl'][0])
        subComponentFound = False
        for subComponent in results.exception.args[0]['subComponents']:
            if subComponent["name"] == self.modifyComponentLdapUserStorageProvider["subComponents"]["org.keycloak.storage.ldap.mappers.LDAPStorageMapper"][0]["name"]:
                subComponentFound = True
                break
        self.assertTrue(subComponentFound,"Sub component not found in the sub components")
        self.assertEquals(subComponent["config"]["groups.dn"][0], 
                     self.modifyComponentLdapUserStorageProvider["subComponents"]["org.keycloak.storage.ldap.mappers.LDAPStorageMapper"][0]["config"]["groups.dn"][0],
                     "groups.dn: " + subComponent["config"]["groups.dn"][0] + ": " + self.modifyComponentLdapUserStorageProvider["subComponents"]["org.keycloak.storage.ldap.mappers.LDAPStorageMapper"][0]["config"]["groups.dn"][0])
        subComponentFound = False
        for subComponent in results.exception.args[0]['subComponents']:
            if subComponent["name"] == self.modifyComponentLdapUserStorageProvider["subComponents"]["org.keycloak.storage.ldap.mappers.LDAPStorageMapper"][1]["name"]:
                subComponentFound = True
                break
        self.assertTrue(subComponentFound,"Sub component not found in the sub components")
        self.assertEquals(subComponent["config"]["groups.dn"][0], 
                     self.modifyComponentLdapUserStorageProvider["subComponents"]["org.keycloak.storage.ldap.mappers.LDAPStorageMapper"][1]["config"]["groups.dn"][0],
                     "groups.dn: " + subComponent["config"]["groups.dn"][0] + ": " + self.modifyComponentLdapUserStorageProvider["subComponents"]["org.keycloak.storage.ldap.mappers.LDAPStorageMapper"][1]["config"]["groups.dn"][0])

    def test_do_not_modify_component_ldap_user_storage_provider(self):
        set_module_args(self.doNotModifyComponentLdapUserStorageProvider)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.assertFalse(results.exception.args[0]['changed'])
    
        self.assertEquals(results.exception.args[0]['component']['name'], self.doNotModifyComponentLdapUserStorageProvider['name'],"name: " + results.exception.args[0]['component']['name'])
        self.assertEquals(results.exception.args[0]['component']['config']['vendor'][0], self.doNotModifyComponentLdapUserStorageProvider['config']['vendor'][0] ,"vendor: " + results.exception.args[0]['component']['config']['vendor'][0])
        self.assertEquals(results.exception.args[0]['component']['config']['connectionUrl'][0], self.doNotModifyComponentLdapUserStorageProvider['config']['connectionUrl'][0], "connectionUrl: " + results.exception.args[0]['component']['config']['connectionUrl'][0])
        subComponentFound = False
        for subComponent in results.exception.args[0]['subComponents']:
            if subComponent["name"] == self.doNotModifyComponentLdapUserStorageProvider["subComponents"]["org.keycloak.storage.ldap.mappers.LDAPStorageMapper"][0]["name"]:
                subComponentFound = True
                break
        self.assertTrue(subComponentFound,"Sub component not found in the sub components")
        self.assertEquals(subComponent["config"]["groups.dn"][0], 
                     self.doNotModifyComponentLdapUserStorageProvider["subComponents"]["org.keycloak.storage.ldap.mappers.LDAPStorageMapper"][0]["config"]["groups.dn"][0],
                     "groups.dn: " + subComponent["config"]["groups.dn"][0] + ": " + self.doNotModifyComponentLdapUserStorageProvider["subComponents"]["org.keycloak.storage.ldap.mappers.LDAPStorageMapper"][0]["config"]["groups.dn"][0])
        subComponentFound = False
        for subComponent in results.exception.args[0]['subComponents']:
            if subComponent["name"] == self.doNotModifyComponentLdapUserStorageProvider["subComponents"]["org.keycloak.storage.ldap.mappers.LDAPStorageMapper"][1]["name"]:
                subComponentFound = True
                break
        self.assertTrue(subComponentFound,"Sub component not found in the sub components")
        self.assertEquals(subComponent["config"]["groups.dn"][0], 
                     self.doNotModifyComponentLdapUserStorageProvider["subComponents"]["org.keycloak.storage.ldap.mappers.LDAPStorageMapper"][1]["config"]["groups.dn"][0],
                     "groups.dn: " + subComponent["config"]["groups.dn"][0] + ": " + self.doNotModifyComponentLdapUserStorageProvider["subComponents"]["org.keycloak.storage.ldap.mappers.LDAPStorageMapper"][1]["config"]["groups.dn"][0])

    def test_modify_component_ldap_user_storage_provider_force(self):
        self.modifyComponentLdapUserStorageProviderForce['force'] = True
        
        set_module_args(self.modifyComponentLdapUserStorageProviderForce)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.assertTrue(results.exception.args[0]['changed'])
    
        self.assertEquals(results.exception.args[0]['component']['name'], self.modifyComponentLdapUserStorageProviderForce['name'],"name: " + results.exception.args[0]['component']['name'])
        self.assertEquals(results.exception.args[0]['component']['config']['vendor'][0], self.modifyComponentLdapUserStorageProviderForce['config']['vendor'][0] ,"vendor: " + results.exception.args[0]['component']['config']['vendor'][0])
        self.assertEquals(results.exception.args[0]['component']['config']['connectionUrl'][0], self.modifyComponentLdapUserStorageProviderForce['config']['connectionUrl'][0], "connectionUrl: " + results.exception.args[0]['component']['config']['connectionUrl'][0])
        subComponentFound = False
        for subComponent in results.exception.args[0]['subComponents']:
            if subComponent["name"] == self.modifyComponentLdapUserStorageProviderForce["subComponents"]["org.keycloak.storage.ldap.mappers.LDAPStorageMapper"][0]["name"]:
                subComponentFound = True
                break
        self.assertTrue(subComponentFound,"Sub component not found in the sub components")
        self.assertEquals(subComponent["config"]["groups.dn"][0], 
                     self.modifyComponentLdapUserStorageProviderForce["subComponents"]["org.keycloak.storage.ldap.mappers.LDAPStorageMapper"][0]["config"]["groups.dn"][0],
                     "groups.dn: " + subComponent["config"]["groups.dn"][0] + ": " + self.modifyComponentLdapUserStorageProviderForce["subComponents"]["org.keycloak.storage.ldap.mappers.LDAPStorageMapper"][0]["config"]["groups.dn"][0])
        subComponentFound = False
        for subComponent in results.exception.args[0]['subComponents']:
            if subComponent["name"] == self.modifyComponentLdapUserStorageProviderForce["subComponents"]["org.keycloak.storage.ldap.mappers.LDAPStorageMapper"][1]["name"]:
                subComponentFound = True
                break
        self.assertTrue(subComponentFound,"Sub component not found in the sub components")
        self.assertEquals(subComponent["config"]["groups.dn"][0], 
                     self.modifyComponentLdapUserStorageProviderForce["subComponents"]["org.keycloak.storage.ldap.mappers.LDAPStorageMapper"][1]["config"]["groups.dn"][0],
                     "groups.dn: " + subComponent["config"]["groups.dn"][0] + ": " + self.modifyComponentLdapUserStorageProviderForce["subComponents"]["org.keycloak.storage.ldap.mappers.LDAPStorageMapper"][1]["config"]["groups.dn"][0])

    def test_delete_component_ldap_user_storage_provider(self):
        self.deleteComponentLdapUserStorageProvider["state"] = "absent"
        set_module_args(self.deleteComponentLdapUserStorageProvider)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.assertTrue(results.exception.args[0]['changed'])
        self.assertRegexpMatches(results.exception.args[0]['msg'], 'deleted', 'component not deleted')
