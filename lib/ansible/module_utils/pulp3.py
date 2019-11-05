# Copyright: (c) 2019, Timo Funke <timoses@msn.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

try:
    from pulpcore.client.pulpcore.exceptions import ApiException
    HAS_PULPCORE_EXCEPTIONS = True
except ImportError:
    HAS_PULPCORE_EXCEPTIONS = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import url_argument_spec

SUPPORTED_PLUGINS = [
    'file',
    'docker',
    'rpm'
]

PUBLICATION_API = {
    'file': {
        'class': 'PublicationsFileApi',
        'module': 'publications_file_api'
    },
    'rpm': {
        'class': 'PublicationsRpmApi',
        'module': 'publications_rpm_api'
    },
}

DISTRIBUTION_API = {
    'file': {
        'class': 'DistributionsFileApi',
        'module': 'distributions_file_api'
    },
    'docker': {
        'class': 'DistributionsDockerApi',
        'module': 'distributions_docker_api'
    },
    'rpm': {
        'class': 'DistributionsRpmApi',
        'module': 'distributions_rpm_api'
    },
}

REMOTE_API = {
    'file': {
        'class': 'RemotesFileApi',
        'module': 'remotes_file_api'
    },
    'docker': {
        'class': 'RemotesDockerApi',
        'module': 'remotes_docker_api'
    },
    'rpm': {
        'class': 'RemotesRpmApi',
        'module': 'remotes_rpm_api'
    }
}

REPOSITORY_API = {
    'class': 'RepositoriesApi',
    'module': 'repositories_api'
}

REPOSITORY_VERSION_API = {
    'class': 'RepositoriesVersionsApi',
    'module': 'repositories_versions_api'
}

TASK_API = {
    'class': 'TasksApi',
    'module': 'tasks_api'
}

def load_pulp_api(module, api):
    from importlib import import_module
    from pulpcore.client.pulpcore.api_client import ApiClient
    from pulpcore.client.pulpcore.configuration import Configuration
    import pulpcore.client.pulpcore.api_client
    import pulpcore.client.pulpcore.configuration

    try:
        api_module = import_module('pulpcore.client.pulpcore.api.%s' % api['module'])
    except ImportError as e:
        module.fail_json(msg="Failed to load module '%s'. Ensure pulpcore-client python module is installed on the target host. Error: %s"
                            % (api['module'], e))

    config = Configuration(host=module.params['url'],
                           username=module.params['url_username'],
                           password=module.params['url_password'])
    config.safe_chars_for_path_param = '/'
    client = ApiClient(configuration=config)

    api_class = getattr(api_module, api['class'])

    return api_class(client)

def load_pulp_plugin_api(module, plugin, api):
    from importlib import import_module
    plugin_base = 'pulpcore.client.pulp_' + plugin
    plugin_api = api[plugin]

    try:
        config_module = import_module('%s.configuration' % plugin_base)
        client_module = import_module('%s.api_client' % plugin_base)
        api_module = import_module('%s.api.%s' % (plugin_base,plugin_api['module']))
    except ImportError as e:
        module.fail_json(msg="Python module pulp-%s-client may not be installed on the target host! Error: %s"
                         % (plugin, e))
    config = config_module.Configuration(host=module.params['url'],
                           username=module.params['url_username'],
                           password=module.params['url_password'])
    config.safe_chars_for_path_param = '/'
    client = client_module.ApiClient(configuration=config)

    api_class = getattr(api_module, plugin_api['class'])
    return api_class(client)

def get_repo(module, name):
    repo_api = load_pulp_api(module, REPOSITORY_API)
    repo_state = repo_api.list(name=name)
    if repo_state.count == 0:
        module.fail_json(msg="Repository '%s' was not found." % name)
    else:
        return repo_state.results[0]

def get_repo_version(module, repository, version=None):
    """ Returns latest version if it is None """
    repo_version_api = load_pulp_api(module, REPOSITORY_VERSION_API)
    repo_version = None

    if version:
        try:
            response = repo_version_api.list(repository.pulp_href, number=version)
            if response.count >= 1:
                return response.results[0]
            else:
                return None
        except ApiException as e:
            module.fail_json(msg="Failed to find version '%s': %s" % (version, e))
    elif repository.latest_version_href:
        try:
            response = repo_version_api.read(repository.latest_version_href)
            return response
        except ApiException as e:
            module.fail_json(msg="Failed to fetch latest version: %s" % e)

    module.fail_json(msg="Repository '%s' does not appear to have any versions." % repository.name)

class PulpAnsibleModule(AnsibleModule):

    def __init__(self):
        module_spec = self.module_spec()

        self.module = AnsibleModule(**module_spec)

        if not HAS_PULPCORE_EXCEPTIONS:
            self.module.fail_json(msg="Python module pulpcore-client does not appear to be installed on the host!")

        self.api_data = self.construct_api_data()

    def construct_api_data(self):
        data = {}
        for api_key, module_key in self.module_to_api_data.items():
            if module_key in self.module.params:
                data[api_key] = self.module.params[module_key]
        return data

    def argument_spec(self):
        argument_spec = url_argument_spec()
        argument_spec.update(
            url=dict(type='str', default='http://localhost:24817'))
        return argument_spec

    def create_or_update(self):
        res = self.api.list(name=self.api_data['name'])
        if res.count == 0:
            self.api.create(self.api_data)
            return True
        elif res.count == 1:
            resource = res.results[0]
            api_data_diff = dict((k, self.api_data[k]) for k in self.api_data.keys() if self.api_data[k] is not None and self.api_data[k] != getattr(resource, k))
            if api_data_diff:
                self.api.update(resource.pulp_href, self.api_data)
                return True

        return False

    def delete(self):
        res = self.api.list(name=self.api_data['name'])
        if res.count == 0:
            return False
        elif res.count == 1:
            resource = res.results[0]
            self.api.delete(resource.pulp_href)
            return True

class PulpPluginAnsibleModule(PulpAnsibleModule):

    def __init__(self):
        PulpAnsibleModule.__init__(self)
        self.pulp_plugin = self.module.params['pulp_plugin']

    def argument_spec(self):
        argument_spec = PulpAnsibleModule.argument_spec(self)
        argument_spec.update(
            pulp_plugin=dict(
                required=True, type='str',
                choices=SUPPORTED_PLUGINS),
        )
        return argument_spec
