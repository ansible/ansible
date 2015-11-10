#!/bin/sh

#
# Test that we do not access private attributes of other objects.
#
# * private attributes of ourself are okay: self._private.
# * Private attributes of other objects are not: self.other._private
#

# Currently the code has many places where we're violating this test so we need
# to clean up the code before we can enable this.  Maybe we'll need to
# selectively blacklist modules so that we can work on this a piece at a time.
#
# Also need to implement whitelist for certain things like bundled libraries
# that violate this.
#
# 23-10-2015: Count was 508 lines
grep -Pri '(?<!self)\._(?!_)' $1|grep -v modules
