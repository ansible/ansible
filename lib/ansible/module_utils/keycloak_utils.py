# -*- coding: utf-8 -*-
# Copyright (c) 2017, INSPQ <philippe.gauthier@inspq.qc.ca>
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

import requests


def isDictEquals(dict1, dict2, exclude=[]):
    '''
Fonction: isDictEquals
Description:    Cette fonction compare deux structures. Elle utilise tous les étéments de la structure
                dict1 et valide que ses éléments se trouvent dans la structure dict2.
                Ca ne veut pas dire que les deux structures sont identiques, Il peut y avoir des
                éléments dans dict2 qui ne sont pas dans dict1.
                Cette fonction est récursive et elle peut s'appeler avec des arguments qui ne sont pas
                de type dict
Arguments:
    dict1:
        type:
            dict pour l'appel de base, peut être de type dict, list, bool, int ou str pour les appels récursifs
        description:
            structure de référence.
    dict2:
        type:
            dict pour l'appel de base, peut être de type dict, list, bool, int ou str pour les appels récursifs
        description:
            structure avec laquelle comparer la structure dict1.
    exclude:
        type:
            list
        description:
            liste des clés à ne pas comparer
        valeur par défaut : liste vide
Retour:
    type:
        bool
    description:
        Retourne vrai (True) si tous les éléments de dict1 se retrouvent dans dict2
        Retourne faux (False), sinon
    '''
    try:
        if type(dict1) is list and type(dict2) is list:
            if len(dict1) == 0 and len(dict2) == 0:
                return True
            for item1 in dict1:
                found = False
                if type(item1) is list:
                    found1 = False
                    for item2 in dict2:
                        if isDictEquals(item1, item2, exclude):
                            found1 = True
                    if found1:
                        found = True
                elif type(item1) is dict:
                    found1 = False
                    for item2 in dict2:
                        if isDictEquals(item1, item2, exclude):
                            found1 = True
                    if found1:
                        found = True
                else:
                    if item1 not in dict2:
                        return False
                    else:
                        found = True
                if not found:
                    return False
            return found
        elif type(dict1) is dict and type(dict2) is dict:
            if len(dict1) == 0 and len(dict2) == 0:
                return True
            for key in dict1:
                if not (exclude and key in exclude):
                    if not isDictEquals(dict1[key], dict2[key], exclude):
                        return False
            return True
        else:
            if type(dict1) == bool and (type(dict2) == str or type(dict2) == unicode):
                return dict1 == str2bool(dict2.decode("utf-8"))
            if type(dict2) == bool and (type(dict1) == str or type(dict1) == unicode):
                return dict2 == str2bool(dict1.decode("utf-8"))
            return dict1 == dict2
    except KeyError:
        return False
    except Exception, e:
        raise e


def str2bool(value):
    if type(value) == unicode:
        return value.decode("utf-8").lower() in ("yes", "true")
    return value.lower() in ("yes", "true")


def login(url, username, password):
    '''
Fonction: login
Description:
    Cette fonction permet de s'authentifier sur le serveur Keycloak.
Arguments:
    url:
        type: str
        description:
            url de base du serveur Keycloak
    username:
        type: str
        description:
            identifiant à utiliser pour s'authentifier au serveur Keycloak
    password:
        type: str
        description:
            Mot de passe pour s'authentifier au serveur Keycloak
    '''
    # Login to Keycloak
    accessToken = ""
    body = {
            'grant_type': 'password',
            'username': username,
            'password': password,
            'client_id': 'admin-cli'
    }
    try:
        loginResponse = requests.post(url + '/auth/realms/master/protocol/openid-connect/token', data=body)
        loginData = loginResponse.json()
        accessToken = loginData['access_token']
    except requests.exceptions.RequestException, e:
        raise e
    except ValueError, e:
        raise e

    return accessToken


def realmLogin(url, realm, username, password):
    # Login to Keycloak
    accessToken = ""
    body = {
            'grant_type': 'password',
            'username': username,
            'password': password,
            'client_id': 'admin-cli'
    }
    try:
        loginResponse = requests.post(url + '/auth/realms/' + realm + '/protocol/openid-connect/token', data=body)
        loginData = loginResponse.json()
        accessToken = loginData['access_token']
    except requests.exceptions.RequestException, e:
        raise e
    except ValueError, e:
        raise e

    return accessToken


def setHeaders(accessToken):
    bearerHeader = "bearer " + accessToken
    headers = {'Authorization': bearerHeader, 'Content-type': 'application/json'}
    return headers


def loginAndSetHeaders(url, username, password):
    headers = {}
    try:
        accessToken = login(url, username, password)
        headers = setHeaders(accessToken)
    except Exception, e:
        raise e
    return headers


def realmLoginAndSetHeaders(url, realm, username, password):
    headers = {}
    try:
        accessToken = realmLogin(url, realm, username, password)
        headers = setHeaders(accessToken)
    except Exception, e:
        raise e
    return headers


def ansible2keycloakClientRoles(ansibleClientRoles):
    keycloakClientRoles = {}
    for clientRoles in ansibleClientRoles:
        keycloakClientRoles[clientRoles["clientid"]] = clientRoles["roles"]
    return keycloakClientRoles


def keycloak2ansibleClientRoles(keycloakClientRoles):
    ansibleClientRoles = []
    for client in keycloakClientRoles.keys():
        role = {}
        role["clientid"] = client
        role["roles"] = keycloakClientRoles[client]
        ansibleClientRoles.append(role)
    return ansibleClientRoles
