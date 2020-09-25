# (C) 2013, James Cammarata <jcammarata@ansible.com>
# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import datetime
import hashlib
import json
import os
import stat
import tarfile
import time
import threading

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.galaxy.user_agent import user_agent
from ansible.module_utils.six import string_types
from ansible.module_utils.six.moves.urllib.error import HTTPError
from ansible.module_utils.six.moves.urllib.parse import quote as urlquote, urlencode, urlparse
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.module_utils.urls import open_url, prepare_multipart
from ansible.utils.display import Display
from ansible.utils.hashing import secure_hash_s
from ansible.utils.path import makedirs_safe

try:
    from urllib.parse import urlparse
except ImportError:
    # Python 2
    from urlparse import urlparse

display = Display()
_CACHE_LOCK = threading.Lock()


def g_connect(versions):
    """
    Wrapper to lazily initialize connection info to Galaxy and verify the API versions required are available on the
    endpoint.

    :param versions: A list of API versions that the function supports.
    """
    def decorator(method):
        def wrapped(self, *args, **kwargs):
            if not self._available_api_versions:
                display.vvvv("Initial connection to galaxy_server: %s" % self.api_server)

                # Determine the type of Galaxy server we are talking to. First try it unauthenticated then with Bearer
                # auth for Automation Hub.
                n_url = self.api_server
                error_context_msg = 'Error when finding available api versions from %s (%s)' % (self.name, n_url)

                if self.api_server == 'https://galaxy.ansible.com' or self.api_server == 'https://galaxy.ansible.com/':
                    n_url = 'https://galaxy.ansible.com/api/'

                try:
                    data = self._call_galaxy(n_url, method='GET', error_context_msg=error_context_msg, cache=True)
                except (AnsibleError, GalaxyError, ValueError, KeyError) as err:
                    # Either the URL doesnt exist, or other error. Or the URL exists, but isn't a galaxy API
                    # root (not JSON, no 'available_versions') so try appending '/api/'
                    if n_url.endswith('/api') or n_url.endswith('/api/'):
                        raise

                    # Let exceptions here bubble up but raise the original if this returns a 404 (/api/ wasn't found).
                    n_url = _urljoin(n_url, '/api/')
                    try:
                        data = self._call_galaxy(n_url, method='GET', error_context_msg=error_context_msg, cache=True)
                    except GalaxyError as new_err:
                        if new_err.http_code == 404:
                            raise err
                        raise

                if 'available_versions' not in data:
                    raise AnsibleError("Tried to find galaxy API root at %s but no 'available_versions' are available "
                                       "on %s" % (n_url, self.api_server))

                # Update api_server to point to the "real" API root, which in this case could have been the configured
                # url + '/api/' appended.
                self.api_server = n_url

                # Default to only supporting v1, if only v1 is returned we also assume that v2 is available even though
                # it isn't returned in the available_versions dict.
                available_versions = data.get('available_versions', {u'v1': u'v1/'})
                if list(available_versions.keys()) == [u'v1']:
                    available_versions[u'v2'] = u'v2/'

                self._available_api_versions = available_versions
                display.vvvv("Found API version '%s' with Galaxy server %s (%s)"
                             % (', '.join(available_versions.keys()), self.name, self.api_server))

            # Verify that the API versions the function works with are available on the server specified.
            available_versions = set(self._available_api_versions.keys())
            common_versions = set(versions).intersection(available_versions)
            if not common_versions:
                raise AnsibleError("Galaxy action %s requires API versions '%s' but only '%s' are available on %s %s"
                                   % (method.__name__, ", ".join(versions), ", ".join(available_versions),
                                      self.name, self.api_server))

            return method(self, *args, **kwargs)
        return wrapped
    return decorator


def _load_cache(b_cache_path, clear=False):
    """ Loads the cache file requested if possible. The file must not be world writable. """
    cache_version = 1

    with _CACHE_LOCK:
        if not os.path.isfile(b_cache_path):
            display.vvvv("Creating Galaxy API response cache file at '%s'" % to_text(b_cache_path))
            with open(b_cache_path, 'w'):
                os.chmod(b_cache_path, 0o600)

        cache_mode = os.stat(b_cache_path).st_mode
        if cache_mode & stat.S_IWOTH:
            display.warning("Galaxy cache has world writable access (%s), ignoring it as a cache source."
                            % to_text(b_cache_path))
            return

        with open(b_cache_path, mode='rb') as fd:
            json_val = to_text(fd.read(), errors='surrogate_or_strict')

        if not json_val:
            json_val = '{}'
        cache = json.loads(json_val)

        if cache.get('version', None) != cache_version:
            display.vvvv("Galaxy cache file at '%s' has an invalid version, clearing" % to_text(b_cache_path))
            cache = {'version': cache_version}

            # Set the cache after we've cleared the existing entries
            with open(b_cache_path, mode='wb') as fd:
                fd.write(to_bytes(json.dumps(cache), errors='surrogate_or_strict'))

        return cache


