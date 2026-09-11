#!/bin/foo

# Shell script with non-standard shebang.

# Since it appears in a files/ or templates/ directory inside an integration test,
# the 'shebang' sanity test should ignore it. This "test" is successful when no
# ignore.txt entry is needed for this file.
