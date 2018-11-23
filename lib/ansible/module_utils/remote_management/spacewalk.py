# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Davide Blasi <davegarath () gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import atexit
import ssl

from ansible.module_utils.basic import env_fallback
from ansible.module_utils.six.moves import xmlrpc_client


def spacewalk_argument_spec():
    return dict(
        url=dict(type='str',
                 required=True,
                 fallback=(env_fallback, ['SPACEWALK_URL']),
                 ),
        login=dict(type='str',
                   required=True,
                   fallback=(env_fallback, ['SPACEWALK_LOGIN']),
                   ),
        password=dict(type='str',
                      required=True,
                      no_log=True,
                      fallback=(env_fallback, ['SPACEWALK_PASSWORD']),
                      ),
        validate_certs=dict(type='bool',
                            required=False,
                            default=True,
                            fallback=(env_fallback, ['SPACEWALK_VALIDATE_CERTS'])),
    )


class Channel(object):

    def __init__(self, module):
        self.module = module
        self.client, self.session = connect_to_api(module)
        self.channels = {'spacewalk_channels': {}}

    def get_all_channels(self):
        """ Get all chennels from spacewalk.
            Fill self.channels for caching pourpose and ready to serves ansible_facts
        """
        module = self.module
        if not self.channels['spacewalk_channels']:
            channels = self.client.channel.listAllChannels(self.session)
            for channel in channels:
                label = channel.pop('label')
                channel_detail = self.get_channel_detail(label)
                channel_detail['last_modified'] = str(channel_detail['last_modified'])
                if 'yumrepo_last_sync' in channel_detail:
                    channel_detail['yumrepo_last_sync'] = str(channel_detail['yumrepo_last_sync'])
                channel = {**channel, **channel_detail}
                self.channels['spacewalk_channels'][label] = channel

        ansible_facts = self.channels
        return ansible_facts

    def get_channel_id(self, channel_label):
        """ Return integer channel_id passing channel label
        """
        if not self.channels['spacewalk_channels']:
            self.get_all_channels()

        if channel_label in self.channels['spacewalk_channels']:
            return self.channels['spacewalk_channels'][channel_label]['id']

    def get_channel_detail(self, channel_label):
        return self.client.channel.software.getDetails(self.session, channel_label)

    def create_channel(self):
        ch_label = self.module.params['label']
        ch_name = self.module.params['name']
        ch_summary = self.module.params['summary']
        ch_archLabel = self.module.params['archLabel']
        ch_parentLabel = self.module.params['parentLabel']
        ch_checksumType = self.module.params['checksumType']
        ch_gpgurl = self.module.params['gpgurl']
        ch_gpgid = self.module.params['gpgid']
        ch_gpgfingerprint = self.module.params['gpgfingerprint']
        ch_gpgKey = {'url': ch_gpgurl, 'id': ch_gpgid, 'fingerprint': ch_gpgfingerprint}

        try:
            res = self.client.channel.software.create(self.session, ch_label, ch_name, ch_summary, ch_archLabel, ch_parentLabel, ch_checksumType, ch_gpgKey)
        except Exception as generic_exception:
            self.module.fail_json(channel=label, action='Create', msg='Error creating channel: %s' % generic_exception)

    def delete_channel(self, ch_label):
        try:
            res = self.client.channel.software.delete(self.session, ch_label)
        except Exception as generic_exception:
            self.module.fail_json(channel=label, action='Delete', msg='Error deleting channel: %s' % generic_exception)

    def channel_comparison(self, label):
        """ Compare playbook inputs with channel in spacewalk and return the differences
        """
        changes = {}
        key_map = {'name': 'name',
                   'summary': 'summary',
                   'archLabel': 'arch_label',
                   'parentLabel': 'parent_channel_label',
                   'checksumType': 'checksum_label',
                   'gpgurl': 'gpg_key_url',
                   'gpgid': 'gpg_key_id',
                   'gpgfingerprint': 'gpg_key_fp',
                   'maintainer_email': 'maintainer_email',
                   'maintainer_name': 'maintainer_name',
                   'maintainer_phone': 'maintainer_phone'
                   }

        if not self.channels['spacewalk_channels']:
            self.get_all_channels()

        if label not in self.channels['spacewalk_channels']:
            self.module.fail_json(msg="Error: no channel %s in channels" % label)

        for keypb, keychannel in key_map.items():
            pb_value = self.module.params[keypb]
            ch_value = self.channels['spacewalk_channels'][label][keychannel]

            if pb_value != ch_value:
                changes[keychannel] = {'original_value': ch_value, 'new_value': pb_value}

        return changes

    def set_channel_detail(self, label, tochange):
        changes = {}
        channel_id = self.get_channel_id(label)

        for key in tochange:
            if key == 'parent_channel_label' or key == 'arch_label':
                self.module.warn("Found different %s in channel %s but cannot be changed. "
                                 "You have to delete and recreate the channel if you want this change." % (key, label))
                continue
            changes[key] = tochange[key]['new_value']

        if not changes:
            return False

        try:
            self.client.channel.software.setDetails(self.session, channel_id, changes)
        except Exception as generic_exception:
            self.module.fail_json(channel=label, action='Update', msg='Error setting changes: %s' % generic_exception)


