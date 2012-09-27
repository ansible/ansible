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
import os
import shlex
import re
import codecs
import jinja2
import yaml
import optparse
import operator
from ansible import errors
from ansible import __version__
import ansible.constants as C
import time
import StringIO
import imp
import glob
import subprocess
import stat
import termios
import tty
from multiprocessing import Manager

VERBOSITY=0

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
    from keyczar.keys import AesKey
    KEYCZAR_AVAILABLE=True
except ImportError:
    pass

###############################################################
# abtractions around keyczar

def key_for_hostname(hostname):
    # fireball mode is an implementation of ansible firing up zeromq via SSH
    # to use no persistent daemons or key management

    key_path = os.path.expanduser("~/.fireball.keys")
    if not os.path.exists(key_path):
        os.makedirs(key_path)
    key_path = os.path.expanduser("~/.fireball.keys/%s" % hostname)

    # use new AES keys every 2 hours, which means fireball must not allow running for longer either
    if not os.path.exists(key_path) or (time.time() - os.path.getmtime(key_path) > 60*60*2):
        key = AesKey.Generate()
        fh = open(key_path, "w")
        fh.write(str(key))
        fh.close()
        return key
    else:
        fh = open(key_path)
        key = AesKey.Read(fh.read())  
        fh.close()
        return key

def encrypt(key, msg):
    return key.Encrypt(msg)

def decrypt(key, msg):
    try:
        return key.Decrypt(msg)
    except keyczar.errors.InvalidSignatureError:
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

    result2 = result.copy()
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

def check_conditional(conditional):
    def is_set(var):
        return not var.startswith("$")
    def is_unset(var):
        return var.startswith("$")
    return eval(conditional)

def is_executable(path):
    '''is the given path executable?'''
    return (stat.S_IXUSR & os.stat(path)[stat.ST_MODE] 
            or stat.S_IXGRP & os.stat(path)[stat.ST_MODE] 
            or stat.S_IXOTH & os.stat(path)[stat.ST_MODE])

def prepare_writeable_dir(tree):
    ''' make sure a directory exists and is writeable '''

    if tree != '/':
        tree = os.path.realpath(os.path.expanduser(tree))
    if not os.path.exists(tree):
        try:
            os.makedirs(tree)
        except (IOError, OSError), e:
            exit("Could not make dir %s: %s" % (tree, e))
    if not os.access(tree, os.W_OK):
        exit("Cannot write to path %s" % tree)

def path_dwim(basedir, given):
    ''' make relative paths work like folks expect '''

    if given.startswith("/"):
        return given
    elif given.startswith("~/"):
        return os.path.expanduser(given)
    else:
        return os.path.join(basedir, given)

def json_loads(data):
    ''' parse a JSON string and return a data structure '''

    return json.loads(data)

def parse_json(raw_data):
    ''' this version for module return data only '''

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
            if t.find("=") == -1:
                raise errors.AnsibleError("failed to parse: %s" % raw_data)
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
            return { "failed" : True, "parsed" : False, "msg" : raw_data }
        return results

_LISTRE = re.compile(r"(\w+)\[(\d+)\]")

class VarNotFoundException(Exception):
    pass

def _varLookup(name, vars, depth=0):
    ''' find the contents of a possibly complex variable in vars. '''

    path = name.split('.')
    space = vars
    for part in path:
        part = varReplace(part, vars, depth=depth + 1)
        if part in space:
            space = space[part]
        elif "[" in part:
            m = _LISTRE.search(part)
            if not m:
                raise VarNotFoundException()
            try:
                space = space[m.group(1)][int(m.group(2))]
            except (KeyError, IndexError):
                raise VarNotFoundException()
        else:
            raise VarNotFoundException()
    return space

_KEYCRE = re.compile(r"\$(?P<complex>\{){0,1}((?(complex)[\w\.\[\]\$\{\}]+|\w+))(?(complex)\})")

def varLookup(varname, vars):
    ''' helper function used by with_items '''

    m = _KEYCRE.search(varname)
    if not m:
        return None
    try:
        return _varLookup(m.group(2), vars)
    except VarNotFoundException:
        return None

def varReplace(raw, vars, do_repr=False, depth=0):
    ''' Perform variable replacement of $variables in string raw using vars dictionary '''
    # this code originally from yum

    if (depth > 20):
        raise errors.AnsibleError("template recursion depth exceeded")

    done = [] # Completed chunks to return

    while raw:
        m = _KEYCRE.search(raw)
        if not m:
            done.append(raw)
            break

        # Determine replacement value (if unknown variable then preserve
        # original)

        try:
            replacement = unicode(_varLookup(m.group(2), vars, depth))
            replacement = varReplace(replacement, vars, depth=depth + 1)
        except VarNotFoundException:
            replacement = m.group()

        start, end = m.span()
        if do_repr:
            replacement = repr(replacement)
            if (start > 0 and
                ((raw[start - 1] == "'" and raw[end] == "'") or
                 (raw[start - 1] == '"' and raw[end] == '"'))):
                start -= 1
                end += 1
        done.append(raw[:start])    # Keep stuff leading up to token
        done.append(replacement)    # Append replacement value
        raw = raw[end:]             # Continue with remainder of string

    return ''.join(done)

