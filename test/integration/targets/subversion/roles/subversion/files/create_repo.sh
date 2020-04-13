#!/usr/bin/env bash

svnadmin create "$1"
svn mkdir "file://$PWD/$1/trunk" -m "make trunk"
svn mkdir "file://$PWD/$1/tags" -m "make tags"
svn mkdir "file://$PWD/$1/branches" -m "make branches"
