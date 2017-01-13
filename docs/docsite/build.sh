#!/bin/bash

make -f Makefile.old clean
make -f Makefile.old modules
make -f Makefile.old directives

time make html
