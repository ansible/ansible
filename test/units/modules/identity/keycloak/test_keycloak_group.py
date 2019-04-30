# -*- coding: utf-8 -*-
# This unit test class need a Keycloak server running on localhost using port 18081.
# An admin user must exist and his password need to be admin.
# It also need a 389-ds server running on port 10389 with the following OU:
# Users: ou=People,dc=example,dc=com
# Groups: ou=Groups,dc=example,dc=com
# The admin bind DN must be cn=Directory Manager
# The password must be Admin123
# Use the following command to create a compliant Docker container:
# docker run -d --rm --name testldap -p 10389:389 minkwe/389ds:latest
# Use the following command to run a Keycloak server with Docker:
# docker run -d --rm --name testkc -p 18081:8080 --link testldap:testldap -e KEYCLOAK_USER=admin -e KEYCLOAK_PASSWORD=admin jboss/keycloak:latest
import collections
import os
import unittest
import socket
from ansible.modules.identity.keycloak import keycloak_group
from ansible.module_utils.keycloak_utils import isDictEquals
from ansible.modules.identity.keycloak import keycloak_component
from units.modules.utils import AnsibleExitJson, AnsibleFailJson, ModuleTestCase, set_module_args

class KeycloakGroupTestCase(ModuleTestCase):
    userStorageComponent = {
        "auth_keycloak_url": "http://localhost:18081/auth",
        "auth_username": "admin",
        "auth_password": "admin",
        "realm": "master",
        "state": "present",
        "name": "forGroupUnitTests",
        "parentId": "master",
        "providerId": "ldap",
        "providerType": "org.keycloak.storage.UserStorageProvider",
        "config": {
            "vendor": ["rhds"],
            "usernameLDAPAttribute": ["uid"],
            "rdnLDAPAttribute": ["uid"],
            "uuidLDAPAttribute": ["nsuniqueid"],
            "userObjectClasses": [
                "inetOrgPerson",
                "organizationalPerson"
                ],
            "connectionUrl": ["ldap://testldap:389"],
            "usersDn": ["ou=People,dc=example,dc=com"],
            "authType": ["simple"],
            "bindDn": ["cn=Directory Manager"],
            "bindCredential": ["Admin123"]
        },
        "subComponents": {
            "org.keycloak.storage.ldap.mappers.LDAPStorageMapper": [{
                "name": "groupMapper",
                "providerId": "group-ldap-mapper",
                "config": {
                    "mode": ["LDAP_ONLY"],
                    "membership.attribute.type": ["DN"],
                    "user.roles.retrieve.strategy": ["LOAD_GROUPS_BY_MEMBER_ATTRIBUTE"],
                    "group.name.ldap.attribute": ["cn"],
                    "membership.ldap.attribute": ["member"],
                    "preserve.group.inheritance": ["true"],
                    "membership.user.ldap.attribute": ["cn"],
                    "group.object.classes": ["groupOfNames"],
                    "groups.dn": ["ou=Groups,dc=example,dc=com"],
                    "drop.non.existing.groups.during.sync": ["false"]
                }
            }],
        },
        "force": False
    }
    groupNotChanged = {
            "auth_username":"admin", 
            "auth_password":"admin",
            "realm":"master",
            "auth_keycloak_url":"http://localhost:18081/auth",
            "name":"test_group_not_changed",
            "attributes": {
                "attr1":["value1"],
                "attr2":["value2"]
            }, 
            "realmRoles": [
                "uma_authorization"
            ], 
            "clientRoles": [{
                "clientid": "master-realm",
                "roles": [
                    "manage-users"
                    ]
                }
            ], 
            "state":"present",
            "force":False
        }
    modifyGroup = {
            "auth_username":"admin", 
            "auth_password":"admin",
            "realm":"master",
            "auth_keycloak_url":"http://localhost:18081/auth",
            "name":"test_modify_group",
            "attributes": {
                "attr1":["value1"],
                "attr2":["value2"]
            }, 
            "realmRoles": [
                "uma_authorization",
            ], 
            "clientRoles": [{
                "clientid": "master-realm",
                "roles": [
                    "manage-users",
                    "view-identity-providers"
                    ]
                }
            ],
            "state":"present",
            "force":False
        }
    deleteGroup = {
            "auth_username":"admin", 
            "auth_password":"admin",
            "realm":"master",
            "auth_keycloak_url":"http://localhost:18081/auth",
            "name":"test_delete_group",
            "attributes": {
                "attr1":["value1"],
                "attr2":["value2"]
            }, 
            "state":"present",
            "force":False
        }
    groupModifyForce = {
            "auth_username":"admin", 
            "auth_password":"admin",
            "realm":"master",
            "auth_keycloak_url":"http://localhost:18081/auth",
            "name":"test_group_modify_force",
            "attributes": {
                "attr1":["value1"],
                "attr2":["value2"]
            }, 
            "realmRoles": [
                "uma_authorization"
            ], 
            "clientRoles": [{
                "clientid": "master-realm",
                "roles": [
                    "manage-users"
                    ]
                }
            ], 
            "state":"present",
            "force":False
        }
    def setUp(self):
        super(KeycloakGroupTestCase, self).setUp()
        self.module = keycloak_component
        set_module_args(self.userStorageComponent)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.module = keycloak_group
        set_module_args(self.groupNotChanged)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        set_module_args(self.modifyGroup)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        set_module_args(self.deleteGroup)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        
    def tearDown(self):
        self.userStorageComponent["state"] = "absent"
        self.module = keycloak_component
        set_module_args(self.userStorageComponent)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        super(KeycloakGroupTestCase, self).tearDown()
        
    def test_create_group_with_attibutes_dict(self):
        toCreate = {
            "auth_username":"admin", 
            "auth_password":"admin",
            "realm":"master",
            "auth_keycloak_url":"http://localhost:18081/auth",
            "name":"test_create_group_with_attibutes_dict",
            "attributes": {
                "attr1":["value1"],
                "attr2":["value2"]
            }, 
            "realmRoles": [
                "uma_authorization"
            ], 
            "clientRoles": [{
                "clientid": "master-realm",
                "roles": [
                    "manage-users",
                    "view-identity-providers"
                    ]
                }
            ],
            "state":"present",
            "force":False
        }

        self.module = keycloak_group
        set_module_args(toCreate)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.assertTrue(results.exception.args[0]['changed'])
        self.assertEquals(results.exception.args[0]["group"]["name"], toCreate["name"], "name: " + results.exception.args[0]["group"]["name"] + " : " + toCreate["name"])
        self.assertTrue(isDictEquals(toCreate["attributes"],results.exception.args[0]["group"]["attributes"]), "attributes: " + str(results.exception.args[0]["group"]["attributes"]) + " : " + str(toCreate["attributes"]))
        self.assertTrue(isDictEquals(toCreate["clientRoles"],results.exception.args[0]["group"]["clientRoles"]), "clientRoles: " + str(results.exception.args[0]["group"]["clientRoles"]) + " : " + str(toCreate["clientRoles"]))
        self.assertTrue(isDictEquals(toCreate["realmRoles"],results.exception.args[0]["group"]["realmRoles"]), "realmRoles: " + str(results.exception.args[0]["group"]["realmRoles"]) + " : " + str(toCreate["realmRoles"]))
        
    def test_create_group_with_attributes_list(self):
        toCreate = {
            "auth_username":"admin", 
            "auth_password":"admin",
            "realm":"master",
            "auth_keycloak_url":"http://localhost:18081/auth",
            "name":"test_create_group_with_attributes_list",
            "attributes": {
                "attr1":["value1"],
                "attr2":["value2"]
            },
            "attributes_list": [
                {
                    "name":"attr1",
                    "value":["value1"]
                    },
                {
                    "name": "attr2",
                    "value":["value2"]
                    }
            ], 
            "realmRoles": [
                "uma_authorization"
            ], 
            "clientRoles": [{
                "clientid": "master-realm",
                "roles": [
                    "manage-users",
                    "view-identity-providers"
                    ]
                }
            ], 
            "state":"present",
            "force":False
        }
        
        self.module = keycloak_group
        set_module_args(toCreate)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.assertTrue(results.exception.args[0]['changed'])
        self.assertEquals(results.exception.args[0]["group"]["name"], toCreate["name"], "name: " + results.exception.args[0]["group"]["name"] + " : " + toCreate["name"])
        self.assertTrue(isDictEquals(toCreate["attributes"],results.exception.args[0]["group"]["attributes"]), "attributes: " + str(results.exception.args[0]["group"]["attributes"]) + " : " + str(toCreate["attributes"]))
        self.assertTrue(isDictEquals(toCreate["clientRoles"],results.exception.args[0]["group"]["clientRoles"]), "clientRoles: " + str(results.exception.args[0]["group"]["clientRoles"]) + " : " + str(toCreate["clientRoles"]))
        self.assertTrue(isDictEquals(toCreate["realmRoles"],results.exception.args[0]["group"]["realmRoles"]), "realmRoles: " + str(results.exception.args[0]["group"]["realmRoles"]) + " : " + str(toCreate["realmRoles"]))

    def test_create_group_with_attributes_dict_and_attributes_list(self):
        toCreate = {
            "auth_username":"admin", 
            "auth_password":"admin",
            "realm":"master",
            "auth_keycloak_url":"http://localhost:18081/auth",
            "name":"test_create_group_with_attributes_dict_and_attributes_list",
            "attributes": {
                "attr1":["value1"],
                "attr2":["value2"]
            }, 
            "attributes_list": [
                {
                    "name":"attr3",
                    "value":["value3"]
                    },
                {
                    "name": "attr4",
                    "value":["value4"]
                    }
            ], 
            "realmRoles": [
                "uma_authorization"
            ], 
            "clientRoles": [{
                "clientid": "master-realm",
                "roles": [
                    "manage-users",
                    "view-identity-providers"
                    ]
                }
            ], 
            "state":"present",
            "force":False
        }
        attributes_dict = {
                "attr1":["value1"],
                "attr2":["value2"],
                "attr3":["value3"],
                "attr4":["value4"]
            }
        
        self.module = keycloak_group
        set_module_args(toCreate)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.assertTrue(results.exception.args[0]['changed'])
        self.assertEquals(results.exception.args[0]["group"]["name"], toCreate["name"], "name: " + results.exception.args[0]["group"]["name"] + " : " + toCreate["name"])
        self.assertTrue(isDictEquals(attributes_dict,results.exception.args[0]["group"]["attributes"]), "attributes: " + str(results.exception.args[0]["group"]["attributes"]) + " : " + str(attributes_dict))
        self.assertTrue(isDictEquals(toCreate["clientRoles"],results.exception.args[0]["group"]["clientRoles"]), "clientRoles: " + str(results.exception.args[0]["group"]["clientRoles"]) + " : " + str(toCreate["clientRoles"]))
        self.assertTrue(isDictEquals(toCreate["realmRoles"],results.exception.args[0]["group"]["realmRoles"]), "realmRoles: " + str(results.exception.args[0]["group"]["realmRoles"]) + " : " + str(toCreate["realmRoles"]))

    def test_create_group_with_user_storage_sync(self):
        toCreate = {
            "auth_username":"admin", 
            "auth_password":"admin",
            "realm":"master",
            "auth_keycloak_url":"http://localhost:18081/auth",
            "name":"test_create_group_with_user_storage_sync",
            "syncLdapMappers": True, 
            "state":"present",
            "force":False
        }
        self.module = keycloak_group
        set_module_args(toCreate)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.assertTrue(results.exception.args[0]['changed'])

    def test_group_not_changed(self):
        self.module = keycloak_group
        set_module_args(self.groupNotChanged)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.assertFalse(results.exception.args[0]['changed'])
        self.assertEquals(results.exception.args[0]["group"]["name"], self.groupNotChanged["name"], "name: " + results.exception.args[0]["group"]["name"] + " : " + self.groupNotChanged["name"])
        self.assertTrue(isDictEquals(self.groupNotChanged["attributes"],results.exception.args[0]["group"]["attributes"]), "attributes: " + str(results.exception.args[0]["group"]["attributes"]) + " : " + str(self.groupNotChanged["attributes"]))
        self.assertTrue(isDictEquals(self.groupNotChanged["clientRoles"],results.exception.args[0]["group"]["clientRoles"]), "clientRoles: " + str(results.exception.args[0]["group"]["clientRoles"]) + " : " + str(self.groupNotChanged["clientRoles"]))
        self.assertTrue(isDictEquals(self.groupNotChanged["realmRoles"],results.exception.args[0]["group"]["realmRoles"]), "realmRoles: " + str(results.exception.args[0]["group"]["realmRoles"]) + " : " + str(self.groupNotChanged["realmRoles"]))

    def test_group_modify_force(self):
        set_module_args(self.groupModifyForce)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        toDoNotChange = self.groupModifyForce.copy()
        toDoNotChange["force"] = True
        set_module_args(toDoNotChange)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.assertTrue(results.exception.args[0]['changed'])
        self.assertEquals(results.exception.args[0]["group"]["name"], toDoNotChange["name"], "name: " + results.exception.args[0]["group"]["name"] + " : " + toDoNotChange["name"])
        self.assertTrue(isDictEquals(toDoNotChange["attributes"],results.exception.args[0]["group"]["attributes"]), "attributes: " + str(results.exception.args[0]["group"]["attributes"]) + " : " + str(toDoNotChange["attributes"]))
        self.assertTrue(isDictEquals(toDoNotChange["clientRoles"], results.exception.args[0]["group"]["clientRoles"]), "clientRoles: " + str(results.exception.args[0]["group"]["clientRoles"]) + " : " + str(toDoNotChange["clientRoles"]))
        self.assertTrue(isDictEquals(toDoNotChange["realmRoles"],results.exception.args[0]["group"]["realmRoles"]), "realmRoles: " + str(results.exception.args[0]["group"]["realmRoles"]) + " : " + str(toDoNotChange["realmRoles"]))

    def test_modify_group(self):
        newToChange = self.modifyGroup.copy()
        newToChange["attributes"] = {
            "added":["thisAttributeBeenAdded"]
            }
        newToChange["realmRoles"] = [
                "uma_authorization",
                "offline_access"
            ]

        newToChange["clientRoles"] = [{
            "clientid": "master-realm",
            "roles": [
                "view-clients",
                "query-realms",
                "view-users"
                ]
            },{
            "clientid": "account",
            "roles": [
                "manage-account-links",
                "view-profile",
                "manage-account"
                ]
            }
        ]

        set_module_args(newToChange)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.assertTrue(results.exception.args[0]['changed'])
        self.assertEquals(results.exception.args[0]["group"]["name"], self.modifyGroup["name"], "name: " + results.exception.args[0]["group"]["name"] + " : " + self.modifyGroup["name"])
        self.assertFalse(isDictEquals(self.modifyGroup["attributes"],results.exception.args[0]["group"]["attributes"]), "attributes: " + str(results.exception.args[0]["group"]["attributes"]) + " : " + str(self.modifyGroup["attributes"]))
        self.assertTrue(isDictEquals(newToChange["attributes"], results.exception.args[0]["group"]["attributes"]), "attributes: " + str(results.exception.args[0]["group"]["attributes"]) + " : " + str(newToChange["attributes"]))
        self.assertTrue(isDictEquals(newToChange["clientRoles"], results.exception.args[0]["group"]["clientRoles"]), "clientRoles: " + str(results.exception.args[0]["group"]["clientRoles"]) + " : " + str(newToChange["clientRoles"]))
        self.assertTrue(isDictEquals(newToChange["realmRoles"], results.exception.args[0]["group"]["realmRoles"]), "realmRoles: " + str(results.exception.args[0]["group"]["realmRoles"]) + " : " + str(newToChange["realmRoles"]))

        
    def test_delete_group(self):
        toDelete = self.deleteGroup.copy()
        toDelete["state"] = "absent"
        set_module_args(toDelete)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.assertTrue(results.exception.args[0]['changed'])
        self.assertEqual(results.exception.args[0]['msg'], "Group {name} has been deleted".format(name=toDelete['name']), 'group has been deleted')
