# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
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

import sys
import re
import os
import shlex
import yaml
import copy
import optparse
import operator
from ansible import errors
from ansible import __version__
from ansible.utils import template
from ansible.utils.display_functions import *
from ansible.utils.plugins import *
from ansible.callbacks import display
import ansible.constants as C
import ast
import time
import StringIO
import stat
import termios
import tty
import pipes
import random
import difflib
import warnings
import traceback
import getpass
import sys
import json

#import vault
from vault import VaultLib

VERBOSITY=0

MAX_FILE_SIZE_FOR_DIFF=1*1024*1024

try:
    import json
except ImportError:
    import simplejson as json

try:
    from hashlib import md5 as _md5
except ImportError:
    from md5 import md5 as _md5

PASSLIB_AVAILABLE = False
try:
    import passlib.hash
    PASSLIB_AVAILABLE = True
except:
    pass

KEYCZAR_AVAILABLE=False
try:
    try:
        # some versions of pycrypto may not have this?
        from Crypto.pct_warnings import PowmInsecureWarning
    except ImportError:
        PowmInsecureWarning = RuntimeWarning

    with warnings.catch_warnings(record=True) as warning_handler:
        warnings.simplefilter("error", PowmInsecureWarning)
        try:
            import keyczar.errors as key_errors
            from keyczar.keys import AesKey
        except PowmInsecureWarning:
            system_warning(
                "The version of gmp you have installed has a known issue regarding " + \
                "timing vulnerabilities when used with pycrypto. " + \
                "If possible, you should update it (ie. yum update gmp)."
            )
            warnings.resetwarnings()
            warnings.simplefilter("ignore")
            import keyczar.errors as key_errors
            from keyczar.keys import AesKey
        KEYCZAR_AVAILABLE=True
except ImportError:
    pass

###############################################################
# Abstractions around keyczar
###############################################################

def key_for_hostname(hostname):
    # fireball mode is an implementation of ansible firing up zeromq via SSH
    # to use no persistent daemons or key management

    if not KEYCZAR_AVAILABLE:
        raise errors.AnsibleError("python-keyczar must be installed on the control machine to use accelerated modes")

    key_path = os.path.expanduser(C.ACCELERATE_KEYS_DIR)
    if not os.path.exists(key_path):
        os.makedirs(key_path, mode=0700)
        os.chmod(key_path, int(C.ACCELERATE_KEYS_DIR_PERMS, 8))
    elif not os.path.isdir(key_path):
        raise errors.AnsibleError('ACCELERATE_KEYS_DIR is not a directory.')

    if stat.S_IMODE(os.stat(key_path).st_mode) != int(C.ACCELERATE_KEYS_DIR_PERMS, 8):
        raise errors.AnsibleError('Incorrect permissions on the private key directory. Use `chmod 0%o %s` to correct this issue, and make sure any of the keys files contained within that directory are set to 0%o' % (int(C.ACCELERATE_KEYS_DIR_PERMS, 8), C.ACCELERATE_KEYS_DIR, int(C.ACCELERATE_KEYS_FILE_PERMS, 8)))

    key_path = os.path.join(key_path, hostname)

    # use new AES keys every 2 hours, which means fireball must not allow running for longer either
    if not os.path.exists(key_path) or (time.time() - os.path.getmtime(key_path) > 60*60*2):
        key = AesKey.Generate()
        fd = os.open(key_path, os.O_WRONLY | os.O_CREAT, int(C.ACCELERATE_KEYS_FILE_PERMS, 8))
        fh = os.fdopen(fd, 'w')
        fh.write(str(key))
        fh.close()
        return key
    else:
        if stat.S_IMODE(os.stat(key_path).st_mode) != int(C.ACCELERATE_KEYS_FILE_PERMS, 8):
            raise errors.AnsibleError('Incorrect permissions on the key file for this host. Use `chmod 0%o %s` to correct this issue.' % (int(C.ACCELERATE_KEYS_FILE_PERMS, 8), key_path))
        fh = open(key_path)
        key = AesKey.Read(fh.read())
        fh.close()
        return key

def encrypt(key, msg):
    return key.Encrypt(msg)

def decrypt(key, msg):
    try:
        return key.Decrypt(msg)
    except key_errors.InvalidSignatureError:
        raise errors.AnsibleError("decryption failed")

###############################################################
# UTILITY FUNCTIONS FOR COMMAND LINE TOOLS
###############################################################

def err(msg):
    ''' print an error message to stderr '''

    print >> sys.stderr, msg

def exit(msg, rc=1):
    ''' quit with an error to stdout and a failure code '''

    err(msg)
    sys.exit(rc)

