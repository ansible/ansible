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
import json
from urllib2 import quote as urlquote, HTTPError
from urlparse import urlparse

from ansible.errors import AnsibleError, AnsibleOptionsError
from ansible.module_utils.urls import open_url

class GalaxyAPI(object):
    ''' This class is meant to be used as a API client for an Ansible Galaxy server '''

    SUPPORTED_VERSIONS = ['v1']

    def __init__(self, galaxy, api_server):

        self.galaxy = galaxy

        try:
            urlparse(api_server, scheme='https')
        except:
            raise AnsibleError("Invalid server API url passed: %s" % api_server)

        server_version = self.get_server_api_version('%s/api/' % (api_server))
        if not server_version:
            raise AnsibleError("Could not retrieve server API version: %s" % api_server)

        if server_version in self.SUPPORTED_VERSIONS:
            self.baseurl = '%s/api/%s' % (api_server, server_version)
            self.version = server_version # for future use
            self.galaxy.display.vvvvv("Base API: %s" % self.baseurl)
        else:
            raise AnsibleError("Unsupported Galaxy server API version: %s" % server_version)

    def get_server_api_version(self, api_server):
        """
        Fetches the Galaxy API current version to ensure
        the API server is up and reachable.
        """
        #TODO: fix galaxy server which returns current_version path (/api/v1) vs actual version (v1)
        # also should set baseurl using supported_versions which has path
        return 'v1'

        try:
            data = json.load(open_url(api_server, validate_certs=self.galaxy.options.validate_certs))
            return data.get("current_version", 'v1')
        except Exception as e:
            # TODO: report error
            return None

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
                self.galaxy.display.display("- downloading role '%s', owned by %s" % (role_name, user_name))
        except:
            raise AnsibleError("- invalid role name (%s). Specify role as format: username.rolename" % role_name)

        url = '%s/roles/?owner__username=%s&name=%s' % (self.baseurl, user_name, role_name)
        self.galaxy.display.vvvv("- %s" % (url))
        try:
            data = json.load(open_url(url, validate_certs=self.galaxy.options.validate_certs))
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
            data = json.load(open_url(url, validate_certs=self.galaxy.options.validate_certs))
            results = data['results']
            done = (data.get('next', None) == None)
            while not done:
                url = '%s%s' % (self.baseurl, data['next'])
                self.galaxy.display.display(url)
                data = json.load(open_url(url, validate_certs=self.galaxy.options.validate_certs))
                results += data['results']
                done = (data.get('next', None) == None)
            return results
        except:
            return None

    def get_list(self, what):
        """
        Fetch the list of items specified.
        """

        try:
            url = '%s/%s/?page_size' % (self.baseurl, what)
            data = json.load(open_url(url, validate_certs=self.galaxy.options.validate_certs))
            if "results" in data:
                results = data['results']
            else:
                results = data
            done = True
            if "next" in data:
                done = (data.get('next', None) == None)
            while not done:
                url = '%s%s' % (self.baseurl, data['next'])
                self.galaxy.display.display(url)
                data = json.load(open_url(url, validate_certs=self.galaxy.options.validate_certs))
                results += data['results']
                done = (data.get('next', None) == None)
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

        self.galaxy.display.debug("Executing query: %s" % search_url)
        try:
            data = json.load(open_url(search_url, validate_certs=self.galaxy.options.validate_certs))
        except HTTPError as e:
            raise AnsibleError("Unsuccessful request to server: %s" % str(e))

        return data
