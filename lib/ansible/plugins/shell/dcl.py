# Copyright (c) 2014, Chris Church <chris@ninemoreminutes.com>
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
from ansible.module_utils.six import text_type
from ansible.module_utils.six.moves import shlex_quote
import ansible.plugins.action.dcl
from ansible.plugins.shell.sh import ShellModule as ShModule
from ansible.utils.display import Display


DOCUMENTATION = '''
    name: dcl
    plugin_type: shell
    version_added: ""
    short_description: DCL shell OpenVMS COmmand line, no separate command...
    description:
      - This is to support OpenVMS,
    extends_documentation_fragment:
      - shell_common
'''


class ShellModule(ShModule):

    # Common shell filenames that this plugin handles
    COMPATIBLE_SHELLS = frozenset(('dcl',))
    # Family of shells this has.  Must match the filename without extension
    SHELL_FAMILY = 'dcl'
    IS_OPENVMS = True
    # commonly used
    ECHO = 'WRITE SYS$OUTPUT'
    COMMAND_SEP = '\n'

    # This is needed for?
    _SHELL_EMBEDDED_PY_EOL = '\n'
    # The next can be done by prepending command with a few extra lines
    #     $ sts = $STATUS  ! keep status
    #     $ DEFINE/USER SYS$OUTPUT NL:  ! these will clobber the dcl status
    #     $ DEFINE/USER SYS$ERROR NL:
    #     $ $STATUS = sts  ! restor previous command's status
    # when generating a script the $ prefix is mandatory, when issuing commands they should be left out.
    _SHELL_REDIRECT_ALLNULL = '\nsts = $STATUS\nDEFINE/USER SYS$OUTPUT NL:\nDEFINE/USER SYS$ERROR NL:\n$STATUS = sts'
    # The next should be prepended to the command
    _SHELL_AND = '\nIF $status THEN '
    # Following are unsupported....
    _SHELL_OR = ''
    _SHELL_SUB_LEFT = ''
    _SHELL_SUB_RIGHT = ''
    _SHELL_GROUP_LEFT = ''
    _SHELL_GROUP_RIGHT = ''

    # can only be done by adding assignment before the command...
    # NOT AFTER IF ... THEN... Quoting will be an issue....
    # strings: "......"
    # variable expansion: 'var' (early, before CLI parsing) &var (late, during CLI parsing)
    #                     ''var'    when variables are inside a string.
    # escaping a "  double up..  "what""ever"""   will show as: what"ever" when printed...
    def env_prefix(self, **kwargs):
        env = self.env.copy()
        env.update(kwargs)
        return ' '.join(['\n$ %s=%s' % (k, shlex_quote(text_type(v))) for k, v in env.items()])

    def get_remote_filename(self, pathname):
        '''
        parse filename from:    remote"user password"::device:[dirpath]filename.type;version
        all parts are optional... including markings ", :, []/<> . ; is non present.
        '''
        if '/' in pathname:
            base_name = os.path.basename(pathname.strip())
            return base_name.strip()
        else:
            display = Display()

            remote = None  
            unparsed = pathname
            display.vvv(unparsed)
            if '::' in unparsed:
                (remote, unparsed) = unparsed.split('::')
                if '"' in remote and remote[-1:] == '"':
                    (node, username) = remote.split('"')
                    if ' ' in username:
                        (username, password) = username.split(' ')
                    else:
                        password = None
                else:
                    node = remote
                    username = None
                    password = None

            display.vvv(unparsed)
            if ':' in unparsed:
                (device, unparsed) = unparsed.split(':')

            display.vvv(unparsed)
            if unparsed[0] == '<' and '>' in unparsed:
                (dirpart, unparsed) = unparsed.split('>')
                dirpath = dirpart.split('<')[1].split('.')
            elif unparsed[0] == '[' and ']' in unparsed:
                (dirpart, unparsed) = unparsed.split(']')
                dirpath = dirpart.split('[')[1].split('.')
            else:
                dirpath =  []

            display.vvv(unparsed)
            if ';' in unparsed:
                (unparsed, version) = unparsed.split(';')

            display.vvv(unparsed)
            if '.' in unparsed:
                (unparsed, filetype) = unparsed.split('.')

            display.vvv(unparsed)
            filename = unparsed
            # this may need more validation ...
            return filename + '.' + filetype

    def join_path(self, *args):
        '''
        Join normal entries, no remote specs
        assume: first  is device, next are directories , last part is filename
        '''
        if type(args) == 'list':
            if args.count == 1:
                # Assume filename
                return args.item()
            if args.count == 2:
                # Assume top of a device... dir = [000000]
                return args[0] + ':[000000]' + args[1]
            return args[0] + ':[' + '.'.join(args[1:-2]) + ']' + args[-1]
        else:
            return ' '.join(args)

    # rwx -> RWED W implies D.
    prot_table = ['', ':E', ':WD', ':WED', ':R', ':RE', ':RWD', ':RWED']
    prot_chars = {'r': ':R', 'w': ':WD', 'x': ':E', 'rw': ':RWD', 'wr': ':RWD',
                  'rx': ':RE', 'xr': ':RE', 'wx': ':WED', 'xw': ':WED',
                  'rwx': ':RWED', 'rxw': ':RWED', 'wrx': ':RWED', 'wxr': ':RWED',
                  'xwr': ':RWED'}

    def unix2vms_mode(self, mode):
        display = Display()
        display.vvv('Handling mode' + mode)
        prot = ['S:RWED']
        if type(mode) == 'int':
            world = 'W' + self.prot_table[mode & 0o007]
            group = 'G' + self.prot_table[(mode >> 3) & 0o007]
            user  = 'U' + self.prot_table[(mode >> 6) & 0o007]
            prot.append([user, group, world])
        else:
            if '+' in mode:
                (who, flag) = mode.split('+')
                if 'u' in who:
                    prot.append('U:' + self.prot_chars[flag])
                if 'g' in who:
                    prot.append('G:' + self.prot_chars[flag])
                if 'o' in who:
                    prot.append('W:' + self.prot_chars[flag])

            if '-' in mode:
                (who, flag) = mode.split('-')
                display.vvv('DCL: subtractive mode not supported')
        return '(' + ','.join(prot) + ')'

    def chmod(self, paths, mode):
        cmd = ['set', 'file', '/protection=' + self.unix2vms_mode(mode)]
        cmd.extend(paths)
        return ' '.join(cmd)

    def chown(self, paths, user):
        cmd = ['set', 'file', '/owner=', user]
        cmd.extend(paths)
        return ' '.join(cmd)

    def mkdtemp(self, basefile=None, system=False, mode=0o700, tmpdir=None):
        '''
        Bit involved.......
        needs Work, like create a directory in sys$scratch and return that name...
        '''
        return ''

    def expand_user(self, user_home_path, username=''):
        '''
        use vms logical SYS$LOGIN:
        '''
        return 'WRITE SYS$OUTPUT F$TRNLNM("SYS$LOGIN")'

    def pwd(self):
        '''
        show default
        '''
        return 'SHOW DEFAULT'

    def quote(self, cmd):
        '''
        No quoting
        '''
        return cmd
