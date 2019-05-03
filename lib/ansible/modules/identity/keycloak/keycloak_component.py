#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, INSPQ <philippe.gauthier@inspq.qc.ca>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: keycloak_component

short_description: Configure LDAP user storage component in Keycloak.

version_added: "2.9"

description:
    - This module creates, removes or update Keycloak component.
    - It can be use to create a LDAP and AD user federation to a realm in the Keycloak server
options:
    realm:
        description:
            - The name of the realm in which is the component.
        required: true
    id:
        description:
            - ID of the component when it have already been created and it is known.
        required: false
    name:
        description:
            - Name of the Component
        required: true
    providerId:
        description:
            - ProviderId of the component
        choices: ["ldap","allowed-client-templates","trusted-hosts","allowed-protocol-mappers","max-clients","scope","consent-required","rsa-generated"]
        required: true
    providerType:
        description:
            - Provider type of component
        choices:
            - org.keycloak.storage.UserStorageProvider
            - org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy
            - org.keycloak.keys.KeyProvider
            - authenticatorConfig
            - requiredActions
        required: true
    parentId:
        description:
            - Parent ID of the component. Use the realm name for top level component.
        required: true
    config:
        description:
            - Configuration of the component to create, update or delete.
        required: false
        suboptions:
            vendor:
                description:
                    - LDAP vendor/product
                    - Value must be a list of one string item.
                type: list
                choices:
                    - ad
                    - tivoli
                    - edirectory
                    - rhds
                    - other
            usernameLDAPAttribute:
                description:
                    - Name of LDAP attribute, which is mapped as Keycloak username.
                    - It is usually uid, for Active Directory it is sAMAccountName.
                    - Value must be a list of one string item.
                type: list
            editMode:
                description:
                    - The Edit Mode configuration option defines the edit policy you have with your LDAP store.
                    - Value must be a list of one string item.
                type: list
                choices:
                    - READ_ONLY
                    - WRITABLE
                    - UNSYNCED
            rdnLDAPAttribute:
                description:
                    - Name of LDAP attribute, which is used as RDN (top attribute) of typical user DN.
                    - Usually it's the same as Username LDAP attribute. For active Directory, it's usually cn.
                    - Value must be a list of one string item.
                type: list
            uuidLDAPAttribute:
                description:
                    - Name of LDAP attribute, which is used as unique object identifier.
                    - For many LDAP vendor it's entryUUI.
                    - For Active Directory it's objectGUID.
                    - For Red Hat Directory Server it's nsuniqueid
                    - Value must be a list of one string item.
                type: list
            userObjectClasses:
                description:
                    - All values of LDAP objectClasses attribute for users in LDAP.
                type: list
            connectionUrl:
                description:
                    - LDAP connection URL in the format [ldap|dlaps]://server.name:port
                    - Value must be a list of one string item.
                type: list
            usersDn:
                description:
                    - Full DN of LDAP tree where users are stored
                    - Value must be a list of one string item.
                type: list
            authType:
                description:
                    - LDAP authentication type.
                    - Value must be a list of one string item.
                type: list
                choices:
                    - simple
                    - none
            bindDn:
                description:
                    - DN of LDAP admin used to authenticate to LDAP server
                    - Value must be a list of one string item.
                type: list
            bindCredential:
                description:
                    - Password for the LDAP admin
                    - Value must be a list of one string item.
                type: list
            changedSyncPeriod:
                description:
                    - Period for synchronization of changed or newly created LDAP users.
                    - To disable changed user synchronization, use -1
                    - Value must be a list of one string item.
                type: list
            fullSyncPeriod:
                description:
                    - Period for full synchronization of LDAP users.
                    - To disable full user synchronization, use -1
                    - Value must be a list of one string item.
                type: list
            pagination:
                description:
                    - Does the LDAP support pagination.
                    - Default value is false if this option is not defined
                    - Value must be a list of one string item.
                type: list
                choices:
                    - true
                    - false
            connectionPooling:
                description:
                    - Does the Keycloak should use connection pooling for accessing the LDAP server?
                    - Default value is true
                    - Value must be a list of one string item.
                type: list
                choices:
                    - true
                    - false
            cachePolicy:
                description:
                    - Cache policy for this user storage provider.
                    - Default value is ["DEFAULT"] if this option is not defined.
                    - Value must be a list of one string item.
                type: list
                choices:
                    - DEFAULT
                    - EVICT_DAILY
                    - EVICT_WEEKLY
                    - MAX_LIFESPAN
                    - NO_CACHE
            useKerberosForPasswordAuthentication:
                description:
                    - User Kerberos module to authenticate users to Kerberos server instead
                    - of authenticate against LDAP server with Active Directory Service API.
                    - Default value is false if this option is not defined
                    - Value must be a list of one string item.
                type: list
                choices:
                    - true
                    - false
            allowKerberosAuthentication:
                description:
                    - Enable or disable HTTP authentication of users with SPNEGO/Kerberos tokens.
                    - Default value is false if option is not defined
                    - Value must be a list of one string item.
                type: list
                choices:
                    - true
                    - false
            importEnabled:
                description:
                    - If true, LDAP users are imported into the Keycloak database and synchronized.
                    - Default value is true if not defined.
                    - Value must be a list of one string item.
                type: list
                choices:
                    - true
                    - false
            syncRegistrations:
                description:
                    - If true, user created in the Keycloak server will be synchronized to LDAP.
                    - Default value is true if not defined.
                    - Value must be a list of one string item.
                type: list
                choices:
                    - true
                    - false
            searchScope:
                description:
                    - For one level, users will be searched in only the usersDn. If subtree,
                    - users will be searched recursively in the usersDn and his children.
                    - For one level, use 1 as value, for subtree, use 2.
                    - Default value is 2 if the option is not defined.
                    - Value must be a list of one string item.
                type: list
                choices:
                    - 1
                    - 2
            priority:
                description:
                    - Order of priority for user search when multiple user storages are defined.
                    - Lowest first
                    - Default value is 0 when this option is not defined.
                    - Value must be a list of one string item.
                type: list
            validatePasswordPolicy:
                description:
                    - If true, users password will be checked against Keycloak password policy.
                    - Default value is true if not defined.
                    - Value must be a list of one string item.
                type: list
                choices:
                    - true
                    - false
            batchSizeForSync:
                description:
                    - Count of LDAP users to be imported in a single transaction.
                    - Value must be a list of one string item.
                type: list
    subComponents:
        description:
            - List of sub components to create inside the component.
            - It can be use to configure group-ldap-mapper for a User Federation.
        type: dict
        suboptions:
            org.keycloak.storage.ldap.mappers.LDAPStorageMapper:
                description:
                    - LDAP storage mappers
                type: list
                suboptions:
                    name:
                        description:
                            - Name of the sub component
                        type: str
                    providerId:
                        description:
                            - Provider ID of the subcomponent's type
                        type: str
                        choices:
                            - user-attribute-ldap-mapper
                            - group-ldap-mapper
                    config:
                        description:
                            - Configuration for the sub component. Structure depends on the component's type.
                        type: dict
                        suboptions:
                            ldap.attribute:
                                description:
                                    - This is for user-attribute-ldap-mapper type.
                                    - LDAP attrribute to map from.
                                    - Value must be a list of one string item.
                                type: list
                            is.mandatory.in.ldap:
                                description:
                                    - This is for user-attribute-ldap-mapper type.
                                    - If true, the attribute must be in the LDAP entry for the user.
                                    - Default value is true if the option is not defined.
                                    - Value must be a list of one string item.
                                type: list
                                choices:
                                    - true
                                    - false
                            read.only:
                                description:
                                    - This is for user-attribute-ldap-mapper type.
                                    - If true, the attribute is read only.
                                    - Default value is false if the option is not defined.
                                    - Value must be a list of one string item.
                                type: list
                                choices:
                                    - true
                                    - false
                            user.model.attribute:
                                description:
                                    - This is for user-attribute-ldap-mapper type.
                                    - Attribute of keycloak user model to map to..
                                    - Value must be a list of one string item.
                                type: list
                            always.read.value.from.ldap:
                                description:
                                    - This is for user-attribute-ldap-mapper type.
                                    - If true, the attribute from LDAP will always override Keycloak user model attribute.
                                    - Default value is true if the option is not defined.
                                    - Value must be a list of one string item.
                                type: list
                                choices:
                                    - true
                                    - false
                            mode:
                                description:
                                    - This option is for group-ldap-mapper.
                                    - LDAP/Keycloak groups synchronization mode.
                                    - Value must be a list of one string item.
                                type: list
                                choices:
                                    - LDAP_ONLY
                                    - IMPORT
                                    - READ_ONLY
                            membership.attribute.type:
                                description:
                                    - This option is for group-ldap-mapper.
                                    - Membership attribute type, DN or UID.
                                    - Value must be a list of one string item.
                                type: list
                                choices:
                                    - DN
                                    - UID
                            user.roles.retrieve.strategy:
                                description:
                                    - This option is for group-ldap-mapper.
                                    - Specify how to retrieve group members.
                                    - Value must be a list of one string item.
                                type: list
                                choices:
                                    - LOAD_GROUPS_BY_MEMBER_ATTRIBUTE
                                    - GET_GROUPS_FROM_USER_MEMBEROF_ATTRIBUTE
                                    - LOAD_GROUPS_BY_MEMBER_ATTRIBUTE_RECURSIVELY
                            group.name.ldap.attribute:
                                description:
                                    - This option is for group-ldap-mapper.
                                    - Name of LDAP attribute which is used as the group name.
                                    - Value must be a list of one string item.
                                type: list
                            membership.ldap.attribute:
                                description:
                                    - This option is for group-ldap-mapper.
                                    - Name of LDAP attribute which is used for membership mapping.
                                    - Value must be a list of one string item.
                                type: list
                            membership.user.ldap.attribute:
                                description:
                                    - This option is for group-ldap-mapper.
                                    - Used only when membership attribute type is UID.
                                    - Name of LDAP attribute which is used for membership mapping.
                                    - Value must be a list of one string item.
                                type: list
                            memberof.ldap.attribute:
                                description:
                                    - This option is for group-ldap-mapper.
                                    - Used only when user.roles.retrieve.strategy is GET_GROUPS_FROM_USER_MEMBEROF_ATTRIBUTE.
                                    - Name of LDAP attribute on LDAP user which is used for membership mapping.
                                    - Value must be a list of one string item.
                                type: list
                            preserve.group.inheritance:
                                description:
                                    - This option is for group-ldap-mapper.
                                    - If true, the LDAP group inheritance will be replicate on the Keycloak server.
                                    - Default value is true if the option is not defined.
                                    - Value must be a list of one string item.
                                type: list
                                choices:
                                    - true
                                    - false
                            groups.dn:
                                description:
                                    - This option is for group-ldap-mapper.
                                    - LDAP DN where groups are.
                                    - Value must be a list of one string item.
                                type: list
                            group.object.classes:
                                description:
                                    - This option is for group-ldap-mapper.
                                    - Object class or classes for LDAP group objects.
                                    - Value must be a list of one string item.
                                type: list
                            drop.non.existing.groups.during.sync:
                                description:
                                    - This option is for group-ldap-mapper.
                                    - If true, the group on Keycloak server that does not exists in LDAP will be dropped.
                                    - Default value is false if the option is not defined.
                                    - Value must be a list of one string item.
                                type: list
                                choices:
                                    - true
                                    - false
    syncUserStorage:
        description:
            - Type of user storage synchronization must be triggerd for
            - org.keycloak.storage.UserStorageProvider component.
            - If the parameter is absent, no sync will be triggered
        required: false
        choices: ["triggerFullSync", "triggerChangedUsersSync"]
    syncLdapMappers:
        description:
            - Type of LDAP mapper synchronization must be triggerd for
            - org.keycloak.storage.ldap.mappers.LDAPStorageMapper/group-ldap-mapper sub components.
            - If the parameter is absent, no sync will be triggered
        required: false
        choices: ["fedToKeycloak", "keycloakToFed"]
    state:
        description:
            - Control if the component must exists or not
        choices: [ "present", "absent" ]
        default: present
        required: false
    force:
        description:
            - If true, allows to remove component and recreate it.
        type: bool
        default: false
