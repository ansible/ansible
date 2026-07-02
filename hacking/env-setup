#!/bin/sh
# usage: source hacking/env-setup [-q]
#    modifies environment for running Ansible from checkout

# prepend a value to a potentially empty path variable
# usage: prepend_path variable_name value
prepend_path()
{
    variable_name="$1"
    value="$2"

    old_value=$( eval "echo \$$variable_name" )

    if [ "x$old_value" != "x" ]; then
        value="$value:"
    fi

    export "$variable_name=$value$old_value"
}

# Default values for shell variables we use
PYTHONPATH=${PYTHONPATH-""}
PATH=${PATH-""}
MANPATH=${MANPATH-$(manpath)}
PYTHON=$(command -v python3 || command -v python)
PYTHON_BIN=${PYTHON_BIN-$PYTHON}

verbosity=${1-info} # Defaults to `info' if unspecified

if [ "$verbosity" = -q ]; then
    verbosity=silent
fi

# When run using source as directed, $0 gets set to bash, so we must use $BASH_SOURCE
if [ -n "$BASH_SOURCE" ] ; then
    HACKING_DIR=$(dirname "$BASH_SOURCE")
elif [ $(basename -- "$0") = "env-setup" ]; then
    HACKING_DIR=$(dirname "$0")
# Works with ksh93 but not pdksh, have to eval to keep ash happy...
elif [ -n "$KSH_VERSION" ] && echo $KSH_VERSION | grep -qv '^@(#)PD KSH'; then
    eval "HACKING_DIR=\$(dirname \"\${.sh.file}\")"
else
    HACKING_DIR="$PWD/hacking"
fi
# The below is an alternative to readlink -fn which doesn't exist on macOS
# Source: http://stackoverflow.com/a/1678636
FULL_PATH=$("$PYTHON_BIN" -c "import os; print(os.path.realpath('$HACKING_DIR'))")
export ANSIBLE_DEV_HOME="$(dirname "$FULL_PATH")"

PREFIX_PYTHONPATH="$ANSIBLE_DEV_HOME/lib"
ANSIBLE_TEST_PREFIX_PYTHONPATH="$ANSIBLE_DEV_HOME/test/lib"
PREFIX_PATH="$ANSIBLE_DEV_HOME/bin"
PREFIX_MANPATH="$ANSIBLE_DEV_HOME/docs/man"

expr "$PYTHONPATH" : "${PREFIX_PYTHONPATH}.*" > /dev/null || prepend_path PYTHONPATH "$PREFIX_PYTHONPATH"
expr "$PYTHONPATH" : "${ANSIBLE_TEST_PREFIX_PYTHONPATH}.*" > /dev/null || prepend_path PYTHONPATH "$ANSIBLE_TEST_PREFIX_PYTHONPATH"
expr "$PATH" : "${PREFIX_PATH}.*" > /dev/null || prepend_path PATH "$PREFIX_PATH"
expr "$MANPATH" : "${PREFIX_MANPATH}.*" > /dev/null || prepend_path MANPATH "$PREFIX_MANPATH"

if [ "$ANSIBLE_DEV_HOME" != "$PWD" ] ; then
    current_dir="$PWD"
else
    current_dir="$ANSIBLE_DEV_HOME"
fi
(
	cd "$ANSIBLE_DEV_HOME"
	if [ "$verbosity" = silent ] ; then
            find . -type f -name "*.pyc" -exec rm -f {} \; > /dev/null 2>&1
	else
            find . -type f -name "*.pyc" -exec rm -f {} \;
	fi
	cd "$current_dir"
)

if [ "$verbosity" != silent ] ; then
    cat <<- EOF

	Setting up Ansible to run out of checkout...

	PATH=$PATH
	PYTHONPATH=$PYTHONPATH
	MANPATH=$MANPATH

	Remember, you may wish to specify your host file with -i

	Done!

	EOF
fi
