#
# (c) 2015 Peter Sprygada, <psprygada@ansible.com>
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

from distutils.version import LooseVersion

from ansible.module_utils.basic import AnsibleModule, env_fallback, get_exception
from ansible.module_utils.shell import Shell, ShellError, HAS_PARAMIKO
from ansible.module_utils.netcfg import parse

try:
    from jnpr.junos import Device
    from jnpr.junos.utils.config import Config
    from jnpr.junos.version import VERSION
    from jnpr.junos.exception import RpcError, ConfigLoadError, CommitError
    from jnpr.junos.exception import LockError, UnlockError
    if not LooseVersion(VERSION) >= LooseVersion('1.2.2'):
        HAS_PYEZ = False
    else:
        HAS_PYEZ = True
except ImportError:
    HAS_PYEZ = False

try:
    import jxmlease
    HAS_JXMLEASE = True
except ImportError:
    HAS_JXMLEASE = False

try:
    from lxml import etree
except ImportError:
    import xml.etree.ElementTree as etree


NET_COMMON_ARGS = dict(
    host=dict(required=True),
    port=dict(type='int'),
    username=dict(fallback=(env_fallback, ['ANSIBLE_NET_USERNAME'])),
    password=dict(no_log=True, fallback=(env_fallback, ['ANSIBLE_NET_PASSWORD'])),
    ssh_keyfile=dict(fallback=(env_fallback, ['ANSIBLE_NET_SSH_KEYFILE']), type='path'),
    timeout=dict(default=0, type='int'),
    transport=dict(default='netconf', choices=['cli', 'netconf']),
    provider=dict(type='dict')
)


def to_list(val):
    if isinstance(val, (list, tuple)):
        return list(val)
    elif val is not None:
        return [val]
    else:
        return list()


def xml_to_json(val):
    if isinstance(val, basestring):
        return jxmlease.parse(val)
    else:
        return jxmlease.parse_etree(val)

def xml_to_string(val):
    return etree.tostring(val)


class Cli(object):

    def __init__(self, module):
        self.module = module
        self.shell = None

    def connect(self, **kwargs):
        host = self.module.params['host']
        port = self.module.params['port'] or 22

        username = self.module.params['username']
        password = self.module.params['password']
        key_filename = self.module.params['ssh_keyfile']

        allow_agent = (key_filename is not None) or (key_filename is None and password is None)

        try:
            self.shell = Shell()
            self.shell.open(host, port=port, username=username, password=password,
                    key_filename=key_filename, allow_agent=allow_agent)
        except ShellError:
            e = get_exception()
            msg = 'failed to connect to %s:%s - %s' % (host, port, str(e))
            self.module.fail_json(msg=msg)

        if self.shell._matched_prompt.strip().endswith('%'):
            self.shell.send('cli')
        self.shell.send('set cli screen-length 0')

    def run_commands(self, commands, **kwargs):
        try:
            return self.shell.send(commands)
        except ShellError:
            e = get_exception()
            self.module.fail_json(msg=e.message, commands=commands)

    def configure(self, commands, **kwargs):
        commands = to_list(commands)
        commands.insert(0, 'configure')

        if kwargs.get('comment'):
            commands.append('commit comment "%s"' % kwargs.get('comment'))
        else:
            commands.append('commit and-quit')

        responses = self.shell.send(commands)
        responses.pop(0)
        responses.pop()
        return responses

    def disconnect(self):
        self.shell.close()


