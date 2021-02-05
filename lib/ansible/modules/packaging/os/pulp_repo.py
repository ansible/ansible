#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Joe Adams <@sysadmind>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: pulp_repo
author: "Joe Adams (@sysadmind)"
short_description: Add or remove Pulp repos from a remote host.
description:
  - Add or remove Pulp repos from a remote host.
version_added: "2.3"
options:
  add_export_distributor:
    description:
      - Whether or not to add the export distributor to new C(rpm) repositories.
    type: bool
    default: 'no'
  feed:
    description:
      - Upstream feed URL to receive updates from.
  force_basic_auth:
    description:
      - httplib2, the library used by the M(uri) module only sends
        authentication information when a webservice responds to an initial
        request with a 401 status. Since some basic auth services do not
        properly send a 401, logins will fail. This option forces the sending of
        the Basic authentication header upon initial request.
    type: bool
    default: 'no'
  generate_sqlite:
    description:
      - Boolean flag to indicate whether sqlite files should be generated during
        a repository publish.
    required: false
    type: bool
    default: 'no'
    version_added: "2.8"
  feed_ca_cert:
    description:
      - CA certificate string used to validate the feed source SSL certificate.
        This can be the file content or the path to the file.
        The ca_cert alias will be removed in Ansible 2.14.
    type: str
    aliases: [ importer_ssl_ca_cert, ca_cert ]
  feed_client_cert:
    version_added: "2.9.2"
    description:
      - Certificate used as the client certificate when synchronizing the
        repository. This is used to communicate authentication information to
        the feed source. The value to this option must be the full path to the
        certificate. The specified file may be the certificate itself or a
        single file containing both the certificate and private key. This can be
        the file content or the path to the file.
      - If not specified the default value will come from client_cert. Which will
        change in Ansible 2.14.
    type: str
    aliases: [ importer_ssl_client_cert ]
  feed_client_key:
    version_added: "2.9.2"
    description:
      - Private key to the certificate specified in I(importer_ssl_client_cert),
        assuming it is not included in the certificate file itself. This can be
        the file content or the path to the file.
      - If not specified the default value will come from client_key. Which will
        change in Ansible 2.14.
    type: str
    aliases: [ importer_ssl_client_key ]
  name:
    description:
      - Name of the repo to add or remove. This correlates to repo-id in Pulp.
    required: true
  proxy_host:
    description:
      - Proxy url setting for the pulp repository importer. This is in the
        format scheme://host.
    required: false
    default: null
  proxy_port:
    description:
      - Proxy port setting for the pulp repository importer.
    required: false
    default: null
  proxy_username:
    description:
      - Proxy username for the pulp repository importer.
    required: false
    default: null
    version_added: "2.8"
  proxy_password:
    description:
      - Proxy password for the pulp repository importer.
    required: false
    default: null
    version_added: "2.8"
  publish_distributor:
    description:
      - Distributor to use when state is C(publish). The default is to
        publish all distributors.
  pulp_host:
    description:
      - URL of the pulp server to connect to.
    default: http://127.0.0.1
  relative_url:
    description:
      - Relative URL for the local repository.
    required: true
  repo_type:
    description:
      - Repo plugin type to use (i.e. C(rpm), C(docker)).
    default: rpm
  repoview:
    description:
      - Whether to generate repoview files for a published repository. Setting
        this to "yes" automatically activates `generate_sqlite`.
    required: false
    type: bool
    default: 'no'
    version_added: "2.8"
  serve_http:
    description:
      - Make the repo available over HTTP.
    type: bool
    default: 'no'
  serve_https:
    description:
      - Make the repo available over HTTPS.
    type: bool
    default: 'yes'
  state:
    description:
      - The repo state. A state of C(sync) will queue a sync of the repo.
        This is asynchronous but not delayed like a scheduled sync. A state of
        C(publish) will use the repository's distributor to publish the content.
    default: present
    choices: [ "present", "absent", "sync", "publish" ]
  url_password:
    description:
      - The password for use in HTTP basic authentication to the pulp API.
        If the I(url_username) parameter is not specified, the I(url_password)
        parameter will not be used.
  url_username:
    description:
      - The username for use in HTTP basic authentication to the pulp API.
  validate_certs:
    description:
      - If C(no), SSL certificates will not be validated. This should only be
        used on personally controlled sites using self-signed certificates.
    type: bool
    default: 'yes'
  wait_for_completion:
    description:
      - Wait for asynchronous tasks to complete before returning.
    type: bool
    default: 'no'
