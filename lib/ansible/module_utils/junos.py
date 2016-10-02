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
import re
import shlex

from distutils.version import LooseVersion

from ansible.module_utils.pycompat24 import get_exception
from ansible.module_utils.network import register_transport, to_list
from ansible.module_utils.network import NetworkError
from ansible.module_utils.shell import CliBase
from ansible.module_utils.six import string_types

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


SUPPORTED_CONFIG_FORMATS = ['text', 'xml']


def xml_to_json(val):
    if isinstance(val, string_types):
        return jxmlease.parse(val)
    else:
        return jxmlease.parse_etree(val)


def xml_to_string(val):
    return etree.tostring(val)


class Netconf(object):

    def __init__(self):
        if not HAS_PYEZ:
            raise NetworkError(
                msg='junos-eznc >= 1.2.2 is required but does not appear to be installed.  '
                'It can be installed using `pip install junos-eznc`'
            )
        if not HAS_JXMLEASE:
            raise NetworkError(
                msg='jxmlease is required but does not appear to be installed.  '
                'It can be installed using `pip install jxmlease`'
            )
        self.device = None
        self.config = None
        self._locked = False
        self._connected = False
        self.default_output = 'xml'

    def raise_exc(self, msg):
        if self.device:
            if self._locked:
                self.config.unlock()
            self.disconnect()
        raise NetworkError(msg)

    def connect(self, params, **kwargs):
        host = params['host']

        kwargs = dict()
        kwargs['port'] = params.get('port') or 830

        kwargs['user'] = params['username']

        if params['password']:
            kwargs['passwd'] = params['password']

        if params['ssh_keyfile']:
            kwargs['ssh_private_key_file'] = params['ssh_keyfile']

        kwargs['gather_facts'] = False

        try:
            self.device = Device(host, **kwargs)
            self.device.open()
        except ConnectError:
            exc = get_exception()
            self.raise_exc('unable to connect to %s: %s' % (host, str(exc)))

        self.config = Config(self.device)
        self._connected = True

    def disconnect(self):
        try:
            self.device.close()
        except AttributeError:
            pass
        self._connected = False

    ### Command methods ###

    def run_commands(self, commands):
        responses = list()

        for cmd in commands:
            meth = getattr(self, cmd.args.get('command_type'))
            responses.append(meth(str(cmd), output=cmd.output))

        for index, cmd in enumerate(commands):
            if cmd.output == 'xml':
                responses[index] = xml_to_json(responses[index])
            elif cmd.args.get('command_type') == 'rpc':
                responses[index] = str(responses[index].text).strip()
            elif 'RpcError' in responses[index]:
                raise NetworkError(responses[index])


        return responses

    def cli(self, commands, output='xml'):
        '''Send commands to the device.'''
        try:
            return self.device.cli(commands, format=output, warning=False)
        except (ValueError, RpcError):
            exc = get_exception()
            self.raise_exc('Unable to get cli output: %s' % str(exc))

    def rpc(self, command, output='xml'):
        name, kwargs = rpc_args(command)
        meth = getattr(self.device.rpc, name)
        reply = meth({'format': output}, **kwargs)
        return reply

    ### Config methods ###

    def get_config(self, config_format="text"):
        if config_format not in SUPPORTED_CONFIG_FORMATS:
            self.raise_exc(msg='invalid config format.  Valid options are '
                               '%s' % ', '.join(SUPPORTED_CONFIG_FORMATS))

        ele = self.rpc('get_configuration', output=config_format)

        if config_format == 'text':
            return unicode(ele.text).strip()
        else:
            return ele

    def load_config(self, config, commit=False, replace=False, confirm=None,
                    comment=None, config_format='text', overwrite=False):

        if all([replace, overwrite]):
            self.raise_exc('setting both replace and overwrite to True is invalid')

        if replace:
            merge = False
            overwrite = False
        elif overwrite:
            merge = True
            overwrite = False
        else:
            merge = True
            overwrite = False

        if overwrite and config_format == 'set':
            self.raise_exc('replace cannot be True when config_format is `set`')

        self.lock_config()

        try:
            candidate = '\n'.join(config)
            self.config.load(candidate, format=config_format, merge=merge,
                             overwrite=overwrite)

        except ConfigLoadError:
            exc = get_exception()
            self.raise_exc('Unable to load config: %s' % str(exc))

        diff = self.config.diff()

        self.check_config()

        if all((commit, diff)):
            self.commit_config(comment=comment, confirm=confirm)

        self.unlock_config()

        return diff

    def save_config(self):
        raise NotImplementedError

    ### end of Config ###

    def get_facts(self, refresh=True):
        if refresh:
            self.device.facts_refresh()
        return self.device.facts

    def unlock_config(self):
        try:
            self.config.unlock()
            self._locked = False
        except UnlockError:
            exc = get_exception()
            raise NetworkError('unable to unlock config: %s' % str(exc))

    def lock_config(self):
        try:
            self.config.lock()
            self._locked = True
        except LockError:
            exc = get_exception()
            raise NetworkError('unable to lock config: %s' % str(exc))

    def check_config(self):
        if not self.config.commit_check():
            self.raise_exc(msg='Commit check failed')

    def commit_config(self, comment=None, confirm=None):
        try:
            kwargs = dict(comment=comment)
            if confirm and confirm > 0:
                kwargs['confirm'] = confirm
            return self.config.commit(**kwargs)
        except CommitError:
            exc = get_exception()
            raise NetworkError('unable to commit config: %s' % str(exc))

    def confirm_commit(self, checkonly=False):
        try:
            resp = self.rpc('get_commit_information')
            needs_confirm = 'commit confirmed, rollback' in resp[0][4].text
            if checkonly:
                return needs_confirm
            return self.commit_config()
        except IndexError:
            # if there is no comment tag, the system is not in a commit
            # confirmed state so just return
            pass

    def rollback_config(self, identifier, commit=True, comment=None):

        self.lock_config()

        try:
            self.config.rollback(identifier)
        except ValueError:
            exc = get_exception()
            self.raise_exc('Unable to rollback config: $s' % str(exc))

        diff = self.config.diff()
        if commit:
            self.commit_config(comment=comment)

        self.unlock_config()
        return diff

