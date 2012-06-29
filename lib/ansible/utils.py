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

###############################################################

import sys
import os
import shlex
import re
import codecs
import jinja2
import yaml
import optparse
from operator import methodcaller
try:
    import json
except ImportError:
    import simplejson as json

from ansible import errors
import ansible.constants as C

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

def bigjson(result):
    ''' format JSON output (uncompressed) '''
    result2 = result.copy()
    return json.dumps(result2, sort_keys=True, indent=4)

def smjson(result):
    ''' format JSON output (compressed) '''
    result2 = result.copy()
    return json.dumps(result2, sort_keys=True)

def task_start_msg(name, conditional):
    if conditional:
        return "NOTIFIED: [%s]" % name
    else:
        return "TASK: [%s]" % name

def regular_generic_msg(hostname, result, oneline, caption):
    ''' output on the result of a module run that is not command '''
    if not oneline:
        return "%s | %s >> %s\n" % (hostname, caption, bigjson(result))
    else:
        return "%s | %s >> %s\n" % (hostname, caption, smjson(result))

def regular_success_msg(hostname, result, oneline):
    ''' output the result of a successful module run '''
    return regular_generic_msg(hostname, result, oneline, 'success')

def regular_failure_msg(hostname, result, oneline):
    ''' output the result of a failed module run '''
    return regular_generic_msg(hostname, result, oneline, 'FAILED')

def command_generic_msg(hostname, result, oneline, caption):
    ''' output the result of a command run '''
    rc     = result.get('rc', '0')
    stdout = result.get('stdout','')
    stderr = result.get('stderr', '')
    msg    = result.get('msg', '')
    if not oneline:
        buf = "%s | %s | rc=%s >>\n" % (hostname, caption, result.get('rc',0))
        if stdout:
            buf += stdout
        if stderr:
            buf += stderr
        if msg:
            buf += msg
        buf += "\n"
        return buf
    else:
        if stderr:
            return "%s | %s | rc=%s | (stdout) %s (stderr) %s\n" % (hostname, caption, rc, stdout, stderr)
        else:
            return "%s | %s | rc=%s | (stdout) %s\n" % (hostname, caption, rc, stdout)

def command_success_msg(hostname, result, oneline):
    ''' output from a successful command run '''
    return command_generic_msg(hostname, result, oneline, 'success')

def command_failure_msg(hostname, result, oneline):
    ''' output from a failed command run '''
    return command_generic_msg(hostname, result, oneline, 'FAILED')

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
    failed = False
    rc = 0
    if type(result) == dict:
        failed = result.get('failed', 0)
        rc     = result.get('rc', 0)
    if rc != 0:
        return True    
    return failed

def host_report_msg(hostname, module_name, result, oneline):
    ''' summarize the JSON results for a particular host '''
    buf = ''
    failed = is_failed(result)
    if module_name in [ 'command', 'shell', 'raw' ] and 'ansible_job_id' not in result:
        if not failed:
            buf = command_success_msg(hostname, result, oneline)
        else:
            buf = command_failure_msg(hostname, result, oneline)
    else:
        if not failed:
            buf = regular_success_msg(hostname, result, oneline)
        else:
            buf = regular_failure_msg(hostname, result, oneline)
    return buf

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
    return json.loads(data)

def parse_json(data):
    ''' this version for module return data only '''
    try:
        return json.loads(data)
    except:
        # not JSON, but try "Baby JSON" which allows many of our modules to not
        # require JSON and makes writing modules in bash much simpler
        results = {}
        try :
            tokens = shlex.split(data)
        except: 
            print "failed to parse json: "+ data
            raise; 
            
        for t in tokens:
            if t.find("=") == -1:
                raise errors.AnsibleError("failed to parse: %s" % data)
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
            return { "failed" : True, "parsed" : False, "msg" : data }
        return results

_LISTRE = re.compile(r"(\w+)\[(\d+)\]")

def _varLookup(name, vars):
    ''' find the contents of a possibly complex variable in vars. '''
    path = name.split('.')
    space = vars
    for part in path:
        if part in space:
            space = space[part]
        elif "[" in part:
            m = _LISTRE.search(part)
            if not m:
                return
            try:
                space = space[m.group(1)][int(m.group(2))]
            except (KeyError, IndexError):
                return
        else:
            return
    return space

_KEYCRE = re.compile(r"\$(?P<complex>\{){0,1}((?(complex)[\w\.\[\]]+|\w+))(?(complex)\})")
#                        if { -> complex     if complex, allow . and need trailing }

def varLookup(varname, vars):
    m = _KEYCRE.search(varname)
    if not m:
        return None
    return _varLookup(m.group(2), vars)

