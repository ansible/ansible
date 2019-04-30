# Copyright (c) 2017, Eike Frost <ei@kefro.st>
#
# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json
import urllib

from ansible.module_utils.urls import open_url
from ansible.module_utils.six.moves.urllib.parse import urlencode
from ansible.module_utils.six.moves.urllib.error import HTTPError
from ansible.module_utils.keycloak_utils import isDictEquals 
from ansible.module_utils.keycloak_utils import keycloak2ansibleClientRoles

URL_TOKEN = "{url}/realms/{realm}/protocol/openid-connect/token"
URL_CLIENT = "{url}/admin/realms/{realm}/clients/{id}"
URL_CLIENTS = "{url}/admin/realms/{realm}/clients"
URL_CLIENT_ROLES = "{url}/admin/realms/{realm}/clients/{id}/roles"
URL_CLIENT_SECRET = "{url}/admin/realms/{realm}/clients/{id}/client-secret"

URL_CLIENTTEMPLATE = "{url}/admin/realms/{realm}/client-templates/{id}"
URL_CLIENTTEMPLATES = "{url}/admin/realms/{realm}/client-templates"

URL_GROUPS = "{url}/admin/realms/{realm}/groups"
URL_GROUP = "{url}/admin/realms/{realm}/groups/{groupid}"
URL_GROUP_CLIENT_ROLE_MAPPING = "{url}/admin/realms/{realm}/groups/{groupid}/role-mappings/clients/{clientid}"
URL_GROUP_REALM_ROLE_MAPPING = "{url}/admin/realms/{realm}/groups/{groupid}/role-mappings/realm"

URL_COMPONENTS = "{url}/admin/realms/{realm}/components"
URL_COMPONENT = "{url}/admin/realms/{realm}/components/{id}"
URL_COMPONENT_BY_NAME_TYPE_PARENT = "{url}/admin/realms/{realm}/components?name={name}&type={type}&parent={parent}"
URL_SUB_COMPONENTS = "{url}/admin/realms/{realm}/components?parent={parent}"

URL_USERS = "{url}/admin/realms/{realm}/users"
URL_USER = "{url}/admin/realms/{realm}/users/{id}"
URL_USER_ROLE_MAPPINGS = "{url}/admin/realms/{realm}/users/{id}/role-mappings"
URL_USER_REALM_ROLE_MAPPINGS = "{url}/admin/realms/{realm}/users/{id}/role-mappings/realm"
URL_USER_CLIENTS_ROLE_MAPPINGS = "{url}/admin/realms/{realm}/users/{id}/role-mappings/clients"
URL_USER_CLIENT_ROLE_MAPPINGS = "{url}/admin/realms/{realm}/users/{id}/role-mappings/clients/{client_id}"
URL_USER_GROUPS = "{url}/admin/realms/{realm}/users/{id}/groups"
URL_USER_GROUP = "{url}/admin/realms/{realm}/users/{id}/groups/{group_id}"

URL_USER_STORAGE = "{url}/admin/realms/{realm}/user-storage"
URL_USER_STORAGE_SYNC = "{url}/admin/realms/{realm}/user-storage/{id}/sync?action={action}"
URL_USER_STORAGE_MAPPER_SYNC = "{url}/admin/realms/{realm}/user-storage/{parentid}/mappers/{id}/sync?direction={direction}"

URL_AUTHENTICATION_FLOWS = "{url}/admin/realms/{realm}/authentication/flows"
URL_AUTHENTICATION_FLOW = "{url}/admin/realms/{realm}/authentication/flows/{id}"
URL_AUTHENTICATION_FLOW_COPY = "{url}/admin/realms/{realm}/authentication/flows/{copyfrom}/copy"
URL_AUTHENTICATION_FLOW_EXECUTIONS = "{url}/admin/realms/{realm}/authentication/flows/{flowalias}/executions"
URL_AUTHENTICATION_FLOW_EXECUTIONS_EXECUTION = "{url}/admin/realms/{realm}/authentication/flows/{flowalias}/executions/execution"
URL_AUTHENTICATION_EXECUTIONS_CONFIG = "{url}/admin/realms/{realm}/authentication/executions/{id}/config"
URL_AUTHENTICATION_CONFIG = "{url}/admin/realms/{realm}/authentication/config/{id}"

URL_IDPS = "{url}/admin/realms/{realm}/identity-provider/instances"
URL_IDP = "{url}/admin/realms/{realm}/identity-provider/instances/{alias}"
URL_IDP_MAPPERS = "{url}/admin/realms/{realm}/identity-provider/instances/{alias}/mappers"
URL_IDP_MAPPER = "{url}/admin/realms/{realm}/identity-provider/instances/{alias}/mappers/{id}"

URL_REALMS = "{url}/admin/realms"
URL_REALM = "{url}/admin/realms/{realm}"
URL_REALM_EVENT_CONFIG = "{url}/admin/realms/{realm}/events/config"

URL_REALM_ROLES = "{url}/admin/realms/{realm}/roles"
URL_REALM_ROLE = "{url}/admin/realms/{realm}/roles/{name}"
URL_REALM_ROLE_COMPOSITES = "{url}/admin/realms/{realm}/roles/{name}/composites"

def keycloak_argument_spec():
    """
    Returns argument_spec of options common to keycloak_*-modules

    :return: argument_spec dict
    """
    return dict(
        auth_keycloak_url=dict(type='str', aliases=['url'], required=True),
        auth_client_id=dict(type='str', default='admin-cli'),
        auth_realm=dict(type='str', default='master'),
        auth_client_secret=dict(type='str', default=None),
        auth_username=dict(type='str', required=True),
        auth_password=dict(type='str', required=True, no_log=True),
        validate_certs=dict(type='bool', default=True)
    )


def camel(words):
    return words.split('_')[0] + ''.join(x.capitalize() or '_' for x in words.split('_')[1:])


