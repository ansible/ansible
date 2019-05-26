#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.onyx import onyx_telemetry_agent
from units.modules.utils import set_module_args
from .onyx_module import TestOnyxModule, load_fixture


class TestOnyxTelemetryAgentModule(TestOnyxModule):

    module = onyx_telemetry_agent
    docker_enabled = True
    container_exists = True
    CONTAINER_NAME = "telemetry-test"
    CONTAINER_IMAGE = "mellanox/telemetry-agent"
    CONTAINER_IMAGE_VER = "latest"
    FAKE_USER = 'user'
    FAKE_PWD = 'pwd'
    FAKE_SERVER = 'server'
    PROTOCOL = 'http'
    IMAGE_PATH = '/path'
    NO_USR_URL = '%s://%s%s' % (PROTOCOL, FAKE_SERVER, IMAGE_PATH)
    USR_URL = '%s://%s@%s%s' % (PROTOCOL, FAKE_USER, FAKE_SERVER, IMAGE_PATH)
    USR_PWD_URL = '%s://%s:%s@%s%s' % (PROTOCOL, FAKE_USER, FAKE_PWD,
                                       FAKE_SERVER, IMAGE_PATH)

    LOCATION = dict(
        server=FAKE_SERVER,
        protocol=PROTOCOL,
        path=IMAGE_PATH,
        image=CONTAINER_IMAGE,
        version=CONTAINER_IMAGE_VER,
        username=FAKE_USER,
        password=FAKE_PWD)

    CMD_NO_DOCKER_START = 'docker no start %s' % CONTAINER_NAME
    CMD_DOCKER_PULL = "docker pull %s:%s" % (
        CONTAINER_IMAGE, CONTAINER_IMAGE_VER)
    CMD_DOCKER_START = "docker start %s %s %s now-and-init privileged network sdk" % (
        CONTAINER_IMAGE, CONTAINER_IMAGE_VER, CONTAINER_NAME)
    CMD_NO_DOCKER_SHUTDOWN = "no docker shutdown"
    CMD_IMAGE_FETCH = 'image fetch %s {0}'.format(
        module.OnyxTelemetryAgentModule.IMAGE_FILE)
    CMD_IMAGE_LOAD = 'docker load %s' % module.OnyxTelemetryAgentModule.IMAGE_FILE

    def setUp(self):
        super(TestOnyxTelemetryAgentModule, self).setUp()
        self.docker_enabled = True
        self.container_exists = True

        self.mock_get_dockers_state = patch.object(
            self.module.OnyxTelemetryAgentModule,
            '_get_dockers_state')
        self.get_dockers_state = self.mock_get_dockers_state.start()

        self.mock_load_config = patch(
            'ansible.module_utils.network.onyx.onyx.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_get_docker_containers = patch.object(
            self.module.OnyxTelemetryAgentModule, '_get_docker_containers')
        self.get_docker_containers = self.mock_get_docker_containers.start()

    def tearDown(self):
        super(TestOnyxTelemetryAgentModule, self).tearDown()
        self.mock_get_docker_containers.stop()
        self.mock_load_config.stop()
        self.mock_get_dockers_state.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        docker_state_cfg = 'onyx_show_docker_state.cfg'
        docker_state_data = load_fixture(docker_state_cfg)
        if not self.docker_enabled:
            docker_state_data = dict(docker_state_data)
            docker_state_data["Dockers state"] = "disabled"
        docker_containers_cfg = 'onyx_show_docker_containers.cfg'
        docker_containers_data = load_fixture(docker_containers_cfg)
        if not self.container_exists:
            docker_containers_data = list(docker_containers_data)
            del docker_containers_data[0]

        self.get_dockers_state.return_value = docker_state_data
        self.get_docker_containers.return_value = docker_containers_data
        self.load_config.return_value = None

    def test_pull_no_change(self):
        self.docker_enabled = True
        self.container_exists = True
        set_module_args(
            dict(name=self.CONTAINER_NAME,
                 install_mode='pull'))
        self.execute_module(changed=False)

    def test_pull_docker_enabled(self):
        self.docker_enabled = True
        self.container_exists = False
        set_module_args(
            dict(name=self.CONTAINER_NAME,
                 install_mode='pull'))
        commands = [
            self.CMD_DOCKER_PULL,
            self.CMD_DOCKER_START
        ]
        self.execute_module(changed=True, commands=commands)

    def test_pull_docker_disabled(self):
        self.docker_enabled = False
        set_module_args(
            dict(name=self.CONTAINER_NAME,
                 install_mode='pull'))
        commands = [
            self.CMD_NO_DOCKER_SHUTDOWN,
            self.CMD_DOCKER_PULL,
            self.CMD_DOCKER_START
        ]
        self.execute_module(changed=True, commands=commands)

    def test_remove_docker(self):
        self.docker_enabled = True
        set_module_args(
            dict(name=self.CONTAINER_NAME,
                 state='absent'))
        commands = [
            self.CMD_NO_DOCKER_START
        ]
        self.execute_module(changed=True, commands=commands)

    def test_remove_docker_no_change(self):
        self.docker_enabled = True
        self.container_exists = False
        set_module_args(
            dict(name=self.CONTAINER_NAME,
                 state='absent'))
        self.execute_module(changed=False)

    def test_fetch_no_change(self):
        self.docker_enabled = True
        self.container_exists = True
        set_module_args(
            dict(name=self.CONTAINER_NAME,
                 install_mode='fetch',
                 location=self.LOCATION))
        self.execute_module(changed=False)

    def test_fetch_docker_enabled(self):
        self.docker_enabled = True
        self.container_exists = False
        set_module_args(
            dict(name=self.CONTAINER_NAME,
                 install_mode='fetch',
                 location=self.LOCATION))
        url = self.USR_PWD_URL
        commands = [
            self.CMD_IMAGE_FETCH % url,
            self.CMD_IMAGE_LOAD,
            self.CMD_DOCKER_START
        ]
        self.execute_module(changed=True, commands=commands)

    def test_fetch_docker_no_usr(self):
        self.docker_enabled = True
        self.container_exists = False
        location = dict(self.LOCATION)
        del location['username']
        del location['password']
        set_module_args(
            dict(name=self.CONTAINER_NAME,
                 install_mode='fetch',
                 location=location))
        url = self.NO_USR_URL
        commands = [
            self.CMD_IMAGE_FETCH % url,
            self.CMD_IMAGE_LOAD,
            self.CMD_DOCKER_START
        ]
        self.execute_module(changed=True, commands=commands)

    def test_fetch_docker_no_pwd(self):
        self.docker_enabled = True
        self.container_exists = False
        location = dict(self.LOCATION)
        del location['password']
        set_module_args(
            dict(name=self.CONTAINER_NAME,
                 install_mode='fetch',
                 location=location))
        url = self.USR_URL
        commands = [
            self.CMD_IMAGE_FETCH % url,
            self.CMD_IMAGE_LOAD,
            self.CMD_DOCKER_START
        ]
        self.execute_module(changed=True, commands=commands)

    def test_fetch_docker_disabled(self):
        self.docker_enabled = False
        set_module_args(
            dict(name=self.CONTAINER_NAME,
                 install_mode='fetch',
                 location=self.LOCATION))
        url = self.USR_PWD_URL
        commands = [
            self.CMD_NO_DOCKER_SHUTDOWN,
            self.CMD_IMAGE_FETCH % url,
            self.CMD_IMAGE_LOAD,
            self.CMD_DOCKER_START
        ]
        self.execute_module(changed=True, commands=commands)
