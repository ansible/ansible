import base64
import os
import re
import random
import shlex
import time

class ShellModule(object):

    def __init__(self):
        pass

    def _escape(self, value, include_vars=False):
        '''
        Return value escaped for use in PowerShell command.
        '''
        # http://www.techotopia.com/index.php/Windows_PowerShell_1.0_String_Quoting_and_Escape_Sequences
        # http://stackoverflow.com/questions/764360/a-list-of-string-replacements-in-python
        subs = [('\n', '`n'), ('\r', '`r'), ('\t', '`t'), ('\a', '`a'),
                ('\b', '`b'), ('\f', '`f'), ('\v', '`v'), ('"', '`"'),
                ('\'', '`\''), ('`', '``'), ('\x00', '`0')]
        if include_vars:
            subs.append(('$', '`$'))
        pattern = '|'.join('(%s)' % re.escape(p) for p, s in subs)
        substs = [s for p, s in subs]
        replace = lambda m: substs[m.lastindex - 1]
        return re.sub(pattern, replace, value)

    def _get_script_cmd(self, script):
        '''
        Convert a PowerShell script to a single base64-encoded command.
        '''
        encoded_script = base64.b64encode(script.encode('utf-16-le'))
        return ' '.join(['PowerShell', '-NoProfile', '-NonInteractive',
                         '-EncodedCommand', encoded_script])

    def env_prefix(self, **kwargs):
        return ''

    def join_path(self, *args):
        return os.path.join(*args).replace('/', '\\')

    def chmod(self, mode, path):
        return ''

    def remove(self, path, recurse=False):
        path = self._escape(path)
        if recurse:
            return self._get_script_cmd('''Remove-Item "%s" -Force -Recurse;''' % path)
        else:
            return self._get_script_cmd('''Remove-Item "%s" -Force;''' % path)

    def mkdtemp(self, basefile=None, system=False, mode=None):
        if not basefile:
            basefile = 'ansible-tmp-%s-%s' % (time.time(), random.randint(0, 2**48))
        basefile = self._escape(basefile)
        # FIXME: Support system temp path!
        return self._get_script_cmd('''(New-Item -Type Directory -Path $env:temp -Name "%s").FullName;''' % basefile)

    def md5(self, path):
        path = self._escape(path)
        return self._get_script_cmd('''(Get-FileHash -Path "%s" -Algorithm MD5).Hash.ToLower();''' % path)

    def build_module_command(self, env_string, shebang, cmd, rm_tmp=None):
        cmd_parts = shlex.split(cmd, posix=False)
        if not cmd_parts[0].lower().endswith('.ps1'):
            cmd_parts[0] = '%s.ps1' % cmd_parts[0]
        cmd_parts = ['PowerShell', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Unrestricted', '-File'] + ['"%s"' % x for x in cmd_parts]
        script = ' '.join(cmd_parts)
        if rm_tmp:
            script = '%s; Remove-Item "%s" -Force -Recurse;' % (script, self._escape(rm_tmp))
        return self._get_script_cmd(script)
