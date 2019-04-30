from ansible.modules.identity.keycloak import keycloak_user, keycloak_group, keycloak_role
from ansible.module_utils.keycloak_utils import isDictEquals
from units.modules.utils import AnsibleExitJson, AnsibleFailJson, ModuleTestCase, set_module_args

class KeycloakUserTestCase(ModuleTestCase):
    testGroups = [
        {
            "auth_username":"admin", 
            "auth_password":"admin",
            "realm":"master",
            "auth_keycloak_url":"http://localhost:18081/auth",
            "name":"testUserGroup1",
            "state":"present",
            "force":False
            },
        {
            "auth_username":"admin", 
            "auth_password":"admin",
            "realm":"master",
            "auth_keycloak_url":"http://localhost:18081/auth",
            "name":"testUserGroup2",
            "state":"present",
            "force":False
            }
        ]
    compareExcludes = ["auth_keycloak_url", "auth_username", "auth_password", "realm", "state", "force", "credentials","_ansible_keep_remote_files","_ansible_remote_tmp"]
    testRoles = [
        {
            "auth_username":"admin", 
            "auth_password":"admin",
            "realm":"master",
            "auth_keycloak_url":"http://localhost:18081/auth",
            "name":"testUserRole1",
            "description":"Test1",
            "state":"present",
            "force":False
        },
                {
            "auth_username":"admin", 
            "auth_password":"admin",
            "realm":"master",
            "auth_keycloak_url":"http://localhost:18081/auth",
            "name":"testUserRole2",
            "description":"Test2",
            "state":"present",
            "force":False
        }]

    testUsers = [
        {
            "auth_keycloak_url": "http://localhost:18081/auth",
            "auth_username": "admin",
            "auth_password": "admin",
            "realm": "master",
            "username": "createuser",
            "firstName": "Create",
            "lastName": "User",
            "email": "user1@user.ca",
            "enabled": True,
            "emailVerified": False,
            "credentials": [{"temporary": 'false',"type": "password","value": "password"}], 
            "clientRoles": [{"clientId": "master-realm","roles": ["manage-clients"]}],
            "realmRoles": ["testUserRole1","testUserRole2"],
            "attributes": {"attr1": ["value1"],"attr2": ["value2"]},
            "groups": ["testUserGroup1","testUserGroup2"],
            "state":"absent",
            "force":"no"
        },
        {
            "auth_keycloak_url": "http://localhost:18081/auth",
            "auth_username": "admin",
            "auth_password": "admin",
            "realm": "master",
            "username": "usernotchanged",
            "firstName": "ThisUser",
            "lastName": "DoNotChange",
            "email": "user2@user.ca",
            "enabled": True,
            "emailVerified": False,
            "credentials": [{"temporary": 'false',"type": "password","value": "password"}],
            "clientRoles": [{"clientId": "master-realm","roles": ["manage-clients"]}],
            "realmRoles": ["testUserRole1","testUserRole2"],
            "attributes": {"attr1": ["value1"],"attr2": ["value2"]},
            "groups": ["testUserGroup1","testUserGroup2"],
            "state": "present",
            "force": False
        },
        {
            "auth_keycloak_url": "http://localhost:18081/auth",
            "auth_username": "admin",
            "auth_password": "admin",
            "realm": "master",
            "username": "usermodifyforce",
            "firstName": "ThisUser",
            "lastName": "ModifiedForce",
            "email": "user3@user.ca",
            "enabled": True,
            "emailVerified": False,
            "credentials": [{"temporary": 'false',"type": "password","value": "password"}],
            "clientRoles": [{"clientId": "master-realm","roles": ["manage-clients"]}],
            "realmRoles": ["testUserRole1","testUserRole2"],
            "attributes": {"attr1": ["value1"],"attr2": ["value2"]},
            "groups": ["testUserGroup1","testUserGroup2"],
            "state":"present",
            "force": False
        },
        {
            "auth_keycloak_url": "http://localhost:18081/auth",
            "auth_username": "admin",
            "auth_password": "admin",
            "realm": "master",
            "username": "modifyuser",
            "firstName": "Modify",
            "lastName": "User",
            "email": "user4@user.ca",
            "enabled": True,
            "emailVerified": False,
            "credentials": [{"temporary": 'false',"type": "password","value": "password"}],
            "clientRoles": [{"clientId": "master-realm","roles": ["manage-clients"]}],
            "realmRoles": ["testUserRole1"],
            "attributes": {"attr1": ["value1"],"attr2": ["value2"]},
            "groups": ["testUserGroup1"],
            "state":"present",
            "force": False
        },
        {
            "auth_keycloak_url": "http://localhost:18081/auth",
            "auth_username": "admin",
            "auth_password": "admin",
            "realm": "master",
            "username": "delete",
            "firstName": "Delete",
            "lastName": "User",
            "email": "user5@user.ca",
            "enabled": True,
            "emailVerified": False,
            "credentials": [{"temporary": 'false',"type": "password","value": "password"}],
            "clientRoles": [{"clientId": "master-realm","roles": ["manage-clients"]}],
            "realmRoles": ["uma_authorization","offline_access"],
            "attributes": {"attr1": ["value1"],"attr2": ["value2"]},
            "groups": ["testUserGroup1","testUserGroup2"],
            "state":"present",
            "force": False
        }
    ]
    
    def setUp(self):
        super(KeycloakUserTestCase, self).setUp()
        self.module = keycloak_group
        for theGroup in self.testGroups:
            theGroup["state"] = "present"
            set_module_args(theGroup)
            with self.assertRaises(AnsibleExitJson) as results:
                self.module.main()
        self.module = keycloak_role
        for theRole in self.testRoles:
            theRole["state"] = "present"
            set_module_args(theRole)
            with self.assertRaises(AnsibleExitJson) as results:
                self.module.main()
        self.module = keycloak_user
        for theUser in self.testUsers:
            set_module_args(theUser)
            with self.assertRaises(AnsibleExitJson) as results:
                self.module.main()
    def tearDown(self):
        self.module = keycloak_group
        for theGroup in self.testGroups:
            theGroup["state"] = "absent"
            set_module_args(theGroup)
            with self.assertRaises(AnsibleExitJson) as results:
                self.module.main()
        self.module = keycloak_role
        for theRole in self.testRoles:
            theRole["state"] = "absent"
            set_module_args(theRole)
            with self.assertRaises(AnsibleExitJson) as results:
                self.module.main()
        super(KeycloakUserTestCase, self).tearDown()           
 
    def test_create_user(self):
        toCreate = self.testUsers[0].copy()
        toCreate["state"] = "present"
        set_module_args(toCreate)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.assertTrue(results.exception.args[0]['changed'])
        self.assertTrue(isDictEquals(toCreate, results.exception.args[0]["user"], self.compareExcludes), "user: " + str(toCreate) + " : " + str(results.exception.args[0]["user"]))

    def test_user_not_changed(self):
        toDoNotChange = self.testUsers[1].copy()
        set_module_args(toDoNotChange)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.assertFalse(results.exception.args[0]['changed'])
        self.assertTrue(isDictEquals(toDoNotChange, results.exception.args[0]["user"], self.compareExcludes), "user: " + str(toDoNotChange) + " : " + str(results.exception.args[0]["user"]))

    def test_user_modify_force(self):
        toDoNotChange = self.testUsers[2].copy()
        toDoNotChange["force"] = True
        set_module_args(toDoNotChange)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.assertTrue(results.exception.args[0]['changed'])
        self.assertTrue(isDictEquals(toDoNotChange, results.exception.args[0]["user"], self.compareExcludes), "user: " + str(toDoNotChange) + " : " + str(results.exception.args[0]["user"]))

    def test_modify_user(self):
        toChange = self.testUsers[3].copy()
        toChange["lastName"] = "Modified"
        toChange["clientRoles"] = [{"clientId": "master-realm","roles": ["manage-clients","query-groups"]}]
        toChange["realmRoles"] = ["testUserRole1","testUserRole2"]
        set_module_args(toChange)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.assertTrue(results.exception.args[0]['changed'])
        self.assertTrue(isDictEquals(toChange, results.exception.args[0]["user"], self.compareExcludes), "user: " + str(toChange) + " : " + str(results.exception.args[0]["user"]))
        
    def test_delete_user(self):
        toDelete = self.testUsers[4].copy()
        toDelete["state"] = "absent"
        set_module_args(toDelete)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.assertTrue(results.exception.args[0]['changed'])
        self.assertRegexpMatches(results.exception.args[0]['msg'], 'deleted', 'User not deleted')