class Netconf(object):

    def __init__(self, module):
        self.module = module
        self.device = None
        self.config = None
        self._locked = False

    def _fail(self, msg):
        if self.device:
            if self._locked:
                self.config.unlock()
            self.disconnect()
        self.module.fail_json(msg=msg)

    def connect(self, **kwargs):
        try:
            host = self.module.params['host']
            port = self.module.params['port'] or 830

            user = self.module.params['username']
            passwd = self.module.params['password']
            key_filename = self.module.params['ssh_keyfile']

            self.device = Device(host, user=user, passwd=passwd, port=port,
                    gather_facts=False, ssh_private_key_file=key_filename).open()

            self.config = Config(self.device)

        except Exception, exc:
            self._fail('unable to connect to %s: %s' % (host, str(exc)))

    def run_commands(self, commands, **kwargs):
        response = list()
        fmt = kwargs.get('format') or 'xml'

        for cmd in to_list(commands):
            try:
                resp = self.device.cli(command=cmd, format=fmt)
                response.append(resp)
            except (ValueError, RpcError), exc:
                self._fail('Unable to get cli output: %s' % str(exc))
            except Exception, exc:
                self._fail('Uncaught exception - please report: %s' % str(exc))

        return response

    def unlock_config(self):
        try:
            self.config.unlock()
            self._locked = False
        except UnlockError, exc:
            self.module.log('unable to unlock config: {0}'.format(str(exc)))

    def lock_config(self):
        try:
            self.config.lock()
            self._locked = True
        except LockError, exc:
            self.module.log('unable to lock config: {0}'.format(str(exc)))

    def check_config(self):
        if not self.config.commit_check():
            self._fail(msg='Commit check failed')

    def commit_config(self, comment=None, confirm=None):
        try:
            kwargs = dict(comment=comment)
            if confirm and confirm > 0:
                kwargs['confirm'] = confirm
            return self.config.commit(**kwargs)
        except CommitError, exc:
            msg = 'Unable to commit configuration: {0}'.format(str(exc))
            self._fail(msg=msg)

    def load_config(self, candidate, action='replace', comment=None,
            confirm=None, format='text', commit=True):

        merge = action == 'merge'
        overwrite = action == 'overwrite'

        self.lock_config()

        try:
            self.config.load(candidate, format=format, merge=merge,
                    overwrite=overwrite)
        except ConfigLoadError, exc:
            msg = 'Unable to load config: {0}'.format(str(exc))
            self._fail(msg=msg)

        diff = self.config.diff()
        self.check_config()
        if commit and diff:
            self.commit_config(comment=comment, confirm=confirm)

        self.unlock_config()

        return diff

    def rollback_config(self, identifier, commit=True, comment=None):

        self.lock_config()

        try:
            result = self.config.rollback(identifier)
        except Exception, exc:
            msg = 'Unable to rollback config: {0}'.format(str(exc))
            self._fail(msg=msg)

        diff = self.config.diff()
        if commit:
            self.commit_config(comment=comment)

        self.unlock_config()
        return diff

    def disconnect(self):
        if self.device:
            self.device.close()

    def get_facts(self, refresh=True):
        if refresh:
            self.device.facts_refresh()
        return self.device.facts

    def get_config(self, config_format="text"):
        if config_format not in ['text', 'set', 'xml']:
            msg = 'invalid config format... must be one of xml, text, set'
            self._fail(msg=msg)

        ele = self.rpc('get_configuration', format=config_format)
        if config_format in ['text', 'set']:
           return str(ele.text).strip()
        elif config_format == "xml":
            return ele

    def rpc(self, name, format='xml', **kwargs):
        meth = getattr(self.device.rpc, name)
        reply = meth({'format': format}, **kwargs)
        return reply


class NetworkModule(AnsibleModule):

    def __init__(self, *args, **kwargs):
        super(NetworkModule, self).__init__(*args, **kwargs)
        self.connection = None
        self._connected = False

    @property
    def connected(self):
        return self._connected

    def _load_params(self):
        super(NetworkModule, self)._load_params()
        provider = self.params.get('provider') or dict()
        for key, value in provider.items():
            if key in NET_COMMON_ARGS:
                if self.params.get(key) is None and value is not None:
                    self.params[key] = value

    def connect(self):
        cls = globals().get(str(self.params['transport']).capitalize())
        try:
            self.connection = cls(self)
        except TypeError:
            e = get_exception()
            self.fail_json(msg=e.message)

        self.connection.connect()

        msg = 'connecting to host: {username}@{host}:{port}'.format(**self.params)
        self.log(msg)

        self._connected = True

    def load_config(self, commands, **kwargs):
        if not self.connected:
            self.connect()
        return self.connection.load_config(commands, **kwargs)

    def rollback_config(self, identifier, commit=True):
        if not self.connected:
            self.connect()
        return self.connection.rollback_config(identifier)

    def run_commands(self, commands, **kwargs):
        if not self.connected:
            self.connect()
        return self.connection.run_commands(commands, **kwargs)

    def disconnect(self):
        if self.connected:
            self.connection.disconnect()
            self._connected = False

    def get_config(self, **kwargs):
        if not self.connected:
            self.connect()
        return self.connection.get_config(**kwargs)

    def get_facts(self, **kwargs):
        if not self.connected:
            self.connect()
        return self.connection.get_facts(**kwargs)

def get_module(**kwargs):
    """Return instance of NetworkModule
    """
    argument_spec = NET_COMMON_ARGS.copy()
    if kwargs.get('argument_spec'):
        argument_spec.update(kwargs['argument_spec'])
    kwargs['argument_spec'] = argument_spec
    kwargs['check_invalid_arguments'] = False

    module = NetworkModule(**kwargs)

    if module.params['transport'] == 'cli' and not HAS_PARAMIKO:
        module.fail_json(msg='paramiko is required but does not appear to be installed')
    elif module.params['transport'] == 'netconf' and not HAS_PYEZ:
        module.fail_json(msg='junos-eznc >= 1.2.2 is required but does not appear to be installed')
    elif module.params['transport'] == 'netconf' and not HAS_JXMLEASE:
        module.fail_json(msg='jxmlease is required but does not appear to be installed')

    module.connect()
    return module