def jsonify(result, format=False):
    ''' format JSON output (uncompressed or uncompressed) '''

    if result is None:
        return "{}"
    result2 = result.copy()
    for key, value in result2.items():
        if type(value) is str:
            result2[key] = value.decode('utf-8', 'ignore')
    if format:
        return json.dumps(result2, sort_keys=True, indent=4)
    else:
        return json.dumps(result2, sort_keys=True)

def write_tree_file(tree, hostname, buf):
    ''' write something into treedir/hostname '''

    # TODO: might be nice to append playbook runs per host in a similar way
    # in which case, we'd want append mode.
    path = os.path.join(tree, hostname)
    fd = open(path, "w+")
    fd.write(buf)
    fd.close()

def is_failed(result):
    ''' is a given JSON result a failed result? '''

    return ((result.get('rc', 0) != 0) or (result.get('failed', False) in [ True, 'True', 'true']))

def is_changed(result):
    ''' is a given JSON result a changed result? '''

    return (result.get('changed', False) in [ True, 'True', 'true'])

def check_conditional(conditional, basedir, inject, fail_on_undefined=False):

    if conditional is None or conditional == '':
        return True

    if isinstance(conditional, list):
        for x in conditional:
            if not check_conditional(x, basedir, inject, fail_on_undefined=fail_on_undefined):
                return False
        return True

    if not isinstance(conditional, basestring):
        return conditional

    conditional = conditional.replace("jinja2_compare ","")
    # allow variable names
    if conditional in inject and '-' not in str(inject[conditional]):
        conditional = inject[conditional]
    conditional = template.template(basedir, conditional, inject, fail_on_undefined=fail_on_undefined)
    original = str(conditional).replace("jinja2_compare ","")
    # a Jinja2 evaluation that results in something Python can eval!
    presented = "{%% if %s %%} True {%% else %%} False {%% endif %%}" % conditional
    conditional = template.template(basedir, presented, inject)
    val = conditional.strip()
    if val == presented:
        # the templating failed, meaning most likely a 
        # variable was undefined. If we happened to be 
        # looking for an undefined variable, return True,
        # otherwise fail
        if "is undefined" in conditional:
            return True
        elif "is defined" in conditional:
            return False
        else:
            raise errors.AnsibleError("error while evaluating conditional: %s" % original)
    elif val == "True":
        return True
    elif val == "False":
        return False
    else:
        raise errors.AnsibleError("unable to evaluate conditional: %s" % original)

def is_executable(path):
    '''is the given path executable?'''
    return (stat.S_IXUSR & os.stat(path)[stat.ST_MODE]
            or stat.S_IXGRP & os.stat(path)[stat.ST_MODE]
            or stat.S_IXOTH & os.stat(path)[stat.ST_MODE])

def unfrackpath(path):
    ''' 
    returns a path that is free of symlinks, environment
    variables, relative path traversals and symbols (~)
    example:
    '$HOME/../../var/mail' becomes '/var/spool/mail'
    '''
    return os.path.normpath(os.path.realpath(os.path.expandvars(os.path.expanduser(path))))

def prepare_writeable_dir(tree,mode=0777):
    ''' make sure a directory exists and is writeable '''

    # modify the mode to ensure the owner at least
    # has read/write access to this directory
    mode |= 0700

    # make sure the tree path is always expanded
    # and normalized and free of symlinks
    tree = unfrackpath(tree)

    if not os.path.exists(tree):
        try:
            os.makedirs(tree, mode)
        except (IOError, OSError), e:
            raise errors.AnsibleError("Could not make dir %s: %s" % (tree, e))
    if not os.access(tree, os.W_OK):
        raise errors.AnsibleError("Cannot write to path %s" % tree)
    return tree

def path_dwim(basedir, given):
    '''
    make relative paths work like folks expect.
    '''

    if given.startswith("/"):
        return os.path.abspath(given)
    elif given.startswith("~"):
        return os.path.abspath(os.path.expanduser(given))
    else:
        if basedir is None:
            basedir = "."
        return os.path.abspath(os.path.join(basedir, given))

def path_dwim_relative(original, dirname, source, playbook_base, check=True):
    ''' find one file in a directory one level up in a dir named dirname relative to current '''
    # (used by roles code)

    basedir = os.path.dirname(original)
    if os.path.islink(basedir):
        basedir = unfrackpath(basedir)
        template2 = os.path.join(basedir, dirname, source)
    else:
        template2 = os.path.join(basedir, '..', dirname, source)
    source2 = path_dwim(basedir, template2)
    if os.path.exists(source2):
        return source2
    obvious_local_path = path_dwim(playbook_base, source)
    if os.path.exists(obvious_local_path):
        return obvious_local_path
    if check:
        raise errors.AnsibleError("input file not found at %s or %s" % (source2, obvious_local_path))
    return source2 # which does not exist

