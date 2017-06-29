#!/bin/bash

# ansible-makepage [-q|--quiet] module_name|file.rst
# A small script to make it easier to build a single documentation
# page during development.

PROG=$(basename "$0")

if [[ $# -gt 2 ]]; then
   USAGE="YES"
fi

while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    -q|--quiet)
    QUIET="YES"
    shift
    ;;
    *)
    PAGE="$1"
    shift
    ;; 
esac
done

if [ "$USAGE" == "YES" ] || [[ -z "$PAGE" ]]; then
  echo 
  echo "$PROG - build a single page of the ansible documentation."
  echo 
  echo "Usage: $PROG [-q|--quiet] module_name|file.rst" 
  echo "   [-q|--quiet]   do not sound terminal bell when complete."
  echo "   module name, e.g. setup or rst file e.g. intro_windows.rst" 
  echo 
  exit 1
fi

# append _module.rst if the file doesn't end in '.rst'
if [[ $PAGE == *".rst"* ]]; then
  FILE=$PAGE
else
  FILE=${PAGE}_module.rst
fi

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd "$DIR/../docsite"

make clean modules staticmin

# workaround for missing css

cp _themes/srtd/static/css/theme.min.css ./_build/html/_static/css

make htmlsingle rst="$FILE"


if [ "$QUIET" != "YES" ]; then
   echo 
fi

echo "$PROG Done."
