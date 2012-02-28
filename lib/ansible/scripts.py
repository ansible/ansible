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

from optparse import OptionParser
import sys
import constants as C

def base_ans_parser():
    parser = OptionParser()
    parser.add_option("-H", "--host-list", dest="host_list",
        help="path to hosts list", default=C.DEFAULT_HOST_LIST)
    parser.add_option("-L", "--library", dest="module_path",
        help="path to module library", default=C.DEFAULT_MODULE_PATH)
    parser.add_option('-u', '--user', default=C.DEFAULT_REMOTE_USER, 
        dest='remote_user', help='set the default username')
    parser.add_option("-P", "--askpass", default=False, action="store_true",
        help="ask the user to input the ssh password for connecting")
    parser.add_option('-f','--forks', dest='forks', default=C.DEFAULT_FORKS, type='int',
        help='set the number of forks to start up')
    return parser

# other functions as needed for nicely handling output from json back
# to things people might be more inclined to deal with at a bash prompt


def error_print(msg):
    print >> sys.stderr, msg
    
