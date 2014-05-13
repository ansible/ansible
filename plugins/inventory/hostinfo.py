#!/usr/bin/python
#
# Dynamic inventory for Ansible with a hostinfo <https://github.com/dwagon/Hostinfo> backend.
# List groupings of servers based on predefined hostinfo queries in hostinfo.ini
#
# Written by Andy Zaugg
# Date:  12/05/14
#

import sys, os, json, ConfigParser
from optparse import OptionParser

baseDir = ""
#-------------------------------------------------------------------------------------------------------------
def generateHostList(config, hosts):
	for section in config.sections():

		# Ensure that each section has a defined host section
		if not config.has_option(section, "hosts"):
			print "Ignoring section: %s" % section
			continue

		hosts[section] = []
	
		# Get a list of hosts to include	
		for item in config.get(section, "hosts").split(","):
			if 'hostinfo ' in item:
				hosts[section] = hosts[section] + [ host.strip() for host in os.popen(item).readlines() ] 
			else:
				hosts[section].append(item.strip())

		# pop out ignored hosts
		if config.has_option(section, "ignorehosts"):
			for item in config.get(section, "ignorehosts").split(","):
				if 'hostinfo ' in item:
					ignoreH = [ host.strip() for host in os.popen(item).readlines() ] 
					hosts[section] = [z for z in hosts[section] if z not in ignoreH]
				else:
					try:
						hosts[section].pop(hosts[section].index(item.strip()))
					except ValueError:
						continue
	return hosts
					
#-------------------------------------------------------------------------------------------------------------
def getConfig(configFile):
	config = ConfigParser.RawConfigParser()
	try:
		config.readfp(open(configFile))
		return config
	except IOError:
		print "Unable to locate config file: %s" % configFile
		sys.exit()	
#-------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
	# Grab option as per "<http://docs.ansible.com/developing_inventory.html>"
	parser = OptionParser(usage="%prog [options] --list | --host <machine>")
	parser.add_option('--list', default=False, dest="lst", action="store_true",
			help="Create a JSON grouping of Hostinfo servers for Ansible")
	parser.add_option('--host', default=None, dest="host",
			help="Create host specific details for a given host")
	(options, args) = parser.parse_args()


	configFile = "hostinfo.ini" #% baseDir
	config = getConfig(configFile)

	hosts = {}


	hosts = generateHostList(config, hosts)

	if options.lst:
		print json.dumps(hosts)

