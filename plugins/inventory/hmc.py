#!/usr/bin/env python

# This file requests lpar inventory information from an IBM frame via the
# Hardware Management Console. You are not required to have ssh keys set
# up but you will need to supply a username on the command line.
# 
# usage: hmc.py --host <hmc> --user <username>
#
# Written by Kate McDonald <https://github.com/katishna>
# 2015
# With thanks to Melissa Donohue for all the python help

from subprocess import Popen,PIPE
import os, sys
import ConfigParser
import json

result = {}

class HMCinventory(object):

# read some settings from the .ini
    def read_settings(self):
        config = ConfigParser.SafeConfigParser()
        config.read(os.path.dirname(os.path.realpath(__file__)) + '/hmc.ini')

        # server
        if config.has_option('hmc', 'hostname'):
            self.hmcname = config.get('hmc', 'hostname')

        # login
        if config.has_option('hmc', 'username'):
            self.hmc_username = config.get('hmc', 'username')


# gets a list of frames on the HMC
    def get_frames(self, hmcname, username):
        data = {}
        pipe = Popen(['ssh', '-l', username, hmcname, 'lssyscfg', '-r', 'sys', '-F', 'name'], stdout=PIPE, universal_newlines=False)
        data = [x[:-1] for x in pipe.stdout.readlines()]
        return data

# gets a list of LPARs on a given frame
    def get_lpars(self, hmcname, username, frame):
        data = {}
        lparData = Popen(['ssh', '-l', username, hmcname, 'lssyscfg', '-r', 'lpar', '-m', frame, '-F', 'name'], stdout=PIPE)
        data  = [x[:-1] for x in lparData.stdout.readlines()]
        return data

        
    def __init__(self):

        self.hmcname = None
        self.hmc_username = None

        self.read_settings()

        if self.hmcname and self.hmc_username:

            HMC = self.hmcname
            USER = self.hmc_username
            framelist = self.get_frames(HMC, USER)
            for frame in framelist:
                print frame
                data = self.get_lpars(HMC, USER, frame)
                print json.dumps(data)

        else:
            print >> sys.stderr, "Error: Configuration of server and username are required in hmc.ini."
            sys.exit(1)

HMCinventory()

