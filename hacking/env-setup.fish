#!/usr/bin/env fish
# usage: . ./hacking/env-setup [-q]
#    modifies environment for running Ansible from checkout
set HACKING_DIR (dirname (status -f))
set FULL_PATH (python -c "import os; print(os.path.realpath('$HACKING_DIR'))")
set ANSIBLE_HOME (dirname $FULL_PATH)
set PREFIX_PYTHONPATH $ANSIBLE_HOME/lib 
set PREFIX_PATH $ANSIBLE_HOME/bin 
set PREFIX_MANPATH $ANSIBLE_HOME/docs/man

# Set PYTHONPATH
if not set -q PYTHONPATH
    set -gx PYTHONPATH $PREFIX_PYTHONPATH
else
    switch PYTHONPATH
        case "$PREFIX_PYTHONPATH*"
        case "*"
            echo "Appending PYTHONPATH"
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
        set -gx MANPATH $PREFIX_MANPATH
    else
        set -gx MANPATH $PREFIX_MANPATH $MANPATH
    end
end

set -gx ANSIBLE_LIBRARY $ANSIBLE_HOME/library

# Generate egg_info so that pkg_resources works
pushd $ANSIBLE_HOME
python setup.py egg_info
if test -e $PREFIX_PYTHONPATH/ansible*.egg-info
    rm -r $PREFIX_PYTHONPATH/ansible*.egg-info
end
mv ansible*egg-info $PREFIX_PYTHONPATH
popd


if set -q argv 
    switch $argv
    case '-q' '--quiet'
    case '*'
        echo ""
        echo "Setting up Ansible to run out of checkout..."
        echo ""
        echo "PATH=$PATH"
        echo "PYTHONPATH=$PYTHONPATH"
        echo "ANSIBLE_LIBRARY=$ANSIBLE_LIBRARY"
        echo "MANPATH=$MANPATH"
        echo ""

        echo "Remember, you may wish to specify your host file with -i"
        echo ""
        echo "Done!"
        echo ""
   end
end