Netconf = register_transport('netconf')(Netconf)


class Cli(CliBase):

    CLI_PROMPTS_RE = [
        re.compile(r"[\r\n]?[\w+\-\.:\/\[\]]+(?:\([^\)]+\)){,3}(?:>|#) ?$"),
        re.compile(r"\[\w+\@[\w\-\.]+(?: [^\]])\] ?[>#\$] ?$")
    ]

    CLI_ERRORS_RE = [
        re.compile(r"unkown command")
    ]

    def connect(self, params, **kwargs):
        super(Cli, self).connect(params, **kwargs)
        if self.shell._matched_prompt.strip().endswith('%'):
            self.execute('cli')
        self.execute('set cli screen-length 0')

    def configure(self, commands, comment=None):
        cmds = ['configure']
        cmds.extend(to_list(commands))

        if comment:
            cmds.append('commit and-quit comment "%s"' % comment)
        else:
            cmds.append('commit and-quit')

        responses = self.execute(cmds)
        return responses[1:-1]

Cli = register_transport('cli', default=True)(Cli)

def split(value):
    lex = shlex.shlex(value)
    lex.quotes = '"'
    lex.whitespace_split = True
    lex.commenters = ''
    return list(lex)

def rpc_args(args):
    kwargs = dict()
    args = split(args)
    name = args.pop(0)
    for arg in args:
        key, value = arg.split('=')
        if str(value).upper() in ['TRUE', 'FALSE']:
            kwargs[key] = bool(value)
        elif re.match(r'^[0-9]+$', value):
            kwargs[key] = int(value)
        else:
            kwargs[key] = str(value)
    return (name, kwargs)
