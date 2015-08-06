#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# (c) 2015, Ravi Bhure <ravibhure@gmail.com>
#
# This file is part of Ansible,
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

######################################################################

"""
Check_MK / OMD Server external inventory script.
================================================

Returns hosts and hostgroups from Check_MK / OMD Server using LQL to livestatus socket.

Configuration is read from `omd.ini`.

Tested with Check_MK/Nagios/Icinga Server with OMD.

For more details, see: https://mathias-kettner.de/checkmk_livestatus.html
"""

import os,sys
import ConfigParser
import socket
import argparse

try:
    import json
except:
    import simplejson as json

def do_connect():
  """ Initialize socket connection """

  url = read_settings()
  parts = url.split(":")
  if parts[0] == "unix":
      if len(parts) != 2:
          raise Exception("Invalid livestatus unix url: %s. "
                 "Correct example is 'unix:/var/run/nagios/rw/live'" % url)
      s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
      target = parts[1]

  elif parts[0] == "tcp":
      try:
          host = parts[1]
          port = int(parts[2])
      except:
          raise Exception("Invalid livestatus tcp url '%s'. "
                 "Correct example is 'tcp:somehost:6557'" % url)
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      target = (host, port)
  else:
      raise Exception("Invalid livestatus url '%s'. "
              "Must begin with 'tcp:' or 'unix:'" % url)

  # Create connection
  try:
      s.connect(target)
  except Exception, e:
      print >>sys.stderr, 'Error while connecting to socket on %s - %s' % (target,e)
      sys.exit(1)

  # Declare connection
  return s

def read_settings():
  """ Reads the settings from the omd.ini file """

  config = ConfigParser.SafeConfigParser()
  config.read(os.path.dirname(os.path.realpath(__file__)) + '/omd.ini')
  url = config.get('omd', 'socketurl')
  return url

def inventory_data(query):
  """ Generate inventory data """

  s = do_connect()
  s.send(query)
  s.shutdown(socket.SHUT_WR)
  answer = s.recv(100000000)
  table = answer.split('\n')[:-1]

  return json.dumps({'hosts': table}, sort_keys=True, indent=2)

def print_list():
  """ Returns all host """

  query = "GET hosts \nColumns: host_name \n"
  print inventory_data(query)

def print_host(host):
  """ Returns a host """

  query = "GET hosts \nColumns: host_name \nFilter: host_name = %s\n" % host
  print inventory_data(query)

def print_group(hostgroup):
  """ Returns a list of all hosts in given hostgroup """

  query = "GET hosts \nColumns: host_name \nFilter: host_groups >= %s\n" % hostgroup
  print inventory_data(query)

def get_args(args_list):
  parser = argparse.ArgumentParser(
      description='ansible inventory script reading from check_mk / omd monitoring')
  mutex_group = parser.add_mutually_exclusive_group(required=True)
  help_list = 'list all hosts from check_mk / omd server'
  mutex_group.add_argument('--list', action='store_true', help=help_list)
  help_host = 'display variables for a host'
  mutex_group.add_argument('--host', help=help_host)
  help_hostgroup = 'display variables for a hostgroup'
  mutex_group.add_argument('--hostgroup', help=help_hostgroup)
  return parser.parse_args(args_list)


def main(args_list):
  args = get_args(args_list)
  if args.list:
      print_list()
  if args.host:
      print_host(args.host)
  if args.hostgroup:
      print_group(args.hostgroup)


if __name__ == '__main__':
  main(sys.argv[1:])
