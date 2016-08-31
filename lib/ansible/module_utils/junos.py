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

from ansible.module_utils.pycompat24 import get_exception
from ansible.module_utils.network import NetworkError, register_transport, to_list
from ansible.module_utils.shell import CliBase
from ansible.module_utils.six import string_types

# temporary fix until modules are update.  to be removed before 2.2 final
from ansible.module_utils.network import get_module

try:
    from jnpr.junos import Device
    from jnpr.junos.utils.config import Config
    from jnpr.junos.version import VERSION
    from jnpr.junos.exception import RpcError, ConnectError, ConfigLoadError, CommitError
    from jnpr.junos.exception import LockError, UnlockError
    if LooseVersion(VERSION) < LooseVersion('1.2.2'):
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


def xml_to_json(val):
    if isinstance(val, string_types):
        return jxmlease.parse(val)
    else:
        return jxmlease.parse_etree(val)


def xml_to_string(val):
    return etree.tostring(val)


class Netconf(object):

    def __init__(self):
        self.device = None
        self.config = None
        self._locked = False
        self._connected = False

    def _error(self, msg):
        if self.device:
            if self._locked:
                self.config.unlock()
            self.disconnect()
        raise NetworkError(msg)

    def _log(self, msg):
        # Logging is a complex topic and a discussion will be started after 2.2
        # is released
        pass

    def connect(self, params, **kwargs):
        host = params['host']
        port = params.get('port') or 830

        user = params['username']
        passwd = params['password']

        try:
            self.device = Device(host, user=user, passwd=passwd, port=port, gather_facts=False).open()
        except ConnectError:
            exc = get_exception()
            self._error('unable to connect to %s: %s' % (host, str(exc)))

        self.config = Config(self.device)
        self._connected = True

    def disconnect(self):
        if self.device:
            self.device.close()
        self._connected = False

    ### Command methods ###

    def run_commands(self, commands, **kwargs):
        output = kwargs.get('format') or 'xml'
        return self.execute(to_list(commands), format=output)

    def execute(self, commands, format='xml', **kwargs):
        '''Send commands to the device.'''
        try:
            return self.device.cli(commands, format=format)
        except (ValueError, RpcError):
            exc = get_exception()
            self._error('Unable to get cli output: %s' % str(exc))

    ### Config methods ###

    def unlock_config(self):
        try:
            self.config.unlock()
            self._locked = False
        except UnlockError:
            exc = get_exception()
            self._log('unable to unlock config: %s' % str(exc))

    def lock_config(self):
        try:
            self.config.lock()
            self._locked = True
        except LockError:
            exc = get_exception()
            self._log('unable to lock config: %s' % str(exc))

    def check_config(self):
        if not self.config.commit_check():
            self._error(msg='Commit check failed')

    def commit_config(self, comment=None, confirm=None):
        try:
            kwargs = dict(comment=comment)
            if confirm and confirm > 0:
                kwargs['confirm'] = confirm
            return self.config.commit(**kwargs)
        except CommitError:
            exc = get_exception()
            self._error('Unable to commit configuration: %s' % str(exc))

    def load_config(self, candidate, action='replace', comment=None, confirm=None, format='text', commit=True):

        merge = action == 'merge'
        overwrite = action == 'overwrite'

        self.lock_config()

        try:
            self.config.load(candidate, format=format, merge=merge, overwrite=overwrite)
        except ConfigLoadError:
            exc = get_exception()
            self._error('Unable to load config: %s' % str(exc))

        diff = self.config.diff()
        self.check_config()
        if commit and diff:
            self.commit_config(comment=comment, confirm=confirm)

        self.unlock_config()

        return diff

    def rollback_config(self, identifier, commit=True, comment=None):

        self.lock_config()

        try:
            self.config.rollback(identifier)
        except ValueError:
            exc = get_exception()
            self._error('Unable to rollback config: $s' % str(exc))

        diff = self.config.diff()
        if commit:
            self.commit_config(comment=comment)

        self.unlock_config()
        return diff

    def get_facts(self, refresh=True):
        if refresh:
            self.device.facts_refresh()
        return self.device.facts

    def get_config(self, config_format="text"):
        if config_format not in ['text', 'set', 'xml']:
            msg = 'invalid config format... must be one of xml, text, set'
            self._error(msg=msg)

        ele = self.rpc('get_configuration', format=config_format)
        if config_format in ['text', 'set']:
            return str(ele.text).strip()
        elif config_format == "xml":
            return ele

    def rpc(self, name, format='xml', **kwargs):
        meth = getattr(self.device.rpc, name)
        reply = meth({'format': format}, **kwargs)
        return reply
Netconf = register_transport('netconf')(Netconf)


class Cli(CliBase):

    CLI_PROMPTS_RE = [
        re.compile(r"[\r\n]?[\w+\-\.:\/\[\]]+(?:\([^\)]+\)){,3}(?:>|#) ?$"),
        re.compile(r"\[\w+\@[\w\-\.]+(?: [^\]])\] ?[>#\$] ?$")
    ]

    CLI_ERRORS_RE = [
        re.compile(r"% ?Error"),
        re.compile(r"% ?Bad secret"),
        re.compile(r"invalid input", re.I),
        re.compile(r"(?:incomplete|ambiguous) command", re.I),
        re.compile(r"connection timed out", re.I),
        re.compile(r"[^\r\n]+ not found", re.I),
        re.compile(r"'[^']' +returned error code: ?\d+"),
    ]

    def connect(self, params, **kwargs):
        super(Cli, self).connect(params, **kwargs)

        if self.shell._matched_prompt.strip().endswith('%'):
            self.execute('cli')
        self.execute('set cli screen-length 0')

    def authorize(self, params, **kwargs):
        raise NotImplementedError

    ### Config methods ###

    def configure(self, commands, **kwargs):
        cmds = ['configure']
        cmds.extend(to_list(commands))

        if kwargs.get('comment'):
            cmds.append('commit and-quit comment "%s"' % kwargs.get('comment'))
        else:
            cmds.append('commit and-quit')

        responses = self.execute(cmds)
        return responses[1:-1]

    def get_config(self, include_defaults=False, **kwargs):
        raise NotImplementedError

    def save_config(self):
        self.execute(['copy running-config startup-config'])
Cli = register_transport('cli', default=True)(Cli)