def json_loads(data):
    ''' parse a JSON string and return a data structure '''

    return json.loads(data)

def parse_json(raw_data):
    ''' this version for module return data only '''

    orig_data = raw_data

    # ignore stuff like tcgetattr spewage or other warnings
    data = filter_leading_non_json_lines(raw_data)

    try:
        return json.loads(data)
    except:
        # not JSON, but try "Baby JSON" which allows many of our modules to not
        # require JSON and makes writing modules in bash much simpler
        results = {}
        try:
            tokens = shlex.split(data)
        except:
            print "failed to parse json: "+ data
            raise

        for t in tokens:
            if "=" not in t:
                raise errors.AnsibleError("failed to parse: %s" % orig_data)
            (key,value) = t.split("=", 1)
            if key == 'changed' or 'failed':
                if value.lower() in [ 'true', '1' ]:
                    value = True
                elif value.lower() in [ 'false', '0' ]:
                    value = False
            if key == 'rc':
                value = int(value)
            results[key] = value
        if len(results.keys()) == 0:
            return { "failed" : True, "parsed" : False, "msg" : orig_data }
        return results

def smush_braces(data):
    ''' smush Jinaj2 braces so unresolved templates like {{ foo }} don't get parsed weird by key=value code '''
    while '{{ ' in data:
        data = data.replace('{{ ', '{{')
    while ' }}' in data:
        data = data.replace(' }}', '}}')
    return data

def smush_ds(data):
    # things like key={{ foo }} are not handled by shlex.split well, so preprocess any YAML we load
    # so we do not have to call smush elsewhere
    if type(data) == list:
        return [ smush_ds(x) for x in data ]
    elif type(data) == dict:
        for (k,v) in data.items():
            data[k] = smush_ds(v)
        return data
    elif isinstance(data, basestring):
        return smush_braces(data)
    else:
        return data

def parse_yaml(data, path_hint=None):
    ''' convert a yaml string to a data structure.  Also supports JSON, ssssssh!!!'''

    stripped_data = data.lstrip()
    loaded = None
    if stripped_data.startswith("{") or stripped_data.startswith("["):
        # since the line starts with { or [ we can infer this is a JSON document.
        try:
            loaded = json.loads(data)
        except ValueError, ve:
            if path_hint:
                raise errors.AnsibleError(path_hint + ": " + str(ve))
            else:
                raise errors.AnsibleError(str(ve))
    else:
        # else this is pretty sure to be a YAML document
        loaded = yaml.safe_load(data)

    return smush_ds(loaded)

def process_common_errors(msg, probline, column):
    replaced = probline.replace(" ","")

    if ":{{" in replaced and "}}" in replaced:
        msg = msg + """
This one looks easy to fix.  YAML thought it was looking for the start of a 
hash/dictionary and was confused to see a second "{".  Most likely this was
meant to be an ansible template evaluation instead, so we have to give the 
parser a small hint that we wanted a string instead. The solution here is to 
just quote the entire value.

For instance, if the original line was:

    app_path: {{ base_path }}/foo

It should be written as:

    app_path: "{{ base_path }}/foo"
"""
        return msg

    elif len(probline) and len(probline) > 1 and len(probline) > column and probline[column] == ":" and probline.count(':') > 1:
        msg = msg + """
This one looks easy to fix.  There seems to be an extra unquoted colon in the line 
and this is confusing the parser. It was only expecting to find one free 
colon. The solution is just add some quotes around the colon, or quote the 
entire line after the first colon.

For instance, if the original line was:

    copy: src=file.txt dest=/path/filename:with_colon.txt

It can be written as:

    copy: src=file.txt dest='/path/filename:with_colon.txt'

Or:
    
    copy: 'src=file.txt dest=/path/filename:with_colon.txt'


"""
        return msg
    else:
        parts = probline.split(":")
        if len(parts) > 1:
            middle = parts[1].strip()
            match = False
            unbalanced = False
            if middle.startswith("'") and not middle.endswith("'"):
                match = True
            elif middle.startswith('"') and not middle.endswith('"'):
                match = True
            if len(middle) > 0 and middle[0] in [ '"', "'" ] and middle[-1] in [ '"', "'" ] and probline.count("'") > 2 or probline.count('"') > 2:
                unbalanced = True
            if match:
                msg = msg + """
This one looks easy to fix.  It seems that there is a value started 
with a quote, and the YAML parser is expecting to see the line ended 
with the same kind of quote.  For instance:

    when: "ok" in result.stdout

Could be written as:

   when: '"ok" in result.stdout'

or equivalently:

   when: "'ok' in result.stdout"

"""
                return msg

            if unbalanced:
                msg = msg + """
We could be wrong, but this one looks like it might be an issue with 
unbalanced quotes.  If starting a value with a quote, make sure the 
line ends with the same set of quotes.  For instance this arbitrary 
example:

    foo: "bad" "wolf"

Could be written as:

    foo: '"bad" "wolf"'

"""
                return msg

    return msg