_FILEPIPECRE = re.compile(r"\$(?P<special>FILE|PIPE)\(([^\}]+)\)")
def varReplaceFilesAndPipes(basedir, raw):
    done = [] # Completed chunks to return

    while raw:
        m = _FILEPIPECRE.search(raw)
        if not m:
            done.append(raw)
            break

        # Determine replacement value (if unknown variable then preserve
        # original)

        if m.group(1) == "FILE":
            try:
                f = open(path_dwim(basedir, m.group(2)), "r")
            except IOError:
                raise VarNotFoundException()
            replacement = f.read()
            f.close()
        elif m.group(1) == "PIPE":
            p = subprocess.Popen(m.group(2), shell=True, stdout=subprocess.PIPE)
            (stdout, stderr) = p.communicate()
            if p.returncode != 0:
                raise VarNotFoundException()
            replacement = stdout

        start, end = m.span()
        done.append(raw[:start])    # Keep stuff leading up to token
        done.append(replacement.rstrip())    # Append replacement value
        raw = raw[end:]             # Continue with remainder of string

    return ''.join(done)


def template(basedir, text, vars, do_repr=False):
    ''' run a text buffer through the templating engine until it no longer changes '''

    prev_text = ''
    try:
        text = text.decode('utf-8')
    except UnicodeEncodeError:
        pass # already unicode
    text = varReplace(unicode(text), vars, do_repr)
    text = varReplaceFilesAndPipes(basedir, text)
    return text

def template_from_file(basedir, path, vars):
    ''' run a file through the templating engine '''

    environment = jinja2.Environment(loader=jinja2.FileSystemLoader(basedir), trim_blocks=False)
    environment.filters['to_json'] = json.dumps
    environment.filters['from_json'] = json.loads
    environment.filters['to_yaml'] = yaml.dump
    environment.filters['from_yaml'] = yaml.load
    data = codecs.open(path_dwim(basedir, path), encoding="utf8").read()
    t = environment.from_string(data)
    vars = vars.copy()
    res = t.render(vars)
    if data.endswith('\n') and not res.endswith('\n'):
        res = res + '\n'
    return template(basedir, res, vars)

def parse_yaml(data):
    ''' convert a yaml string to a data structure '''

    return yaml.load(data)

def parse_yaml_from_file(path):
    ''' convert a yaml file to a data structure '''

    try:
        data = file(path).read()
        return parse_yaml(data)
    except IOError:
        raise errors.AnsibleError("file not found: %s" % path)
    except yaml.YAMLError, exc:
        if hasattr(exc, 'problem_mark'):
            mark = exc.problem_mark
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
        else:
            # No problem markers means we have to throw a generic
            # "stuff messed up" type message. Sry bud.
            msg = "Could not parse YAML. Check over %s again." % path
        raise errors.AnsibleYAMLValidationFailed(msg)

def parse_kv(args):
    ''' convert a string of key/value items to a dict '''

    options = {}
    if args is not None:
        # attempting to split a unicode here does bad things
        vargs = shlex.split(str(args), posix=True)
        for x in vargs:
            if x.find("=") != -1:
                k, v = x.split("=",1)
                options[k]=v
    return options

def md5(filename):
    ''' Return MD5 hex digest of local file, or None if file is not present. '''

    if not os.path.exists(filename):
        return None
    digest = _md5()
    blocksize = 64 * 1024
    infile = open(filename, 'rb')
    block = infile.read(blocksize)
    while block:
        digest.update(block)
        block = infile.read(blocksize)
    infile.close()
    return digest.hexdigest()

def default(value, function):
    ''' syntactic sugar around lazy evaluation of defaults '''
    if value is None:
        return function()
    return value

def _gitinfo():
    ''' returns a string containing git branch, commit id and commit date '''
    result = None
    repo_path = os.path.join(os.path.dirname(__file__), '..', '..', '.git')

    if os.path.exists(repo_path):
        # Check if the .git is a file. If it is a file, it means that we are in a submodule structure.
        if os.path.isfile(repo_path):
            try:
                gitdir = yaml.load(open(repo_path)).get('gitdir')
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
    async_opts=False, connect_opts=False, subset_opts=False):
    ''' create an options parser for any ansible script '''

    parser = SortedOptParser(usage, version=version("%prog"))
    parser.add_option('-v','--verbose', default=False, action="callback",
        callback=increment_debug, help="verbose mode (-vvv for more)")

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
    parser.add_option('-M', '--module-path', dest='module_path',
        help="specify path(s) to module library (default=%s)" % constants.DEFAULT_MODULE_PATH,
        default=constants.DEFAULT_MODULE_PATH)

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
        parser.add_option("-s", "--sudo", default=False, action="store_true",
            dest='sudo', help="run operations with sudo (nopasswd)")
        parser.add_option('-U', '--sudo-user', dest='sudo_user', help='desired sudo user (default=root)',
            default=None)   # Can't default to root because we need to detect when this option was given
        parser.add_option('-u', '--user', default=constants.DEFAULT_REMOTE_USER,
            dest='remote_user',
            help='connect as this user (default=%s)' % constants.DEFAULT_REMOTE_USER)

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

    return parser

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

    filtered_lines = StringIO.StringIO()
    stop_filtering = False
    for line in buf.splitlines():
        if stop_filtering or "=" in line or line.startswith('{') or line.startswith('['):
            stop_filtering = True
            filtered_lines.write(line + '\n')
    return filtered_lines.getvalue()

def import_plugins(directory):
    modules = {}
    for path in glob.glob(os.path.join(directory, '*.py')):
        if path.startswith("_"):
            continue
        name, ext = os.path.splitext(os.path.basename(path))
        if not name.startswith("_"):
            modules[name] = imp.load_source(name, path)
    return modules
