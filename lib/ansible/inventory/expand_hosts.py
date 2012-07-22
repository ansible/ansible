#
# $Id: expand_hosts.py,v 1.9 2012/07/22 16:17:57 fangchin Exp $
#
# (c) 2012, Zettar Inc.
# Written by Chin Fang <fangchin@zettar.com>
#
# This file is part of Ansible
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.
#
'''
This module is for enhancing ansible's inventory parsing capability such
that it can deal with hostnames specified using a simple pattern in the
form of [beg:end:step], example: [1:5:2] where if beg is not specified, it
defaults to 0. If step is not specified, it defaults to 1.
'''
import sys
from pprint import pprint

def detect_range(line = None):
    '''
    A helper function that checks a given host line to see if it contains
    a range pattern. The following are examples:

    o node[1:6]
    o node[1:6:2]
    o node[1:6].example.com
    o node[1:6:2].example.com
    o node[1:6]-webserver
    o node[1:6:2]-database

    Returnes True if the given line contains a pattern, else False.
    '''
    if (not line.startswith("[") and 
        line.find("[") != -1 and 
        line.find(":") != -1 and
        line.find("]") != -1 and
        line.index("[") < line.index(":") < line.index("]")):   
        return True
    else:
        return False
        
def expand_hostname_range(line = None):
    '''
    A helper function that expands a given line that contains a pattern
    specified in def detect_range, and returns a list that consists
    of the expanded version.

    The '[' and ']' characters are used to maintain the pseudo-code
    appearance. They are replaced in this function with '|' to ease
    string splitting.

    References: http://ansible.github.com/patterns.html#hosts-and-groups
    '''
    all_hosts = []
    if line:
        # A hostname such as db[1:6:2]-node is considered to consists
        # three parts: 
        # head: 'db'
        # nrange: [1:6:2]; range is a built-in. Can't use the name
        # tail: '-node'
        
        (head, nrange, tail) = line.replace('[','|').replace(']','|').split('|')
        bounds = nrange.split(":")
        lbounds = len(bounds)
        beg = bounds[0]
        end = bounds[1]
        lbounds = len(bounds)
        if lbounds == 2:
            step = 1
        elif lbounds == 3:
            step = bounds[2]
        else:
            raise ValueError("host range incorrectly specified!")
        
        if not beg:
            beg = "0"
            
        if not end:
            raise ValueError("host range incorrectly specified!")
            
        if not step:
            step = "1"
               
        for _ in range(int(beg), int(end), int(step)):
            hname = ''.join((head, str(_), tail))
            all_hosts.append(hname)
                   
        return all_hosts

def main():
    '''
    A function for self-testing.
    '''
    test_data = ["[webservers]",
                 "[dbservers]",
                 "[webservers:!phoenix]",
                 "[atlanta:vars]",
                 "[southeast:childern]",
                 "mail.example.com",
                 "www.example.com",
                 "db.example.com",
                 "node[:6]", 
                 "node[1:6]",
                 "node[1:6:2]",
                 "node[:5].example.com",
                 "node[1:6].example.com",
                 "node[1:6:2].example.com",
                 "node[:6]-webserver", 
                 "node[1:6]-webserver",
                 "node[1:6:2]-webserver"]

    for data in test_data:
        print "===> testing %s..." % data
        if detect_range(data):
            all_hosts = expand_hostname_range(data)
            pprint(all_hosts)
        else:
            print "!!! Not expanded!!! %s" % data

    return 0
    
if __name__ == '__main__':
    sys.exit(main())