def process_yaml_error(exc, data, path=None, show_content=True):
    if hasattr(exc, 'problem_mark'):
        mark = exc.problem_mark
        if show_content:
            if mark.line -1 >= 0:
                before_probline = data.split("\n")[mark.line-1]
            else:
                before_probline = ''
            probline = data.split("\n")[mark.line]
            arrow = " " * mark.column + "^"
            msg = """Syntax Error while loading YAML script, %s
Note: The error may actually appear before this position: line %s, column %s

%s
%s
%s""" % (path, mark.line + 1, mark.column + 1, before_probline, probline, arrow)

            unquoted_var = None
            if '{{' in probline and '}}' in probline:
                if '"{{' not in probline or "'{{" not in probline:
                    unquoted_var = True

            msg = process_common_errors(msg, probline, mark.column)
            if not unquoted_var:
                msg = process_common_errors(msg, probline, mark.column)
            else:
                msg = msg + """
We could be wrong, but this one looks like it might be an issue with
missing quotes.  Always quote template expression brackets when they 
start a value. For instance:            

    with_items:
      - {{ foo }}

Should be written as:

    with_items:
      - "{{ foo }}"      

"""
                msg = process_common_errors(msg, probline, mark.column)
        else:
            # most likely displaying a file with sensitive content,
            # so don't show any of the actual lines of yaml just the
            # line number itself
            msg = """Syntax error while loading YAML script, %s
The error appears to have been on line %s, column %s, but may actually
be before there depending on the exact syntax problem.
""" % (path, mark.line + 1, mark.column + 1)

    else:
        # No problem markers means we have to throw a generic
        # "stuff messed up" type message. Sry bud.
        if path:
            msg = "Could not parse YAML. Check over %s again." % path
        else:
            msg = "Could not parse YAML."
    raise errors.AnsibleYAMLValidationFailed(msg)


def parse_yaml_from_file(path, vault_password=None):
    ''' convert a yaml file to a data structure '''

    data = None
    show_content = True

    try:
        data = open(path).read()
    except IOError:
        raise errors.AnsibleError("file could not read: %s" % path)

    vault = VaultLib(password=vault_password)
    if vault.is_encrypted(data):
        data = vault.decrypt(data)
        show_content = False

    try:
        return parse_yaml(data, path_hint=path)
    except yaml.YAMLError, exc:
        process_yaml_error(exc, data, path, show_content)

def parse_kv(args):
    ''' convert a string of key/value items to a dict '''
    options = {}
    if args is not None:
        # attempting to split a unicode here does bad things
        args = args.encode('utf-8')
        try:
            vargs = shlex.split(args, posix=True)
        except ValueError, ve:
            if 'no closing quotation' in str(ve).lower():
                raise errors.AnsibleError("error parsing argument string, try quoting the entire line.")
            else:
                raise
        vargs = [x.decode('utf-8') for x in vargs]
        for x in vargs:
            if "=" in x:
                k, v = x.split("=",1)
                options[k]=v
    return options

def merge_hash(a, b):
    ''' recursively merges hash b into a
    keys from b take precedence over keys from a '''

    result = copy.deepcopy(a)

    # next, iterate over b keys and values
    for k, v in b.iteritems():
        # if there's already such key in a
        # and that key contains dict
        if k in result and isinstance(result[k], dict):
            # merge those dicts recursively
            result[k] = merge_hash(a[k], v)
        else:
            # otherwise, just copy a value from b to a
            result[k] = v

    return result

def md5s(data):
    ''' Return MD5 hex digest of data. '''

    digest = _md5()
    try:
        digest.update(data)
    except UnicodeEncodeError:
        digest.update(data.encode('utf-8'))
    return digest.hexdigest()

def md5(filename):
    ''' Return MD5 hex digest of local file, or None if file is not present. '''

    if not os.path.exists(filename):
        return None
    digest = _md5()
    blocksize = 64 * 1024
    try:
        infile = open(filename, 'rb')
        block = infile.read(blocksize)
        while block:
            digest.update(block)
            block = infile.read(blocksize)
        infile.close()
    except IOError, e:
        raise errors.AnsibleError("error while accessing the file %s, error was: %s" % (filename, e))
    return digest.hexdigest()

def default(value, function):
    ''' syntactic sugar around lazy evaluation of defaults '''
    if value is None:
        return function()
    return value

