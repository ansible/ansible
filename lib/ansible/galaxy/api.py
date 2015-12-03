#!/usr/bin/env python

########################################################################
#
# (C) 2013, James Cammarata <jcammarata@ansible.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#
########################################################################

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import urllib

from urllib2 import quote as urlquote, HTTPError
from urlparse import urlparse

from ansible.errors import AnsibleError
from ansible.module_utils.urls import open_url

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class GalaxyAPI(object):
    ''' This class is meant to be used as a API client for an Ansible Galaxy server '''

    SUPPORTED_VERSIONS = ['v1']

    def __init__(self, galaxy, config, api_server):

        self.galaxy = galaxy
        self.config = config
        
        try:
            urlparse(api_server, scheme='https')
        except:
            raise AnsibleError("Invalid server API url passed: %s" % api_server)

        self.validate_certs = True
        if self.galaxy.options.validate_certs == False:
            self.validate_certs = False
        elif config.get_key('validate_certs') == False:
            self.validate_certs = False
        display.vvv('Check for valid certs: %s' % self.validate_certs)

        server_version = self.get_server_api_version('%s/api/' % (api_server))
       
        if server_version in self.SUPPORTED_VERSIONS:
            self.baseurl = '%s/api/%s' % (api_server, server_version)
            self.version = server_version # for future use
            display.vvvvv("Base API: %s" % self.baseurl)
        else:
            raise AnsibleError("Unsupported Galaxy server API version: %s" % server_version)

    def __auth_header(self):
        token = self.config.get_key('access_token')
        if token is None:
            raise AnsibleError("No access token. You must first use login to authenticate and obtain an access token.")
        return {'Authorization': 'Token ' + token}

    def __call_galaxy(self, url, args=None, headers=None, method=None):
        if args and not headers:
            headers = self.__auth_header()
        try:
            resp = open_url(url, data=args, validate_certs=self.validate_certs, headers=headers, method=method)
            data = json.load(resp)
        except HTTPError as e:
            res = json.load(e)
            raise AnsibleError(res['detail'])
        return data

    def get_server_api_version(self, api_server):
        """
        Fetches the Galaxy API current version to ensure
        the API server is up and reachable.
        """
        try:
            data = json.load(open_url(api_server, validate_certs=self.validate_certs))
            return data['current_version']
        except Exception as e:
            raise AnsibleError("Could not retrieve server API version: %s" % api_server)
    
    def authenticate(self, github_token):
        """
        Retrieve an authentication token
        """
        url = '%s/tokens/' % self.baseurl
        args = urllib.urlencode({"github_token": github_token})
        resp = open_url(url, data=args, validate_certs=self.validate_certs, method="POST")
        data = json.load(resp)
        return data

    def create_import_task(self, github_user, github_repo, reference=None, alternate_name=None):
        """
        Post an import request
        """
        url = '%s/imports/' % self.baseurl
        args = urllib.urlencode({
            "github_user": github_user,
            "github_repo": github_repo,
            "reference": reference,
            "alternate_role_name": alternate_name
        })
        data = self.__call_galaxy(url, args=args)
        if data.get('results', None):
            return data['results']
        return data

    def get_import_task(self, task_id=None, github_user=None, github_repo=None):
        """
        Check the status of an import task. Returns only the most recent import task when
        given github_user/github_repo.
        """
        url = '%s/imports/' % self.baseurl
        if not task_id is None:
            url = "%s?id=%d" % (url,task_id)
        elif not github_user is None and not github_repo is None:
            url = "%s?github_user=%s&github_repo=%s" % (url,github_user,github_repo)
        else:
            raise AnsibleError("Expected task_id or github_user and github_repo")
        
        data = self.__call_galaxy(url)
        return data['results']

       
    def lookup_role_by_name(self, role_name, notify=True):
        """
        Find a role by name
        """
        role_name = urlquote(role_name)

        try:
            parts = role_name.split(".")
            user_name = ".".join(parts[0:-1])
            role_name = parts[-1]
            if notify:
                display.display("- downloading role '%s', owned by %s" % (role_name, user_name))
        except:
            raise AnsibleError("- invalid role name (%s). Specify role as format: username.rolename" % role_name)

        url = '%s/roles/?owner__username=%s&name=%s' % (self.baseurl, user_name, role_name)
        display.vvvv("- %s" % (url))
        try:
            data = json.load(open_url(url, validate_certs=self.validate_certs))
            if len(data["results"]) != 0:
                return data["results"][0]
        except:
            # TODO: report on connection/availability errors
            pass

        return None

    def fetch_role_related(self, related, role_id):
        """
        Fetch the list of related items for the given role.
        The url comes from the 'related' field of the role.
        """

        try:
            url = '%s/roles/%d/%s/?page_size=50' % (self.baseurl, int(role_id), related)
            data = json.load(open_url(url, validate_certs=self.validate_certs))
            results = data['results']
            done = (data.get('next', None) is None)
            while not done:
                url = '%s%s' % (self.baseurl, data['next'])
                display.display(url)
                data = json.load(open_url(url, validate_certs=self.validate_certs))
                results += data['results']
                done = (data.get('next', None) is None)
            return results
        except:
            return None

    def get_list(self, what):
        """
        Fetch the list of items specified.
        """
        try:
            url = '%s/%s/?page_size' % (self.baseurl, what)
            data = json.load(open_url(url, validate_certs=self.validate_certs))
            if "results" in data:
                results = data['results']
            else:
                results = data
            done = True
            if "next" in data:
                done = (data.get('next', None) is None)
            while not done:
                url = '%s%s' % (self.baseurl, data['next'])
                display.display(url)
                data = json.load(open_url(url, validate_certs=self.validate_certs))
                results += data['results']
                done = (data.get('next', None) is None)
            return results
        except Exception as error:
            raise AnsibleError("Failed to download the %s list: %s" % (what, str(error)))

    def search_roles(self, search, platforms=None, tags=None):

        search_url = self.baseurl + '/roles/?page=1'

        if search:
            search_url += '&search=' + urlquote(search)

        if tags is None:
            tags = []
        elif isinstance(tags, basestring):
            tags = tags.split(',')

        for tag in tags:
            search_url += '&chain__tags__name=' + urlquote(tag)

        if platforms is None:
            platforms = []
        elif isinstance(platforms, basestring):
            platforms = platforms.split(',')

        for plat in platforms:
            search_url += '&chain__platforms__name=' + urlquote(plat)

        display.debug("Executing query: %s" % search_url)

        try:
            data = json.load(open_url(search_url, validate_certs=self.validate_certs))
        except HTTPError as e:
            raise AnsibleError("Unsuccessful request to server: %s" % str(e))

        return data

    def add_secret(self, source, github_user, github_repo, secret):
        url = "%s/notification_secrets/" % self.baseurl
        args = urllib.urlencode({
            "source": source,
            "github_user": github_user,
            "github_repo": github_repo,
            "secret": secret
        })
        data = self.__call_galaxy(url, args=args)
        return data

    def list_secrets(self):
        url = "%s/notification_secrets" % self.baseurl
        data = self.__call_galaxy(url, headers=self.__auth_header())
        return data

    def remove_secret(self, secret_id):
        url = "%s/notification_secrets/%s/" % (self.baseurl, secret_id)
        data = self.__call_galaxy(url, headers=self.__auth_header(), method='DELETE')
        return data

    def delete_role(self, github_user, github_repo):
        url = "%s/removerole/?github_user=%s&github_repo=%s" % (self.baseurl,github_user,github_repo)
        data = self.__call_galaxy(url, headers=self.__auth_header(), method='DELETE')
        return data
        