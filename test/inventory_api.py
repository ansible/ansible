#!/usr/bin/env python

import json
import sys

from optparse import OptionParser

parser = OptionParser()
parser.add_option('-l', '--list', default=False, dest="list_hosts", action="store_true")
parser.add_option('-H', '--host', default=None, dest="host")
parser.add_option('-e', '--extra-vars', default=None, dest="extra")

options, args = parser.parse_args()

systems = {
    "ungrouped": [ "jupiter", "saturn" ],
    "greek": [ "zeus", "hera", "poseidon" ],
    "norse": [ "thor", "odin", "loki" ],
    "major-god": [ "zeus", "odin" ],
}

variables = {
    "thor": {
        "hammer": True
        },
    "zeus": {},
}

if options.list_hosts == True:
    print json.dumps(systems)
    sys.exit(0)

if options.host is not None:
    if options.extra:
        k,v = options.extra.split("=")
        variables[options.host][k] = v
    print json.dumps(variables[options.host])
    sys.exit(0)

parser.print_help()
sys.exit(1)