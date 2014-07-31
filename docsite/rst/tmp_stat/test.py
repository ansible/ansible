#!/usr/bin/env python
# -*- coding: UTF-8 -*-


# import defaults
import textwrap
import re

opt_indent="        "

_ITALIC = re.compile(r"I\(([^)]+)\)")
_BOLD   = re.compile(r"B\(([^)]+)\)")
_MODULE = re.compile(r"M\(([^)]+)\)")
_URL    = re.compile(r"U\(([^)]+)\)")
_CONST  = re.compile(r"C\(([^)]+)\)")
PAGER   = 'less'
LESS_OPTS = 'FRSX' # -F (quit-if-one-screen) -R (allow raw ansi control chars)
                   # -S (chop long lines) -X (disable termcap init and de-init)


def tty_ify(text):

    t = _ITALIC.sub("`" + r"\1" + "'", text)    # I(word) => `word'
    t = _BOLD.sub("*" + r"\1" + "*", t)         # B(word) => *word*
    t = _MODULE.sub("[" + r"\1" + "]", t)       # M(word) => [word]
    t = _URL.sub(r"\1", t)                      # U(word) => word
    t = _CONST.sub("`" + r"\1" + "'", t)        # C(word) => `word'

    return t


#####################################################################
#
#        UNITTEST
#
#   Purpose : make a random list of parameters
#
#   For one example :
#       - each parameter is defined by a random set of value
#           which defines the number of columns
#       - each list of parameters can have a random number of
#           lines
#
#       Ex :    param1   definiton1  definiton2
#               param2   definiton1  definiton2
#               etc..
#
#       Python form : [[param1, definition1, definition2],
#                       [param2, definition1, definition2],
#                       etc..
#
#       The actual behaviour of any over long line is to go to
#       the next line.
#
#####################################################################


import random
import string

# max values for words, columns and lines
letters_max_numb = random.randrange(6, 33)
cols_max_numb = random.randrange(3, 6)
params_max_numb = random.randrange(3, 20)

def make_a_word():
    word = ''.join([random.choice(string.letters) for i in range(random.randrange(4, letters_max_numb, 1))])
    return word

def make_a_line():
    line = [make_a_word() for i in range(1, cols_max_numb)]
    return line

def make_a_param_list():
    param_list = [make_a_line() for i in range(1, params_max_numb)]
    return param_list

def format_param(p=list, cols_width=list):
    indentf = zip(p, cols_width)
    line = []
    for word,col_len in indentf:
        line.append(word + ' ' * (col_len-len(word)))
    return ''.join(line)

#print make_a_word()
#print make_a_line()
#print make_a_param_list()

parameters = make_a_param_list()

print("\nParameters:\n")

# number of columns
column_nb = len(parameters[0])

# parameters list in column
cols_list = [[p[n] for p in parameters] for n in range(column_nb)]

# max columns strings list
maxcol_strs = [max(cols_list[n], key=len) for n in range(column_nb)]

# final columns widths list
cols_width = [len(s) + 3 for s in maxcol_strs]

for p in parameters:
    parameter = format_param(p, cols_width)
    print(textwrap.fill(tty_ify(parameter), initial_indent="  ",
                        subsequent_indent=opt_indent))
