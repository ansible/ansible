#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2018, Eike Frost <ei@kefro.st>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: keycloak_realm

short_description: Allows administration of Keycloak realms via Keycloak API

version_added: "2.6"

description:
    - This module allows the administration of Keycloak realms via the Keycloak REST API. It
      requires access to the REST API via OpenID Connect; the user connecting and the client being
      used must have the requisite access rights. In a default Keycloak installation, admin-cli
      and an admin user would work, as would a separate client definition with the scope tailored
      to your needs and a user having the expected roles.

    - The names of module options are snake_cased versions of the camelCase ones found in the
      Keycloak API and its documentation at U(http://www.keycloak.org/docs-api/3.4/rest-api/).
      Aliases are provided (if an option has an alias, it is the camelCase'd version used in the
      API).

options:
    state:
        description:
            - State of the realm once this module has run
            - On C(present), the realm will be created (or updated if it exists already).
            - On C(absent), the realm will be removed if it exists
        choices: ['present', 'absent']
        default: 'present'

    name:
        description:
            - Name of the realm to be acted on. Either this or I(realm) is required. If both are
              given, I(name) specifies the current name of the realm, while I(realm) specifies the
              new name thereof.
        required: True

    realm:
        description:
            - Name of the realm. Either this or I(name) is required.

    access_code_lifespan:
        description:
            - Client login timeout in seconds.
        aliases:
            - accessCodeLifespan

    access_code_lifespan_login:
        description:
            - Login timeout in seconds.
        aliases:
            - accessCodeLifespanLogin

    access_code_lifespan_user_action:
        description:
            - User-initiated action lifespan in seconds.
        aliases:
            - accessCodeLifespanUserAction

    access_token_lifespan:
        description:
            - Access token lifespan in seconds.
        aliases:
            - accessTokenLifespan

    access_token_lifespan_for_implicit_flow:
        description:
            - Access token lifespan for implicit flow in seconds.
        aliases:
            - accessTokenLifespanForImplicitFlow

    account_theme:
        description:
            - Theme for user account management pages. Keycloak ships with C(base) and C(keycloak).
        aliases:
            - accountTheme

    action_token_generated_by_admin_lifespan:
        description:
            - Default admin-initiated action lifespan in seconds.
        aliases:
            - actionTokenGeneratedByAdminLifespan

    action_token_generated_by_user_lifespan:
        description:
            - User-initiated action lifespan in seconds.
        aliases:
            - actionTokenGeneratedByUserLifespan

    admin_events_details_enabled:
        description:
            - Include representation for admin events or not.
        type: bool
        aliases:
            - adminEventsDetailsEnabled

    admin_events_enabled:
        description:
            - Save admin events or not.
        type: bool
        aliases:
            - adminEventsEnabled

    admin_theme:
        description:
            - Theme for admin console. Keycloak ships with C(base) and C(keycloak).
        aliases:
            - adminTheme

    attributes:
        description:
            - A freeform dict used by Keycloak and extensions to save further attributes for a realm.
              A non-exhaustive list of options is given below. Some of these are duplications of
              other API keys -- as noted via references below.
        suboptions:
            _browser_header.contentSecurityPolicy:
                description:
                    - See I(browser_security_headers).
            _browser_header.strictTransportSecurity:
                description:
                    - See I(browser_security_headers).
            _browser_header.xContentTypeOptions:
                description:
                    - See I(browser_security_headers).
            _browser_header.xFrameOptions:
                description:
                    - See I(browser_security_headers).
            _browser_header.xRobotsTag:
                description:
                    - See I(browser_security_headers).
            _browser_header.xXSSProtection:
                description:
                    - See I(browser_security_headers).
            actionTokenGeneratedByAdminLifespan:
                description:
                    - See I(action_token_generated_by_admin_lifespan)
            actionTokenGeneratedByUserLifespan:
                description:
                    - See I(action_token_generated_by_user_lifespan)
            actionTokenGeneratedByUserLifespan.idp-verify-account-via-email:
                description:
                    - Override user-initiated action lifespan for IdP account email verification, in seconds.
            actionTokenGeneratedByUserLifespan.reset-credentials:
                description:
                    - Override user-initiated action lifespan for resetting credentials/forget password, in seconds.
            actionTokenGeneratedByUserLifespan.verify-email:
                description:
                    - Override user-initiated action lifespan for email verification, in seconds.
            actionTokenGeneratedByUserLifespan.execute-actions:
                description:
                    - Override user-initiated action lifespan for execute actions, in seconds.
            bruteForceProtected:
                description:
                    - See I(brute_force_protected)
                type: bool
            displayName:
                description:
                    - See I(display_name)
            displayNameHtml:
                description:
                    - See I(display_name_html)
            failureFactor:
                description:
                    - See I(failure_factor)
            maxDeltaTimeSeconds:
                description:
                    - See I(max_delta_time_seconds)
            maxFailureWaitSeconds:
                description:
                    - See I(max_failure_wait_seconds)
            minimumQuickLoginWaitSeconds:
                description:
                    - See I(minimum_quick_login_wait_seconds)
            quickLoginCheckMilliSeconds:
                description:
                    - See I(quick_login_check_milli_seconds)
            waitIncrementSeconds:
                description:
                    - See I(wait_increment_seconds)

    browser_flow:
        description:
            - Authentication flow binding for browser flow.
        aliases:
            - browserFlow

    browser_security_headers:
        description:
            - Browser security headers for this realm.
        aliases:
            - browserSecurityHeaders
        suboptions:
            contentSecurityPolicy:
                description:
                    - Content-Security-Policy (CSP) browser header for this realm.
            xContentTypeOptions:
                description:
                    - X-Content-Type-Options browser header for this realm.
            xFrameOptions:
                description:
                    - X-Frame-Options browser header for this realm.
            xRobotsTag:
                description:
                    - X-Robots-Tag browser header for this realm (see U(https://developers.google.com/search/reference/robots_meta_tag))
                    - C(none) for no header.
            xXSSProtection:
                description:
                    - X-XSS-Protection browser header for this realm.
            strictTransportSecurity:
                description:
                    - Strict-Transport-Security (HSTS) browser header for this realm.

    brute_force_protected:
        description:
            - Is brute force detection enabled for this realm or not.
        aliases:
            - bruteForceProtected
        type: bool

    client_authentication_flow:
        description:
            - Authentication flow binding for client authentication flow.
        aliases:
            - clientAuthenticationFlow

    default_groups:
        description:
            - List of default groups for this realm. Usually with a prepended path, i.e. C(/test) for group C(test).
        aliases:
            - defaultGroups

    default_locale:
        description:
            - Default locale for this realm; usually a two-letter country code.
        aliases:
            - defaultLocale

    default_roles:
        description:
            - List of default roles for users of this realm
        aliases:
            - defaultRoles

    direct_grant_flow:
        description:
            - Authentication flow binding for direct grant flow.
        aliases:
            - directGrantFlow

    display_name:
        description:
            - Displayed name of this realm (regular text).
        aliases:
            - displayName

    display_name_html:
        description:
            - Displayed name of this realm (HTML)
        aliases:
            - displayNameHtml

    docker_authentication_flow:
        description:
            - Authentication flow binding for docker authentication flow.
        aliases:
            - dockerAuthenticationFlow

    duplicate_emails_allowed:
        description:
            - Specifies whether multiple users are allowed to have the same email address.
        type: bool
        aliases:
            - duplicateEmailsAllowed

    edit_username_allowed:
        description:
            - Specifies whether users of this realm are allowed to edit their own username.
        type: bool
        aliases:
            - editUsernameAllowed

    email_theme:
        description:
            - Theme for mails sent by Keycloak. Keycloak ships with C(base) and C(keycloak).
        aliases:
            - emailTheme

    enabled:
        description:
            - Specifies whether this realm is enabled.
        type: bool

    enabled_event_types:
        description:
            - List of event types to be saved. This list may be extensible through SPIs in Keycloak.
              Keycloak (3.4) ships the following listed types by default
            - C(SEND_RESET_PASSWORD)
            - C(REGISTER_NODE_ERROR)
            - C(REMOVE_TOTP)
            - C(REVOKE_GRANT)
            - C(UPDATE_TOTP)
            - C(LOGIN_ERROR)
            - C(CLIENT_LOGIN)
            - C(IDENTITY_PROVIDER_RETRIEVE_TOKEN_ERROR)
            - C(RESET_PASSWORD_ERROR)
            - C(IMPERSONATE_ERROR)
            - C(CODE_TO_TOKEN_ERROR)
            - C(CUSTOM_REQUIRED_ACTION)
            - C(RESTART_AUTHENTICATION)
            - C(CLIENT_INFO)
            - C(IMPERSONATE)
            - C(UPDATE_PROFILE_ERROR)
            - C(VALIDATE_ACCESS_TOKEN)
            - C(LOGIN)
            - C(UPDATE_PASSWORD_ERROR)
            - C(CLIENT_INITIATED_ACCOUNT_LINKING)
            - C(IDENTITY_PROVIDER_LOGIN)
            - C(TOKEN_EXCHANGE)
            - C(LOGOUT)
            - C(REGISTER)
            - C(CLIENT_INFO_ERROR)
            - C(CLIENT_REGISTER)
            - C(IDENTITY_PROVIDER_LINK_ACCOUNT)
            - C(INTROSPECT_TOKEN_ERROR)
            - C(REFRESH_TOKEN)
            - C(UPDATE_PASSWORD)
            - C(INTROSPECT_TOKEN)
            - C(CLIENT_DELETE)
            - C(FEDERATED_IDENTITY_LINK_ERROR)
            - C(IDENTITY_PROVIDER_FIRST_LOGIN)
            - C(CLIENT_DELETE_ERROR)
            - C(VERIFY_EMAIL)
            - C(CLIENT_LOGIN_ERROR)
            - C(RESTART_AUTHENTICATION_ERROR)
            - C(EXECUTE_ACTIONS)
            - C(REMOVE_FEDERATED_IDENTITY_ERROR)
            - C(TOKEN_EXCHANGE_ERROR)
            - C(UNREGISTER_NODE)
            - C(REGISTER_NODE)
            - C(SEND_IDENTITY_PROVIDER_LINK_ERROR)
            - C(INVALID_SIGNATURE)
            - C(USER_INFO_REQUEST_ERROR)
            - C(EXECUTE_ACTION_TOKEN_ERROR)
            - C(SEND_VERIFY_EMAIL)
            - C(IDENTITY_PROVIDER_RESPONSE)
            - C(EXECUTE_ACTIONS_ERROR)
            - C(REMOVE_FEDERATED_IDENTITY)
            - C(IDENTITY_PROVIDER_RETRIEVE_TOKEN)
            - C(IDENTITY_PROVIDER_POST_LOGIN)
            - C(IDENTITY_PROVIDER_LINK_ACCOUNT_ERROR)
            - C(UNREGISTER_NODE_ERROR)
            - C(VALIDATE_ACCESS_TOKEN_ERROR)
            - C(UPDATE_EMAIL)
            - C(REGISTER_ERROR)
            - C(REVOKE_GRANT_ERROR)
            - C(EXECUTE_ACTION_TOKEN)
            - C(LOGOUT_ERROR)
            - C(UPDATE_EMAIL_ERROR)
            - C(CLIENT_UPDATE_ERROR)
            - C(INVALID_SIGNATURE_ERROR)
            - C(UPDATE_PROFILE)
            - C(CLIENT_REGISTER_ERROR)
            - C(FEDERATED_IDENTITY_LINK)
            - C(USER_INFO_REQUEST)
            - C(IDENTITY_PROVIDER_RESPONSE_ERROR)
            - C(SEND_IDENTITY_PROVIDER_LINK)
            - C(SEND_VERIFY_EMAIL_ERROR)
            - C(IDENTITY_PROVIDER_LOGIN_ERROR)
            - C(RESET_PASSWORD)
            - C(CLIENT_INITIATED_ACCOUNT_LINKING_ERROR)
            - C(REMOVE_TOTP_ERROR)
            - C(VERIFY_EMAIL_ERROR)
            - C(SEND_RESET_PASSWORD_ERROR)
            - C(CLIENT_UPDATE)
            - C(REFRESH_TOKEN_ERROR)
            - C(CUSTOM_REQUIRED_ACTION_ERROR)
            - C(IDENTITY_PROVIDER_POST_LOGIN_ERROR)
            - C(UPDATE_TOTP_ERROR)
            - C(CODE_TO_TOKEN)
            - C(IDENTITY_PROVIDER_FIRST_LOGIN_ERROR)
        aliases:
            - enabledEventTypes

    events_enabled:
        description:
            - Specifies whether to save events or not.
        type: bool
        aliases:
            - eventsEnabled

    events_expiration:
        description:
            - If I(events_enabled) is True, this specifies the time after which events are expired
              automatically, in seconds.
        aliases:
            - eventsExpiration

    events_listeners:
        description:
            - List of listeners which receive events for this realm. Keycloak ships with C(jboss-logging) and C(email).
        aliases:
            - eventsListeners

    failure_factor:
        description:
            - For brute force detection, how many failures are allowed before a wait is triggered.
        aliases:
            - failureFactor

    id:
        description:
            - Internal id of this realm. When a realm is created, this should be the same as I(realm) (and indeed
              if you do not specify this parameter it will be set to I(realm) when creating a realm).

    internationalization_enabled:
        description:
            - Specifies whether internationalization features are enabled for this realm.
        type: bool
        aliases:
            - internationalizationEnabled

    login_theme:
        description:
            - Theme for the login screen. Keycloak ships with C(base) and C(keycloak).
        aliases:
            - loginTheme

    login_with_email_allowed:
        description:
            - Specifies whether users may log in with their email address instead of their username.
        type: bool
        aliases:
            - loginWithEmailAllowed

    max_delta_time_seconds:
        description:
            - For brute force detection, failure reset time in seconds.
        aliases:
            - maxDeltaTimeSeconds

    max_failure_wait_seconds:
        description:
            - For brute force detection, max wait time in seconds.
        aliases:
            - maxFailureWaitSeconds

    minimum_quick_login_wait_seconds:
        description:
            - For brute force detection, minimum wait after quick login in seconds.
        aliases:
            - minimumQuickLoginWaitSeconds

    not_before:
        description:
            - Unix timestamp specifying a cut-off for tokens and sessions; any tokens issued before
              this time are revoked.
        aliases:
            - notBefore

    offline_session_idle_timeout:
        description:
            - Time an offline session is allowed to idle before logout, in seconds.
        aliases:
            - offlineSessionIdleTimeout

    otp_policy_algorithm:
        description:
            - One time password hash algorithm
        choices:
            - HmacSHA1
            - HmacSHA256
            - HmacSHA512
        aliases:
            - otpPolicyAlgorithm

    otp_policy_digits:
        description:
            - One time password amount of digits
        choices:
            - 6
            - 8
        aliases:
            - otpPolicyDigits

    otp_policy_initial_counter:
        description:
            - Initial counter value for tokens when I(otp_policy_type) is set to C(hotp).
        aliases:
            - otpPolicyInitialCounter

    otp_policy_look_ahead_window:
        description:
            - One time password lookahead window (in case server and client are out of sync time-wise).
        aliases:
            - otpPolicyLookAheadWindow

    otp_policy_period:
        description:
            - One time password token period.
        aliases:
            - otpPolicyPeriod

    otp_policy_type:
        description:
            - Type of one time password algorithm
        choices:
            - totp
            - hotp
        aliases:
            - otpPolicyType

    password_policy:
        description:
            - String representing the password policy for this realm. An example would be
              C(lowerCase(1) and specialChars(1)). Built-in password policy checkers are
            - C(lowerCase(n))
            - C(specialChars(n))
            - C(forceExpiredPasswordChange(n))
            - C(hashIterations(n))
            - C(passwordHistory(n))
            - C(upperCase(n))
            - C(length(n))
            - C(digits(n))
            - C(notUsername(undefined))
            - C(hashAlgorithm(pbkdf2-sha256))
            - C(regexPattern(regex))
            - C(passwordBlacklist(filename))
        aliases:
            - passwordPolicy

    permanent_lockout:
        description:
            - For brute force detection, specifies whether a user will be logged out permanently when
              the detection triggers.
        type: bool
        aliases:
            - permanentLockout

    quick_login_check_milli_seconds:
        description:
            - For brute force detection, if failures happen concurrently within this time in
              milliseconds, lock out the user.
        aliases:
            - quickLoginCheckMilliSeconds

    refresh_token_max_reuse:
        description:
            - Maximum number of times a refresh token can be reused when I(revoke_refresh_token) is set to C(True).
        aliases:
            - refreshTokenMaxReuse

    registration_allowed:
        description:
            - Specifies whether user registration is allowed for this realm.
        type: bool
        aliases:
            - registrationAllowed

    registration_email_as_username:
        description:
            - Specifies whether the email address is used as username when user I(registration_allowed) is C(True).
        type: bool
        aliases:
            - registrationEmailAsUsername

    registration_flow:
        description:
            - Authentication flow binding for registration flow.
        aliases:
            - registrationFlow

    remember_me:
        description:
            - Specifies whether to show a Remember Me checkbox to the user on the login page to allow
              reusing a session across browser restarts.
        type: bool
        aliases:
            - rememberMe

    required_credentials:
        description:
            - A list of required credentials for this realm. By default it just containst C(password).
        aliases:
            - requiredCredentials

    reset_credentials_flow:
        description:
            - Authentication flow binding for reset credentials flow.
        aliases:
            - resetCredentialsFlow

    reset_password_allowed:
        description:
            - Specifies whether users can request to reset passwords.
        type: bool
        aliases:
            - resetPasswordAllowed

    revoke_refresh_token:
        description:
            - Specifies whether a refresh token is revoked upon use.
            - Also see I(refresh_token_max_reuse)
        type: bool
        aliases:
            - revokeRefreshToken

    smtp_server:
        description:
            - SMTP server configuration details for sending mails from Keycloak
        aliases:
            - smtpServer
        suboptions:
            auth:
                description:
                    - Specifies whether SMTP auth is used.
                type: bool
            envelopeFrom:
                description:
                    - Envelope from email address.
            from:
                description:
                    - From email address.
                required: True
            fromDisplayName:
                description:
                    - Displayed name for the from email address.
            host:
                description:
                    - Hostname of the SMTP server.
                required: True
            password:
                description:
                    - If I(auth) is set to C(True), password for the SMTP server.
            port:
                description:
                    - Port of the SMTP server.
            replyTo:
                description:
                    - Reply-to email address.
            replyToDisplayName:
                description:
                    - Reply-to email address displayed name.
            ssl:
                description:
                    - Specifies whether to use SSL when connecting to the SMTP server.
                type: bool
            starttls:
                description:
                    - Specifies whether to use STARTTLS when connecting to the SMTP server.
                type: bool
            user:
                description:
                    - If I(auth) is set to C(True), username for the SMTP server.

    ssl_required:
        description:
            - Specifies whether HTTPS is enforced and for what addresses.
            - C(none) doesn't enforce HTTPS.
            - C(all) enforces HTTPS on all requests.
            - C(external) enforces HTTPS on all requests that are not localhost or private IP space.
        choices:
            - none
            - all
            - external
        aliases:
            - sslRequired

    sso_session_idle_timeout:
        description:
            - Time an SSO session is allowed to idle before it expires, in seconds.
        aliases:
            - ssoSessionIdleTimeout

    sso_session_max_lifespan:
        description:
            - Maximum lifetime for an SSO session, in seconds.
        aliases:
            - ssoSessionMaxLifespan

    supported_locales:
        description:
            - List of supported locales for this realm. Keycloak (3.4) ships with C(ca), C(de),
              C(en), C(es), C(fr), C(it), C(ja), C(lt), C(nl), C(no), c(pt-BR), c(ru), c(sv), and
              c(zh-CN).
        aliases:
            - supportedLocales

    verify_email:
        description:
            - Specifies whether a user needs to verify their email the first time they log in.
        type: bool
        aliases:
            - verifyEmail

    wait_increment_seconds:
        description:
            - For brute force detection, wait increment in seconds per failure.
        aliases:
            - waitIncrementSeconds

notes:
    - In the API, a realm representation has further fields which are not covered in this module
      since they have their own API endpoints and (hopefully) their own Ansible modules. Sorted by
      ansible_module, they are
    - M(keycloak_scope) for I(clientScopeMappings) and I(scopeMappings)
    - M(keycloak_client) for I(client)
    - M(keycloak_clienttemplate) for I(clientTemplates)
    - M(keycloak_group) for I(groups)
    - No ansible module yet for I(authenticationFlows), I(authenticatorConfig), I(components),
      I(users), I(protocolMappers) (but see M(keycloak_client) and M(keycloak_clienttemplate)),
      I(identityProviders), I(roles), I(requiredActions), I(userFederationMappers),
      I(userFederationProviders), and I(federatedUsers)

extends_documentation_fragment:
    - keycloak

author:
    - Eike Frost (@eikef)
'''

EXAMPLES = '''
- name: Create a new Keycloak Realm named my-test-realm
  local_action:
    module: keycloak_realm
    auth_client_id: admin-cli
    auth_keycloak_url: https://auth.example.com/auth
    auth_realm: master
    auth_username: USERNAME
    auth_password: PASSWORD
    state: present
    realm: my-test-realm

- name: Rename a Keycloak realm from my-test-realm to my-new-test-realm
  local_action:
    module: keycloak_realm
    auth_client_id: admin-cli
    auth_keycloak_url: https://auth.example.com/auth
    auth_realm: master
    auth_username: USERNAME
    auth_password: PASSWORD
    name: my-test-realm
    realm: my-new-test-realm

- name: Delete a Keycloak realm
  local_action:
    module: keycloak_realm
    auth_client_id: admin-cli
    auth_keycloak_url: https://auth.example.com/auth
    auth_realm: master
    auth_username: USERNAME
    auth_password: PASSWORD
    state: absent
    realm: my-new-test-realm

- name: Create/update a Keycloak realm with some options set
  local_action:
    module: keycloak_realm
    auth_client_id: admin-cli
    auth_keycloak_url: https://auth.example.com/auth
    auth_realm: master
    auth_username: USERNAME
    auth_password: PASSWORD
    state: present
    realm: my-test-realm
    access_token_lifespan: 600
    admin_events_enabled: true
    admin_theme: keycloak
    browser_security_headers:
        contentSecurityPolicy: "frame-src 'self'; frame-ancestors 'self'; object-src 'none';"
        strictTransportSecurity: "max-age=31536000; includeSubDomains"
        xContentTypeOptions: "nosniff"
        xFrameOptions: "SAMEORIGIN"
        xRobotsTag: "none"
        xXSSProtection: "1; mode=block"
    password_policy: "lowerCase(1) and specialChars(1)"
    smtp_server:
        host: test.example.com
        from: test@example.com
        user: testuser
        password: testpassword
'''

RETURN = '''
msg:
  description: Message as to what action was taken
  returned: always
  type: string
  sample: Realm my-test-realm has been created.

proposed:
    description: realm representation of proposed changes to realm
    returned: always
    type: dict
    sample: {
         "realm": "my-test-realm"
    }

existing:
    description: realm representation of existing realm (sample is truncated)
    returned: always
    type: dict
    sample: {}

end_state:
    description: realm representation of realm after module execution (sample is truncated)
    returned: always
    type: dict
    sample: {
        "accessCodeLifespan": 60,
        "accessCodeLifespanLogin": 1800,
        "accessCodeLifespanUserAction": 300,
        "accessTokenLifespan": 600,
        "accessTokenLifespanForImplicitFlow": 900,
        "actionTokenGeneratedByAdminLifespan": 43200,
        "actionTokenGeneratedByUserLifespan": 300,
        "adminEventsDetailsEnabled": false,
        "adminEventsEnabled": true,
        "adminTheme": "keycloak"
    }
'''

from ansible.module_utils.keycloak import KeycloakAPI, camel, keycloak_argument_spec
from ansible.module_utils.basic import AnsibleModule


def main():
    """
    Module execution

    :return:
    """
    argument_spec = keycloak_argument_spec()

    meta_args = dict(
        state=dict(default='present', choices=['present', 'absent']),
        name=dict(type='str'),
        realm=dict(type='str'),
        access_code_lifespan=dict(type='int', aliases=['accessCodeLifespan']),
        access_code_lifespan_login=dict(type='int', aliases=['accessCodeLifespanLogin']),
        access_code_lifespan_user_action=dict(type='int', aliases=['accessCodeLifespanUserAction']),
        access_token_lifespan=dict(type='int', aliases=['accessTokenLifespan']),
        access_token_lifespan_for_implicit_flow=dict(type='int', aliases=['accessTokenLifespanForImplicitFlow']),
        account_theme=dict(type='str', aliases=['accountTheme']),
        action_token_generated_by_admin_lifespan=dict(type='int', aliases=['actionTokenGeneratedByAdminLifespan']),
        action_token_generated_by_user_lifespan=dict(type='int', aliases=['actionTokenGeneratedByUserLifespan']),
        admin_events_details_enabled=dict(type='bool', aliases=['adminEventsDetailsEnabled']),
        admin_events_enabled=dict(type='bool', aliases=['adminEventsEnabled']),
        admin_theme=dict(type='str', aliases=['adminTheme']),
        attributes=dict(type='dict'),
        browser_flow=dict(type='str', aliases=['browserFlow']),
        browser_security_headers=dict(type='dict', aliases=['browserSecurityHeaders'], options=dict(
            contentSecurityPolicy=dict(type='str'),
            xContentTypeOptions=dict(type='str'),
            xFrameOptions=dict(type='str'),
            xRobotsTag=dict(type='str'),
            xXSSProtection=dict(type='str'),
            strictTransportSecurity=dict(type='str'),
        )),
        brute_force_protected=dict(type='bool', aliases=['bruteForceProtected']),
        client_authentication_flow=dict(type='str', aliases=['clientAuthenticationFlow']),
        default_groups=dict(type='list', aliases=['defaultGroups']),
        default_locale=dict(type='str', aliases=['defaultLocale']),
        default_roles=dict(type='list', elements='str', aliases=['defaultRoles']),
        direct_grant_flow=dict(type='str', aliases=['directGrantFlow']),
        display_name=dict(type='str', aliases=['displayName']),
        display_name_html=dict(type='str', aliases=['displayNameHtml']),
        docker_authentication_flow=dict(type='str', aliases=['dockerAuthenticationFlow']),
        duplicate_emails_allowed=dict(type='bool', aliases=['duplicateEmailsAllowed']),
        edit_username_allowed=dict(type='bool', aliases=['editUsernameAllowed']),
        email_theme=dict(type='str', aliases=['emailTheme']),
        enabled=dict(type='bool'),
        enabled_event_types=dict(type='list', elements='str', aliases=['enabledEventTypes']),
        events_enabled=dict(type='bool', aliases=['eventsEnabled']),
        events_expiration=dict(type='int', aliases=['eventsExpiration']),
        events_listeners=dict(type='list', elements='str', aliases=['eventsListeners']),
        failure_factor=dict(type='int', aliases=['failureFactor']),
        id=dict(type='str'),
        internationalization_enabled=dict(type='bool', aliases=['internationalizationEnabled']),
        login_theme=dict(type='str', aliases=['loginTheme']),
        login_with_email_allowed=dict(type='bool', aliases=['loginWithEmailAllowed']),
        max_delta_time_seconds=dict(type='int', aliases=['maxDeltaTimeSeconds']),
        max_failure_wait_seconds=dict(type='int', aliases=['maxFailureWaitSeconds']),
        minimum_quick_login_wait_seconds=dict(type='int', aliases=['minimumQuickLoginWaitSeconds']),
        not_before=dict(type='int', aliases=['notBefore']),
        offline_session_idle_timeout=dict(type='int', aliases=['offlineSessionIdleTimeout']),
        otp_policy_algorithm=dict(type='str', aliases=['otpPolicyAlgorithm'], choices=['HmacSHA1', 'HmacSHA256', 'HmacSHA512']),
        otp_policy_digits=dict(type='int', aliases=['otpPolicyDigits'], choices=[6, 8]),
        otp_policy_initial_counter=dict(type='int', aliases=['otpPolicyInitialCounter']),
        otp_policy_look_ahead_window=dict(type='int', aliases=['otpPolicyLookAheadWindow']),
        otp_policy_period=dict(type='int', aliases=['otpPolicyPeriod']),
        otp_policy_type=dict(type='str', aliases=['otpPolicyType'], choices=['totp', 'hotp']),
        password_policy=dict(type='str', aliases=['passwordPolicy']),
        permanent_lockout=dict(type='bool', aliases=['permanentLockout']),
        quick_login_check_milli_seconds=dict(type='int', aliases=['quickLoginCheckMilliSeconds']),
        refresh_token_max_reuse=dict(type='int', aliases=['refreshTokenMaxReuse']),
        registration_allowed=dict(type='bool', aliases=['registrationAllowed']),
        registration_email_as_username=dict(type='bool', aliases=['registrationEmailAsUsername']),
        registration_flow=dict(type='str', aliases=['registrationFlow']),
        remember_me=dict(type='bool', aliases=['rememberMe']),
        required_credentials=dict(type='list', elements='str', aliases=['requiredCredentials']),
        reset_credentials_flow=dict(type='str', aliases=['resetCredentialsFlow']),
        reset_password_allowed=dict(type='bool', aliases=['resetPasswordAllowed']),
        revoke_refresh_token=dict(type='bool', aliases=['revokeRefreshToken']),
        smtp_server=dict(type='dict', aliases=['smtpServer'], options={
            'auth': dict(type='bool'),
            'envelopeFrom': dict(type='str'),
            'from': dict(type='str', required=True),
            'fromDisplayName': dict(type='str'),
            'host': dict(type='str', required=True),
            'password': dict(type='str', no_log=True),
            'port': dict(type='int'),
            'replyTo': dict(type='str'),
            'replyToDisplayName': dict(type='str'),
            'ssl': dict(type='bool'),
            'starttls': dict(type='bool'),
            'user': dict(type='str'),
        }),
        ssl_required=dict(type='str', aliases=['sslRequired'], choices=['none', 'all', 'external']),
        sso_session_idle_timeout=dict(type='int', aliases=['ssoSessionIdleTimeout']),
        sso_session_max_lifespan=dict(type='int', aliases=['ssoSessionMaxLifespan']),
        supported_locales=dict(type='list', elements='str', aliases=['supportedLocales']),
        verify_email=dict(type='bool', aliases=['verifyEmail']),
        wait_increment_seconds=dict(type='int', aliases=['waitIncrementSeconds']),
    )
    argument_spec.update(meta_args)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           required_one_of=([['name', 'realm']]))

    result = dict(changed=False, msg='', diff={}, proposed={}, existing={}, end_state={})

    # Obtain access token, initialize API
    kc = KeycloakAPI(module)

    state = module.params.get('state')
    realm = module.params.get('name') if module.params.get('name') is not None else module.params.get('realm')

    # convert module parameters to realm representation parameters (if they belong in there)
    realm_params = [x for x in module.params
                    if x not in list(keycloak_argument_spec().keys()) + ['state', 'name'] and
                    module.params.get(x) is not None]

    # If the I(realm) is not set, assume I(name) as the default.
    if module.params.get('realm') is None:
        realm_params['realm'] = realm

    before_realm = kc.get_realm_by_name(realm)
    before_realm = {} if before_realm is None else before_realm

    # Build a proposed changeset from parameters given to this module
    changeset = dict()

    for realm_param in realm_params:
        # lists in the Keycloak API are sorted
        new_param_value = module.params.get(realm_param)
        if isinstance(new_param_value, list):
            try:
                new_param_value = sorted(new_param_value)
            except TypeError:
                pass
        changeset[camel(realm_param)] = new_param_value

    # Whether creating or updating a realm, take the before-state and merge the changeset into it
    updated_realm = before_realm.copy()
    updated_realm.update(changeset)

    result['proposed'] = changeset
    result['existing'] = before_realm

    # If the realm does not exist yet, before_realm is still empty
    if before_realm == dict():
        if state == 'absent':
            # do nothing and exit
            if module._diff:
                result['diff'] = dict(before='', after='')
            result['msg'] = 'Realm does not exist, doing nothing.'
            module.exit_json(**result)

        # create new realm
        result['changed'] = True

        # when creating a realm, the id should be the same as the realm name -- otherwise bugs magically appear
        if 'id' not in updated_realm:
            updated_realm['id'] = updated_realm['realm']

        if module.check_mode:
            if module._diff:
                result['diff'] = dict(before='', after=updated_realm)

            module.exit_json(**result)

        kc.create_realm(updated_realm)
        after_realm = kc.get_realm_by_name(realm)

        if module._diff:
            result['diff'] = dict(before='', after=after_realm)

        result['end_state'] = after_realm

        result['msg'] = 'Realm %s has been created.' % realm
        module.exit_json(**result)
    else:
        if state == 'present':
            # update existing realm
            result['changed'] = True
            if module.check_mode:
                # We can only compare the current realm with the proposed updates we have
                if module._diff:
                    result['diff'] = dict(before=before_realm,
                                          after=updated_realm)
                result['changed'] = (before_realm != updated_realm)

                module.exit_json(**result)
            kc.update_realm(updated_realm, realm=realm)

            if realm != updated_realm['realm']:
                after_realm = kc.get_realm_by_name(updated_realm['realm'])
            else:
                after_realm = kc.get_realm_by_name(realm)

            if before_realm == after_realm:
                result['changed'] = False
            if module._diff:
                result['diff'] = dict(before=before_realm,
                                      after=after_realm)
            result['end_state'] = after_realm

            result['msg'] = 'Realm %s has been updated.' % realm
            module.exit_json(**result)
        else:
            # Delete existing realm
            result['changed'] = True
            if module._diff:
                result['diff']['before'] = before_realm
                result['diff']['after'] = ''

            if module.check_mode:
                module.exit_json(**result)

            kc.delete_realm(realm=realm)
            result['proposed'] = dict()
            result['end_state'] = dict()
            result['msg'] = 'Realm %s has been deleted.' % realm
            module.exit_json(**result)
    module.exit_json(**result)

if __name__ == '__main__':
    main()