def varReplace(raw, vars):
    '''Perform variable replacement of $vars

    @param raw: String to perform substitution on.  
    @param vars: Dictionary of variables to replace. Key is variable name
        (without $ prefix). Value is replacement string.
    @return: Input raw string with substituted values.
    '''
    # this code originally from yum

    done = []                      # Completed chunks to return

    while raw:
        m = _KEYCRE.search(raw)
        if not m:
            done.append(raw)
            break

        # Determine replacement value (if unknown variable then preserve
        # original)
        varname = m.group(2)

        replacement = unicode(_varLookup(varname, vars) or m.group())

        start, end = m.span()
        done.append(raw[:start])    # Keep stuff leading up to token
        done.append(replacement)    # Append replacement value
        raw = raw[end:]             # Continue with remainder of string

    return ''.join(done)

def _template(text, vars, setup_cache=None):
    ''' run a text buffer through the templating engine '''
    vars = vars.copy()
    vars['hostvars'] = setup_cache
    text = varReplace(unicode(text), vars)
    return text

def template(text, vars, setup_cache=None):
    ''' run a text buffer through the templating engine 
        until it no longer changes '''
    prev_text = ''
    while prev_text != text:
        prev_text = text
        text = _template(text, vars, setup_cache)
    return text

def template_from_file(basedir, path, vars, setup_cache):
    ''' run a file through the templating engine '''
    environment = jinja2.Environment(loader=jinja2.FileSystemLoader(basedir), trim_blocks=False)
    data = codecs.open(path_dwim(basedir, path), encoding="utf8").read()
    template = environment.from_string(data)
    vars = vars.copy()
    vars['hostvars'] = setup_cache
    res = template.render(vars)
    if data.endswith('\n') and not res.endswith('\n'):
        res = res + '\n'
    return res

def parse_yaml(data):
    return yaml.load(data)
  
def parse_yaml_from_file(path):
    try:
        data = file(path).read()
    except IOError:
        raise errors.AnsibleError("file not found: %s" % path)
    return parse_yaml(data)

def parse_kv(args):
    ''' convert a string of key/value items to a dict '''
    options = {}
    if args is not None:
        vargs = shlex.split(args, posix=True)
        for x in vargs:
            if x.find("=") != -1:
                k, v = x.split("=", 1)
                options[k]=v
    return options

class SortedOptParser(optparse.OptionParser):
    '''Optparser which sorts the options by opt before outputting --help'''
    def format_help(self, formatter=None):
        self.option_list.sort(key=methodcaller('get_opt_string'))
        return optparse.OptionParser.format_help(self, formatter=None)

def base_parser(constants=C, usage="", output_opts=False, runas_opts=False, async_opts=False, connect_opts=False):
    ''' create an options parser for any ansible script '''

    parser = SortedOptParser(usage)
    parser.add_option('-v','--verbose', default=False, action="store_true",
        help='verbose mode')
    parser.add_option('-f','--forks', dest='forks', default=constants.DEFAULT_FORKS, type='int',
        help="specify number of parallel processes to use (default=%s)" % constants.DEFAULT_FORKS)
    parser.add_option('-i', '--inventory-file', dest='inventory',
        help="specify inventory host file (default=%s)" % constants.DEFAULT_HOST_LIST, 
        default=constants.DEFAULT_HOST_LIST)
    parser.add_option('-k', '--ask-pass', default=False, dest='ask_pass', action='store_true',
        help='ask for SSH password')
    parser.add_option('--private-key', default=None, dest='private_key_file',
        help='use this file to authenticate the connection')
    parser.add_option('-K', '--ask-sudo-pass', default=False, dest='ask_sudo_pass', action='store_true',
        help='ask for sudo password')
    parser.add_option('-M', '--module-path', dest='module_path',
        help="specify path(s) to module library (default=%s)" % constants.DEFAULT_MODULE_PATH,
        default=constants.DEFAULT_MODULE_PATH)
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
                          choices=C.DEFAULT_TRANSPORT_OPTS,
                          default=C.DEFAULT_TRANSPORT,
                          help="connection type to use (default=%s)" % C.DEFAULT_TRANSPORT)

    if async_opts:
        parser.add_option('-P', '--poll', default=constants.DEFAULT_POLL_INTERVAL, type='int',
            dest='poll_interval', 
            help="set the poll interval if using -B (default=%s)" % constants.DEFAULT_POLL_INTERVAL)
        parser.add_option('-B', '--background', dest='seconds', type='int', default=0,
            help='run asynchronously, failing after X seconds (default=N/A)')

    return parser