def _gitinfo():
    ''' returns a string containing git branch, commit id and commit date '''
    result = None
    repo_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.git')

    if os.path.exists(repo_path):
        # Check if the .git is a file. If it is a file, it means that we are in a submodule structure.
        if os.path.isfile(repo_path):
            try:
                gitdir = yaml.safe_load(open(repo_path)).get('gitdir')
                # There is a posibility the .git file to have an absolute path.
                if os.path.isabs(gitdir):
                    repo_path = gitdir
                else:
                    repo_path = os.path.join(repo_path.split('.git')[0], gitdir)
            except (IOError, AttributeError):
                return ''
        f = open(os.path.join(repo_path, "HEAD"))
        branch = f.readline().split('/')[-1].rstrip("\n")
        f.close()
        branch_path = os.path.join(repo_path, "refs", "heads", branch)
        if os.path.exists(branch_path):
            f = open(branch_path)
            commit = f.readline()[:10]
            f.close()
            date = time.localtime(os.stat(branch_path).st_mtime)
            if time.daylight == 0:
                offset = time.timezone
            else:
                offset = time.altzone
            result = "({0} {1}) last updated {2} (GMT {3:+04d})".format(branch, commit,
                time.strftime("%Y/%m/%d %H:%M:%S", date), offset / -36)
    else:
        result = ''
    return result

def version(prog):
    result = "{0} {1}".format(prog, __version__)
    gitinfo = _gitinfo()
    if gitinfo:
        result = result + " {0}".format(gitinfo)
    return result

def getch():
    ''' read in a single character '''
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def sanitize_output(str):
    ''' strips private info out of a string '''

    private_keys = ['password', 'login_password']

    filter_re = [
        # filter out things like user:pass@foo/whatever
        # and http://username:pass@wherever/foo
        re.compile('^(?P<before>.*:)(?P<password>.*)(?P<after>\@.*)$'),
    ]

    parts = str.split()
    output = ''
    for part in parts:
        try:
            (k,v) = part.split('=', 1)
            if k in private_keys:
                output += " %s=VALUE_HIDDEN" % k
            else:
                found = False
                for filter in filter_re:
                    m = filter.match(v)
                    if m:
                        d = m.groupdict()
                        output += " %s=%s" % (k, d['before'] + "********" + d['after'])
                        found = True
                        break
                if not found:
                    output += " %s" % part
        except:
            output += " %s" % part

    return output.strip()

####################################################################
# option handling code for /usr/bin/ansible and ansible-playbook
# below this line

class SortedOptParser(optparse.OptionParser):
    '''Optparser which sorts the options by opt before outputting --help'''

    def format_help(self, formatter=None):
        self.option_list.sort(key=operator.methodcaller('get_opt_string'))
        return optparse.OptionParser.format_help(self, formatter=None)

def increment_debug(option, opt, value, parser):
    global VERBOSITY
    VERBOSITY += 1

