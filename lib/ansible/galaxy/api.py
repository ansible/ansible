# (C) 2013, James Cammarata <jcammarata@ansible.com>
# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import base64
import json
import os
import tarfile
import uuid

from ansible import context
from ansible.errors import AnsibleError
from ansible.module_utils.six import string_types
from ansible.module_utils.six.moves.urllib.error import HTTPError
from ansible.module_utils.six.moves.urllib.parse import quote as urlquote, urlencode
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.module_utils.urls import open_url
from ansible.utils.display import Display
from ansible.utils.hashing import secure_hash_s

display = Display()


def g_connect(versions):
    """ Wrapper to lazily initialize connection info to galaxy and verify API version available. """
    def decorator(method):
        def wrapped(self, *args, **kwargs):
            if not self.initialized:
                display.vvvv("Initial connection to galaxy_server: %s" % self.api_server)

                # Determine the type of Galaxy server we are talking to. First try it unauthenticated then with Bearer
                # auth for Automation Hub.
                n_url = _urljoin(self.api_server, 'api')
                error_context_msg = 'Error when finding available api versions from %s (%s)' % (self.name, n_url)

                try:
                    data = self._call_galaxy(n_url, method='GET', error_context_msg=error_context_msg)
                except GalaxyError as e:
                    if e.http_code != 401:
                        raise

                    # Assume this is v3 (Automation Hub) and auth is required
                    headers = {}
                    self._add_auth_token(headers, n_url, token_type='Bearer', required=True)
                    data = self._call_galaxy(n_url, headers=headers, method='GET', error_context_msg=error_context_msg)

                # Default to only supporting v1, if only v1 is returned we also assume that v2 is available even though
                # it isn't returned in the available_versions dict.
                available_versions = data.get('available_versions', {'v1': '/api/v1'})
                if list(available_versions.keys()) == ['v1']:
                    available_versions['v2'] = '/api/v2'

                self.available_api_versions = available_versions
                display.vvvv("Found API version '%s' with Galaxy server %s (%s)"
                             % (', '.join(available_versions.keys()), self.name, self.api_server))

                self.initialized = True

            # Verify that the API versions the function works with are available on the server specified.
            available_versions = set(self.available_api_versions.keys())
            common_versions = set(versions).intersection(available_versions)
            if not common_versions:
                raise AnsibleError("Galaxy action %s requires API versions '%s' but only '%s' are available on %s %s"
                                   % (method.__name__, ", ".join(versions), ", ".join(available_versions),
                                      self.name, self.api_server))

            return method(self, *args, **kwargs)
        return wrapped
    return decorator


def _urljoin(*args):
    return '/'.join(to_native(a, errors='surrogate_or_strict').strip('/') for a in args + ('',) if a)


class GalaxyError(AnsibleError):
    """ Error for bad Galaxy server responses. """

    def __init__(self, http_error, message):
        super(GalaxyError, self).__init__(message)
        self.http_code = http_error.code
        self.url = http_error.url

        try:
            http_msg = to_text(http_error.read())
            err_info = json.loads(http_msg)
        except (AttributeError, ValueError):
            err_info = {}

        url_split = http_error.url.split('/')
        if 'v2' in url_split:
            galaxy_msg = err_info.get('message', 'Unknown error returned by Galaxy server.')
            code = err_info.get('code', 'Unknown')
            full_error_msg = "%s (HTTP Code: %d, Message: %s Code: %s)" % (message, self.http_code, galaxy_msg, code)
        elif 'v3' in url_split:
            errors = err_info.get('errors', [])
            if not errors:
                errors = [{}]  # Defaults are set below, we just need to make sure 1 error is present.

            message_lines = []
            for error in errors:
                error_msg = error.get('detail') or error.get('title') or 'Unknown error returned by Galaxy server.'
                error_code = error.get('code') or 'Unknown'
                message_line = "(HTTP Code: %d, Message: %s Code: %s)" % (self.http_code, error_msg, error_code)
                message_lines.append(message_line)

            full_error_msg = "%s %s" % (message, ', '.join(message_lines))
        else:
            # v1 and unknown API endpoints
            galaxy_msg = err_info.get('default', 'Unknown error returned by Galaxy server.')
            full_error_msg = "%s (HTTP Code: %d, Message: %s)" % (message, self.http_code, galaxy_msg)

        self.message = to_native(full_error_msg)


