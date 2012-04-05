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
import jinja2
import yaml
from optparse import OptionParser


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
    # hide some internals magic from command line userland
    result2 = result.copy()
    if 'invocation' in result2:
        del result2['invocation']
    return json.dumps(result2, sort_keys=True, indent=4)

def smjson(result):
    ''' format JSON output (compressed) '''
    # hide some internals magic from command line userland
    result2 = result.copy()
    if 'invocation' in result2:
        del result2['invocation']
    return json.dumps(result2, sort_keys=True)

def task_start_msg(name, conditional):
    if conditional:
        return "\nNOTIFIED: [%s] **********\n" % name
    else:
        return "\nTASK: [%s] *********\n" % name

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
    if module_name in [ 'command', 'shell' ] and 'ansible_job_id' not in result:
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

def async_poll_status(jid, host, clock, result):
    if 'finished' in result:
        return "<job %s> finished on %s" % (jid, host)
    elif 'failed' in result:
        return "<job %s> FAILED on %s" % (jid, host)
    else:
        return "<job %s> polling on %s, %s remaining" % (jid, host, clock)

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
        tokens = shlex.split(data)
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

_KEYCRE = re.compile(r"\$(\w+)")

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
        varname = m.group(1).lower()
        replacement = str(vars.get(varname, m.group()))

        start, end = m.span()
        done.append(raw[:start])    # Keep stuff leading up to token
        done.append(replacement)    # Append replacement value
        raw = raw[end:]             # Continue with remainder of string

    return ''.join(done)

def template(text, vars):
    ''' run a text buffer through the templating engine '''
    text = varReplace(str(text), vars)
    template = jinja2.Template(text)
    return template.render(vars)

def double_template(text, vars):
    return template(template(text, vars), vars)

def template_from_file(path, vars):
    ''' run a file through the templating engine '''
    data = file(path).read()
    return template(data, vars)

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
    vargs = shlex.split(args, posix=True) 
    for x in vargs:
        if x.find("=") != -1:
            k, v = x.split("=")
            options[k]=v
    return options

def base_parser(constants=C, usage="", output_opts=False, runas_opts=False, async_opts=False):
    ''' create an options parser for any ansible script '''

    parser = OptionParser(usage)
    parser.add_option('-D','--debug', default=False, action="store_true",
        help='enable standard error debugging of modules.')
    parser.add_option('-f','--forks', dest='forks', default=constants.DEFAULT_FORKS, type='int',
        help='number of parallel processes to use')
    parser.add_option('-i', '--inventory-file', dest='inventory',
       help='inventory host file', default=constants.DEFAULT_HOST_LIST)
    parser.add_option('-k', '--ask-pass', default=False, action='store_true',
        help='ask for SSH password')
    parser.add_option('-M', '--module-path', dest='module_path',
       help="path to module library", default=constants.DEFAULT_MODULE_PATH)
    parser.add_option('-T', '--timeout', default=constants.DEFAULT_TIMEOUT, type='int',
        dest='timeout', help='set the SSH timeout in seconds')
    parser.add_option('-p', '--port', default=constants.DEFAULT_REMOTE_PORT, type='int',
        dest='remote_port', help='set the remote ssh port')

    if output_opts:
        parser.add_option('-o', '--one-line', dest='one_line', action='store_true',
            help='condense output')
        parser.add_option('-t', '--tree', dest='tree', default=None,
            help='log output to this directory')

    if runas_opts:
        parser.add_option("-s", "--sudo", default=False, action="store_true",
            dest='sudo', help="run operations with sudo (nopasswd)")
        parser.add_option('-u', '--user', default=constants.DEFAULT_REMOTE_USER,
            dest='remote_user', help='connect as this user')
    
    if async_opts:
        parser.add_option('-P', '--poll', default=constants.DEFAULT_POLL_INTERVAL, type='int',
            dest='poll_interval', help='set the poll interval if using -B')
        parser.add_option('-B', '--background', dest='seconds', type='int', default=0,
            help='run asynchronously, failing after X seconds')

    return parser