def base_parser(constants=C, usage="", output_opts=False, runas_opts=False,
    async_opts=False, connect_opts=False, subset_opts=False, check_opts=False, diff_opts=False):
    ''' create an options parser for any ansible script '''

    parser = SortedOptParser(usage, version=version("%prog"))
    parser.add_option('-v','--verbose', default=False, action="callback",
        callback=increment_debug, help="verbose mode (-vvv for more, -vvvv to enable connection debugging)")

    parser.add_option('-f','--forks', dest='forks', default=constants.DEFAULT_FORKS, type='int',
        help="specify number of parallel processes to use (default=%s)" % constants.DEFAULT_FORKS)
    parser.add_option('-i', '--inventory-file', dest='inventory',
        help="specify inventory host file (default=%s)" % constants.DEFAULT_HOST_LIST,
        default=constants.DEFAULT_HOST_LIST)
    parser.add_option('-k', '--ask-pass', default=False, dest='ask_pass', action='store_true',
        help='ask for SSH password')
    parser.add_option('--private-key', default=C.DEFAULT_PRIVATE_KEY_FILE, dest='private_key_file',
        help='use this file to authenticate the connection')
    parser.add_option('-K', '--ask-sudo-pass', default=False, dest='ask_sudo_pass', action='store_true',
        help='ask for sudo password')
    parser.add_option('--ask-su-pass', default=False, dest='ask_su_pass', action='store_true', 
        help='ask for su password')
    parser.add_option('--ask-vault-pass', default=False, dest='ask_vault_pass', action='store_true', 
        help='ask for vault password')
    parser.add_option('--vault-password-file', default=None, dest='vault_password_file',
        help="vault password file")
    parser.add_option('--list-hosts', dest='listhosts', action='store_true',
        help='outputs a list of matching hosts; does not execute anything else')
    parser.add_option('-M', '--module-path', dest='module_path',
        help="specify path(s) to module library (default=%s)" % constants.DEFAULT_MODULE_PATH,
        default=None)

    if subset_opts:
        parser.add_option('-l', '--limit', default=constants.DEFAULT_SUBSET, dest='subset',
            help='further limit selected hosts to an additional pattern')

    parser.add_option('-T', '--timeout', default=constants.DEFAULT_TIMEOUT, type='int',
        dest='timeout',
        help="override the SSH timeout in seconds (default=%s)" % constants.DEFAULT_TIMEOUT)

    if output_opts:
        parser.add_option('-o', '--one-line', dest='one_line', action='store_true',
            help='condense output')
        parser.add_option('-t', '--tree', dest='tree', default=None,
            help='log output to this directory')

    if runas_opts:
        parser.add_option("-s", "--sudo", default=constants.DEFAULT_SUDO, action="store_true",
            dest='sudo', help="run operations with sudo (nopasswd)")
        parser.add_option('-U', '--sudo-user', dest='sudo_user', default=None,
                          help='desired sudo user (default=root)')  # Can't default to root because we need to detect when this option was given
        parser.add_option('-u', '--user', default=constants.DEFAULT_REMOTE_USER,
            dest='remote_user', help='connect as this user (default=%s)' % constants.DEFAULT_REMOTE_USER)

        parser.add_option('-S', '--su', default=constants.DEFAULT_SU,
                          action='store_true', help='run operations with su')
        parser.add_option('-R', '--su-user', help='run operations with su as this '
                                                  'user (default=%s)' % constants.DEFAULT_SU_USER)

    if connect_opts:
        parser.add_option('-c', '--connection', dest='connection',
                          default=C.DEFAULT_TRANSPORT,
                          help="connection type to use (default=%s)" % C.DEFAULT_TRANSPORT)

    if async_opts:
        parser.add_option('-P', '--poll', default=constants.DEFAULT_POLL_INTERVAL, type='int',
            dest='poll_interval',
            help="set the poll interval if using -B (default=%s)" % constants.DEFAULT_POLL_INTERVAL)
        parser.add_option('-B', '--background', dest='seconds', type='int', default=0,
            help='run asynchronously, failing after X seconds (default=N/A)')

    if check_opts:
        parser.add_option("-C", "--check", default=False, dest='check', action='store_true',
            help="don't make any changes; instead, try to predict some of the changes that may occur"
        )

    if diff_opts:
        parser.add_option("-D", "--diff", default=False, dest='diff', action='store_true',
            help="when changing (small) files and templates, show the differences in those files; works great with --check"
        )


    return parser

def ask_vault_passwords(ask_vault_pass=False, ask_new_vault_pass=False, confirm_vault=False, confirm_new=False):

    vault_pass = None
    new_vault_pass = None

    if ask_vault_pass:
        vault_pass = getpass.getpass(prompt="Vault password: ")

    if ask_vault_pass and confirm_vault:
        vault_pass2 = getpass.getpass(prompt="Confirm Vault password: ")
        if vault_pass != vault_pass2:
            raise errors.AnsibleError("Passwords do not match")

    if ask_new_vault_pass:
        new_vault_pass = getpass.getpass(prompt="New Vault password: ")

    if ask_new_vault_pass and confirm_new:
        new_vault_pass2 = getpass.getpass(prompt="Confirm New Vault password: ")
        if new_vault_pass != new_vault_pass2:
            raise errors.AnsibleError("Passwords do not match")

    # enforce no newline chars at the end of passwords
    if vault_pass:
        vault_pass = vault_pass.strip()
    if new_vault_pass:
        new_vault_pass = new_vault_pass.strip()

    return vault_pass, new_vault_pass

def ask_passwords(ask_pass=False, ask_sudo_pass=False, ask_su_pass=False, ask_vault_pass=False):
    sshpass = None
    sudopass = None
    su_pass = None
    vault_pass = None
    sudo_prompt = "sudo password: "
    su_prompt = "su password: "

    if ask_pass:
        sshpass = getpass.getpass(prompt="SSH password: ")
        sudo_prompt = "sudo password [defaults to SSH password]: "

    if ask_sudo_pass:
        sudopass = getpass.getpass(prompt=sudo_prompt)
        if ask_pass and sudopass == '':
            sudopass = sshpass

    if ask_su_pass:
        su_pass = getpass.getpass(prompt=su_prompt)

    if ask_vault_pass:
        vault_pass = getpass.getpass(prompt="Vault password: ")

    return (sshpass, sudopass, su_pass, vault_pass)