extends_documentation_fragment:
    - keycloak

author:
    - Philippe Gauthier (@elfelip)
'''

EXAMPLES = '''
    - name: Create a LDAP User Storage provider. A full sync of users and a fedToKeycloak sync for group mappers will be triggered.
      keycloak_component:
        auth_keycloak_url: http://localhost:8080/auth
        auth_sername: admin
        auth_password: password
        realm: master
        name: ActiveDirectory
        providerId: ldap
        providerType: org.keycloak.storage.UserStorageProvider
        config:
          vendor:
          - "ad"
          usernameLDAPAttribute:
          - "sAMAccountName"
          rdnLDAPAttribute:
          - "cn"
          uuidLDAPAttribute:
          - "objectGUID"
          userObjectClasses:
          - "person"
          - "organizationalPerson"
          - "user"
          connectionUrl:
          - "ldap://ldap.server.com:389"
          usersDn:
          - "OU=USERS,DC=server,DC=com"
          authType:
          - "simple"
          bindDn:
          - "CN=keycloak,OU=USERS,DC=server,DC=com"
          bindCredential:
          - "UnTresLongMotDePasseQuePersonneNeConnait"
          changedSyncPeriod:
          - "86400"
          fullSyncPeriod:
          - "604800"
        subComponents:
          org.keycloak.storage.ldap.mappers.LDAPStorageMapper:
          - name: "groupMapper"
            providerId: "group-ldap-mapper"
            config:
              mode:
                - "READ_ONLY"
              membership.attribute.type:
                - "DN"
              user.roles.retrieve.strategy:
                - "LOAD_GROUPS_BY_MEMBER_ATTRIBUTE"
              group.name.ldap.attribute:
                - "cn"
              membership.ldap.attribute:
                - "member"
              preserve.group.inheritance:
                - "true"
              membership.user.ldap.attribute:
                - "uid"
              group.object.classes:
                - "groupOfNames"
              groups.dn:
                - "cn=groups,OU=SEC,DC=SANTEPUBLIQUE,DC=RTSS,DC=QC,DC=CA"
              drop.non.existing.groups.during.sync:
                - "false"
        syncUserStorage: triggerFullSync
        syncLdapMappers: fedToKeycloak
        state: present

    - name: Re-create LDAP User Storage provider.
      keycloak_component:
        auth_keycloak_url: http://localhost:8080/auth
        auth_sername: admin
        auth_password: password
        realm: master
        name: ActiveDirectory
        providerId: ldap
        providerType: org.keycloak.storage.UserStorageProvider
        config:
          vendor:
          - "ad"
          usernameLDAPAttribute:
          - "sAMAccountName"
          rdnLDAPAttribute:
          - "cn"
          uuidLDAPAttribute:
          - "objectGUID"
          userObjectClasses:
          - "person"
          - "organizationalPerson"
          - "user"
          connectionUrl:
          - "ldap://ldap.server.com:389"
          usersDn:
          - "OU=USERS,DC=server,DC=com"
          authType:
          - "simple"
          bindDn:
          - "CN=keycloak,OU=USERS,DC=server,DC=com"
          bindCredential:
          - "UnTresLongMotDePasseQuePersonneNeConnait"
          changedSyncPeriod:
          - "86400"
          fullSyncPeriod:
          - "604800"
        subComponents:
          org.keycloak.storage.ldap.mappers.LDAPStorageMapper:
          - name: "groupMapper"
            providerId: "group-ldap-mapper"
            config:
              mode:
                - "READ_ONLY"
              membership.attribute.type:
                - "DN"
              user.roles.retrieve.strategy:
                - "LOAD_GROUPS_BY_MEMBER_ATTRIBUTE"
              group.name.ldap.attribute:
                - "cn"
              membership.ldap.attribute:
                - "member"
              preserve.group.inheritance:
                - "true"
              membership.user.ldap.attribute:
                - "uid"
              group.object.classes:
                - "groupOfNames"
              groups.dn:
                - "cn=groups,OU=SEC,DC=SANTEPUBLIQUE,DC=RTSS,DC=QC,DC=CA"
              drop.non.existing.groups.during.sync:
                - "false"
        state: present
        force: yes

    - name: Remove User Storage Provider.
      keycloak_component:
        auth_keycloak_url: http://localhost:8080/auth
        auth_sername: admin
        auth_password: password
        realm: master
        name: ActiveDirectory
        providerId: ldap
        providerType: org.keycloak.storage.UserStorageProvider
        state: absent