class KeycloakAPI(object):
    """ Keycloak API access; Keycloak uses OAuth 2.0 to protect its API, an access token for which
        is obtained through OpenID connect
    """
    def __init__(self, module):
        self.module = module
        self.token = None
        self._connect()

    def _connect(self):
        """ Obtains an access_token and saves it for use in API accesses
        """
        self.baseurl = self.module.params.get('auth_keycloak_url')
        self.validate_certs = self.module.params.get('validate_certs')

        auth_url = URL_TOKEN.format(url=self.baseurl, realm=self.module.params.get('auth_realm'))

        payload = {'grant_type': 'password',
                   'client_id': self.module.params.get('auth_client_id'),
                   'client_secret': self.module.params.get('auth_client_secret'),
                   'username': self.module.params.get('auth_username'),
                   'password': self.module.params.get('auth_password')}

        # Remove empty items, for instance missing client_secret
        payload = dict((k, v) for k, v in payload.items() if v is not None)

        try:
            r = json.load(open_url(auth_url, method='POST',
                                   validate_certs=self.validate_certs, data=urlencode(payload)))
        except ValueError as e:
            self.module.fail_json(msg='API returned invalid JSON when trying to obtain access token from %s: %s'
                                      % (auth_url, str(e)))
        except Exception as e:
            self.module.fail_json(msg='Could not obtain access token from %s: %s'
                                      % (auth_url, str(e)))

        if 'access_token' in r:
            self.token = r['access_token']
            self.restheaders = {'Authorization': 'Bearer ' + self.token,
                                'Content-Type': 'application/json'}

        else:
            self.module.fail_json(msg='Could not obtain access token from %s' % auth_url)

    def get_clients(self, realm='master', filter=None):
        """ Obtains client representations for clients in a realm

        :param realm: realm to be queried
        :param filter: if defined, only the client with clientId specified in the filter is returned
        :return: list of dicts of client representations
        """
        clientlist_url = URL_CLIENTS.format(url=self.baseurl, realm=realm)
        if filter is not None:
            clientlist_url += '?clientId=%s' % filter

        try:
            return json.load(open_url(clientlist_url, method='GET', headers=self.restheaders,
                                      validate_certs=self.validate_certs))
        except ValueError as e:
            self.module.fail_json(msg='API returned incorrect JSON when trying to obtain list of clients for realm %s: %s'
                                      % (realm, str(e)))
        except Exception as e:
            self.module.fail_json(msg='Could not obtain list of clients for realm %s: %s'
                                      % (realm, str(e)))

    def get_client_by_clientid(self, client_id, realm='master'):
        """ Get client representation by clientId
        :param client_id: The clientId to be queried
        :param realm: realm from which to obtain the client representation
        :return: dict with a client representation or None if none matching exist
        """
        r = self.get_clients(realm=realm, filter=client_id)
        if len(r) > 0:
            clientrep = r[0]
            clients_url = URL_CLIENTS.format(url=self.baseurl, realm=realm)
            client_roles_url = URL_CLIENT_ROLES.format(url=self.baseurl, realm=realm, id=clientrep['id'])
            self.add_client_roles_to_representation(clients_url, client_roles_url, clientrep)
            return clientrep
        else:
            return None

    def get_client_by_id(self, id, realm='master'):
        """ Obtain client representation by id

        :param id: id (not clientId) of client to be queried
        :param realm: client from this realm
        :return: dict of client representation or None if none matching exist
        """
        client_url = URL_CLIENT.format(url=self.baseurl, realm=realm, id=id)
        clients_url = URL_CLIENTS.format(url=self.baseurl, realm=realm)
        client_roles_url = URL_CLIENT_ROLES.format(url=self.baseurl, realm=realm, id=id)
        try:
            clientrep = json.load(open_url(client_url, method='GET', headers=self.restheaders,
                                      validate_certs=self.validate_certs))
            self.add_client_roles_to_representation(clients_url, client_roles_url, clientrep)
            return clientrep
        
        except HTTPError as e:
            if e.code == 404:
                return None
            else:
                self.module.fail_json(msg='Could not obtain client %s for realm %s: %s'
                                          % (id, realm, str(e)))
        except ValueError as e:
            self.module.fail_json(msg='API returned incorrect JSON when trying to obtain client %s for realm %s: %s'
                                      % (id, realm, str(e)))
        except Exception as e:
            self.module.fail_json(msg='Could not obtain client %s for realm %s: %s'
                                      % (id, realm, str(e)))

    def get_client_secret_by_id(self, id, realm='master'):
        """ Obtain client representation by id
        :param id: id (not clientId) of client to be queried
        :param realm: client from this realm
        :return: dict of client representation or None if none matching exist
        """
        client_url = URL_CLIENT.format(url=self.baseurl, realm=realm, id=id)
        client_secret_url = URL_CLIENT_SECRET.format(url=self.baseurl, realm=realm, id=id)
        try:
            clientrep = json.load(open_url(client_url, method='GET', headers=self.restheaders,
                                      validate_certs=self.validate_certs))
            if clientrep[camel('public_client')]:
                clientsecretrep = None
            else:
                clientsecretrep = json.load(open_url(client_secret_url, method='GET', headers=self.restheaders,
                                      validate_certs=self.validate_certs))
            return clientsecretrep
        
        except HTTPError as e:
            if e.code == 404:
                return None
            else:
                self.module.fail_json(msg='Could not obtain client %s for realm %s: %s'
                                          % (id, realm, str(e)))
        except ValueError as e:
            self.module.fail_json(msg='API returned incorrect JSON when trying to obtain client %s for realm %s: %s'
                                      % (id, realm, str(e)))
        except Exception as e:
            self.module.fail_json(msg='Could not obtain client %s for realm %s: %s'
                                      % (id, realm, str(e)))

    def get_client_id(self, client_id, realm='master'):
        """ Obtain id of client by client_id

        :param client_id: client_id of client to be queried
        :param realm: client template from this realm
        :return: id of client (usually a UUID)
        """
        result = self.get_client_by_clientid(client_id, realm)
        if isinstance(result, dict) and 'id' in result:
            return result['id']
        else:
            return None

    def update_client(self, id, clientrep, realm="master"):
        """ Update an existing client
        :param id: id (not clientId) of client to be updated in Keycloak
        :param clientrep: corresponding (partial/full) client representation with updates
        :param realm: realm the client is in
        :return: HTTPResponse object on success
        """
        client_url = URL_CLIENT.format(url=self.baseurl, realm=realm, id=id)
        roles_url = URL_REALM_ROLES.format(url=self.baseurl, realm=realm)
        clients_url = URL_CLIENTS.format(url=self.baseurl, realm=realm)
        client_roles_url = URL_CLIENT_ROLES.format(url=self.baseurl, realm=realm, id=id)
                
        try:
            client_roles = None 
            if camel('client_roles') in clientrep:
                client_roles = clientrep[camel('client_roles')]
                del(clientrep[camel('client_roles')])
            client_protocol_mappers = None 
            if camel('protocol_mappers') in clientrep:
                client_protocol_mappers = clientrep[camel('protocol_mappers')]
                del(clientrep[camel('protocol_mappers')])
            putResponse = open_url(client_url, method='PUT', headers=self.restheaders,
                            data=json.dumps(clientrep), validate_certs=self.validate_certs)
            if client_protocol_mappers is not None:
                clientrep[camel('protocol_mappers')] = client_protocol_mappers
                self.create_or_update_client_mappers(client_url, clientrep)
            if client_roles is not None:
                self.create_or_update_client_roles(client_roles, roles_url, clients_url, client_roles_url)
            return putResponse

        except Exception as e:
            self.module.fail_json(msg='Could not update client %s in realm %s: %s'
                                      % (id, realm, str(e)))

    def create_client(self, clientrep, realm="master"):
        """ Create a client in keycloak
        :param clientrep: Client representation of client to be created. Must at least contain field clientId
        :param realm: realm for client to be created
        :return: HTTPResponse object on success
        """
        roles_url = URL_REALM_ROLES.format(url=self.baseurl, realm=realm)
        clients_url = URL_CLIENTS.format(url=self.baseurl, realm=realm)
        
        try:
            client_roles = None 
            if camel('client_roles') in clientrep:
                client_roles = clientrep[camel('client_roles')]
                del(clientrep[camel('client_roles')])
            client_protocol_mappers = None 
            if camel('protocol_mappers') in clientrep:
                client_protocol_mappers = clientrep[camel('protocol_mappers')]
                del(clientrep[camel('protocol_mappers')])
            postResponse = open_url(clients_url, method='POST', headers=self.restheaders,
                            data=json.dumps(clientrep), validate_certs=self.validate_certs)
            client_url = URL_CLIENT.format(url=self.baseurl, realm=realm, id=self.get_client_id(clientrep[camel('client_id')], realm))
            if client_protocol_mappers is not None:
                clientrep[camel('protocol_mappers')] = client_protocol_mappers
                self.create_or_update_client_mappers(client_url, clientrep)
            if client_roles is not None:
                client_roles_url = URL_CLIENT_ROLES.format(url=self.baseurl, realm=realm, id=self.get_client_id(clientrep[camel('client_id')], realm))
                self.create_or_update_client_roles(client_roles, roles_url, clients_url, client_roles_url)
        
            return postResponse
            
        except Exception as e:
            self.module.fail_json(msg='Could not create client %s in realm %s: %s'
                                      % (clientrep['clientId'], realm, str(e)))

    def delete_client(self, id, realm="master"):
        """ Delete a client from Keycloak

        :param id: id (not clientId) of client to be deleted
        :param realm: realm of client to be deleted
        :return: HTTPResponse object on success
        """
        client_url = URL_CLIENT.format(url=self.baseurl, realm=realm, id=id)

        try:
            return open_url(client_url, method='DELETE', headers=self.restheaders,
                            validate_certs=self.validate_certs)
        except Exception as e:
            self.module.fail_json(msg='Could not delete client %s in realm %s: %s'
                                      % (id, realm, str(e)))

    def get_client_templates(self, realm='master'):
        """ Obtains client template representations for client templates in a realm

        :param realm: realm to be queried
        :return: list of dicts of client representations
        """
        url = URL_CLIENTTEMPLATES.format(url=self.baseurl, realm=realm)

        try:
            return json.load(open_url(url, method='GET', headers=self.restheaders,
                                      validate_certs=self.validate_certs))
        except ValueError as e:
            self.module.fail_json(msg='API returned incorrect JSON when trying to obtain list of client templates for realm %s: %s'
                                      % (realm, str(e)))
        except Exception as e:
            self.module.fail_json(msg='Could not obtain list of client templates for realm %s: %s'
                                      % (realm, str(e)))

    def get_client_template_by_id(self, id, realm='master'):
        """ Obtain client template representation by id

        :param id: id (not name) of client template to be queried
        :param realm: client template from this realm
        :return: dict of client template representation or None if none matching exist
        """
        url = URL_CLIENTTEMPLATE.format(url=self.baseurl, id=id, realm=realm)

        try:
            return json.load(open_url(url, method='GET', headers=self.restheaders,
                                      validate_certs=self.validate_certs))
        except ValueError as e:
            self.module.fail_json(msg='API returned incorrect JSON when trying to obtain client templates %s for realm %s: %s'
                                      % (id, realm, str(e)))
        except Exception as e:
            self.module.fail_json(msg='Could not obtain client template %s for realm %s: %s'
                                      % (id, realm, str(e)))

    def get_client_template_by_name(self, name, realm='master'):
        """ Obtain client template representation by name

        :param name: name of client template to be queried
        :param realm: client template from this realm
        :return: dict of client template representation or None if none matching exist
        """
        result = self.get_client_templates(realm)
        if isinstance(result, list):
            result = [x for x in result if x['name'] == name]
            if len(result) > 0:
                return result[0]
        return None

    def get_client_template_id(self, name, realm='master'):
        """ Obtain client template id by name

        :param name: name of client template to be queried
        :param realm: client template from this realm
        :return: client template id (usually a UUID)
        """
        result = self.get_client_template_by_name(name, realm)
        if isinstance(result, dict) and 'id' in result:
            return result['id']
        else:
            return None

    def update_client_template(self, id, clienttrep, realm="master"):
        """ Update an existing client template
        :param id: id (not name) of client template to be updated in Keycloak
        :param clienttrep: corresponding (partial/full) client template representation with updates
        :param realm: realm the client template is in
        :return: HTTPResponse object on success
        """
        url = URL_CLIENTTEMPLATE.format(url=self.baseurl, realm=realm, id=id)

        try:
            return open_url(url, method='PUT', headers=self.restheaders,
                            data=json.dumps(clienttrep), validate_certs=self.validate_certs)
        except Exception as e:
            self.module.fail_json(msg='Could not update client template %s in realm %s: %s'
                                      % (id, realm, str(e)))

    def create_client_template(self, clienttrep, realm="master"):
        """ Create a client in keycloak
        :param clienttrep: Client template representation of client template to be created. Must at least contain field name
        :param realm: realm for client template to be created in
        :return: HTTPResponse object on success
        """
        url = URL_CLIENTTEMPLATES.format(url=self.baseurl, realm=realm)

        try:
            return open_url(url, method='POST', headers=self.restheaders,
                            data=json.dumps(clienttrep), validate_certs=self.validate_certs)
        except Exception as e:
            self.module.fail_json(msg='Could not create client template %s in realm %s: %s'
                                      % (clienttrep['clientId'], realm, str(e)))

    def delete_client_template(self, id, realm="master"):
        """ Delete a client template from Keycloak

        :param id: id (not name) of client to be deleted
        :param realm: realm of client template to be deleted
        :return: HTTPResponse object on success
        """
        url = URL_CLIENTTEMPLATE.format(url=self.baseurl, realm=realm, id=id)

        try:
            return open_url(url, method='DELETE', headers=self.restheaders,
                            validate_certs=self.validate_certs)
        except Exception as e:
            self.module.fail_json(msg='Could not delete client template %s in realm %s: %s'
                                      % (id, realm, str(e)))

    def get_groups(self, realm="master"):
        """ Fetch the name and ID of all groups on the Keycloak server.

        To fetch the full data of the group, make a subsequent call to
        get_group_by_groupid, passing in the ID of the group you wish to return.

        :param realm: Return the groups of this realm (default "master").
        """
        groups_url = URL_GROUPS.format(url=self.baseurl, realm=realm)
        try:
            grouprep = json.load(open_url(groups_url, method="GET", headers=self.restheaders,
                                      validate_certs=self.validate_certs))
            return grouprep
        except Exception as e:
            self.module.fail_json(msg="Could not fetch list of groups in realm %s: %s"
                                      % (realm, str(e)))

    def get_group_by_groupid(self, gid, realm="master"):
        """ Fetch a keycloak group from the provided realm using the group's unique ID.

        If the group does not exist, None is returned.

        gid is a UUID provided by the Keycloak API
        :param gid: UUID of the group to be returned
        :param realm: Realm in which the group resides; default 'master'.
        """
        groups_url = URL_GROUP.format(url=self.baseurl, realm=realm, groupid=gid)
        try:
            grouprep = json.load(open_url(groups_url, method="GET", headers=self.restheaders,
                                      validate_certs=self.validate_certs))
            if "clientRoles" in grouprep:
                tmpClientRoles = grouprep["clientRoles"]
                grouprep["clientRoles"] = keycloak2ansibleClientRoles(tmpClientRoles)

            return grouprep
        except HTTPError as e:
            if e.code == 404:
                return None
            else:
                self.module.fail_json(msg="Could not fetch group %s in realm %s: %s"
                                          % (gid, realm, str(e)))
        except Exception as e:
            self.module.fail_json(msg="Could not fetch group %s in realm %s: %s"
                                      % (gid, realm, str(e)))

    def get_group_by_name(self, name, realm="master"):
        """ Fetch a keycloak group within a realm based on its name.

        The Keycloak API does not allow filtering of the Groups resource by name.
        As a result, this method first retrieves the entire list of groups - name and ID -
        then performs a second query to fetch the group.

        If the group does not exist, None is returned.
        :param name: Name of the group to fetch.
        :param realm: Realm in which the group resides; default 'master'
        """
        groups_url = URL_GROUPS.format(url=self.baseurl, realm=realm)
        try:
            all_groups = self.get_groups(realm=realm)

            for group in all_groups:
                if group['name'] == name:
                    return self.get_group_by_groupid(group['id'], realm=realm)

            return None

        except Exception as e:
            self.module.fail_json(msg="Could not fetch group %s in realm %s: %s"
                                      % (name, realm, str(e)))

    def create_group(self, grouprep, realm="master"):
        """ Create a Keycloak group.

        :param grouprep: a GroupRepresentation of the group to be created. Must contain at minimum the field name.
        :return: HTTPResponse object on success
        """
        groups_url = URL_GROUPS.format(url=self.baseurl, realm=realm)
        try:
            # Remove roles because they are not supported by the POST method of the Keycloak endpoint.
            groupreptocreate = grouprep.copy()
            if "realmRoles" in groupreptocreate:
                del(groupreptocreate['realmRoles'])
            if "clientRoles" in groupreptocreate:
                del(groupreptocreate['clientRoles'])
            # Remove the id if it is defined. This can happen when force is true.
            if "id" in groupreptocreate:
                del(groupreptocreate['id'])
            return open_url(groups_url, method='POST', headers=self.restheaders,
                            data=json.dumps(groupreptocreate), validate_certs=self.validate_certs)
        except Exception as e:
            self.module.fail_json(msg="Could not create group %s in realm %s: %s"
                                      % (grouprep['name'], realm, str(e)))

    def update_group(self, grouprep, realm="master"):
        """ Update an existing group.

        :param grouprep: A GroupRepresentation of the updated group.
        :return HTTPResponse object on success
        """
        group_url = URL_GROUP.format(url=self.baseurl, realm=realm, groupid=grouprep['id'])

        try:
            # remove roles because they are not supported by the PUT method of the Keycloak endpoint.
            groupreptoupdate = grouprep.copy()
            if "realmRoles" in groupreptoupdate:
                del(groupreptoupdate['realmRoles'])
            if "clientRoles" in groupreptoupdate:
                del(groupreptoupdate['clientRoles'])
            return open_url(group_url, method='PUT', headers=self.restheaders,
                            data=json.dumps(groupreptoupdate), validate_certs=self.validate_certs)
        except Exception as e:
            self.module.fail_json(msg='Could not update group %s in realm %s: %s'
                                      % (grouprep['name'], realm, str(e)))

    def delete_group(self, name=None, groupid=None, realm="master"):
        """ Delete a group. One of name or groupid must be provided.

        Providing the group ID is preferred as it avoids a second lookup to
        convert a group name to an ID.

        :param name: The name of the group. A lookup will be performed to retrieve the group ID.
        :param groupid: The ID of the group (preferred to name).
        :param realm: The realm in which this group resides, default "master".
        """

        if groupid is None and name is None:
            # prefer an exception since this is almost certainly a programming error in the module itself.
            raise Exception("Unable to delete group - one of group ID or name must be provided.")

        # only lookup the name if groupid isn't provided.
        # in the case that both are provided, prefer the ID, since it's one
        # less lookup.
        if groupid is None and name is not None:
            for group in self.get_groups(realm=realm):
                if group['name'] == name:
                    groupid = group['id']
                    break

        # if the group doesn't exist - no problem, nothing to delete.
        if groupid is None:
            return None

        # should have a good groupid by here.
        group_url = URL_GROUP.format(realm=realm, groupid=groupid, url=self.baseurl)
        try:
            return open_url(group_url, method='DELETE', headers=self.restheaders,
                            validate_certs=self.validate_certs)

        except Exception as e:
            self.module.fail_json(msg="Unable to delete group %s: %s" % (groupid, str(e)))
            
    def get_client_roles(self, client_id, realm='master'):
        """ Get all client's roles

        :param client_id: id of the client
        :return: Client's roles representation is added to the client representation as clientRoles key
        """
        try:
            client_roles_url = URL_CLIENT_ROLES.format(url=self.baseurl,realm=realm,id=client_id)
            clientRolesRepresentation = json.load(open_url(client_roles_url, method='GET', headers=self.restheaders))
            return clientRolesRepresentation
        except Exception as e:
            self.module.fail_json(msg="Unable to get client's %s roles in realm %s: %s" % (client_id, realm, str(e)))

    def add_client_roles_to_representation(self, clientSvcBaseUrl, clientRolesUrl, clientRepresentation):
        """ Add client roles and their composites to the client representation in order to return this information to the user

        :param clientSvcBaseUrl: url of the client
        :param clientRolesUrl: url of the client roles
        :param clientRepresentation: actual representation of the client
        :return: nothing, the roles representation is added to the client representation as clientRoles key
        """
        try:
            clientRolesRepresentation = json.load(open_url(clientRolesUrl, method='GET', headers=self.restheaders))
            for clientRole in clientRolesRepresentation:
                if clientRole["composite"]:
                    clientRole["composites"] = json.load(open_url(clientRolesUrl + '/' + clientRole['name'] +'/composites', method='GET', headers=self.restheaders))
                    
                    for roleComposite in clientRole["composites"]:
                        if roleComposite['clientRole']:
                            roleCompositeClient = json.load(open_url(clientSvcBaseUrl + '/' + roleComposite['containerId'], method='GET', headers=self.restheaders))
                            roleComposite["clientId"] = roleCompositeClient["clientId"]
            clientRepresentation['clientRoles'] = clientRolesRepresentation
        except Exception as e:
            self.module.fail_json(msg="Unable to add client roles %s: %s" % (clientRepresentation["id"], str(e)))
        
    def create_or_update_client_roles(self, newClientRoles, roleSvcBaseUrl, clientSvcBaseUrl, clientRolesUrl):
        """ Create or update client roles. Client roles can be added, updated or removed depending of the state.

        :param newClientRoles: Client roles to be added, updated or removed.
        :param roleSvcBaseUrl: Url to query realm roles
        :param clientSvcBaseUrl: Url to list clients
        :param clientRolesUrl: Url of the actual client roles
        :return: True if the client roles have changed, False otherwise
        """
        try:
            changed = False
            # Manage the roles
            if newClientRoles is not None:
                for newClientRole in newClientRoles:
                    changeNeeded = False
                    desiredState = "present"
                    # If state key is included in the client role representation, save its value and remove the key from the representation.
                    if "state" in newClientRole:
                        desiredState = newClientRole["state"]
                        del(newClientRole["state"])
                    if 'composites' in newClientRole and newClientRole['composites'] is not None:
                        newComposites = newClientRole['composites']
                        for newComposite in newComposites:
                            if "id" in newComposite and newComposite["id"] is not None:
                                keycloakClients=json.load(open_url(clientSvcBaseUrl, method='GET', headers=self.restheaders))
                                for keycloakClient in keycloakClients:
                                    if keycloakClient['clientId'] == newComposite["id"]:
                                        roles=json.load(open_url(clientSvcBaseUrl + '/' + keycloakClient['id'] + '/roles', method='GET', headers=self.restheaders))
                                        for role in roles:
                                            if role["name"] == newComposite["name"]:
                                                newComposite['id'] = role['id']
                                                newComposite['clientRole'] = True
                                                break
                            else:
                                realmRoles=json.load(open_url(roleSvcBaseUrl, method='GET', headers=self.restheaders))
                                for realmRole in realmRoles:
                                    if realmRole["name"] == newComposite["name"]:
                                        newComposite['id'] = realmRole['id']
                                        newComposite['clientRole'] = False
                                        break;
                        
                    clientRoleFound = False
                    clientRoles = json.load(open_url(clientRolesUrl, method='GET', headers=self.restheaders))
                    if len(clientRoles) > 0:
                        # Check if role to be created already exist for the client
                        for clientRole in clientRoles:
                            if (clientRole['name'] == newClientRole['name']):
                                clientRoleFound = True
                                break
                        # If we have to create the role because it does not exist and the desired state is present, or it exists and the desired state is absent
                        if (not clientRoleFound and desiredState != "absent") or (clientRoleFound and desiredState == "absent"):
                            changeNeeded = True
                        else:
                            if "composites" in newClientRole and newClientRole['composites'] is not None:
                                excludes = []
                                excludes.append("composites")
                                if not isDictEquals(newClientRole, clientRole, excludes):
                                    changeNeeded = True
                                else:
                                    for newComposite in newClientRole['composites']:
                                        compositeFound = False
                                        if 'composites' not in clientRole or clientRole['composites'] is None:
                                            changeNeeded = True
                                            break
                                        for existingComposite in clientRole['composites']:
                                            if isDictEquals(newComposite,existingComposite):
                                                compositeFound = True
                                                break
                                        if not compositeFound:
                                            changeNeeded = True
                                            break
                            else:
                                if not isDictEquals(newClientRole, clientRole):
                                    changeNeeded = True
                    elif desiredState != "absent":
                        changeNeeded = True
                    if changeNeeded and desiredState != "absent":
                        # If role must be modified
                        newRoleRepresentation = {}
                        newRoleRepresentation["name"] = newClientRole['name'].decode("utf-8")
                        newRoleRepresentation["description"] = newClientRole['description'].decode("utf-8")
                        newRoleRepresentation["composite"] = newClientRole['composite'] if "composite" in newClientRole else False
                        newRoleRepresentation["clientRole"] = newClientRole['clientRole'] if "clientRole" in newClientRole else True
                        data=json.dumps(newRoleRepresentation)
                        if clientRoleFound:
                            open_url(clientRolesUrl + '/' + newClientRole['name'], method='PUT', headers=self.restheaders, data=data)
                        else:
                            open_url(clientRolesUrl, method='POST', headers=self.restheaders, data=data)
                        changed = True
                        # Composites role
                        if 'composites' in newClientRole and newClientRole['composites'] is not None and len(newClientRole['composites']) > 0:
                            newComposites = newClientRole['composites']
                            if clientRoleFound and "composites" in clientRole:
                                rolesToDelete = []
                                for roleTodelete in clientRole['composites']:
                                    tmprole = {}
                                    tmprole['id'] = roleTodelete['id']
                                    rolesToDelete.append(tmprole)
                                data=json.dumps(rolesToDelete)
                                open_url(clientRolesUrl + '/' + newClientRole['name'] + '/composites', method='DELETE', headers=self.restheaders, data=data)
                            data=json.dumps(newClientRole["composites"])
                            open_url(clientRolesUrl + '/' + newClientRole['name'] + '/composites', method='POST', headers=self.restheaders, data=data)
                    elif changeNeeded and desiredState == "absent" and clientRoleFound:
                        open_url(clientRolesUrl + '/' + newClientRole['name'], method='DELETE', headers=self.restheaders)
                        changed = True
            return changed
        except Exception as e:
            self.module.fail_json(msg="Unable to create or update client roles %s: %s" % (clientRolesUrl, str(e)))
    
    def create_or_update_client_mappers(self, clientUrl, clientRepresentation):
        """ Create or update client protocol mappers. Mappers can be added, updated or removed depending of the state.

        :param clientUrl: Keycloak API url of the client
        :param clientRepresentation: Desired representation of the client including protocolMappers list
        :return: True if the client roles have changed, False otherwise
        """
        try:
            changed = False
            if camel('protocol_mappers') in clientRepresentation and clientRepresentation[camel('protocol_mappers')] is not None:
                newClientProtocolMappers = clientRepresentation[camel('protocol_mappers')]
                # Get existing mappers from the client
                clientMappers = json.load(open_url(clientUrl + '/protocol-mappers/models', method='GET', headers=self.restheaders))
                
                for newClientProtocolMapper in newClientProtocolMappers:
                    desiredState = "present"
                    # If state key is included in the mapper representation, save its value and remove the key from the representation.
                    if "state" in newClientProtocolMapper:
                        desiredState = newClientProtocolMapper["state"]
                        del(newClientProtocolMapper["state"])
                    clientMapperFound = False
                    # Check if mapper already exist for the client
                    for clientMapper in clientMappers:
                        if (clientMapper['name'] == newClientProtocolMapper['name']):
                            clientMapperFound = True
                            break
                    # If mapper exists for the client
                    if clientMapperFound:
                        if desiredState == "absent":
                            # Delete the mapper
                            open_url(clientUrl + '/protocol-mappers/models/' + clientMapper['id'], method='DELETE', headers=self.restheaders)
                            changed = True
                        else:
                            if not isDictEquals(newClientProtocolMapper, clientMapper):
                                # If changed has been introduced for the mapper
                                changed = True
                                newClientProtocolMapper["id"] = clientMapper["id"]
                                data=json.dumps(newClientProtocolMapper)
                                # Modify the mapper
                                open_url(clientUrl + '/protocol-mappers/models/' + clientMapper['id'], method='PUT', headers=self.restheaders, data=data)
                        
                    else: # If mapper does not exist for the client
                        if desiredState != "absent":
                            # Create the mapper
                            data=json.dumps(newClientProtocolMapper)
                            open_url(clientUrl + '/protocol-mappers/models', method='POST', headers=self.restheaders, data=data)
                            changed = True
            return changed
        except Exception as e:
            self.module.fail_json(msg="Unable to create or update client mappers %s: %s" % (clientRepresentation["id"], str(e)))

    def add_attributes_list_to_attributes_dict(self, AttributesList, AttributesDict):
        """
        Add items form an attribute list which is not a Keycloak standard to as an attribute dict.
        
        :param AttributesList: List of attribute to add
        :param AttributesDict: Dict of attributes in which to add the list
        :return: nothing
        """
        if AttributesList is not None:
            if AttributesDict is None:
                AttributesDict = {}
            for attr in AttributesList:
                if "name" in attr and attr["name"] is not None and "value" in attr:
                    AttributesDict[attr["name"]] = attr["value"]
                    
    def assing_roles_to_group(self, groupRepresentation, groupRealmRoles, groupClientRoles, realm='master'):
        """
        Assing roles to group. Roles can be composites of other roles. 
        Composites can be composed by realm and client roles.
        Every member of the group will inherit those roles.
        
        :param groupRepresentation: Representation of the group to assign roles
        :param groupRealmRoles: Realm roles to assign to group
        :param groupClientRoles: Clients roles to assign to group.
        :param realm: Realm
        :return: True if roles have been assigned or revoked to the group. False otherwise.
        """
        try:
            roleSvcBaseUrl = URL_REALM_ROLES.format(url=self.baseurl, realm=realm)
            clientSvcBaseUrl = URL_CLIENTS.format(url=self.baseurl, realm=realm)
            # Get the id of the group
            if 'id' in groupRepresentation:
                gid = groupRepresentation['id']
            else:
                gid = self.get_group_by_name(name=groupRepresentation['name'], realm=realm)['id']
            changed = False
            # Assing Realm Roles
            realmRolesRepresentation = []
            if groupRealmRoles is not None:
                for realmRole in groupRealmRoles:
                    # Look for existing role into group representation
                    if not "realmRoles" in groupRepresentation or not realmRole in groupRepresentation["realmRoles"]:
                        roleid = None
                        # Get all realm roles
                        realmRoles = json.load(open_url(roleSvcBaseUrl, method='GET', headers=self.restheaders))
                        # Find the role id
                        for role in realmRoles:
                            if role["name"] == realmRole:
                                roleid = role["id"]
                                break
                        if roleid is not None:
                            realmRoleRepresentation = {}
                            realmRoleRepresentation["id"] = roleid
                            realmRoleRepresentation["name"] = realmRole
                            realmRolesRepresentation.append(realmRoleRepresentation)
                if len(realmRolesRepresentation) > 0 :
                    data=json.dumps(realmRolesRepresentation)
                    # Assing Role
                    open_url(URL_GROUP_REALM_ROLE_MAPPING.format(url=self.baseurl, realm=realm, groupid=gid), method='POST', headers=self.restheaders, data=data)
                    changed = True
    
            if groupClientRoles is not None:
                # If there is change to do for client roles
                if not "clientRoles" in groupRepresentation or not isDictEquals(groupClientRoles, groupRepresentation["clientRoles"]):
                    # Assing clients roles            
                    for clientRolesToAssing in groupClientRoles:    
                        rolesToAssing = []
                        clientIdOfClientRole = clientRolesToAssing['clientid']
                        # Get the id of the client
                        clients = json.load(open_url(clientSvcBaseUrl + '?clientId=' + clientIdOfClientRole, method='GET', headers=self.restheaders))
                        if len(clients) > 0 and "id" in clients[0]:
                            clientId = clients[0]["id"]
                            # Get the client roles
                            clientRoles = json.load(open_url(URL_CLIENT_ROLES.format(url=self.baseurl, realm=realm, id=clientId), method='GET', headers=self.restheaders))
                            for clientRoleToAssing in clientRolesToAssing["roles"]:
                                # Find his Id
                                for clientRole in clientRoles:
                                    if clientRole["name"] == clientRoleToAssing:
                                        newRole = {}
                                        newRole["id"] = clientRole["id"]
                                        newRole["name"] = clientRole["name"]
                                        rolesToAssing.append(newRole)
                                        break
                        if len(rolesToAssing) > 0:
                            # Delete exiting client Roles
                            open_url(URL_GROUP_CLIENT_ROLE_MAPPING.format(url=self.baseurl, realm=realm, groupid=gid, clientid=clientId), method='DELETE', headers=self.restheaders)
                            data=json.dumps(rolesToAssing)
                            # Assing Role
                            open_url(URL_GROUP_CLIENT_ROLE_MAPPING.format(url=self.baseurl, realm=realm, groupid=gid, clientid=clientId), method='POST', headers=self.restheaders, data=data)
                            changed = True
                    
            return changed
        except Exception as e:
            self.module.fail_json(msg="Unable to assign roles to group %s: %s" % (groupRepresentation['name'], str(e)))
    
    def sync_ldap_groups(self, direction, realm='master'):
        """
        Synchronize groups between Keycloak and LDAP. Every group mappers of users storage providers will be synchronized. 
        The direction parameter will specify how the synchronization will be done.
        
        :param direction: fedToKeycloak or keycloakToFed
        :param realm: Realm
        :return: Nothing
        """
        try:
            LDAPUserStorageProviderType = "org.keycloak.storage.UserStorageProvider"
            componentSvcBaseUrl = URL_COMPONENTS.format(url=self.baseurl, realm=realm)
            userStorageBaseUrl = URL_USER_STORAGE.format(url=self.baseurl, realm=realm)
            # Get all components of type org.keycloak.storage.UserStorageProvider
            components = json.load(open_url(componentSvcBaseUrl + '?type=' + LDAPUserStorageProviderType, method='GET', headers=self.restheaders))
            for component in components:
                # Get all sub components of type group-ldap-mapper
                subComponents = json.load(open_url(componentSvcBaseUrl + "?parent=" + component["id"] + "&providerId=group-ldap-mapper", method='GET', headers=self.restheaders))
                # For each group mappers
                for subComponent in subComponents:
                    if subComponent["providerId"] == 'group-ldap-mapper':
                        # Sync groups
                        open_url(userStorageBaseUrl + '/' + subComponent["parentId"] + "/mappers/" + subComponent["id"] + "/sync?direction=" + direction, method='POST', headers=self.restheaders) 
        except Exception as e:
            self.module.fail_json(msg="Unable to sync ldap groups %s: %s" % (direction, str(e)))


    def get_authentication_flow_by_alias(self, alias, realm='master'):
        """
        Get an authentication flow by it's alias
        
        :param alias: Alias of the authentication flow to get.
        :param realm: Realm.
        :return: Authentication flow representation.
        """
        try:
            authenticationFlow = {}
            # Check if the authentication flow exists on the Keycloak serveraders
            authentications = json.load(open_url(URL_AUTHENTICATION_FLOWS.format(url=self.baseurl, realm=realm), method='GET', headers=self.restheaders))
            for authentication in authentications:
                if authentication["alias"] == alias:
                    authenticationFlow = authentication
                    break
            return authenticationFlow
        except Exception as e:
            self.module.fail_json(msg="Unable get authentication flow %s: %s" % (alias, str(e)))

    def delete_authentication_flow_by_id(self, id, realm='master'):
        """ Delete an authentication flow from Keycloak

        :param id: id of authentication flow to be deleted
        :param realm: realm of client to be deleted
        :return: HTTPResponse object on success
        """
        flow_url = URL_AUTHENTICATION_FLOW.format(url=self.baseurl, realm=realm, id=id)

        try:
            return open_url(flow_url, method='DELETE', headers=self.restheaders,
                            validate_certs=self.validate_certs)
        except Exception as e:
            self.module.fail_json(msg='Could not delete authentication flow %s in realm %s: %s'
                                      % (id, realm, str(e)))
        

    def copy_auth_flow(self, config, realm='master'):
        """
        Create a new authentication flow from a copy of another.
        
        :param config: Representation of the authentication flow to create.
        :param realm: Realm.
        :return: Representation of the new authentication flow.
        """    
        try:
            newName = dict(
                newName = config["alias"]
            )
            
            data = json.dumps(newName)
            open_url(URL_AUTHENTICATION_FLOW_COPY.format(url=self.baseurl, realm=realm, copyfrom=urllib.quote(config["copyFrom"])), method='POST', headers=self.restheaders, data=data)
            flowList = json.load(open_url(URL_AUTHENTICATION_FLOWS.format(url=self.baseurl, realm=realm), method='GET', headers=self.restheaders))
            for flow in flowList:
                if flow["alias"] == config["alias"]:
                    return flow
            return None
        except Exception as e:
            self.module.fail_json(msg='Could not copy authentication flow %s in realm %s: %s'
                                      % (config["alias"], realm, str(e)))
    
    def create_empty_auth_flow(self, config, realm='master'):
        """
        Create a new empty authentication flow.
        
        :param config: Representation of the authentication flow to create.
        :param realm: Realm.
        :return: Representation of the new authentication flow.
        """    
        try:
            newFlow = dict(
                alias = config["alias"],
                providerId = config["providerId"],
                topLevel = True
            )
            data = json.dumps(newFlow)
            open_url(URL_AUTHENTICATION_FLOWS.format(url=self.baseurl, realm=realm), method='POST', headers=self.restheaders, data=data)
            flowList = json.load(open_url(URL_AUTHENTICATION_FLOWS.format(url=self.baseurl, realm=realm), method='GET', headers=self.restheaders))
            for flow in flowList:
                if flow["alias"] == config["alias"]:
                    return flow
            return None
        except Exception as e:
            self.module.fail_json(msg='Could not create empty authentication flow %s in realm %s: %s'
                                      % (config["alias"], realm, str(e)))
    
    def create_or_update_executions(self, config, realm='master'):
        """
        Create or update executions for an authentication flow.
        
        :param config: Representation of the authentication flow including it's executions.
        :param realm: Realm
        :return: True if executions have been modified. False otherwise.
        """ 
        try:
            changed = False
        
            if "authenticationExecutions" in config:
                for newExecution in config["authenticationExecutions"]:
                    # Get existing executions on the Keycloak server for this alias
                    existingExecutions = json.load(open_url(URL_AUTHENTICATION_FLOW_EXECUTIONS.format(url=self.baseurl, realm=realm, flowalias=urllib.quote(config["alias"])), method='GET', headers=self.restheaders))
                    executionFound = False
                    for existingExecution in existingExecutions:
                        if "providerId" in existingExecution and existingExecution["providerId"] == newExecution["providerId"]:
                            executionFound = True
                            break
                    if executionFound:
                        # Replace config id of the execution config by it's complete representation
                        if "authenticationConfig" in existingExecution:
                            execConfigId = existingExecution["authenticationConfig"]
                            execConfig = json.load(open_url(URL_AUTHENTICATION_CONFIG.format(url=self.baseurl, realm=realm, id=execConfigId), method='GET', headers=self.restheaders))
                            existingExecution["authenticationConfig"] = execConfig
        
                        # Compare the executions to see if it need changes
                        if not isDictEquals(newExecution, existingExecution):
                            changed = True
                    else:
                        # Create the new execution
                        newExec = {}
                        newExec["provider"] = newExecution["providerId"]
                        newExec["requirement"] = newExecution["requirement"]
                        data = json.dumps(newExec)
                        open_url(URL_AUTHENTICATION_FLOW_EXECUTIONS_EXECUTION.format(url=self.baseurl, realm=realm, flowalias=urllib.quote(config["alias"])), method='POST', headers=self.restheaders, data=data)
                        changed = True
                    if changed:
                        # Get existing executions on the Keycloak server for this alias
                        existingExecutions = json.load(open_url(URL_AUTHENTICATION_FLOW_EXECUTIONS.format(url=self.baseurl, realm=realm, flowalias=urllib.quote(config["alias"])), method='GET', headers=self.restheaders))
                        executionFound = False
                        for existingExecution in existingExecutions:
                            if "providerId" in existingExecution and existingExecution["providerId"] == newExecution["providerId"]:
                                executionFound = True
                                break
                        if executionFound:
                            # Update the existing execution
                            updatedExec = {}
                            updatedExec["id"] = existingExecution["id"]
                            for key in newExecution:
                                # create the execution configuration
                                if key == "authenticationConfig":
                                    # Add the autenticatorConfig to the execution
                                    data = json.dumps(newExecution["authenticationConfig"])
                                    open_url(URL_AUTHENTICATION_EXECUTIONS_CONFIG.format(url=self.baseurl, realm=realm, id=existingExecution["id"]), method='POST', headers=self.restheaders, data=data)
                                else:
                                    updatedExec[key] = newExecution[key]
                            data = json.dumps(updatedExec)
                            open_url(URL_AUTHENTICATION_FLOW_EXECUTIONS.format(url=self.baseurl, realm=realm, flowalias=urllib.quote(config["alias"])), method='PUT', headers=self.restheaders, data=data)
            return changed
        except Exception as e:
            self.module.fail_json(msg='Could not create or update executions for authentication flow %s in realm %s: %s'
                                      % (config["alias"], realm, str(e)))
    
    def get_executions_representation(self, config, realm='master'):
        """
        Get a representation of the executions for an authentication flow.
        
        :param config: Representation of the authentication flow
        :param realm: Realm
        :return: Representation of the executions
        """
        try:
            # Get executions created
            executions = json.load(open_url(URL_AUTHENTICATION_FLOW_EXECUTIONS.format(url=self.baseurl, realm=realm, flowalias=urllib.quote(config["alias"])), method='GET', headers=self.restheaders))
            for execution in executions:
                if "authenticationConfig" in execution:
                    execConfigId = execution["authenticationConfig"]
                    execConfig = json.load(open_url(URL_AUTHENTICATION_CONFIG.format(url=self.baseurl, realm=realm, id=execConfigId), method='GET', headers=self.restheaders))
                    execution["authenticationConfig"] = execConfig
            return executions
        except Exception as e:
            self.module.fail_json(msg='Could not get executions for authentication flow %s in realm %s: %s'
                                      % (config["alias"], realm, str(e)))
                
    def get_component_by_id(self, component_id, realm='master'):
        """
        Get component representation by it's ID
        :param component_id: ID of the component to get
        :param realm: Realm
        :return: Representation of the component
        """
        try:
            component_url = URL_COMPONENT.format(url=self.baseurl, realm=realm, id=component_id)
            return json.load(open_url(component_url, method='GET', headers=self.restheaders))

        except Exception as e:
            self.module.fail_json(msg='Could not get component %s in realm %s: %s'
                                      % (component_id, realm, str(e)))

    def get_component_by_name_provider_and_parent(self, name, provider_type, provider_id, parent_id, realm='master'):
        """
        Get a component by it's name, provider type, provider id and parent
        
        :param name: Name of the component
        :param provider_type: Provider type of the component
        :param provider_id: Provider ID of the component
        :param parent_id: Parent ID of the component. Realm is used as parent for base component.
        :return: Component's representation if found. An empty dict otherwise.
        """
        componentFound = {}
        components = self.get_components_by_name_provider_and_parent(name=name, provider_type=provider_type, parent_id=parent_id, realm=realm)
        
        for component in components:
            if "providerId" in component and component["providerId"] == provider_id:
                componentFound = component
                break
            
        return componentFound
    
    def get_components_by_name_provider_and_parent(self, name, provider_type, parent_id, realm='master'):
        """
        Get components by name, provider and parent
        
        :param name: Name of the component
        :param provider_type: Provider type of the component
        :param provider_id: Provider ID of the component
        :param parent_id: Parent ID of the component. Realm is used as parent for base component.
        :return: List of components found.
        """
        try:
            component_url = URL_COMPONENT_BY_NAME_TYPE_PARENT.format(url=self.baseurl, realm=realm, name=name, type=provider_type, parent=parent_id)
            components = json.load(open_url(component_url, method='GET', headers=self.restheaders))
            return components
        except Exception as e:
            self.module.fail_json(msg='Could not get component %s in realm %s: %s'
                                      % (name, realm, str(e)))
    
    def create_component(self, newComponent, newSubComponents, syncLdapMappers, realm='master'):
        """
        Create a component and it's subComponents
        :param newComponent: Representation of the component to create
        :param newSubComponents: List of subcomponents to create
        :param syncLdapMappers: Mapper synchronization
        :param realm: Realm
        :return: Representation of the component created
        """
        try:
            component_url = URL_COMPONENTS.format(url=self.baseurl, realm=realm)
            open_url(component_url, method='POST', headers=self.restheaders, data=json.dumps(newComponent))
            # Get the new created component
            component = self.get_component_by_name_provider_and_parent(name=newComponent["name"], provider_type=newComponent["providerType"], provider_id=newComponent["providerId"], parent_id=newComponent["parentId"], realm=realm)
            # Create Sub components
            self.create_new_sub_components(component, newSubComponents, syncLdapMappers, realm=realm)
    
            return component
        except Exception as e:
            self.module.fail_json(msg='Could not create component %s in realm %s: %s'
                                      % (newComponent["name"], realm, str(e)))
    
    def create_new_sub_components(self, component, newSubComponents, syncLdapMappers, realm='master'):
        """
        Create subcomponents for a component.
        :param component: Representation of the parent component
        :param newSubComponents: List of subcomponents to create for this parent
        :param syncLdapMappers: Mapper synchronization
        :param realm: Realm
        :return: Nothing
        """
        try:
            # If subcomponents are defined
            if newSubComponents is not None:
                for componentType in newSubComponents.keys():
                    for newSubComponent in newSubComponents[componentType]:
                        newSubComponent["providerType"] = componentType
                        newSubComponent["parentId"] = component["id"]
                        # Create sub component
                        component_url = URL_COMPONENTS.format(url=self.baseurl, realm=realm)
                        open_url(component_url, method='POST', headers=self.restheaders, data=json.dumps(newSubComponent))
                        # Check if users and groups synchronization is needed
                        if component["providerType"] == "org.keycloak.storage.UserStorageProvider" and syncLdapMappers is not "no":
                            # Get subcomponents
                            subComponents = self.get_component_by_name_provider_and_parent(name=newSubComponent["name"], provider_type=newSubComponent["providerType"], parent_id=component["id"], realm=realm)
                            for subComponent in subComponents:
                                # Sync sub component
                                sync_url = URL_USER_STORAGE_MAPPER_SYNC.format(url=self.baseurl, realm=realm, parentid=subComponent["parentId"], id=subComponent["id"], direction=syncLdapMappers)
                                open_url(sync_url, method='POST', headers=self.restheaders)
        except Exception as e:
            self.module.fail_json(msg='Could not create sub components for parent %s in realm %s: %s'
                                      % (component["name"], realm, str(e)))
                            
    def update_component(self, newComponent, realm='master'):
        """
        Update a component.
        :param component: Representation of the component tu update.
        :param realm: Realm
        :return: new representation of the updated component
        """
        try:
            # Add existing component Id to new component
            component_url = URL_COMPONENT.format(url=self.baseurl, realm=realm, id=newComponent["id"])
            open_url(component_url, method='PUT', headers=self.restheaders, data=json.dumps(newComponent))
            return self.get_component_by_id(newComponent['id'], realm=realm)
        except Exception as e:
            self.module.fail_json(msg='Could not update component %s in realm %s: %s'
                                      % (newComponent["name"], realm, str(e)))
    
    def update_sub_components(self, component, newSubComponents, syncLdapMappers, realm='master'):
        try:
            changed=False
            # Get all existing sub components for the component to update.
            subComponents = self.get_all_sub_components(parent_id=component["id"], realm=realm)
            # For all new sub components to update
            for componentType in newSubComponents.keys():
                for newSubComponent in newSubComponents[componentType]:
                    newSubComponent["providerType"] = componentType
                    # Search in al existing subcomponents
                    newSubComponentFound = False
                    for subComponent in subComponents:
                        # If the existing component is the same type than the new component
                        if subComponent["name"] == newSubComponent["name"]:
                            # Compare them to see if the existing component need to be changed
                            if not isDictEquals(newSubComponent, subComponent):
                                # Update the Ids
                                newSubComponent["parentId"] = subComponent["parentId"]
                                newSubComponent["id"] = subComponent["id"]
                                # Update the sub component
                                component_url = URL_COMPONENT.format(url=self.baseurl, realm=realm, id=subComponent["id"])
                                open_url(component_url, method='PUT', headers=self.restheaders, data=json.dumps(newSubComponent))
                                changed = True
                            newSubComponentFound = True
                            # If sync is needed for the subcomponent
                            if component["providerType"] == "org.keycloak.storage.UserStorageProvider" and syncLdapMappers is not "no":
                                # Do the sync
                                sync_url = URL_USER_STORAGE_MAPPER_SYNC.format(url=self.baseurl, realm=realm, parentid=subComponent["parentId"], id=subComponent["id"], direction=syncLdapMappers)
                                open_url(sync_url, method='POST', headers=self.restheaders)
                            break
                    # If sub-component does not already exists
                    if not newSubComponentFound:
                        # Update the parent Id
                        newSubComponent["parentId"] = component["id"]
                        # Create the sub-component
                        component_url = URL_COMPONENTS.format(url=self.baseurl, realm=realm)
                        open_url(component_url, method='POST', headers=self.restheaders, data=json.dumps(newSubComponent))
                        changed = True
                        # Sync LDAP for group mappers
                        if component["providerType"] == "org.keycloak.storage.UserStorageProvider" and syncLdapMappers is not "no":
                            # Get subcomponents
                            subComponents = self.get_component_by_name_provider_and_parent(name=newSubComponent["name"], provider_type=newSubComponent["providerType"], parent_id=component["id"], realm=realm)
                            for subComponent in subComponents:
                                sync_url = URL_USER_STORAGE_MAPPER_SYNC.format(url=self.baseurl, realm=realm, parentid=subComponent["parentId"], id=subComponent["id"], direction=syncLdapMappers)
                                open_url(sync_url, method='POST', headers=self.restheaders)
            return changed
        except Exception as e:
            self.module.fail_json(msg='Could not update component %s in realm %s: %s'
                                      % (component["name"], realm, str(e)))

    def get_all_sub_components(self, parent_id, realm='master'):
        """
        Get a list of sub components representation for a parent component.
        :param parent_ip: ID of the parent component
        :param realm: Realm
        :return: List of representation for the sub component.
        """
        try:
            subcomponents_url = URL_SUB_COMPONENTS.format(url=self.baseurl, realm=realm, parent=parent_id)
            subcomponents = json.load(open_url(subcomponents_url, method='GET', headers=self.restheaders))
            return subcomponents
        except Exception as e:
            self.module.fail_json(msg='Could not get sub components for parent component %s in realm %s: %s'
                                      % (parent_id, realm, str(e)))
        
    def delete_component(self, component_id, realm='master'):
        """
        Delete component from Keycloak server
        :param component_id: Id of the component to delete
        :param realm: Realm
        :return: HTTP response
        """
        try:
            component_url = URL_COMPONENT.format(url=self.baseurl, realm=realm, id=component_id)
            return open_url(component_url, method='DELETE', headers=self.restheaders)
        except Exception as e:
            self.module.fail_json(msg='Could not delete component %s in realm %s: %s'
                                      % (component_id, realm, str(e)))
        
    def sync_user_storage(self, component_id, action, realm='master'):
        """
        Synchronize LDAP user storage component with Keycloak.
        :param component_id: ID of the component to synchronize
        :param action: Type of synchronization ("triggerFullSync" or "triggerChangedUsersSync")
        :param realm: Realm
        :return: HTTP response
        """
        try:
            sync_url=URL_USER_STORAGE_SYNC.format(url=self.baseurl, realm=realm, id=component_id, action=action)
            return open_url(sync_url, method='POST', headers=self.restheaders)
        except Exception as e:
            self.module.fail_json(msg='Could not synchronize component %s action %s in realm %s: %s'
                                      % (component_id, action, realm, str(e)))
            
    def add_idp_endpoints(self, idPConfiguration, url):
        """
        This function extract OpenID connect endpoints from the identity provider's openid-configuration URL.
        Endpoints are added to the idp configuration object received in parameter.
        :param idPConfiguration: Identity provider configuration dict to update.
        :param url: Identity provider's openid-configuration URL.
        :param realm: Realm
        :return: Nothing
        """
        try:
            if url is not None:
                openIdConfig = json.load(open_url(url, method='GET'))
                if 'userinfo_endpoint' in openIdConfig.keys():
                    idPConfiguration["userInfoUrl"] = openIdConfig["userinfo_endpoint"]
                if 'token_endpoint' in openIdConfig.keys():
                    idPConfiguration["tokenUrl"] = openIdConfig["token_endpoint"]
                if 'jwks_uri' in openIdConfig.keys():
                    idPConfiguration["jwksUrl"] = openIdConfig["jwks_uri"]
                if 'issuer' in openIdConfig.keys():
                    idPConfiguration["issuer"] = openIdConfig["issuer"]
                if 'authorization_endpoint' in openIdConfig.keys():
                    idPConfiguration["authorizationUrl"] = openIdConfig["authorization_endpoint"]
                if 'end_session_endpoint' in openIdConfig.keys():
                    idPConfiguration["logoutUrl"] = openIdConfig["end_session_endpoint"]        
        except Exception, e:
            self.module.fail_json(msg='Could not get IdP configuration from endpoint %s: %s'
                                      % (url, str(e)))
    
    def delete_all_idp_mappers(self, alias, realm='master'):
        """
        Delete all mappers for an identity provider
        :param alias: Idp alias to delete mappers from.
        :param realm: Realm
        :return: True if mappers have been deleted, False otherwise.
        """
        changed = False
        try:
            # Get idp's mappers list
            mappers_url = URL_IDP_MAPPERS.format(url=self.baseurl, realm=realm, alias=alias)
            mappers = json.load(open_url(mappers_url, method='GET',headers=self.restheaders))
            for mapper in mappers:
                mapper_url = URL_IDP_MAPPER.format(url=self.baseurl,realm=realm,alias=alias,id=mapper['id'])
                open_url(mapper_url,method='DELETE',headers=self.restheaders)
                changed=True
                
            return changed
        except Exception, e:
            self.module.fail_json(msg='Could not delete mappers for IdP %s in realm %s: %s'
                                      % (alias, realm, str(e)))
         
    
    def create_or_update_idp_mappers(self, alias, idPMappers, realm='master'):
        """
        Create, update or delete mappers for an identity provider.
        :param alias: Idp alias to add, update or delete mappers from.
        :param idPMappers: List of mappers
        :param realm: Realm
        :return: True if mappers have been modified, False otherwise.
        """
        changed = False
        try:
            # Get idp's mappers list
            mappers_url = URL_IDP_MAPPERS.format(url=self.baseurl, realm=realm, alias=alias)
            mappers = json.load(open_url(mappers_url, method='GET',headers=self.restheaders))
            for idPMapper in idPMappers:
                desiredState = "present"
                if "state" in idPMapper:
                    desiredState = idPMapper["state"]
                    del(idPMapper["state"])
                mapperFound = False
                for mapper in mappers:
                    if mapper['name'] == idPMapper['name']:
                        mapperFound = True
                        break
                # If mapper already exist and is different
                if mapperFound and not isDictEquals(idPMapper,mapper):
                    # update the existing mapper
                    for key in idPMapper.keys():
                        mapper[key] = idPMapper[key]
                        mapper_url = URL_IDP_MAPPER.format(url=self.baseurl, realm=realm, alias=alias, id=mapper['id'])
                        open_url(mapper_url, method='PUT', headers=self.restheaders, data=json.dumps(mapper))                        
                    changed = True
                elif mapperFound and desiredState == "absent":
                    # delete the mapper
                    mapper_url = URL_IDP_MAPPER.format(url=self.baseurl,realm=realm,alias=alias,id=mapper['id'])
                    open_url(mapper_url,method='DELETE',headers=self.restheaders)
                    changed = True
                # If the mapper does not already exist
                elif not mapperFound and desiredState != "absent":
                    # Complete the mapper settings with defaults
                    if 'identityProviderMapper' not in idPMapper.keys(): # if mapper's type is provided
                        idPMapper['identityProviderMapper'] = 'oidc-user-attribute-idp-mapper'                
                    idPMapper['identityProviderAlias'] = alias
     
                    # Create it
                    mappers_url=URL_IDP_MAPPERS.format(url=self.baseurl, realm=realm, alias=alias)
                    open_url(mappers_url, method='POST', headers=self.restheaders, data=json.dumps(idPMapper))
                    changed = True

            return changed        
        except Exception ,e :
            self.module.fail_json(msg='Could not create or update mappers for IdP %s in realm %s: %s'
                                      % (alias, realm, str(e)))


    def get_idp_by_alias(self, alias, realm='master'):
        """
        Get an identity provider by alias. Representation of the idp is returned.
        :param alias: Alias of the Idp to get
        :param realm: Realm
        :return: Representation of the Idp.
        """
        try:
            idPRepresentation = {}
            idp_url = URL_IDP.format(url=self.baseurl,realm=realm,alias=alias)
            
            # Get all IdP from Keycloak server
            idPRepresentation = json.load(open_url(idp_url, method='GET', headers=self.restheaders))
            return idPRepresentation
        except Exception ,e :
            self.module.fail_json(msg='Could not get IdP by alias %s in realm %s: %s'
                                      % (alias, realm, str(e)))

    def search_idp_by_alias(self, alias, realm='master'):
        """
        Search an identity provider by alias. Representation of the idp found is returned.
        :param alias: Alias of the Idp to find
        :param realm: Realm
        :return: Representation of the Idp. An empty dict is returned if alias is not found.
        """
        try:
            idPRepresentation = {}
            idps_url = URL_IDPS.format(url=self.baseurl,realm=realm)
            
            # Get all idps from Keycloak server
            listIdPs = json.load(open_url(idps_url, method='GET', headers=self.restheaders))
        
            for idP in listIdPs:
                if idP['alias'] == alias:
                    # Get existing IdP
                    idPRepresentation = idP
                    break
            return idPRepresentation
        except Exception ,e :
            self.module.fail_json(msg='Could not search IdP by alias %s in realm %s: %s'
                                      % (alias, realm, str(e)))

    def search_idp_by_client_id(self, client_id, realm='master'):
        """
        Search an identity provider by its client ID. Representation of the idp found is returned.
        :param alias: Alias of the Idp to find
        :param realm: Realm
        :return: Representation of the Idp. An empty dict is returned if client id is not found.
        """
        try:
            idPRepresentation = {}
            idps_url = URL_IDPS.format(url=self.baseurl,realm=realm)
            
            # Get all idps from Keycloak server
            listIdPs = json.load(open_url(idps_url, method='GET', headers=self.restheaders))
        
            for idP in listIdPs:
                if 'config' in idP and idP['config'] is not None and 'clientId' in idP['config'] and idP['config']['clientId'] == client_id:
                    # Obtenir le IdP exitant
                    idPRepresentation = idP
                    break
            return idPRepresentation
        except Exception ,e :
            self.module.fail_json(msg='Could not search IdP by client Id %s in realm %s: %s'
                                      % (client_id, realm, str(e)))

    def create_idp(self, newIdPRepresentation, realm='master'):
        """
        Create an identity provider on a Keycloak server.
        :param newIdPRepresentation: Representation of the Idp to create.
        :param realm: Realm
        :return: Actual representation of the idp created.
        """
        try:
            idps_url = URL_IDPS.format(url=self.baseurl, realm=realm)
            open_url(idps_url, method='POST', headers=self.restheaders, data=json.dumps(newIdPRepresentation))
            return self.get_idp_by_alias(newIdPRepresentation["alias"], realm)
        except Exception ,e :
            self.module.fail_json(msg='Could not create the IdP %s in realm %s: %s'
                                      % (newIdPRepresentation["alias"], realm, str(e)))

    def update_idp(self, newIdPRepresentation, realm='master'):
        """
        Update an identity provider on a Keycloak server.
        :param newIdPRepresentation: Representation of the Idp to create.
        :param realm: Realm
        :return: Actual representation of the updated idp.
        """
        try:
            idp_url = URL_IDP.format(url=self.baseurl, realm=realm, alias=newIdPRepresentation["alias"])
            open_url(idp_url, method='PUT', headers=self.restheaders, data=json.dumps(newIdPRepresentation))
            return self.get_idp_by_alias(newIdPRepresentation["alias"], realm)
        except Exception ,e :
            self.module.fail_json(msg='Could not update the IdP %s in realm %s: %s'
                                      % (newIdPRepresentation["alias"], realm, str(e)))

    def delete_idp(self, alias, realm='master'):
        """
        Delete an identity provider from a Keycloak server.
        :param alias: Alias of the IdP to delete
        :param realm: Realm
        :return: HTTP response
        """
        try:
            idp_url = URL_IDP.format(url=self.baseurl, realm=realm, alias=alias)
            return open_url(idp_url, method='DELETE', headers=self.restheaders)
        except Exception ,e :
            self.module.fail_json(msg='Could not delete the IdP %s in realm %s: %s'
                                      % (alias, realm, str(e)))

    def get_idp_mappers(self, alias, realm='master'):
        """
        Get all mappers for an identity provider.
        :param alias: Alias of the Idp
        :param realm: Realm
        :return: List of mappers
        """
        try:
            mapper_url = URL_IDP_MAPPERS.format(url=self.baseurl,realm=realm,alias=alias)
            
            # Get all mappers for the IdP from Keycloak server
            idMappers = json.load(open_url(mapper_url, method='GET', headers=self.restheaders))
            return idMappers
        except Exception ,e :
            self.module.fail_json(msg='Could not get IdP mappers for alias %s in realm %s: %s'
                                      % (alias, realm, str(e)))

    def search_realm(self, realm):
        """
        Search a realm by its name.
        :param realm: Name of the realm to find
        :return: Realm representation. An empty dict is returned when realm have not been found
        """
        try:
            realmRepresentation = {}
            realms_url = URL_REALMS.format(url=self.baseurl)
            
            listRealms = json.load(open_url(realms_url, method='GET', headers=self.restheaders))
        
            for theRealm in listRealms:
                if theRealm['realm'] == realm:
                    realmRepresentation = theRealm
                    break
            return realmRepresentation
        except Exception ,e :
            self.module.fail_json(msg='Could not search for realm %s: %s'
                                      % (realm, str(e)))

    def get_realm(self, realm):
        """
        Get a Realm.
        :param realm: realm to get
        :return: Representation of the realm.
        """
        try:
            realm_url = URL_REALM.format(url=self.baseurl, realm=realm)
            realmRepresentation = json.load(open_url(realm_url, method='GET', headers=self.restheaders))
            return realmRepresentation
        except Exception ,e :
            self.module.fail_json(msg='Could get realm %s: %s'
                                      % (realm, str(e)))

    def create_realm(self, newRealmRepresentation):
        """
        Create a new Realm.
        :param newRealmRepresentation: Representation of the realm to create
        :return: Representation of the realm created.
        """
        try:
            realms_url = URL_REALMS.format(url=self.baseurl)
            open_url(realms_url, method='POST', headers=self.restheaders, data=json.dumps(newRealmRepresentation))
            realmRepresentation = self.get_realm(realm=newRealmRepresentation["realm"])
            return realmRepresentation
        except Exception ,e :
            self.module.fail_json(msg='Could not create realm %s: %s'
                                      % (newRealmRepresentation["realm"], str(e)))
            
    def delete_realm(self, realm):
        """
        Delete a Realm.
        :param realm: realm to delete
        :return: HTTP Response.
        """
        try:
            realm_url = URL_REALM.format(url=self.baseurl, realm=realm)
            return open_url(realm_url, method='DELETE', headers=self.restheaders)
        except Exception ,e :
            self.module.fail_json(msg='Could delete realm %s: %s'
                                      % (realm, str(e)))

    def update_realm(self, newRealmRepresentation):
        """
        Update a Realm.
        :param newRealmRepresentation: Updated configuration of the realm
        :return: Realm representation
        """
        try:
            realm_url = URL_REALM.format(url=self.baseurl, realm=newRealmRepresentation["realm"])
            open_url(realm_url, method='PUT', headers=self.restheaders, data=json.dumps(newRealmRepresentation))
            return self.get_realm(newRealmRepresentation["realm"])
        except Exception ,e :
            self.module.fail_json(msg='Could update realm %s: %s'
                                      % (newRealmRepresentation["realm"], str(e)))

    def update_realm_events_config(self, realm, newEventsConfig):
        """
        Update events configuration for a REALM.
        :param realm: Realm to update
        :param eventConfig: new event configuration
        :return: Updated events configuration for the realm.
        """
        try:
            realm_events_config_url = URL_REALM_EVENT_CONFIG.format(url=self.baseurl, realm=realm)
            open_url(realm_events_config_url, method='PUT', headers=self.restheaders, data=json.dumps(newEventsConfig))
            return self.get_realm_events_config(realm=realm)
        except Exception ,e :
            self.module.fail_json(msg='Could not update events config for realm %s: %s'
                                      % (realm, str(e)))
        
    def get_realm_events_config(self, realm):
        """
        Get events configuration for a REALM.
        :param realm: Realm to update
        :return: Updated events configuration for the realm.
        """
        try:
            realm_events_config_url = URL_REALM_EVENT_CONFIG.format(url=self.baseurl, realm=realm)
            return json.load(open_url(realm_events_config_url, method='GET', headers=self.restheaders))
        except Exception ,e :
            self.module.fail_json(msg='Could not get events config for realm %s: %s'
                                      % (realm, str(e)))

    def search_realm_role_by_name(self, name, realm="master"):
        """
        Search a REALM role by its name.
        :param name: Name of the realm role to find
        :param realm: Realm
        :return: Realm role representation. An empty dict is returned when role have not been found
        """
        try:
            rolerep = {}            
            listRoles = self.get_realm_roles(realm=realm)
            for role in listRoles:
                if role['name'] == name:
                    rolerep = role
                    break
            return rolerep
        except Exception ,e :
            self.module.fail_json(msg='Could not search for role % in realm %s: %s'
                                      % (name, realm, str(e)))
    def get_realm_roles(self, realm="master"):
        """
        Get all REALM roles.
        :param realm: Realm
        :return: Realm roles representation.
        """
        try:
            realm_roles_url = URL_REALM_ROLES.format(url=self.baseurl,realm=realm)            
            listRoles = json.load(open_url(realm_roles_url, method='GET', headers=self.restheaders))
            return listRoles
        except Exception ,e :
            self.module.fail_json(msg='Could not get roles in realm %s: %s'
                                      % (realm, str(e)))

    def get_realm_role(self, name, realm="master"):
        """
        Get a REALM role.
        :param name: Name of the realm role to create
        :param realm: Realm
        :return: Realm roles representation.
        """
        try:
            realm_role_url = URL_REALM_ROLE.format(url=self.baseurl,realm=realm,name=name)            
            role = json.load(open_url(realm_role_url, method='GET', headers=self.restheaders))
            return role
        except Exception ,e :
            self.module.fail_json(msg='Could not get role %s in realm %s: %s'
                                      % (name, realm, str(e)))

    def create_realm_role(self, newRoleRepresentation, realm='master'):
        """
        Create a new Realm role.
        :param newRoleRepresentation: Representation of the realm role to create
        :param realm: Realm
        :return: Representation of the realm role created.
        """
        try:
            realm_roles_url = URL_REALM_ROLES.format(url=self.baseurl,realm=realm) 
            open_url(realm_roles_url, method='POST', headers=self.restheaders, data=json.dumps(newRoleRepresentation))
            roleRepresentation = self.get_realm_role(name=newRoleRepresentation['name'], realm=realm)
            return roleRepresentation
        except Exception ,e :
            self.module.fail_json(msg='Could not create realm role %s in realm %s: %s'
                                      % (newRoleRepresentation["name"], realm, str(e)))

    def delete_realm_role(self, name, realm='master'):
        """
        Delete a Realm role.
        :param name: Name of the realm role to delete
        :param realm: Realm
        :return: Representation of the realm role created.
        """
        try:
            realm_role_url = URL_REALM_ROLE.format(url=self.baseurl,realm=realm,name=name) 
            return open_url(realm_role_url, method='DELETE', headers=self.restheaders)
        except Exception ,e :
            self.module.fail_json(msg='Could not delete realm role %s in realm %s: %s'
                                      % (name, realm, str(e)))

    def update_realm_role(self, newRoleRepresentation, realm='master'):
        """
        Update a Realm role.
        :param newRoleRepresentation: Representation of the realm role to update
        :param realm: Realm
        :return: Representation of the updated realm role.
        """
        try:
            realm_role_url = URL_REALM_ROLE.format(url=self.baseurl,realm=realm,name=newRoleRepresentation["name"]) 
            open_url(realm_role_url, method='PUT', headers=self.restheaders,data=json.dumps(newRoleRepresentation))
            roleRepresentation = self.get_realm_role(name=newRoleRepresentation['name'], realm=realm)
            return roleRepresentation
        except Exception ,e :
            self.module.fail_json(msg='Could not update realm role %s in realm %s: %s'
                                      % (newRoleRepresentation["name"], realm, str(e)))

    def get_realm_role_composites_with_client_id(self, name, realm='master'):
        """
        Get realm role's composites with their clientId
        :param name: Name of the role to get the composites from
        :param realm: Realm
        :return: Representation of the realm role's composites including the clientIds.
        """
        composites = self.get_realm_role_composites(name=name, realm=realm)
        for composite in composites:
            if composite["clientRole"]:
                composite["clientId"] = self.get_client_by_id(id=composite["containerId"], realm=realm)["clientId"]
        return composites

    def get_realm_role_composites(self, name, realm='master'):
        """
        Get realm role's composites
        :param name: Name of the role to get the composites from
        :param realm: Realm
        :return: Representation of the realm role's composites.
        """
        try:
            realm_role_composites_url = URL_REALM_ROLE_COMPOSITES.format(url=self.baseurl,realm=realm,name=name) 
            composites = json.load(open_url(realm_role_composites_url, method='GET', headers=self.restheaders))
            return composites
        except Exception ,e :
            self.module.fail_json(msg='Could not get realm role %s composites in realm %s: %s'
                                      % (name, realm, str(e)))

    def create_realm_role_composites(self, newCompositesToCreate, name, realm='master'):
        """
        Create composites for a Realm role.
        :param newCompositesToCreate: Representation of the realm role's composites to create.
        :param name: Name of the realm role
        :param realm: Realm
        :return: HTTP Response
        """
        try:
            realm_role_composites_url = URL_REALM_ROLE_COMPOSITES.format(url=self.baseurl,realm=realm,name=name) 
            return open_url(realm_role_composites_url, method='POST', headers=self.restheaders, data=json.dumps(newCompositesToCreate))
        except Exception ,e :
            self.module.fail_json(msg='Could not create realm role %s composites in realm %s: %s'
                                      % (name, realm, str(e)))

    def create_or_update_realm_role_composites(self, newComposites, newRoleRepresentation, realm='master'):
        """
        Create or update composite roles for a REALM role
        :param newComposites: Representation of the composites to update or create
        :param newRoleRepresentation: Representation of the realm role to update composites.
        :param realm: Realm
        :return: True if composites have changed, False otherwise.
        """
        changed = False
        newCompositesToCreate = []
        try:
            # Get the realm role's composites already present on the Keycloak server
            existingComposites = self.get_realm_role_composites(name=newRoleRepresentation["name"], realm=realm)
            if existingComposites is None:
                existingComposites = []
            for existingComposite in existingComposites:
                newCompositesToCreate.append(existingComposite)
            # If new version of the role is composite and there are composites in it
            if newComposites is not None and newRoleRepresentation["composite"]:
                for newComposite in newComposites:
                    newCompositeFound = False
                    # Search composite to assing in composites of the role on the Keycloak Server
                    for composite in existingComposites:
                        if composite["clientRole"] and "clientId" in newComposite: # If composite is a client role
                            # Get the clientId
                            clientId = self.get_client_by_id(id=composite["containerId"], realm=realm)["clientId"]
                            if composite["name"] == newComposite["name"] and clientId == newComposite["clientId"]:
                                newCompositeFound = True
                                break
                        elif composite["name"] == newComposite["name"]:
                            newCompositeFound = True
                            break
                    # If role is not already assigned to the role
                    if not newCompositeFound:
                        roles = []
                        # If composite is a client role
                        if "clientId" in newComposite:
                            # Get the client
                            client = self.get_client_by_clientid(client_id=newComposite["clientId"], realm=realm)
                            if client != {}:
                                # Get client's roles
                                roles = self.get_client_roles(client_id=client["id"], realm=realm)
                        else: # It is a REALM role
                            # Get all realm roles
                            roles = self.get_realm_roles()
                        # Search in all roles found which is the role to assigne
                        for role in roles:                   
                            # Id role is found
                            if role["name"] == newComposite["name"]:
                                newCompositesToCreate.append(role)
                                changed = True
            if changed:
                self.create_realm_role_composites(newCompositesToCreate=newCompositesToCreate, name=newRoleRepresentation["name"], realm=realm)
            return changed
        
        except Exception ,e :
            self.module.fail_json(msg='Could not create or update realm role %s composites in realm %s: %s'
                                      % (newRoleRepresentation["name"], realm, str(e)))

    def get_user_by_id(self, user_id, realm='master'):
        """
        Get a User by its ID.
        :param user_id: ID of the user.
        :param realm: Realm
        :return: Representation of the user.
        """
        try:
            user_url = URL_USER.format(url=self.baseurl,realm=realm,id=user_id) 
            userRepresentation = json.load(open_url(user_url, method='GET', headers=self.restheaders))
            return userRepresentation
        except Exception ,e :
            self.module.fail_json(msg='Could not get user %s in realm %s: %s'
                                      % (user_id, realm, str(e)))

    def search_user_by_username(self, username, realm="master"):
        """
        Search a user by its username.
        :param username: User name to find
        :return: User representation. An empty dict is returned when role have not been found
        """
        try:
            userrep = {}
            url_search_user_by_username = URL_USERS.format(url=self.baseurl, realm=realm) + '?username=' + username         
            listUsers = json.load(open_url(url_search_user_by_username, method='GET',headers=self.restheaders))
            for user in listUsers:
                if user['username'] == username:
                    userrep = user
                    break
            return userrep
        except Exception ,e :
            self.module.fail_json(msg='Could not search for user %s in realm %s: %s'
                                      % (username, realm, str(e)))
            
    def create_user(self, newUserRepresentation, realm='master'):
        """
        Create a new User.
        :param newUserRepresentation: Representation of the user to create
        :param realm: Realm
        :return: Representation of the user created.
        """
        try:
            users_url = URL_USERS.format(url=self.baseurl,realm=realm) 
            open_url(users_url, method='POST', headers=self.restheaders, data=json.dumps(newUserRepresentation))
            userRepresentation = self.search_user_by_username(username=newUserRepresentation['username'], realm=realm)
            return userRepresentation
        except Exception ,e :
            self.module.fail_json(msg='Could not create user %s in realm %s: %s'
                                      % (newUserRepresentation['username'], realm, str(e)))

    def update_user(self, newUserRepresentation, realm='master'):
        """
        Update a User.
        :param newUserRepresentation: Representation of the user to update. This representation must include the ID of the user.
        :param realm: Realm
        :return: Representation of the updated user.
        """
        try:
            user_url = URL_USER.format(url=self.baseurl,realm=realm,id=newUserRepresentation["id"]) 
            open_url(user_url, method='PUT', headers=self.restheaders, data=json.dumps(newUserRepresentation))
            userRepresentation = self.get_user_by_id(user_id=newUserRepresentation['id'], realm=realm)
            return userRepresentation
        except Exception ,e :
            self.module.fail_json(msg='Could not update user %s in realm %s: %s'
                                      % (newUserRepresentation['username'], realm, str(e)))

    def delete_user(self, user_id, realm='master'):
        """
        Delete a User.
        :param user_id: ID of the user to be deleted
        :param realm: Realm
        :return: HTTP response.
        """
        try:
            user_url = URL_USER.format(url=self.baseurl,realm=realm,id=user_id) 
            return open_url(user_url, method='DELETE', headers=self.restheaders)
        except Exception ,e :
            self.module.fail_json(msg='Could not delete user %s in realm %s: %s'
                                      % (user_id, realm, str(e)))

    def get_user_realm_roles(self, user_id, realm='master'):
        """
        Get realm roles for a user.
        :param user_id: User ID
        :param realm: Realm
        :return: Representation of the realm roles.
        """
        try:
            role_mappings_url = URL_USER_ROLE_MAPPINGS.format(url=self.baseurl,realm=realm,id=user_id) 
            role_mappings = json.load(open_url(role_mappings_url, method='GET', headers=self.restheaders))
            realmRoles = []
            for roleMapping in role_mappings["realmMappings"]:
                realmRoles.append(roleMapping["name"])
            return realmRoles
        except Exception ,e :
            self.module.fail_json(msg='Could not get role mappings for user %s in realm %s: %s'
                                      % (user_id, realm, str(e)))

    def update_user_realm_roles(self, user_id, realmRolesRepresentation, realm='master'):
        """
        Update realm roles for a user.
        :param user_id: User ID
        :param realm: Realm
        :return: Representation of the realm roles.
        """
        try:
            role_mappings_url = URL_USER_REALM_ROLE_MAPPINGS.format(url=self.baseurl,realm=realm,id=user_id) 
            return open_url(role_mappings_url, method='POST', headers=self.restheaders, data=json.dumps(realmRolesRepresentation))
        except Exception ,e :
            self.module.fail_json(msg='Could not update realm role mappings for user %s in realm %s: %s'
                                      % (user_id, realm, str(e)))

    def get_user_client_roles(self, user_id, realm='master'):
        """
        Get client roles for a user.
        :param user_id: User ID
        :param realm: Realm
        :return: Representation of the client roles.
        """
        try:
            clientRoles = []
            role_mappings_url = URL_USER_ROLE_MAPPINGS.format(url=self.baseurl,realm=realm,id=user_id) 
            userMappings = json.load(open_url(role_mappings_url, method='GET', headers=self.restheaders))
            for clientMapping in userMappings["clientMappings"].keys():
                clientRole = {}
                clientRole["clientId"] = userMappings["clientMappings"][clientMapping]["client"]
                roles = []
                for role in userMappings["clientMappings"][clientMapping]["mappings"]:
                    roles.append(role["name"])
                clientRole["roles"] = roles
                clientRoles.append(clientRole)
            return clientRoles
        except Exception ,e :
            self.module.fail_json(msg='Could not get role mappings for user %s in realm %s: %s'
                                      % (user_id, realm, str(e)))

    def delete_user_client_roles(self, user_id, client_id, realm='master'):
        """
        Delete client roles for a user.
        :param user_id: User ID
        :param client_id: Client ID for client roles to delete.
        :param realm: Realm
        :return: HTTP Response.
        """
        try:
            role_mappings_url = URL_USER_CLIENT_ROLE_MAPPINGS.format(url=self.baseurl,realm=realm,id=user_id,client_id=client_id) 
            return open_url(role_mappings_url, method='DELETE', headers=self.restheaders)
        except Exception ,e :
            self.module.fail_json(msg='Could not delete client role mappings for user %s in realm %s: %s'
                                      % (user_id, realm, str(e)))

    def create_user_client_roles(self, user_id, client_id, rolesToAssing, realm='master'):
        """
        Delete client roles for a user.
        :param user_id: User ID
        :param client_id: Client ID for client roles to create.
        :param rolesToAssing: Representation of the client roles to create.
        :param realm: Realm
        :return: HTTP Response.
        """
        try:
            role_mappings_url = URL_USER_CLIENT_ROLE_MAPPINGS.format(url=self.baseurl,realm=realm,id=user_id,client_id=client_id) 
            return open_url(role_mappings_url, method='POST', headers=self.restheaders,data=json.dumps(rolesToAssing))
        except Exception ,e :
            self.module.fail_json(msg='Could not create client role mappings for user %s in realm %s: %s'
                                      % (user_id, realm, str(e)))
            
    def get_user_groups(self, user_id, realm='master'):
        """
        Get groups for a user.
        :param user_id: User ID
        :param realm: Realm
        :return: Representation of the client groups.
        """
        try:
            groups = []
            user_groups_url = URL_USER_GROUPS.format(url=self.baseurl,realm=realm,id=user_id) 
            userGroups = json.load(open_url(user_groups_url, method='GET', headers=self.restheaders))
            for userGroup in userGroups:
                groups.append(userGroup["name"])
            return groups
        except Exception ,e :
            self.module.fail_json(msg='Could not get groups for user %s in realm %s: %s'
                                      % (user_id, realm, str(e)))

    def add_user_in_group(self, user_id, group_id, realm='master'):
        """
        Add a user to a group.
        :param user_id: User ID
        :param group_id: Group Id to add the user to.
        :param realm: Realm
        :return: HTTP Response
        """
        try:
            user_group_url = URL_USER_GROUP.format(url=self.baseurl,realm=realm,id=user_id,group_id=group_id) 
            return open_url(user_group_url, method='PUT', headers=self.restheaders)
        except Exception ,e :
            self.module.fail_json(msg='Could not add user %s in group %s in realm %s: %s'
                                      % (user_id, group_id, realm, str(e)))

    def remove_user_from_group(self, user_id, group_id, realm='master'):
        """
        Remove a user from a group for a user.
        :param user_id: User ID
        :param group_id: Group Id to add the user to.
        :param realm: Realm
        :return: HTTP response
        """
        try:
            user_group_url = URL_USER_GROUP.format(url=self.baseurl,realm=realm,id=user_id,group_id=group_id) 
            return open_url(user_group_url, method='DETETE', headers=self.restheaders)
        except Exception ,e :
            self.module.fail_json(msg='Could not remove user %s from group %s in realm %s: %s'
                                      % (user_id, group_id, realm, str(e)))
            
    def assing_roles_to_user(self, user_id, userRealmRoles, userClientRoles, realm='master'):
        """
        Assign roles to a user.
        :param user_id: user ID to whom assign roles.
        :param userRealmRoles: Realm roles to assign to user.
        :param userClientRoles: Client roles to assign to user.
        :param realm: Realm
        :return: True is user's role have changed, False otherwise.
        """
        try:
            # Get the new created user realm roles
            newUserRealmRoles = self.get_user_realm_roles(user_id=user_id,realm=realm)
            # Get the new created user client roles
            newUserClientRoles =  self.get_user_client_roles(user_id=user_id, realm=realm)

            changed = False
            # Assign Realm Roles
            realmRolesRepresentation = []
            # Get all realm roles
            allRealmRoles = self.get_realm_roles(realm=realm)
            for realmRole in userRealmRoles:
                # Look for existing role into user representation
                if not realmRole in newUserRealmRoles:
                    roleid = None
                    # Find the role id
                    for role in allRealmRoles:
                        if role["name"] == realmRole:
                            roleid = role["id"]
                            break
                    if roleid is not None:
                        realmRoleRepresentation = {}
                        realmRoleRepresentation["id"] = roleid
                        realmRoleRepresentation["name"] = realmRole
                        realmRolesRepresentation.append(realmRoleRepresentation)
            if len(realmRolesRepresentation) > 0 :
                # Assign Role
                self.update_user_realm_roles(user_id=user_id, realmRolesRepresentation=realmRolesRepresentation, realm=realm)
                changed = True
            # Assign clients roles if they need changes           
            if not isDictEquals(userClientRoles, newUserClientRoles):
                for clientToAssingRole in userClientRoles:
                    # Get the client roles
                    client_id = self.get_client_by_clientid(client_id=clientToAssingRole["clientId"], realm=realm)['id']
                    clientRoles = self.get_client_roles(client_id=client_id, realm=realm)
                    if clientRoles != {}:
                    
                        rolesToAssing = []
                        for roleToAssing in clientToAssingRole["roles"]:
                            newRole = {}
                            # Find his Id
                            for clientRole in clientRoles:
                                if clientRole["name"] == roleToAssing:
                                    newRole["id"] = clientRole["id"]
                                    newRole["name"] = roleToAssing
                                    rolesToAssing.append(newRole)
                        if len(rolesToAssing) > 0:
                            # Delete exiting client Roles
                            self.delete_user_client_roles(user_id=user_id, client_id=client_id, realm=realm)
                            # Assign Role
                            self.create_user_client_roles(user_id=user_id, client_id=client_id, rolesToAssing=rolesToAssing, realm=realm)
                            changed = True
                    
            return changed             
        except Exception ,e :
            self.module.fail_json(msg='Could not assign roles to user %s in realm %s: %s'
                                      % (user_id, realm, str(e)))

    def update_user_groups_membership(self, newUserRepresentation, realm='master'):
        """
        Update user's group membership
        :param newUserRepresentation: Representation of the user. This representation must include the ID.
        :param realm: Realm
        :return: True if group membership has been changed. False Otherwise.
        """
        changed = False
        try:
            newUserGroups = self.get_user_groups(user_id=newUserRepresentation['id'], realm=realm)
            # If group membership need to be changed
            if not isDictEquals(newUserRepresentation["groups"], newUserGroups):
                #set user groups
                if "groups" in newUserRepresentation and newUserRepresentation['groups'] is not None:
                    for userGroups in newUserRepresentation["groups"]:
                        # Get groups Available
                        groups = self.get_groups(realm=realm)
                        for group in groups:
                            if "name" in group and group["name"] == userGroups:
                                self.add_user_in_group(user_id=newUserRepresentation["id"], group_id=group["id"], realm=realm)
                                changed = True
            return changed
        except Exception ,e :
            raise e
