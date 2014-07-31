#!/usr/bin/env python
# -*- coding: UTF-8 -*-


# import defaults
import os
import sys


for i in range(1, 20):
    os.system('python {0}/test.py'.format(os.path.dirname(sys.argv[0])))