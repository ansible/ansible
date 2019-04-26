import collections
import os

from ansible.modules.identity.keycloak import keycloak_realm
from units.modules.utils import AnsibleExitJson, AnsibleFailJson, ModuleTestCase, set_module_args
from ansible.module_utils.keycloak_utils import isDictEquals

class KeycloakRealmTestCase(ModuleTestCase):
    toCreateRealm = {
        'realm': 'test_create_realm',
        'url': 'http://localhost:18081/auth',
        'username': 'admin',
        'password': 'admin',
        'displayName': 'Test create realm',
        'displayNameHtml': 'Test Create Realm',
        'accessCodeLifespan': 60,
        'accessCodeLifespanLogin': 1800,
        'accessCodeLifespanUserAction': 300,
        'notBefore':  0,
        'revokeRefreshToken':  False,
        'accessTokenLifespan':  300,
        'accessTokenLifespanForImplicitFlow':  900,
        'ssoSessionIdleTimeout':  1800,
        'ssoSessionMaxLifespan':  36000,
        'offlineSessionIdleTimeout':  2592000,
        'enabled':  True,
        'sslRequired':  "external",
        'registrationAllowed':  False,
        'registrationEmailAsUsername':  False,
        'rememberMe':  False,
        'verifyEmail':  False,
        'loginWithEmailAllowed':  True,
        'duplicateEmailsAllowed':  False,
        'resetPasswordAllowed':  False,
        'editUsernameAllowed':  False,
        'bruteForceProtected':  False,
        'permanentLockout':  False,
        'maxFailureWaitSeconds':  900,
        'minimumQuickLoginWaitSeconds':  60,
        'waitIncrementSeconds':  60,
        'quickLoginCheckMilliSeconds':  1000,
        'maxDeltaTimeSeconds':  43200,
        'failureFactor':  30,
        'defaultRoles':  [ "offline_access", "uma_authorization" ],
        'requiredCredentials':  [ "password" ],
        'passwordPolicy':  "hashIterations(20000)",
        'otpPolicyType':  "totp",
        'otpPolicyAlgorithm':  "HmacSHA1",
        'otpPolicyInitialCounter':  0,
        'otpPolicyDigits':  6,
        'otpPolicyLookAheadWindow':  1,
        'otpPolicyPeriod':  30,
        'smtpServer':  {
            "replyToDisplayName": "root",
            "starttls": "",
            "auth": "",
            "port": "25",
            "host": "localhost",
            "replyTo": "root@localhost",
            "fromDisplayName": "local",
            "envelopeFrom": "root@localhost",
            "ssl": "",
            "smtpServer.from": "root@localhost"
        },
        'eventsConfig':  {
            "eventsEnabled": True,
            "eventsListeners": [ "jboss-logging" ],
            "enabledEventTypes": ["SEND_RESET_PASSWORD", "UPDATE_TOTP", "REMOVE_TOTP", "REVOKE_GRANT", "LOGIN_ERROR", "CLIENT_LOGIN", "RESET_PASSWORD_ERROR", "IMPERSONATE_ERROR", "CODE_TO_TOKEN_ERROR", "CUSTOM_REQUIRED_ACTION", "UPDATE_PROFILE_ERROR", "IMPERSONATE", "LOGIN", "UPDATE_PASSWORD_ERROR", "REGISTER", "LOGOUT", "CLIENT_REGISTER", "UPDATE_PASSWORD", "FEDERATED_IDENTITY_LINK_ERROR", "CLIENT_DELETE", "IDENTITY_PROVIDER_FIRST_LOGIN", "VERIFY_EMAIL", "CLIENT_DELETE_ERROR", "CLIENT_LOGIN_ERROR", "REMOVE_FEDERATED_IDENTITY_ERROR", "EXECUTE_ACTIONS", "SEND_IDENTITY_PROVIDER_LINK_ERROR", "SEND_VERIFY_EMAIL", "EXECUTE_ACTIONS_ERROR", "REMOVE_FEDERATED_IDENTITY", "IDENTITY_PROVIDER_POST_LOGIN", "UPDATE_EMAIL", "REGISTER_ERROR", "REVOKE_GRANT_ERROR", "LOGOUT_ERROR", "UPDATE_EMAIL_ERROR", "CLIENT_UPDATE_ERROR", "UPDATE_PROFILE", "FEDERATED_IDENTITY_LINK", "CLIENT_REGISTER_ERROR", "SEND_VERIFY_EMAIL_ERROR", "SEND_IDENTITY_PROVIDER_LINK", "RESET_PASSWORD", "REMOVE_TOTP_ERROR", "VERIFY_EMAIL_ERROR", "SEND_RESET_PASSWORD_ERROR", "CLIENT_UPDATE", "IDENTITY_PROVIDER_POST_LOGIN_ERROR", "CUSTOM_REQUIRED_ACTION_ERROR", "UPDATE_TOTP_ERROR", "CODE_TO_TOKEN", "IDENTITY_PROVIDER_FIRST_LOGIN_ERROR"],
            "adminEventsEnabled": True,
            "adminEventsDetailsEnabled": True},
        'internationalizationEnabled':  False,
        'supportedLocales':  [  ],
        'browserFlow':  "browser",
        'registrationFlow':  "registration",
        'directGrantFlow':  "direct grant",
        'resetCredentialsFlow':  "reset credentials",
        'clientAuthenticationFlow':  "clients",
        'state': 'absent',
        'force': False,
    }        

    toModifyRealm = {
        'realm': 'test_modify_realm',
        'url': 'http://localhost:18081/auth',
        'username': 'admin',
        'password': 'admin',
        'displayName': 'Test modify realm',
        'displayNameHtml': 'Test Modify Realm',
        'accessCodeLifespan': 60,
        'accessCodeLifespanLogin': 1800,
        'accessCodeLifespanUserAction': 300,
        'notBefore':  0,
        'revokeRefreshToken':  False,
        'accessTokenLifespan':  300,
        'accessTokenLifespanForImplicitFlow':  900,
        'ssoSessionIdleTimeout':  1800,
        'ssoSessionMaxLifespan':  36000,
        'offlineSessionIdleTimeout':  2592000,
        'enabled':  True,
        'sslRequired':  "external",
        'registrationAllowed':  False,
        'registrationEmailAsUsername':  False,
        'rememberMe':  False,
        'verifyEmail':  False,
        'loginWithEmailAllowed':  True,
        'duplicateEmailsAllowed':  False,
        'resetPasswordAllowed':  False,
        'editUsernameAllowed':  False,
        'bruteForceProtected':  False,
        'permanentLockout':  False,
        'maxFailureWaitSeconds':  900,
        'minimumQuickLoginWaitSeconds':  60,
        'waitIncrementSeconds':  60,
        'quickLoginCheckMilliSeconds':  1000,
        'maxDeltaTimeSeconds':  43200,
        'failureFactor':  30,
        'defaultRoles':  [ "offline_access", "uma_authorization" ],
        'requiredCredentials':  [ "password" ],
        'passwordPolicy':  "hashIterations(20000)",
        'otpPolicyType':  "totp",
        'otpPolicyAlgorithm':  "HmacSHA1",
        'otpPolicyInitialCounter':  0,
        'otpPolicyDigits':  6,
        'otpPolicyLookAheadWindow':  1,
        'otpPolicyPeriod':  30,
        'smtpServer':  {
            "replyToDisplayName": "root",
            "starttls": "",
            "auth": "",
            "port": "25",
            "host": "localhost",
            "replyTo": "root@localhost",
            "fromDisplayName": "local",
            "envelopeFrom": "root@localhost",
            "ssl": "",
            "smtpServer.from": "root@localhost"
        },
        'internationalizationEnabled':  False,
        'supportedLocales':  [  ],
        'browserFlow':  "browser",
        'registrationFlow':  "registration",
        'directGrantFlow':  "direct grant",
        'resetCredentialsFlow':  "reset credentials",
        'clientAuthenticationFlow':  "clients",
        'state': 'present',
        'force': False,
    }        
    toDeleteRealm = {
        'realm': 'test_delete_realm',
        'url': 'http://localhost:18081/auth',
        'username': 'admin',
        'password': 'admin',
        'displayName': 'Test delete realm',
        'displayNameHtml': 'Test Delete Realm',
        'state': 'present',
        'force': False
    }        

    toDoNotChangeRealm = {
        'realm': 'test_not_changed_realm',
        'url': 'http://localhost:18081/auth',
        'username': 'admin',
        'password': 'admin',
        'displayName': 'Test not changed realm',
        'displayNameHtml': 'Test Not Changed Realm',
        'accessCodeLifespan': 60,
        'accessCodeLifespanLogin': 1800,
        'accessCodeLifespanUserAction': 300,
        'notBefore':  0,
        'revokeRefreshToken':  False,
        'accessTokenLifespan':  300,
        'accessTokenLifespanForImplicitFlow':  900,
        'ssoSessionIdleTimeout':  1800,
        'ssoSessionMaxLifespan':  36000,
        'offlineSessionIdleTimeout':  2592000,
        'enabled':  True,
        'sslRequired':  "external",
        'registrationAllowed':  False,
        'registrationEmailAsUsername':  False,
        'rememberMe':  False,
        'verifyEmail':  False,
        'loginWithEmailAllowed':  True,
        'duplicateEmailsAllowed':  False,
        'resetPasswordAllowed':  False,
        'editUsernameAllowed':  False,
        'bruteForceProtected':  False,
        'permanentLockout':  False,
        'maxFailureWaitSeconds':  900,
        'minimumQuickLoginWaitSeconds':  60,
        'waitIncrementSeconds':  60,
        'quickLoginCheckMilliSeconds':  1000,
        'maxDeltaTimeSeconds':  43200,
        'failureFactor':  30,
        'defaultRoles':  [ "offline_access", "uma_authorization" ],
        'requiredCredentials':  [ "password" ],
        'passwordPolicy':  "hashIterations(20000)",
        'otpPolicyType':  "totp",
        'otpPolicyAlgorithm':  "HmacSHA1",
        'otpPolicyInitialCounter':  0,
        'otpPolicyDigits':  6,
        'otpPolicyLookAheadWindow':  1,
        'otpPolicyPeriod':  30,
        'smtpServer':  {
            "replyToDisplayName": "root",
            "starttls": "",
            "auth": "",
            "port": "25",
            "host": "localhost",
            "replyTo": "root@localhost",
            "fromDisplayName": "local",
            "envelopeFrom": "root@localhost",
            "ssl": "",
            "smtpServer.from": "root@localhost"
        },
        'eventsConfig':  {
            "eventsEnabled": True,
            "eventsListeners": [ "jboss-logging" ],
            "enabledEventTypes": ["SEND_RESET_PASSWORD", "UPDATE_TOTP", "REMOVE_TOTP", "REVOKE_GRANT", "LOGIN_ERROR", "CLIENT_LOGIN", "RESET_PASSWORD_ERROR", "IMPERSONATE_ERROR", "CODE_TO_TOKEN_ERROR", "CUSTOM_REQUIRED_ACTION", "UPDATE_PROFILE_ERROR", "IMPERSONATE", "LOGIN", "UPDATE_PASSWORD_ERROR", "REGISTER", "LOGOUT", "CLIENT_REGISTER", "UPDATE_PASSWORD", "FEDERATED_IDENTITY_LINK_ERROR", "CLIENT_DELETE", "IDENTITY_PROVIDER_FIRST_LOGIN", "VERIFY_EMAIL", "CLIENT_DELETE_ERROR", "CLIENT_LOGIN_ERROR", "REMOVE_FEDERATED_IDENTITY_ERROR", "EXECUTE_ACTIONS", "SEND_IDENTITY_PROVIDER_LINK_ERROR", "SEND_VERIFY_EMAIL", "EXECUTE_ACTIONS_ERROR", "REMOVE_FEDERATED_IDENTITY", "IDENTITY_PROVIDER_POST_LOGIN", "UPDATE_EMAIL", "REGISTER_ERROR", "REVOKE_GRANT_ERROR", "LOGOUT_ERROR", "UPDATE_EMAIL_ERROR", "CLIENT_UPDATE_ERROR", "UPDATE_PROFILE", "FEDERATED_IDENTITY_LINK", "CLIENT_REGISTER_ERROR", "SEND_VERIFY_EMAIL_ERROR", "SEND_IDENTITY_PROVIDER_LINK", "RESET_PASSWORD", "REMOVE_TOTP_ERROR", "VERIFY_EMAIL_ERROR", "SEND_RESET_PASSWORD_ERROR", "CLIENT_UPDATE", "IDENTITY_PROVIDER_POST_LOGIN_ERROR", "CUSTOM_REQUIRED_ACTION_ERROR", "UPDATE_TOTP_ERROR", "CODE_TO_TOKEN", "IDENTITY_PROVIDER_FIRST_LOGIN_ERROR"],
            "adminEventsEnabled": True,
            "adminEventsDetailsEnabled": True},
        'internationalizationEnabled':  False,
        'supportedLocales':  [  ],
        'browserFlow':  "browser",
        'registrationFlow':  "registration",
        'directGrantFlow':  "direct grant",
        'resetCredentialsFlow':  "reset credentials",
        'clientAuthenticationFlow':  "clients",
        'state': 'present',
        'force': False,
    }        
    toDoNotChangeRealmForce = {
        'realm': 'test_do_not_change_realm_force',
        'url': 'http://localhost:18081/auth',
        'username': 'admin',
        'password': 'admin',
        'displayName': 'Test do not realm rorce',
        'displayNameHtml': 'Test Do Not Change Realm Force',
        'state': 'present',
        'force': False
    }        
    realmExcudes = ["url","username","password","state","force","eventsConfig","_ansible_keep_remote_files","_ansible_remote_tmp"]
    def setUp(self):
        super(KeycloakRealmTestCase, self).setUp()
        self.module = keycloak_realm
        set_module_args(self.toCreateRealm)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        set_module_args(self.toModifyRealm)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        set_module_args(self.toDeleteRealm)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        set_module_args(self.toDoNotChangeRealm)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        set_module_args(self.toDoNotChangeRealmForce)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
 
    def tearDown(self):
        super(KeycloakRealmTestCase, self).tearDown()
 
    def test_create_realm(self):
        toCreate = self.toCreateRealm.copy()
        toCreate["state"] = "present"
        set_module_args(toCreate)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.assertTrue(results.exception.args[0]['changed'])
        self.assertTrue(isDictEquals(toCreate, results.exception.args[0]['realm'], self.realmExcudes), 'Realm created does not comply to specifications.')
        self.assertTrue(results.exception.args[0]["eventsConfig"]["eventsEnabled"], "eventsEnabled: " + str(results.exception.args[0]["eventsConfig"]["eventsEnabled"]))
        self.assertTrue(results.exception.args[0]["eventsConfig"]["adminEventsEnabled"], "adminEventsEnabled: " + str(results.exception.args[0]["eventsConfig"]["adminEventsEnabled"]))
        self.assertTrue(results.exception.args[0]["eventsConfig"]["adminEventsDetailsEnabled"], "adminEventsDetailsEnabled: " + str(results.exception.args[0]["eventsConfig"]["adminEventsDetailsEnabled"]))
        self.assertTrue(isDictEquals(toCreate['eventsConfig'],results.exception.args[0]['eventsConfig']), "Events configuration has not been modified")
        
    def test_modify_realm(self):
        toModify = self.toModifyRealm.copy()
        toModify["displayNameHtml"] = "New name"
        toModify['eventsConfig'] = {
            "eventsEnabled": True,
            "eventsListeners": [ "jboss-logging" ],
            "enabledEventTypes": ["SEND_RESET_PASSWORD", "UPDATE_TOTP", "REMOVE_TOTP", "REVOKE_GRANT", "LOGIN_ERROR", "CLIENT_LOGIN", "RESET_PASSWORD_ERROR", "IMPERSONATE_ERROR", "CODE_TO_TOKEN_ERROR", "CUSTOM_REQUIRED_ACTION", "UPDATE_PROFILE_ERROR", "IMPERSONATE", "LOGIN", "UPDATE_PASSWORD_ERROR", "REGISTER", "LOGOUT", "CLIENT_REGISTER", "UPDATE_PASSWORD", "FEDERATED_IDENTITY_LINK_ERROR", "CLIENT_DELETE", "IDENTITY_PROVIDER_FIRST_LOGIN", "VERIFY_EMAIL", "CLIENT_DELETE_ERROR", "CLIENT_LOGIN_ERROR", "REMOVE_FEDERATED_IDENTITY_ERROR", "EXECUTE_ACTIONS", "SEND_IDENTITY_PROVIDER_LINK_ERROR", "SEND_VERIFY_EMAIL", "EXECUTE_ACTIONS_ERROR", "REMOVE_FEDERATED_IDENTITY", "IDENTITY_PROVIDER_POST_LOGIN", "UPDATE_EMAIL", "REGISTER_ERROR", "REVOKE_GRANT_ERROR", "LOGOUT_ERROR", "UPDATE_EMAIL_ERROR", "CLIENT_UPDATE_ERROR", "UPDATE_PROFILE", "FEDERATED_IDENTITY_LINK", "CLIENT_REGISTER_ERROR", "SEND_VERIFY_EMAIL_ERROR", "SEND_IDENTITY_PROVIDER_LINK", "RESET_PASSWORD", "REMOVE_TOTP_ERROR", "VERIFY_EMAIL_ERROR", "SEND_RESET_PASSWORD_ERROR", "CLIENT_UPDATE", "IDENTITY_PROVIDER_POST_LOGIN_ERROR", "CUSTOM_REQUIRED_ACTION_ERROR", "UPDATE_TOTP_ERROR", "CODE_TO_TOKEN", "IDENTITY_PROVIDER_FIRST_LOGIN_ERROR"],
            "adminEventsEnabled": True,
            "adminEventsDetailsEnabled": True}
        set_module_args(toModify)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.assertTrue(results.exception.args[0]['changed'])
        self.assertTrue(isDictEquals(toModify, results.exception.args[0]['realm'], self.realmExcudes), 'Realm modified does not comply to specifications.')
        #self.assertEqual(results.exception.args[0]['realm']['displayNameHtml'], toModify["namehtml"], "namehtml: " + results.exception.args[0]['realm']['displayNameHtml'])
        self.assertTrue(isDictEquals(toModify['eventsConfig'],results.exception.args[0]['eventsConfig']), "Events configuration has not been modified")

    def test_do_not_change_realm(self):
        set_module_args(self.toDoNotChangeRealm)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.assertFalse(results.exception.args[0]['changed'], "Realm is not supposed to be changed")
        self.assertTrue(isDictEquals(self.toDoNotChangeRealm, results.exception.args[0]['realm'], self.realmExcudes), 'Realm not changed does not comply to specifications.')

    def test_do_not_change_realm_force(self):
        toDoNotChange = self.toDoNotChangeRealmForce.copy()
        toDoNotChange["force"] = True
        set_module_args(toDoNotChange)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.assertTrue(results.exception.args[0]['changed'], "Realm is supposed to be changed")
        self.assertTrue(isDictEquals(toDoNotChange, results.exception.args[0]['realm'], self.realmExcudes), 'Realm not changed force does not comply to specifications.')
        
    def test_delete_realm(self):
        toDelete = self.toDeleteRealm.copy()
        toDelete["state"] = "absent"
        set_module_args(toDelete)
        with self.assertRaises(AnsibleExitJson) as results:
            self.module.main()
        self.assertTrue(results.exception.args[0]['changed'])
        self.assertRegexpMatches(results.exception.args[0]['msg'], 'deleted', 'Realm not deleted')