class GalaxyAPI(object):
    ''' This class is meant to be used as a API client for an Ansible Galaxy server '''

    def __init__(self, galaxy, name, url, username=None, password=None, token=None):
        self.galaxy = galaxy
        self.name = name
        self.username = username
        self.password = password
        self.token = token
        self.api_server = url
        self.validate_certs = not context.CLIARGS['ignore_certs']
        self.initialized = False
        self.available_api_versions = {}

        display.debug('Validate TLS certificates for %s: %s' % (self.api_server, self.validate_certs))

    def _call_galaxy(self, url, args=None, headers=None, method=None, auth_required=False, error_context_msg=None):
        headers = headers or {}
        self._add_auth_token(headers, url, required=auth_required)

        try:
            display.vvvv("Calling Galaxy at %s" % url)
            resp = open_url(url, data=args, validate_certs=self.validate_certs, headers=headers, method=method,
                            timeout=20, unredirected_headers=['Authorization'])
        except HTTPError as e:
            raise GalaxyError(e, error_context_msg)
        except Exception as e:
            raise AnsibleError("Unknown error when attempting to call Galaxy at '%s': %s" % (url, to_native(e)))

        resp_data = to_text(resp.read(), errors='surrogate_or_strict')
        try:
            data = json.loads(resp_data)
        except ValueError as e:
            raise AnsibleError("Failed to parse Galaxy response from '%s' as JSON:\n%s"
                               % (resp.url, to_native(resp_data)))

        return data

    def _add_auth_token(self, headers, url, token_type=None, required=False):
        # Don't add the auth token if one is already present
        if 'Authorization' in headers:
            return

        token = self.token.get() if self.token else None

        # 'Token' for v2 api, 'Bearer' for v3 but still allow someone to override the token if necessary.
        is_v3 = 'v3' in url.split('/')
        token_type = token_type or ('Bearer' if is_v3 else 'Token')

        if token:
            headers['Authorization'] = '%s %s' % (token_type, token)
        elif self.username:
            token = "%s:%s" % (to_text(self.username, errors='surrogate_or_strict'),
                               to_text(self.password, errors='surrogate_or_strict', nonstring='passthru') or '')
            b64_val = base64.b64encode(to_bytes(token, encoding='utf-8', errors='surrogate_or_strict'))
            headers['Authorization'] = 'Basic %s' % to_text(b64_val)
        elif required:
            raise AnsibleError("No access token or username set. A token can be set with --api-key, with "
                               "'ansible-galaxy login', or set in ansible.cfg.")

    @g_connect(['v1'])
    def authenticate(self, github_token):
        """
        Retrieve an authentication token
        """
        url = _urljoin(self.api_server, self.available_api_versions['v1'], "tokens")
        args = urlencode({"github_token": github_token})
        resp = open_url(url, data=args, validate_certs=self.validate_certs, method="POST")
        data = json.loads(to_text(resp.read(), errors='surrogate_or_strict'))
        return data

    @g_connect(['v1'])
    def create_import_task(self, github_user, github_repo, reference=None, role_name=None):
        """
        Post an import request
        """
        url = _urljoin(self.api_server, self.available_api_versions['v1'], "imports")
        args = {
            "github_user": github_user,
            "github_repo": github_repo,
            "github_reference": reference if reference else ""
        }
        if role_name:
            args['alternate_role_name'] = role_name
        elif github_repo.startswith('ansible-role'):
            args['alternate_role_name'] = github_repo[len('ansible-role') + 1:]
        data = self._call_galaxy(url, args=urlencode(args), method="POST")
        if data.get('results', None):
            return data['results']
        return data

    @g_connect(['v1'])
    def get_import_task(self, task_id=None, github_user=None, github_repo=None):
        """
        Check the status of an import task.
        """
        url = _urljoin(self.api_server, self.available_api_versions['v1'], "imports")
        if task_id is not None:
            url = "%s?id=%d" % (url, task_id)
        elif github_user is not None and github_repo is not None:
            url = "%s?github_user=%s&github_repo=%s" % (url, github_user, github_repo)
        else:
            raise AnsibleError("Expected task_id or github_user and github_repo")

        data = self._call_galaxy(url)
        return data['results']

    @g_connect(['v1'])
    def lookup_role_by_name(self, role_name, notify=True):
        """
        Find a role by name.
        """
        role_name = to_text(urlquote(to_bytes(role_name)))

        try:
            parts = role_name.split(".")
            user_name = ".".join(parts[0:-1])
            role_name = parts[-1]
            if notify:
                display.display("- downloading role '%s', owned by %s" % (role_name, user_name))
        except Exception:
            raise AnsibleError("Invalid role name (%s). Specify role as format: username.rolename" % role_name)

        url = _urljoin(self.api_server, self.available_api_versions['v1'], "roles",
                       "?owner__username=%s&name=%s" % (user_name, role_name))[:-1]
        data = self._call_galaxy(url)
        if len(data["results"]) != 0:
            return data["results"][0]
        return None

    @g_connect(['v1'])
    def fetch_role_related(self, related, role_id):
        """
        Fetch the list of related items for the given role.
        The url comes from the 'related' field of the role.
        """

        results = []
        try:
            url = _urljoin(self.api_server, self.available_api_versions['v1'], "roles", role_id, related,
                           "?page_size=50")[:-1]
            data = self._call_galaxy(url)
            results = data['results']
            done = (data.get('next_link', None) is None)
            while not done:
                url = _urljoin(self.api_server, data['next_link'])
                data = self._call_galaxy(url)
                results += data['results']
                done = (data.get('next_link', None) is None)
        except Exception as e:
            display.vvvv("Unable to retrive role (id=%s) data (%s), but this is not fatal so we continue: %s" % (role_id, related, to_text(e)))
        return results

    @g_connect(['v1'])
    def get_list(self, what):
        """
        Fetch the list of items specified.
        """
        try:
            url = _urljoin(self.api_server, self.available_api_versions['v1'], what, "?page_size")[:-1]
            data = self._call_galaxy(url)
            if "results" in data:
                results = data['results']
            else:
                results = data
            done = True
            if "next" in data:
                done = (data.get('next_link', None) is None)
            while not done:
                url = _urljoin(self.api_server, data['next_link'])
                data = self._call_galaxy(url)
                results += data['results']
                done = (data.get('next_link', None) is None)
            return results
        except Exception as error:
            raise AnsibleError("Failed to download the %s list: %s" % (what, to_native(error)))

    @g_connect(['v1'])
    def search_roles(self, search, **kwargs):

        search_url = _urljoin(self.api_server, self.available_api_versions['v1'], "search", "roles", "?")[:-1]

        if search:
            search_url += '&autocomplete=' + to_text(urlquote(to_bytes(search)))

        tags = kwargs.get('tags', None)
        platforms = kwargs.get('platforms', None)
        page_size = kwargs.get('page_size', None)
        author = kwargs.get('author', None)

        if tags and isinstance(tags, string_types):
            tags = tags.split(',')
            search_url += '&tags_autocomplete=' + '+'.join(tags)

        if platforms and isinstance(platforms, string_types):
            platforms = platforms.split(',')
            search_url += '&platforms_autocomplete=' + '+'.join(platforms)

        if page_size:
            search_url += '&page_size=%s' % page_size

        if author:
            search_url += '&username_autocomplete=%s' % author

        data = self._call_galaxy(search_url)
        return data

    @g_connect(['v1'])
    def add_secret(self, source, github_user, github_repo, secret):
        url = _urljoin(self.api_server, self.available_api_versions['v1'], "notification_secrets")
        args = urlencode({
            "source": source,
            "github_user": github_user,
            "github_repo": github_repo,
            "secret": secret
        })
        data = self._call_galaxy(url, args=args, method="POST")
        return data

    @g_connect(['v1'])
    def list_secrets(self):
        url = _urljoin(self.api_server, self.available_api_versions['v1'], "notification_secrets")
        data = self._call_galaxy(url, auth_required=True)
        return data

    @g_connect(['v1'])
    def remove_secret(self, secret_id):
        url = _urljoin(self.api_server, self.available_api_versions['v1'], "notification_secrets", secret_id)
        data = self._call_galaxy(url, auth_required=True, method='DELETE')
        return data

    @g_connect(['v1'])
    def delete_role(self, github_user, github_repo):
        url = _urljoin(self.api_server, self.available_api_versions['v1'], "removerole",
                       "?github_user=%s&github_repo=%s" % (github_user, github_repo))[:-1]
        data = self._call_galaxy(url, auth_required=True, method='DELETE')
        return data

    # Collection APIs #

    @g_connect(['v2', 'v3'])
    def publish_collection(self, collection_path):
        """
        Publishes a collection to a Galaxy server and returns the import task URI.

        :param collection_path: The path to the collection tarball to publish.
        :return: The import task URI that contains the import results.
        """
        display.display("Publishing collection artifact '%s' to %s %s" % (collection_path, self.name, self.api_server))

        b_collection_path = to_bytes(collection_path, errors='surrogate_or_strict')
        if not os.path.exists(b_collection_path):
            raise AnsibleError("The collection path specified '%s' does not exist." % to_native(collection_path))
        elif not tarfile.is_tarfile(b_collection_path):
            raise AnsibleError("The collection path specified '%s' is not a tarball, use 'ansible-galaxy collection "
                               "build' to create a proper release artifact." % to_native(collection_path))

        with open(b_collection_path, 'rb') as collection_tar:
            data = collection_tar.read()

        boundary = '--------------------------%s' % uuid.uuid4().hex
        b_file_name = os.path.basename(b_collection_path)
        part_boundary = b"--" + to_bytes(boundary, errors='surrogate_or_strict')

        form = [
            part_boundary,
            b"Content-Disposition: form-data; name=\"sha256\"",
            to_bytes(secure_hash_s(data), errors='surrogate_or_strict'),
            part_boundary,
            b"Content-Disposition: file; name=\"file\"; filename=\"%s\"" % b_file_name,
            b"Content-Type: application/octet-stream",
            b"",
            data,
            b"%s--" % part_boundary,
        ]
        data = b"\r\n".join(form)

        headers = {
            'Content-type': 'multipart/form-data; boundary=%s' % boundary,
            'Content-length': len(data),
        }

        if 'v3' in self.available_api_versions:
            n_url = _urljoin(self.api_server, self.available_api_versions['v3'], 'artifacts', 'collections')
        else:
            n_url = _urljoin(self.api_server, self.available_api_versions['v2'], 'collections')

        resp = self._call_galaxy(n_url, args=data, headers=headers, method='POST', auth_required=True,
                                 error_context_msg='Error when publishing collection to %s (%s)'
                                                   % (self.name, self.api_server))
        return resp['task']

    @g_connect(['v2', 'v3'])
    def get_collection_information(self, namespace, name, version=None):
        """
        Gets the collection information from the Galaxy server.

        :param namespace: The collection namespace.
        :param name: The collection name.
        :param version: Optional version of the collection to get the information for.
        :return: A dict containing information about the collection specified.
        """
        api_path = self.available_api_versions.get('v3', self.available_api_versions['v2'])
        url_paths = [self.api_server, api_path, 'collections', namespace, name]
        if version is not None:
            url_paths += ['versions', version]

        n_collection_url = _urljoin(*url_paths)
        error_context_msg = 'Error when getting collection information for %s.%s:%s from %s (%s)' \
                            % (namespace, name, version, self.name, self.api_server)
        return self._call_galaxy(n_collection_url, error_context_msg=error_context_msg)

    @g_connect(['v2', 'v3'])
    def get_collection_versions(self, namespace, name):
        """
        Gets a list of available versions for a collection on a Galaxy server.

        :param namespace: The collection namespace.
        :param name: The collection name.
        :return: A list of versions that are available.
        """
        if 'v3' in self.available_api_versions:
            api_path = self.available_api_versions['v3']
            results_key = 'data'
            pagination_path = ['links', 'next']
        else:
            api_path = self.available_api_versions['v2']
            results_key = 'results'
            pagination_path = ['next']

        n_url = _urljoin(self.api_server, api_path, 'collections', namespace, name, 'versions')

        error_context_msg = 'Error when getting available collection versions for %s.%s from %s (%s)' \
                            % (namespace, name, self.name, self.api_server)
        data = self._call_galaxy(n_url, error_context_msg=error_context_msg)

        versions = []
        while True:
            versions += [v['version'] for v in data[results_key]]

            next_link = data
            for path in pagination_path:
                next_link = next_link.get(path, {})

            if not next_link:
                break

            data = self._call_galaxy(to_native(next_link, errors='surrogate_or_strict'),
                                     error_context_msg=error_context_msg)

        return versions