def _urljoin(*args):
    return '/'.join(to_native(a, errors='surrogate_or_strict').strip('/') for a in args + ('',) if a)


class GalaxyError(AnsibleError):
    """ Error for bad Galaxy server responses. """

    def __init__(self, http_error, message):
        super(GalaxyError, self).__init__(message)
        self.http_code = http_error.code
        self.url = http_error.geturl()

        try:
            http_msg = to_text(http_error.read())
            err_info = json.loads(http_msg)
        except (AttributeError, ValueError):
            err_info = {}

        url_split = self.url.split('/')
        if 'v2' in url_split:
            galaxy_msg = err_info.get('message', http_error.reason)
            code = err_info.get('code', 'Unknown')
            full_error_msg = u"%s (HTTP Code: %d, Message: %s Code: %s)" % (message, self.http_code, galaxy_msg, code)
        elif 'v3' in url_split:
            errors = err_info.get('errors', [])
            if not errors:
                errors = [{}]  # Defaults are set below, we just need to make sure 1 error is present.

            message_lines = []
            for error in errors:
                error_msg = error.get('detail') or error.get('title') or http_error.reason
                error_code = error.get('code') or 'Unknown'
                message_line = u"(HTTP Code: %d, Message: %s Code: %s)" % (self.http_code, error_msg, error_code)
                message_lines.append(message_line)

            full_error_msg = "%s %s" % (message, ', '.join(message_lines))
        else:
            # v1 and unknown API endpoints
            galaxy_msg = err_info.get('default', http_error.reason)
            full_error_msg = u"%s (HTTP Code: %d, Message: %s)" % (message, self.http_code, galaxy_msg)

        self.message = to_native(full_error_msg)


class CollectionVersionMetadata:

    def __init__(self, namespace, name, version, download_url, artifact_sha256, dependencies):
        """
        Contains common information about a collection on a Galaxy server to smooth through API differences for
        Collection and define a standard meta info for a collection.

        :param namespace: The namespace name.
        :param name: The collection name.
        :param version: The version that the metadata refers to.
        :param download_url: The URL to download the collection.
        :param artifact_sha256: The SHA256 of the collection artifact for later verification.
        :param dependencies: A dict of dependencies of the collection.
        """
        self.namespace = namespace
        self.name = name
        self.version = version
        self.download_url = download_url
        self.artifact_sha256 = artifact_sha256
        self.dependencies = dependencies