class Repository(object):

    def __init__(self, module):
        self.module = module
        self.client, self.session = connect_to_api(module)
        self.repositories = {'spacewalk_repositories': {}}

    def get_all_repositories(self):
        """ Get all repositories from spacewalk.
            Fill self.repositories for caching pourpose and ready to serves ansible_facts
        """
        module = self.module
        if not self.repositories['spacewalk_repositories']:
            repositories = self.client.channel.software.listUserRepos(self.session)
            for repository in repositories:
                label = repository.pop('label')
                repository_detail = self.get_repository_detail(label)
                repository = {**repository, **repository_detail}
                self.repositories['spacewalk_repositories'][label] = repository

        ansible_facts = self.repositories
        return ansible_facts

    def get_repository_id(self, repository_label):
        """ Return integer repository_id passing repository label
        """
        if not self.repositories['spacewalk_repositories']:
            self.get_all_repositories()

        if repository_label in self.repositories['spacewalk_repositories']:
            return self.repositories['spacewalk_repositories'][repository_label]['id']

    def get_repository_byurl(self, repository_url):
        """ Return integer repository_id passing repository url
        """
        if not self.repositories['spacewalk_repositories']:
            self.get_all_repositories()

        for repository in self.repositories['spacewalk_repositories']:
            if repository_url == self.repositories['spacewalk_repositories'][repository]['sourceUrl']:
                return self.repositories['spacewalk_repositories'][repository]

    def get_repository_detail(self, repository_label):
        return self.client.channel.software.getRepoDetails(self.session, repository_label)

    def create_repository(self):
        label = self.module.params['label']
        repotype = self.module.params['repotype']
        repourl = self.module.params['repourl']
        sslCaCert = self.module.params['sslCaCert']
        sslCliCert = self.module.params['sslCliCert']
        sslCliKey = self.module.params['sslCliKey']

        try:
            self.client.channel.software.createRepo(self.session, label, repotype, repourl, sslCaCert, sslCliCert, sslCliKey)
        except Exception as generic_exception:
            if 'already a defined repository with given url' in generic_exception.faultString:
                """ Handler Exception if there is an other repository with the same url
                   Search duplicate repository url raising AlreadyExists exception
                """
                repository = self.get_repository_byurl(repourl)
                message = "There is repository '%s' with same repository url: '%s'" % (repository.get('label'), repourl)
                raise AlreadyExists(301, message, repository)

            self.module.fail_json(repository=label, action='Create', msg='Error creating repository %s: %s' % (label, generic_exception))

    def delete_repository(self, label):
        try:
            self.client.channel.software.removeRepo(self.session, label)
        except Exception as generic_exception:
            self.module.fail_json(repository=label, action='Delete', msg='Error deleting repository: %s' % generic_exception)

    def repository_comparison(self, label):
        """ Compare playbook inputs with repository in spacewalk and return the differences
        """
        changes = {}
        key_map = {'label': 'label',
                   'repourl': 'sourceUrl',
                   'repotype': 'type',
                   'sslCaCert': 'sslCaCert',
                   'sslCliCert': 'sslCliCert',
                   'sslCliKey': 'sslCliKey'
                   }

        if not self.repositories['spacewalk_repositories']:
            self.get_all_repositories()

        if label not in self.repositories['spacewalk_repositories']:
            self.module.fail_json(msg="Error: no repository %s in repositories" % label)

        repo = self.repositories['spacewalk_repositories'][label]

        for keypb, keyrepository in key_map.items():
            if keyrepository in repo:
                pb_value = self.module.params[keypb]
                rp_value = repo[keyrepository]

                if pb_value != rp_value:
                    changes[keyrepository] = {'original_value': rp_value, 'new_value': pb_value}

        return changes

    def set_repository_url(self, label, url):
        try:
            self.client.channel.software.updateRepoUrl(self.session, label, url)
        except Exception as generic_exception:
            self.module.fail_json(repository=label, action='Update', msg='Error setting url: %s' % generic_exception)

    def set_repository_label(self, repoid, label):
        try:
            self.client.channel.software.updateRepoLabel(self.session, repoid, label)
        except Exception as generic_exception:
            self.module.fail_json(repository=label, action='Update', msg='Error setting label: %s' % generic_exception)

    def set_repository_ssl(self, label, sslCaCert, sslCliCert, sslCliKey):
        try:
            self.client.channel.software.updateRepoUrl(self.session, label, sslCaCert, sslCliCert, sslCliKey)
        except Exception as generic_exception:
            self.module.fail_json(repository=label, action='Update', msg='Error setting ssl: %s' % generic_exception)

    def update(self, label, changes):
        if 'sourceUrl' in changes:
            url = changes['sourceUrl']['new_value']
            self.set_repository_url(label, url)
            return 1
        self.module.fail_json(repository=label, action='Update', msg='Error Change not implemented yet: %s' % changes)