'''

RETURN = '''
component:
  description: JSON representation for the component.
  returned: on success
  type: dict
subComponents:
  description: JSON representation of the sub components list.
  returned: on success
  type: list
msg:
  description: Error message if it is the case
  returned: on error
  type: str
changed:
  description: Return True if the operation changed the component on the keycloak server, false otherwise.
  returned: always
  type: bool
'''

from ansible.module_utils.keycloak import KeycloakAPI, keycloak_argument_spec, isDictEquals, remove_arguments_with_value_none
# import module snippets
from ansible.module_utils.basic import AnsibleModule


def main():
    argument_spec = keycloak_argument_spec()
    config_spec = dict(
        vendor=dict(type='list', choices=['ad', 'tivoli', 'edirectory', 'rhds', 'other']),
        usernameLDAPAttribute=dict(type='list'),
        editMode=dict(type='list', choices=['READ_ONLY', 'WRITABLE', 'UNSYNCED']),
        rdnLDAPAttribute=dict(type='list'),
        uuidLDAPAttribute=dict(type='list'),
        userObjectClasses=dict(type='list'),
        connectionUrl=dict(type='list'),
        usersDn=dict(type='list'),
        authType=dict(type='list', choices=['simple', 'none']),
        bindDn=dict(type='list'),
        bindCredential=dict(type='list'),
        changedSyncPeriod=dict(type='list'),
        fullSyncPeriod=dict(type='list'),
        pagination=dict(type='list', choices=['true', 'false']),
        connectionPooling=dict(type='list', choices=['true', 'false']),
        cachePolicy=dict(type='list', choices=['DEFAULT', 'EVICT_DAILY', 'EVICT_WEEKLY', 'MAX_LIFESPAN', 'NO_CACHE']),
        useKerberosForPasswordAuthentication=dict(type='list', choices=['true', 'false']),
        allowKerberosAuthentication=dict(type='list', choices=['true', 'false']),
        importEnabled=dict(type='list', choices=['true', 'false']),
        syncRegistrations=dict(type='list', choices=['true', 'false']),
        searchScope=dict(type='list', choices=['1', '2']),
        priority=dict(type='list'),
        validatePasswordPolicy=dict(type='list', choices=['true', 'false']),
        batchSizeForSync=dict(type='list')
    )
    ldapstoragemapper_spec = {
        'ldap.attribute': {'type': 'list'},
        'is.mandatory.in.ldap': {'type': 'list', 'choices': ['true', 'false']},
        'read.only': {'type': 'list', 'choices': ['true', 'false']},
        'user.model.attribute': {'type': 'list'},
        'always.read.value.from.ldap': {'type': 'list', 'choices': ['true', 'false']},
        'mode': {'type': 'list', 'choices': ['LDAP_ONLY', 'READ_ONLY', 'IMPORT']},
        'membership.attribute.type': {'type': 'list', 'choices': ['DN', 'UID']},
        'user.roles.retrieve.strategy': {'type': 'list', 'choices': [
            'LOAD_GROUPS_BY_MEMBER_ATTRIBUTE',
            'GET_GROUPS_FROM_USER_MEMBEROF_ATTRIBUTE',
            'LOAD_GROUPS_BY_MEMBER_ATTRIBUTE_RECURSIVELY'
        ]},
        'group.name.ldap.attribute': {'type': 'list'},
        'membership.ldap.attribute': {'type': 'list'},
        'membership.user.ldap.attribute': {'type': 'list'},
        'memberof.ldap.attribute': {'type': 'list'},
        'preserve.group.inheritance': {'type': 'list', 'choices': ['true', 'false']},
        'groups.dn': {'type': 'list'},
        'group.object.classes': {'type': 'list'},
        'drop.non.existing.groups.during.sync': {'type': 'list', 'choices': ['true', 'false']}
    }
    subcomponents_config_spec = dict(
        name=dict(type='str'),
        providerId=dict(type='str'),
        config=dict(type='dict', options=ldapstoragemapper_spec)
    )
    subcomponents_spec = {
        'org.keycloak.storage.ldap.mappers.LDAPStorageMapper': {'type': 'list', 'options': subcomponents_config_spec}
    }
    meta_args = dict(
        id=dict(type='str'),
        name=dict(type='str', required=True),
        realm=dict(type='str', required=True),
        providerId=dict(
            choices=[
                "ldap",
                "allowed-client-templates",
                "trusted-hosts",
                "allowed-protocol-mappers",
                "max-clients",
                "scope",
                "consent-required",
                "rsa-generated"],
            required=True),
        providerType=dict(
            choices=[
                "org.keycloak.storage.UserStorageProvider",
                "org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy",
                "org.keycloak.keys.KeyProvider",
                "authenticatorConfig",
                "requiredActions"],
            required=True),
        parentId=dict(type='str'),
        config=dict(type='dict', options=config_spec),
        subComponents=dict(type='dict', options=subcomponents_spec),
        syncUserStorage=dict(choices=["triggerFullSync", "triggerChangedUsersSync"]),
        syncLdapMappers=dict(choices=["fedToKeycloak", "keycloakToFed"]),
        state=dict(choices=["absent", "present"], default='present'),
        force=dict(type='bool', default=False),
    )
    argument_spec.update(meta_args)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    result = dict(changed=False, msg='', diff={}, component='', subComponents='')

    # Obtain access token, initialize API
    kc = KeycloakAPI(module)

    realm = module.params.get('realm')
    state = module.params.get('state')
    force = module.params.get('force')

    # Create a representation from module parameters
    newComponent = {}
    newComponent["id"] = module.params.get('id')
    newComponent["name"] = module.params.get('name')
    newComponent["providerId"] = module.params.get('providerId')
    newComponent["providerType"] = module.params.get('providerType')
    newComponent["parentId"] = module.params.get('parentId') if module.params.get('parentId') is not None else realm
    newComponent["config"] = module.params.get("config")
    remove_arguments_with_value_none(newComponent["config"])
    newSubComponents = module.params.get("subComponents")
    remove_arguments_with_value_none(newSubComponents)
    syncUserStorage = module.params.get('syncUserStorage') if module.params.get('syncUserStorage') is not None else "no"
    syncLdapMappers = module.params.get('syncLdapMappers') if module.params.get('syncLdapMappers') is not None else "no"

    changed = False

    component = kc.get_component_by_name_provider_and_parent(
        name=newComponent["name"],
        provider_type=newComponent["providerType"],
        provider_id=newComponent["providerId"],
        parent_id=newComponent["parentId"],
        realm=realm)

    if component == {}:  # If component does not exist
        if (state == 'present'):  # If desired stat is present
            # Create the component and it's sub-components
            component = kc.create_component(
                newComponent=newComponent,
                newSubComponents=newSubComponents,
                syncLdapMappers=syncLdapMappers,
                realm=realm)
            subComponents = kc.get_all_sub_components(parent_id=component["id"], realm=realm)
            if syncUserStorage != 'no':  # If user synchronization is needed
                kc.sync_user_storage(component_id=component['id'], action=syncUserStorage, realm=realm)
                result['component'] = component
            changed = True
            result['component'] = component
            result['subComponents'] = subComponents
            result['changed'] = changed
        elif state == 'absent':  # Id desired state is absent, return absent and do nothing.
            result['msg'] = newComponent["name"] + ' absent'
            result['component'] = newComponent
            result['changed'] = changed

    else:  # If component already exist
        if (state == 'present'):  # if desired state is present
            if force:  # If force option is true
                # Delete the existing component
                kc.delete_component(component_id=component["id"], realm=realm)
                changed = True
                # Re-create the component.
                component = kc.create_component(newComponent=newComponent, newSubComponents=newSubComponents, syncLdapMappers=syncLdapMappers, realm=realm)
            else:  # If force option is false
                # Copy existing id in new component
                newComponent['id'] = component['id']
                newComponent['parentId'] = component['parentId']
                excludes = []
                # Compare the new component with the existing
                excludes.append("bindCredential")
                if not isDictEquals(newComponent, component, excludes):  # If the component need to be changed
                    # Update the component
                    component = kc.update_component(newComponent=newComponent, realm=realm)
                    changed = True
                # Update sub components
                if kc.update_sub_components(component=newComponent, newSubComponents=newSubComponents, syncLdapMappers=syncLdapMappers, realm=realm):
                    changed = True
            if syncUserStorage != 'no':  # If user synchronization is needed
                kc.sync_user_storage(component_id=component['id'], action=syncUserStorage, realm=realm)

            result['component'] = component
            result['subComponents'] = kc.get_all_sub_components(parent_id=component["id"], realm=realm)
            result['changed'] = changed

        elif state == 'absent':  # if desired state is absent
            # Delete the component
            kc.delete_component(component_id=component['id'], realm=realm)
            changed = True
            result['msg'] = newComponent["name"] + ' deleted'
            result['changed'] = changed

    module.exit_json(**result)


if __name__ == '__main__':
    main()
