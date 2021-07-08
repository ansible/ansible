#!/usr/bin/env fish
# usage: . ./hacking/env-setup [-q]
#    modifies environment for running Ansible from checkout
set HACKING_DIR (dirname (status -f))
set FULL_PATH (python -c "import os; print(os.path.realpath('$HACKING_DIR'))")
set ANSIBLE_HOME (dirname $FULL_PATH)
set PREFIX_PYTHONPATH $ANSIBLE_HOME/lib
set PREFIX_PATH $ANSIBLE_HOME/bin
set PREFIX_MANPATH $ANSIBLE_HOME/docs/man

# set quiet flag
if test (count $argv) -ge 1
    switch $argv
        case '-q' '--quiet'
            set QUIET "true"
        case '*'
    end
end

# Set PYTHONPATH
if not set -q PYTHONPATH
    set -gx PYTHONPATH $PREFIX_PYTHONPATH
else
    switch PYTHONPATH
        case "$PREFIX_PYTHONPATH*"
        case "*"
            if not [ $QUIET ]
                echo "Appending PYTHONPATH"
            end
            set -gx PYTHONPATH "$PREFIX_PYTHONPATH:$PYTHONPATH"
    end
end

# Set PATH
if not contains $PREFIX_PATH $PATH
    set -gx PATH $PREFIX_PATH $PATH
end

# Set MANPATH
if not contains $PREFIX_MANPATH $MANPATH
    if not set -q MANPATH
        set -gx MANPATH $PREFIX_MANPATH:
    else
        set -gx MANPATH $PREFIX_MANPATH $MANPATH
    end
end

# Set PYTHON_BIN
if not set -q PYTHON_BIN
    if test (which python3)
        set -gx PYTHON_BIN (which python3)
    else if test (which python)
        set -gx PYTHON_BIN (which python)
    else
        echo "No valid Python found"
        exit 1
    end
end

#
# Generate egg_info so that pkg_resources works
#

# Do the work in a fuction
function gen_egg_info
    # Cannot use `test` on wildcards.
    # @see https://github.com/fish-shell/fish-shell/issues/5960
    if count $PREFIX_PYTHONPATH/ansible*.egg-info > /dev/null
        rm -rf $PREFIX_PYTHONPATH/ansible*.egg-info
    end

    if [ $QUIET ]
        set options '-q'
    end

    eval $PYTHON_BIN setup.py $options egg_info

end


pushd $ANSIBLE_HOME

if [ $QUIET ]
    gen_egg_info ^ /dev/null
    find . -type f -name "*.pyc" -exec rm -f '{}' ';' ^ /dev/null
else
    gen_egg_info
    find . -type f -name "*.pyc" -exec rm -f '{}' ';'
end

popd

if not [ $QUIET ]
    echo ""
    echo "Setting up Ansible to run out of checkout..."
    echo ""
    echo "PATH=$PATH"
    echo "PYTHONPATH=$PYTHONPATH"
    echo "PYTHON_BIN=$PYTHON_BIN"
    echo "ANSIBLE_LIBRARY=$ANSIBLE_LIBRARY"
    echo "MANPATH=$MANPATH"
    echo ""
    echo "Remember, you may wish to specify your host file with -i"
    echo ""
    echo "Done!"
    echo ""
end

set -e QUIET