notes:
  - This module can currently only create distributors and importers on rpm
    repositories. Contributions to support other repo types are welcome.
extends_documentation_fragment:
  - url
'''

EXAMPLES = '''
- name: Create a new repo with name 'my_repo'
  pulp_repo:
    name: my_repo
    relative_url: my/repo
    state: present

- name: Create a repo with a feed and a relative URL
  pulp_repo:
    name: my_centos_updates
    repo_type: rpm
    feed: http://mirror.centos.org/centos/6/updates/x86_64/
    relative_url: centos/6/updates
    url_username: admin
    url_password: admin
    force_basic_auth: yes
    state: present

- name: Remove a repo from the pulp server
  pulp_repo:
    name: my_old_repo
    repo_type: rpm
    state: absent
'''

RETURN = '''
repo:
  description: Name of the repo that the action was performed on.
  returned: success
  type: str
  sample: my_repo
'''

import json
import os
from time import sleep

# import module snippets
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url
from ansible.module_utils.urls import url_argument_spec


class pulp_server(object):
    """
    Class to interact with a Pulp server
    """

    def __init__(self, module, pulp_host, repo_type, wait_for_completion=False):
        self.module = module
        self.host = pulp_host
        self.repo_type = repo_type
        self.repo_cache = dict()
        self.wait_for_completion = wait_for_completion

    def check_repo_exists(self, repo_id):
        try:
            self.get_repo_config_by_id(repo_id)
        except IndexError:
            return False
        else:
            return True

    def compare_repo_distributor_config(self, repo_id, **kwargs):
        repo_config = self.get_repo_config_by_id(repo_id)

        for distributor in repo_config['distributors']:
            for key, value in kwargs.items():
                if key not in distributor['config'].keys():
                    return False

                if not distributor['config'][key] == value:
                    return False

        return True

    def compare_repo_importer_config(self, repo_id, **kwargs):
        repo_config = self.get_repo_config_by_id(repo_id)

        for importer in repo_config['importers']:
            for key, value in kwargs.items():
                if value is not None:
                    if key not in importer['config'].keys():
                        return False

                    if not importer['config'][key] == value:
                        return False

        return True

    def create_repo(
        self,
        repo_id,
        relative_url,
        feed=None,
        generate_sqlite=False,
        serve_http=False,
        serve_https=True,
        proxy_host=None,
        proxy_port=None,
        proxy_username=None,
        proxy_password=None,
        repoview=False,
        ssl_ca_cert=None,
        ssl_client_cert=None,
        ssl_client_key=None,
        add_export_distributor=False
    ):
        url = "%s/pulp/api/v2/repositories/" % self.host
        data = dict()
        data['id'] = repo_id
        data['distributors'] = []

        if self.repo_type == 'rpm':
            yum_distributor = dict()
            yum_distributor['distributor_id'] = "yum_distributor"
            yum_distributor['distributor_type_id'] = "yum_distributor"
            yum_distributor['auto_publish'] = True
            yum_distributor['distributor_config'] = dict()
            yum_distributor['distributor_config']['http'] = serve_http
            yum_distributor['distributor_config']['https'] = serve_https
            yum_distributor['distributor_config']['relative_url'] = relative_url
            yum_distributor['distributor_config']['repoview'] = repoview
            yum_distributor['distributor_config']['generate_sqlite'] = generate_sqlite or repoview
            data['distributors'].append(yum_distributor)

            if add_export_distributor:
                export_distributor = dict()
                export_distributor['distributor_id'] = "export_distributor"
                export_distributor['distributor_type_id'] = "export_distributor"
                export_distributor['auto_publish'] = False
                export_distributor['distributor_config'] = dict()
                export_distributor['distributor_config']['http'] = serve_http
                export_distributor['distributor_config']['https'] = serve_https
                export_distributor['distributor_config']['relative_url'] = relative_url
                export_distributor['distributor_config']['repoview'] = repoview
                export_distributor['distributor_config']['generate_sqlite'] = generate_sqlite or repoview
                data['distributors'].append(export_distributor)

            data['importer_type_id'] = "yum_importer"
            data['importer_config'] = dict()

            if feed:
                data['importer_config']['feed'] = feed

            if proxy_host:
                data['importer_config']['proxy_host'] = proxy_host

            if proxy_port:
                data['importer_config']['proxy_port'] = proxy_port

            if proxy_username:
                data['importer_config']['proxy_username'] = proxy_username

            if proxy_password:
                data['importer_config']['proxy_password'] = proxy_password

            if ssl_ca_cert:
                data['importer_config']['ssl_ca_cert'] = ssl_ca_cert

            if ssl_client_cert:
                data['importer_config']['ssl_client_cert'] = ssl_client_cert

            if ssl_client_key:
                data['importer_config']['ssl_client_key'] = ssl_client_key

            data['notes'] = {
                "_repo-type": "rpm-repo"
            }

        response, info = fetch_url(
            self.module,
            url,
            data=json.dumps(data),
            method='POST')

        if info['status'] != 201:
            self.module.fail_json(
                msg="Failed to create repo.",
                status_code=info['status'],
                response=info['msg'],
                url=url)
        else:
            return True

    def delete_repo(self, repo_id):
        url = "%s/pulp/api/v2/repositories/%s/" % (self.host, repo_id)
        response, info = fetch_url(self.module, url, data='', method='DELETE')

        if info['status'] != 202:
            self.module.fail_json(
                msg="Failed to delete repo.",
                status_code=info['status'],
                response=info['msg'],
                url=url)

        if self.wait_for_completion:
            self.verify_tasks_completed(json.load(response))

        return True

    def get_repo_config_by_id(self, repo_id):
        if repo_id not in self.repo_cache.keys():
            repo_array = [x for x in self.repo_list if x['id'] == repo_id]
            self.repo_cache[repo_id] = repo_array[0]

        return self.repo_cache[repo_id]

    def publish_repo(self, repo_id, publish_distributor):
        url = "%s/pulp/api/v2/repositories/%s/actions/publish/" % (self.host, repo_id)

        # If there's no distributor specified, we will publish them all
        if publish_distributor is None:
            repo_config = self.get_repo_config_by_id(repo_id)

            for distributor in repo_config['distributors']:
                data = dict()
                data['id'] = distributor['id']
                response, info = fetch_url(
                    self.module,
                    url,
                    data=json.dumps(data),
                    method='POST')

                if info['status'] != 202:
                    self.module.fail_json(
                        msg="Failed to publish the repo.",
                        status_code=info['status'],
                        response=info['msg'],
                        url=url,
                        distributor=distributor['id'])
        else:
            data = dict()
            data['id'] = publish_distributor
            response, info = fetch_url(
                self.module,
                url,
                data=json.dumps(data),
                method='POST')

            if info['status'] != 202:
                self.module.fail_json(
                    msg="Failed to publish the repo",
                    status_code=info['status'],
                    response=info['msg'],
                    url=url,
                    distributor=publish_distributor)

        if self.wait_for_completion:
            self.verify_tasks_completed(json.load(response))

        return True

    def sync_repo(self, repo_id):
        url = "%s/pulp/api/v2/repositories/%s/actions/sync/" % (self.host, repo_id)
        response, info = fetch_url(self.module, url, data='', method='POST')

        if info['status'] != 202:
            self.module.fail_json(
                msg="Failed to schedule a sync of the repo.",
                status_code=info['status'],
                response=info['msg'],
                url=url)

        if self.wait_for_completion:
            self.verify_tasks_completed(json.load(response))

        return True

    def update_repo_distributor_config(self, repo_id, **kwargs):
        url = "%s/pulp/api/v2/repositories/%s/distributors/" % (self.host, repo_id)
        repo_config = self.get_repo_config_by_id(repo_id)

        for distributor in repo_config['distributors']:
            distributor_url = "%s%s/" % (url, distributor['id'])
            data = dict()
            data['distributor_config'] = dict()

            for key, value in kwargs.items():
                data['distributor_config'][key] = value

            response, info = fetch_url(
                self.module,
                distributor_url,
                data=json.dumps(data),
                method='PUT')

            if info['status'] != 202:
                self.module.fail_json(
                    msg="Failed to set the relative url for the repository.",
                    status_code=info['status'],
                    response=info['msg'],
                    url=url)

    def update_repo_importer_config(self, repo_id, **kwargs):
        url = "%s/pulp/api/v2/repositories/%s/importers/" % (self.host, repo_id)
        data = dict()
        importer_config = dict()

        for key, value in kwargs.items():
            if value is not None:
                importer_config[key] = value

        data['importer_config'] = importer_config

        if self.repo_type == 'rpm':
            data['importer_type_id'] = "yum_importer"

        response, info = fetch_url(
            self.module,
            url,
            data=json.dumps(data),
            method='POST')

        if info['status'] != 202:
            self.module.fail_json(
                msg="Failed to set the repo importer configuration",
                status_code=info['status'],
                response=info['msg'],
                importer_config=importer_config,
                url=url)

    def set_repo_list(self):
        url = "%s/pulp/api/v2/repositories/?details=true" % self.host
        response, info = fetch_url(self.module, url, method='GET')

        if info['status'] != 200:
            self.module.fail_json(
                msg="Request failed",
                status_code=info['status'],
                response=info['msg'],
                url=url)

        self.repo_list = json.load(response)

    def verify_tasks_completed(self, response_dict):
        for task in response_dict['spawned_tasks']:
            task_url = "%s%s" % (self.host, task['_href'])

            while True:
                response, info = fetch_url(
                    self.module,
                    task_url,
                    data='',
                    method='GET')

                if info['status'] != 200:
                    self.module.fail_json(
                        msg="Failed to check async task status.",
                        status_code=info['status'],
                        response=info['msg'],
                        url=task_url)

                task_dict = json.load(response)

                if task_dict['state'] == 'finished':
                    return True

                if task_dict['state'] == 'error':
                    self.module.fail_json(msg="Asynchronous task failed to complete.", error=task_dict['error'])

                sleep(2)


def main():
    argument_spec = url_argument_spec()
    argument_spec.update(
        add_export_distributor=dict(default=False, type='bool'),
        feed=dict(),
        generate_sqlite=dict(default=False, type='bool'),
        feed_ca_cert=dict(aliases=['importer_ssl_ca_cert', 'ca_cert'], deprecated_aliases=[dict(name='ca_cert', version='2.14')]),
        feed_client_cert=dict(aliases=['importer_ssl_client_cert']),
        feed_client_key=dict(aliases=['importer_ssl_client_key'], no_log=True),
        name=dict(required=True, aliases=['repo']),
        proxy_host=dict(),
        proxy_port=dict(),
        proxy_username=dict(),
        proxy_password=dict(no_log=True),
        publish_distributor=dict(),
        pulp_host=dict(default="https://127.0.0.1"),
        relative_url=dict(),
        repo_type=dict(default="rpm"),
        repoview=dict(default=False, type='bool'),
        serve_http=dict(default=False, type='bool'),
        serve_https=dict(default=True, type='bool'),
        state=dict(
            default="present",
            choices=['absent', 'present', 'sync', 'publish']),
        wait_for_completion=dict(default=False, type="bool"))
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True)

    add_export_distributor = module.params['add_export_distributor']
    feed = module.params['feed']
    generate_sqlite = module.params['generate_sqlite']
    importer_ssl_ca_cert = module.params['feed_ca_cert']
    importer_ssl_client_cert = module.params['feed_client_cert']
    if importer_ssl_client_cert is None and module.params['client_cert'] is not None:
        importer_ssl_client_cert = module.params['client_cert']
        module.deprecate("To specify client certificates to be used with the repo to sync, and not for communication with the "
                         "Pulp instance, use the new options `feed_client_cert` and `feed_client_key` (available since "
                         "Ansible 2.9.2). Until Ansible 2.14, the default value for `feed_client_cert` will be taken from "
                         "`client_cert` if only the latter is specified", version="2.14")
    importer_ssl_client_key = module.params['feed_client_key']
    if importer_ssl_client_key is None and module.params['client_key'] is not None:
        importer_ssl_client_key = module.params['client_key']
        module.deprecate("In Ansible 2.9.2 `feed_client_key` option was added. Until 2.14 the default value will come from client_key option", version="2.14")
    proxy_host = module.params['proxy_host']
    proxy_port = module.params['proxy_port']
    proxy_username = module.params['proxy_username']
    proxy_password = module.params['proxy_password']
    publish_distributor = module.params['publish_distributor']
    pulp_host = module.params['pulp_host']
    relative_url = module.params['relative_url']
    repo = module.params['name']
    repo_type = module.params['repo_type']
    repoview = module.params['repoview']
    serve_http = module.params['serve_http']
    serve_https = module.params['serve_https']
    state = module.params['state']
    wait_for_completion = module.params['wait_for_completion']

    if (state == 'present') and (not relative_url):
        module.fail_json(msg="When state is present, relative_url is required.")

    # Ensure that the importer_ssl_* is the content and not a file path
    if importer_ssl_ca_cert is not None:
        importer_ssl_ca_cert_file_path = os.path.abspath(importer_ssl_ca_cert)
        if os.path.isfile(importer_ssl_ca_cert_file_path):
            importer_ssl_ca_cert_file_object = open(importer_ssl_ca_cert_file_path, 'r')
            try:
                importer_ssl_ca_cert = importer_ssl_ca_cert_file_object.read()
            finally:
                importer_ssl_ca_cert_file_object.close()

    if importer_ssl_client_cert is not None:
        importer_ssl_client_cert_file_path = os.path.abspath(importer_ssl_client_cert)
        if os.path.isfile(importer_ssl_client_cert_file_path):
            importer_ssl_client_cert_file_object = open(importer_ssl_client_cert_file_path, 'r')
            try:
                importer_ssl_client_cert = importer_ssl_client_cert_file_object.read()
            finally:
                importer_ssl_client_cert_file_object.close()

    if importer_ssl_client_key is not None:
        importer_ssl_client_key_file_path = os.path.abspath(importer_ssl_client_key)
        if os.path.isfile(importer_ssl_client_key_file_path):
            importer_ssl_client_key_file_object = open(importer_ssl_client_key_file_path, 'r')
            try:
                importer_ssl_client_key = importer_ssl_client_key_file_object.read()
            finally:
                importer_ssl_client_key_file_object.close()

    server = pulp_server(module, pulp_host, repo_type, wait_for_completion=wait_for_completion)
    server.set_repo_list()
    repo_exists = server.check_repo_exists(repo)

    changed = False

    if state == 'absent' and repo_exists:
        if not module.check_mode:
            server.delete_repo(repo)

        changed = True

    if state == 'sync':
        if not repo_exists:
            module.fail_json(msg="Repository was not found. The repository can not be synced.")

        if not module.check_mode:
            server.sync_repo(repo)

        changed = True

    if state == 'publish':
        if not repo_exists:
            module.fail_json(msg="Repository was not found. The repository can not be published.")

        if not module.check_mode:
            server.publish_repo(repo, publish_distributor)

        changed = True

    if state == 'present':
        if not repo_exists:
            if not module.check_mode:
                server.create_repo(
                    repo_id=repo,
                    relative_url=relative_url,
                    feed=feed,
                    generate_sqlite=generate_sqlite,
                    serve_http=serve_http,
                    serve_https=serve_https,
                    proxy_host=proxy_host,
                    proxy_port=proxy_port,
                    proxy_username=proxy_username,
                    proxy_password=proxy_password,
                    repoview=repoview,
                    ssl_ca_cert=importer_ssl_ca_cert,
                    ssl_client_cert=importer_ssl_client_cert,
                    ssl_client_key=importer_ssl_client_key,
                    add_export_distributor=add_export_distributor)

            changed = True

        else:
            # Check to make sure all the settings are correct
            # The importer config gets overwritten on set and not updated, so
            # we set the whole config at the same time.
            if not server.compare_repo_importer_config(
                repo,
                feed=feed,
                proxy_host=proxy_host,
                proxy_port=proxy_port,
                proxy_username=proxy_username,
                proxy_password=proxy_password,
                ssl_ca_cert=importer_ssl_ca_cert,
                ssl_client_cert=importer_ssl_client_cert,
                ssl_client_key=importer_ssl_client_key
            ):
                if not module.check_mode:
                    server.update_repo_importer_config(
                        repo,
                        feed=feed,
                        proxy_host=proxy_host,
                        proxy_port=proxy_port,
                        proxy_username=proxy_username,
                        proxy_password=proxy_password,
                        ssl_ca_cert=importer_ssl_ca_cert,
                        ssl_client_cert=importer_ssl_client_cert,
                        ssl_client_key=importer_ssl_client_key)

                changed = True

            if relative_url is not None:
                if not server.compare_repo_distributor_config(
                    repo,
                    relative_url=relative_url
                ):
                    if not module.check_mode:
                        server.update_repo_distributor_config(
                            repo,
                            relative_url=relative_url)

                    changed = True

            if not server.compare_repo_distributor_config(repo, generate_sqlite=generate_sqlite):
                if not module.check_mode:
                    server.update_repo_distributor_config(repo, generate_sqlite=generate_sqlite)

                changed = True

            if not server.compare_repo_distributor_config(repo, repoview=repoview):
                if not module.check_mode:
                    server.update_repo_distributor_config(repo, repoview=repoview)

                changed = True

            if not server.compare_repo_distributor_config(repo, http=serve_http):
                if not module.check_mode:
                    server.update_repo_distributor_config(repo, http=serve_http)

                changed = True

            if not server.compare_repo_distributor_config(repo, https=serve_https):
                if not module.check_mode:
                    server.update_repo_distributor_config(repo, https=serve_https)

                changed = True

    module.exit_json(changed=changed, repo=repo)


if __name__ == '__main__':
    main()