def connect_to_api(module, disconnect_atexit=True):
    """
    """
    url = module.params['url']
    login = module.params['login']
    password = module.params['password']
    validate_certs = module.params['validate_certs']

    if not url:
        module.fail_json(msg="Url parameter is missing."
                             " Please specify this parameter in task or"
                             " export environment variable like 'export SPACEWALK_URL=URL_API'")

    if not login:
        module.fail_json(msg="Login parameter is missing."
                             " Please specify this parameter in task or"
                             " export environment variable like 'export SPACEWALK_LOGIN=LOGIN'")

    if not password:
        module.fail_json(msg="Password parameter is missing."
                             " Please specify this parameter in task or"
                             " export environment variable like 'export SPACEWALK_PASSWORD=PASSWORD'")

    if validate_certs and not hasattr(ssl, 'SSLContext'):
        module.fail_json(msg='No support changing verification mode with python < 2.7.9. Either update '
                             'python or use validate_certs=false.')

    ssl_context = None
    if not validate_certs and hasattr(ssl, 'SSLContext'):
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        ssl_context.verify_mode = ssl.CERT_NONE

    try:
        client = xmlrpc_client.Server(url, context=ssl_context)
    except Exception as generic_exc:
        module.fail_json(msg="Unknown error while connecting to Spacewalk URL: %s : %s" % (url, generic_exc))

    try:
        session = client.auth.login(login, password)
    except Exception as generic_exc:
        module.fail_json(msg="Login invalid while connecting to Spacewalk URL: %s : %s" % (url, generic_exc))

    if disconnect_atexit:
        atexit.register(spacelk_logout, client, session)

    return (client, session)


def spacelk_logout(client, session):
    client.auth.logout(session)


class AlreadyExists(Exception):
    def __init__(self, failError, failMessage, obj):
        self.failError = failError
        self.failMessage = failMessage
        self.obj = obj