def do_encrypt(result, encrypt, salt_size=None, salt=None):
    if PASSLIB_AVAILABLE:
        try:
            crypt = getattr(passlib.hash, encrypt)
        except:
            raise errors.AnsibleError("passlib does not support '%s' algorithm" % encrypt)

        if salt_size:
            result = crypt.encrypt(result, salt_size=salt_size)
        elif salt:
            result = crypt.encrypt(result, salt=salt)
        else:
            result = crypt.encrypt(result)
    else:
        raise errors.AnsibleError("passlib must be installed to encrypt vars_prompt values")

    return result

def last_non_blank_line(buf):

    all_lines = buf.splitlines()
    all_lines.reverse()
    for line in all_lines:
        if (len(line) > 0):
            return line
    # shouldn't occur unless there's no output
    return ""

def filter_leading_non_json_lines(buf):
    '''
    used to avoid random output from SSH at the top of JSON output, like messages from
    tcagetattr, or where dropbear spews MOTD on every single command (which is nuts).

    need to filter anything which starts not with '{', '[', ', '=' or is an empty line.
    filter only leading lines since multiline JSON is valid.
    '''

    kv_regex = re.compile(r'.*\w+=\w+.*')
    filtered_lines = StringIO.StringIO()
    stop_filtering = False
    for line in buf.splitlines():
        if stop_filtering or kv_regex.match(line) or line.startswith('{') or line.startswith('['):
            stop_filtering = True
            filtered_lines.write(line + '\n')
    return filtered_lines.getvalue()

def boolean(value):
    val = str(value)
    if val.lower() in [ "true", "t", "y", "1", "yes" ]:
        return True
    else:
        return False

def make_sudo_cmd(sudo_user, executable, cmd):
    """
    helper function for connection plugins to create sudo commands
    """
    # Rather than detect if sudo wants a password this time, -k makes
    # sudo always ask for a password if one is required.
    # Passing a quoted compound command to sudo (or sudo -s)
    # directly doesn't work, so we shellquote it with pipes.quote()
    # and pass the quoted string to the user's shell.  We loop reading
    # output until we see the randomly-generated sudo prompt set with
    # the -p option.
    randbits = ''.join(chr(random.randint(ord('a'), ord('z'))) for x in xrange(32))
    prompt = '[sudo via ansible, key=%s] password: ' % randbits
    success_key = 'SUDO-SUCCESS-%s' % randbits
    sudocmd = '%s -k && %s %s -S -p "%s" -u %s %s -c %s' % (
        C.DEFAULT_SUDO_EXE, C.DEFAULT_SUDO_EXE, C.DEFAULT_SUDO_FLAGS,
        prompt, sudo_user, executable or '$SHELL', pipes.quote('echo %s; %s' % (success_key, cmd)))
    return ('/bin/sh -c ' + pipes.quote(sudocmd), prompt, success_key)


def make_su_cmd(su_user, executable, cmd):
    """
    Helper function for connection plugins to create direct su commands
    """
    # TODO: work on this function
    randbits = ''.join(chr(random.randint(ord('a'), ord('z'))) for x in xrange(32))
    prompt = 'assword: '
    success_key = 'SUDO-SUCCESS-%s' % randbits
    sudocmd = '%s %s %s %s -c %s' % (
        C.DEFAULT_SU_EXE, C.DEFAULT_SU_FLAGS, su_user, executable or '$SHELL',
        pipes.quote('echo %s; %s' % (success_key, cmd))
    )
    return ('/bin/sh -c ' + pipes.quote(sudocmd), prompt, success_key)

_TO_UNICODE_TYPES = (unicode, type(None))

def to_unicode(value):
    if isinstance(value, _TO_UNICODE_TYPES):
        return value
    return value.decode("utf-8")

def get_diff(diff):
    # called by --diff usage in playbook and runner via callbacks
    # include names in diffs 'before' and 'after' and do diff -U 10

    try:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            ret = []
            if 'dst_binary' in diff:
                ret.append("diff skipped: destination file appears to be binary\n")
            if 'src_binary' in diff:
                ret.append("diff skipped: source file appears to be binary\n")
            if 'dst_larger' in diff:
                ret.append("diff skipped: destination file size is greater than %d\n" % diff['dst_larger'])
            if 'src_larger' in diff:
                ret.append("diff skipped: source file size is greater than %d\n" % diff['src_larger'])
            if 'before' in diff and 'after' in diff:
                if 'before_header' in diff:
                    before_header = "before: %s" % diff['before_header']
                else:
                    before_header = 'before'
                if 'after_header' in diff:
                    after_header = "after: %s" % diff['after_header']
                else:
                    after_header = 'after'
                differ = difflib.unified_diff(to_unicode(diff['before']).splitlines(True), to_unicode(diff['after']).splitlines(True), before_header, after_header, '', '', 10)
                for line in list(differ):
                    ret.append(line)
            return u"".join(ret)
    except UnicodeDecodeError:
        return ">> the files are different, but the diff library cannot compare unicode strings"

