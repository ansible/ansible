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
try:
    import json
except ImportError:
    import simplejson as json

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
    return json.dumps(result, sort_keys=True, indent=4)

def smjson(result):
    ''' format JSON output (compressed) '''
    return json.dumps(result, sort_keys=True)

def task_start_msg(name, conditional):
    if conditional:
        return "NOTIFIED: [%s] **********\n" % name
    else:
        return "TASK: [%s] *********\n" % name

def regular_generic_msg(hostname, result, oneline, caption):
    ''' output on the result of a module run that is not command '''
    if not oneline:
        return "%s | %s >>\n%s" % (hostname, caption, bigjson(result))
    else:
        return "%s | %s >> %s" % (hostname, caption, smjson(result))

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
        return buf
    else:
        if stderr:
            return "%s | %s | rc=%s | (stdout) %s (stderr) %s" % (hostname, caption, rc, stdout, stderr)
        else:
            return "%s | %s | rc=%s | (stdout) %s" % (hostname, caption, rc, stdout)

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
    if module_name == 'command':
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

def dark_hosts_msg(results):
    ''' summarize the results of all uncontactable hosts '''
    buf = ''
    if len(results['dark'].keys()) > 0:
        buf += "*** Hosts which could not be contacted or did not respond: ***"
        for hostname in results['dark'].keys():
            buf += "%s:\n%s\n" % (hostname, results['dark'][hostname])
    buf += "\n"
    return buf

def has_dark_hosts(results):
    ''' are there any uncontactable hosts? '''
    return len(results['dark'].keys()) > 0

def contacted_hosts(results):
    ''' what are the contactable hosts? '''
    return sorted(results['contacted'])

def contacted_host_result(results, hostname):
    ''' what are the results for a given host? '''
    return results['contacted'][hostname]

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
    if given.startswith("/"):
        return given
    elif given.startswith("~/"):
        return os.path.expanduser(given)
    else:
        return os.path.join(basedir, given)

  