class GalaxyAPI:
    """ This class is meant to be used as a API client for an Ansible Galaxy server """

    def __init__(self, galaxy, name, url, username=None, password=None, token=None, validate_certs=True,
                 available_api_versions=None, clear_response_cache=False, no_cache=True):
        self.galaxy = galaxy
        self.name = name
        self.username = username
        self.password = password
        self.token = token
        self.api_server = url
        self.validate_certs = validate_certs
        self._available_api_versions = available_api_versions or {}

        b_cache_dir = to_bytes(C.config.get_config_value('GALAXY_CACHE_DIR'), errors='surrogate_or_strict')
        makedirs_safe(b_cache_dir, mode=0o700)
        self._b_cache_path = os.path.join(b_cache_dir, b'api.json')

        if clear_response_cache:
            with _CACHE_LOCK:
                if os.path.exists(self._b_cache_path):
                    display.vvvv("Clearing cache file (%s)" % to_text(self._b_cache_path))
                    os.unlink(self._b_cache_path)

        self._cache = None
        if not no_cache:
            self._cache = _load_cache(self._b_cache_path)

        display.debug('Validate TLS certificates for %s: %s' % (self.api_server, self.validate_certs))

    @property
    @g_connect(['v1', 'v2', 'v3'])
    def available_api_versions(self):
        # Calling g_connect will populate self._available_api_versions
        return self._available_api_versions

    def _call_galaxy(self, url, args=None, headers=None, method=None, auth_required=False, error_context_msg=None,
                     cache=False):
        url_info = urlparse(url)
        if cache and self._cache:
            server_cache = self._cache.setdefault(url_info.netloc, {})
            iso_datetime_format = '%Y-%m-%dT%H:%M:%SZ'

            valid = False
            if url_info.path in server_cache:
                expires = datetime.datetime.strptime(server_cache[url_info.path]['expires'], iso_datetime_format)
                valid = datetime.datetime.utcnow() < expires

            if valid and not url_info.query:
                # Got a hit on the cache and we aren't getting a paginated response
                path_cache = server_cache[url_info.path]
                if path_cache.get('paginated'):
                    if '/v3/' in url_info.path:
                        res = {'links': {'next': None}}
                    else:
                        res = {'next': None}

                    # Technically some v3 paginated APIs return in 'data' but the caller checks the keys for this so
                    # always returning the cache under results is fine.
                    res['results'] = []
                    for result in path_cache['results']:
                        res['results'].append(result)

                else:
                    res = path_cache['results']

                return res

            elif not url_info.query:
                # The cache entry had expired or does not exist, start a new blank entry to be filled later.
                expires = datetime.datetime.utcnow()
                expires += datetime.timedelta(days=1)
                server_cache[url_info.path] = {
                    'expires': expires.strftime(iso_datetime_format),
                    'paginated': False,
                }

        headers = headers or {}
        self._add_auth_token(headers, url, required=auth_required)

        try:
            display.vvvv("Calling Galaxy at %s" % url)
            resp = open_url(to_native(url), data=args, validate_certs=self.validate_certs, headers=headers,
                            method=method, timeout=20, http_agent=user_agent(), follow_redirects='safe')
        except HTTPError as e:
            raise GalaxyError(e, error_context_msg)
        except Exception as e:
            raise AnsibleError("Unknown error when attempting to call Galaxy at '%s': %s" % (url, to_native(e)))

        resp_data = to_text(resp.read(), errors='surrogate_or_strict')
        try:
            data = json.loads(resp_data)
        except ValueError:
            raise AnsibleError("Failed to parse Galaxy response from '%s' as JSON:\n%s"
                               % (resp.url, to_native(resp_data)))

        if cache and self._cache:
            path_cache = self._cache[url_info.netloc][url_info.path]

            # v3 can return data or results for paginated results. Scan the result so we can determine what to cache.
            paginated_key = None
            for key in ['data', 'resulsts']:
                if key in data:
                    paginated_key = key
                    break

            if paginated_key:
                path_cache['paginated'] = True
                results = path_cache.setdefault('results', [])
                for result in data[paginated_key]:
                    results.append(result)

            else:
                path_cache['results'] = data

            self._set_cache()

        return data

    def _add_auth_token(self, headers, url, token_type=None, required=False):
        # Don't add the auth token if one is already present
        if 'Authorization' in headers:
            return

        if not self.token and required:
            raise AnsibleError("No access token or username set. A token can be set with --api-key "
                               "or at {0}.".format(to_native(C.GALAXY_TOKEN_PATH)))

        if self.token:
            headers.update(self.token.headers())

    def _set_cache(self):
        with _CACHE_LOCK:
            with open(self._b_cache_path, mode='wb') as fd:
                fd.write(to_bytes(json.dumps(self._cache), errors='surrogate_or_strict'))

    @g_connect(['v1'])
    def authenticate(self, github_token):
        """
        Retrieve an authentication token
        """
        url = _urljoin(self.api_server, self.available_api_versions['v1'], "tokens") + '/'
        args = urlencode({"github_token": github_token})
        resp = open_url(url, data=args, validate_certs=self.validate_certs, method="POST", http_agent=user_agent())
        data = json.loads(to_text(resp.read(), errors='surrogate_or_strict'))
        return data

    @g_connect(['v1'])
    def create_import_task(self, github_user, github_repo, reference=None, role_name=None):
        """
        Post an import request
        """
        url = _urljoin(self.api_server, self.available_api_versions['v1'], "imports") + '/'
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
                       "?owner__username=%s&name=%s" % (user_name, role_name))
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
                           "?page_size=50")
            data = self._call_galaxy(url)
            results = data['results']
            done = (data.get('next_link', None) is None)

            # https://github.com/ansible/ansible/issues/64355
            # api_server contains part of the API path but next_link includes the /api part so strip it out.
            url_info = urlparse(self.api_server)
            base_url = "%s://%s/" % (url_info.scheme, url_info.netloc)

            while not done:
                url = _urljoin(base_url, data['next_link'])
                data = self._call_galaxy(url)
                results += data['results']
                done = (data.get('next_link', None) is None)
        except Exception as e:
            display.warning("Unable to retrieve role (id=%s) data (%s), but this is not fatal so we continue: %s"
                            % (role_id, related, to_text(e)))
        return results

    @g_connect(['v1'])
    def get_list(self, what):
        """
        Fetch the list of items specified.
        """
        try:
            url = _urljoin(self.api_server, self.available_api_versions['v1'], what, "?page_size")
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

        search_url = _urljoin(self.api_server, self.available_api_versions['v1'], "search", "roles", "?")

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
        url = _urljoin(self.api_server, self.available_api_versions['v1'], "notification_secrets") + '/'
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
        url = _urljoin(self.api_server, self.available_api_versions['v1'], "notification_secrets", secret_id) + '/'
        data = self._call_galaxy(url, auth_required=True, method='DELETE')
        return data

    @g_connect(['v1'])
    def delete_role(self, github_user, github_repo):
        url = _urljoin(self.api_server, self.available_api_versions['v1'], "removerole",
                       "?github_user=%s&github_repo=%s" % (github_user, github_repo))
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
            sha256 = secure_hash_s(collection_tar.read(), hash_func=hashlib.sha256)

        content_type, b_form_data = prepare_multipart(
            {
                'sha256': sha256,
                'file': {
                    'filename': b_collection_path,
                    'mime_type': 'application/octet-stream',
                },
            }
        )

        headers = {
            'Content-type': content_type,
            'Content-length': len(b_form_data),
        }

        if 'v3' in self.available_api_versions:
            n_url = _urljoin(self.api_server, self.available_api_versions['v3'], 'artifacts', 'collections') + '/'
        else:
            n_url = _urljoin(self.api_server, self.available_api_versions['v2'], 'collections') + '/'

        resp = self._call_galaxy(n_url, args=b_form_data, headers=headers, method='POST', auth_required=True,
                                 error_context_msg='Error when publishing collection to %s (%s)'
                                                   % (self.name, self.api_server))

        return resp['task']

    @g_connect(['v2', 'v3'])
    def wait_import_task(self, task_id, timeout=0):
        """
        Waits until the import process on the Galaxy server has completed or the timeout is reached.

        :param task_id: The id of the import task to wait for. This can be parsed out of the return
            value for GalaxyAPI.publish_collection.
        :param timeout: The timeout in seconds, 0 is no timeout.
        """
        state = 'waiting'
        data = None

        # Construct the appropriate URL per version
        if 'v3' in self.available_api_versions:
            full_url = _urljoin(self.api_server, self.available_api_versions['v3'],
                                'imports/collections', task_id, '/')
        else:
            full_url = _urljoin(self.api_server, self.available_api_versions['v2'],
                                'collection-imports', task_id, '/')

        display.display("Waiting until Galaxy import task %s has completed" % full_url)
        start = time.time()
        wait = 2

        while timeout == 0 or (time.time() - start) < timeout:
            try:
                data = self._call_galaxy(full_url, method='GET', auth_required=True,
                                         error_context_msg='Error when getting import task results at %s' % full_url)
            except GalaxyError as e:
                if e.http_code != 404:
                    raise
                # The import job may not have started, and as such, the task url may not yet exist
                display.vvv('Galaxy import process has not started, wait %s seconds before trying again' % wait)
                time.sleep(wait)
                continue

            state = data.get('state', 'waiting')

            if data.get('finished_at', None):
                break

            display.vvv('Galaxy import process has a status of %s, wait %d seconds before trying again'
                        % (state, wait))
            time.sleep(wait)

            # poor man's exponential backoff algo so we don't flood the Galaxy API, cap at 30 seconds.
            wait = min(30, wait * 1.5)
        if state == 'waiting':
            raise AnsibleError("Timeout while waiting for the Galaxy import process to finish, check progress at '%s'"
                               % to_native(full_url))

        for message in data.get('messages', []):
            level = message['level']
            if level == 'error':
                display.error("Galaxy import error message: %s" % message['message'])
            elif level == 'warning':
                display.warning("Galaxy import warning message: %s" % message['message'])
            else:
                display.vvv("Galaxy import message: %s - %s" % (level, message['message']))

        if state == 'failed':
            code = to_native(data['error'].get('code', 'UNKNOWN'))
            description = to_native(
                data['error'].get('description', "Unknown error, see %s for more details" % full_url))
            raise AnsibleError("Galaxy import process failed: %s (Code: %s)" % (description, code))

    @g_connect(['v2', 'v3'])
    def get_collection_version_metadata(self, namespace, name, version):
        """
        Gets the collection information from the Galaxy server about a specific Collection version.

        :param namespace: The collection namespace.
        :param name: The collection name.
        :param version: Version of the collection to get the information for.
        :return: CollectionVersionMetadata about the collection at the version requested.
        """
        api_path = self.available_api_versions.get('v3', self.available_api_versions.get('v2'))
        url_paths = [self.api_server, api_path, 'collections', namespace, name, 'versions', version, '/']

        n_collection_url = _urljoin(*url_paths)
        error_context_msg = 'Error when getting collection version metadata for %s.%s:%s from %s (%s)' \
                            % (namespace, name, version, self.name, self.api_server)
        data = self._call_galaxy(n_collection_url, error_context_msg=error_context_msg, cache=True)

        return CollectionVersionMetadata(data['namespace']['name'], data['collection']['name'], data['version'],
                                         data['download_url'], data['artifact']['sha256'],
                                         data['metadata']['dependencies'])

    @g_connect(['v2', 'v3'])
    def get_collection_versions(self, namespace, name):
        """
        Gets a list of available versions for a collection on a Galaxy server.

        :param namespace: The collection namespace.
        :param name: The collection name.
        :return: A list of versions that are available.
        """
        relative_link = False
        if 'v3' in self.available_api_versions:
            api_path = self.available_api_versions['v3']
            pagination_path = ['links', 'next']
            relative_link = True  # AH pagination results are relative an not an absolute URI.
        else:
            api_path = self.available_api_versions['v2']
            pagination_path = ['next']

        collection_info_url = _urljoin(self.api_server, api_path, 'collections', namespace, name, '/')
        versions_url = _urljoin(self.api_server, api_path, 'collections', namespace, name, 'versions', '/')
        versions_url_info = urlparse(versions_url)

        # We should only rely on the cache if the latest version has not changed. This may slow things down but it
        # ensures we are not waiting a day before finding any new collections that have been published.
        if self._cache:
            server_cache = self._cache.setdefault(versions_url_info.netloc, {})
            error_context_msg = 'Error when getting the latest version info for %s.%s from %s (%s)' \
                                % (namespace, name, self.name, self.api_server)
            data = self._call_galaxy(collection_info_url, error_context_msg=error_context_msg)

            latest_version = data.get('latest_version', {}).get('version')
            version_cache = self._cache.setdefault(urlparse(self.api_server).netloc, {}).setdefault('latest_versions',
                                                                                                    {})
            cached_latest_version = version_cache.get('%s.%s' % (namespace, name), None)

            if cached_latest_version != latest_version:
                version_cache['%s.%s' % (namespace, name)] = latest_version
                if versions_url_info.path in server_cache:
                    del server_cache[versions_url_info.path]

                self._set_cache()

        error_context_msg = 'Error when getting available collection versions for %s.%s from %s (%s)' \
                            % (namespace, name, self.name, self.api_server)
        data = self._call_galaxy(versions_url, error_context_msg=error_context_msg, cache=True)

        if 'data' in data:
            # v3 automation-hub is the only known API that uses `data`
            # since v3 pulp_ansible does not, we cannot rely on version
            # to indicate which key to use
            results_key = 'data'
        else:
            results_key = 'results'

        versions = []
        while True:
            versions += [v['version'] for v in data[results_key]]

            next_link = data
            for path in pagination_path:
                next_link = next_link.get(path, {})

            if not next_link:
                break
            elif relative_link:
                # TODO: This assumes the pagination result is relative to the root server. Will need to be verified
                # with someone who knows the AH API.
                next_link = versions_url.replace(versions_url_info.path, next_link)

            data = self._call_galaxy(to_native(next_link, errors='surrogate_or_strict'),
                                     error_context_msg=error_context_msg, cache=True)

        return versions