def is_list_of_strings(items):
    for x in items:
        if not isinstance(x, basestring):
            return False
    return True

def safe_eval(expr, locals={}, include_exceptions=False):
    '''
    this is intended for allowing things like:
    with_items: a_list_variable
    where Jinja2 would return a string
    but we do not want to allow it to call functions (outside of Jinja2, where
    the env is constrained)

    Based on:
    http://stackoverflow.com/questions/12523516/using-ast-and-whitelists-to-make-pythons-eval-safe
    '''

    # this is the whitelist of AST nodes we are going to 
    # allow in the evaluation. Any node type other than 
    # those listed here will raise an exception in our custom
    # visitor class defined below.
    SAFE_NODES = set(
        (
            ast.Expression,
            ast.Compare,
            ast.Str,
            ast.List,
            ast.Tuple,
            ast.Dict,
            ast.Call,
            ast.Load,
            ast.BinOp,
            ast.UnaryOp,
            ast.Num,
            ast.Name,
            ast.Add,
            ast.Sub,
            ast.Mult,
            ast.Div,
        )
    )

    # AST node types were expanded after 2.6
    if not sys.version.startswith('2.6'):
        SAFE_NODES.union(
            set(
                (ast.Set,)
            )
        )

    # builtin functions that are not safe to call
    INVALID_CALLS = (
       'classmethod', 'compile', 'delattr', 'eval', 'execfile', 'file',
       'filter', 'help', 'input', 'object', 'open', 'raw_input', 'reduce',
       'reload', 'repr', 'setattr', 'staticmethod', 'super', 'type',
    )

    class CleansingNodeVisitor(ast.NodeVisitor):
        def generic_visit(self, node):
            if type(node) not in SAFE_NODES:
                #raise Exception("invalid expression (%s) type=%s" % (expr, type(node)))
                raise Exception("invalid expression (%s)" % expr)
            super(CleansingNodeVisitor, self).generic_visit(node)
        def visit_Call(self, call):
            if call.func.id in INVALID_CALLS:
                raise Exception("invalid function: %s" % call.func.id)

    if not isinstance(expr, basestring):
        # already templated to a datastructure, perhaps?
        if include_exceptions:
            return (expr, None)
        return expr

    try:
        parsed_tree = ast.parse(expr, mode='eval')
        cnv = CleansingNodeVisitor()
        cnv.visit(parsed_tree)
        compiled = compile(parsed_tree, expr, 'eval')
        result = eval(compiled, {}, locals)

        if include_exceptions:
            return (result, None)
        else:
            return result
    except SyntaxError, e:
        # special handling for syntax errors, we just return
        # the expression string back as-is
        if include_exceptions:
            return (expr, None)
        return expr
    except Exception, e:
        if include_exceptions:
            return (expr, e)
        return expr


def listify_lookup_plugin_terms(terms, basedir, inject):

    if isinstance(terms, basestring):
        # someone did:
        #    with_items: alist
        # OR
        #    with_items: {{ alist }}

        stripped = terms.strip()
        if not (stripped.startswith('{') or stripped.startswith('[')) and not stripped.startswith("/") and not stripped.startswith('set(['):
            # if not already a list, get ready to evaluate with Jinja2
            # not sure why the "/" is in above code :)
            try:
                new_terms = template.template(basedir, "{{ %s }}" % terms, inject)
                if isinstance(new_terms, basestring) and "{{" in new_terms:
                    pass
                else:
                    terms = new_terms
            except:
                pass

        if '{' in terms or '[' in terms:
            # Jinja2 already evaluated a variable to a list.
            # Jinja2-ified list needs to be converted back to a real type
            # TODO: something a bit less heavy than eval
            return safe_eval(terms)

        if isinstance(terms, basestring):
            terms = [ terms ]

    return terms

def combine_vars(a, b):

    if C.DEFAULT_HASH_BEHAVIOUR == "merge":
        return merge_hash(a, b)
    else:
        return dict(a.items() + b.items())

def random_password(length=20, chars=C.DEFAULT_PASSWORD_CHARS):
    '''Return a random password string of length containing only chars.'''

    password = []
    while len(password) < length:
        new_char = os.urandom(1)
        if new_char in chars:
            password.append(new_char)

    return ''.join(password)

def before_comment(msg):
    ''' what's the part of a string before a comment? '''
    msg = msg.replace("\#","**NOT_A_COMMENT**")
    msg = msg.split("#")[0]
    msg = msg.replace("**NOT_A_COMMENT**","#")
    return msg



