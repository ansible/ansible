#!/usr/bin/env bash

set -ux

#
# Check that with no filters set, all of these modules run as expected
#
ANSIBLE_CONFIG=no_filters.ini ansible-playbook copy.yml  -i ../../inventory -vvv "$@"
if test $? != 0 ; then
	echo "### Failed to run copy with no filters applied"
	exit 1
fi
ANSIBLE_CONFIG=no_filters.ini ansible-playbook pause.yml  -i ../../inventory -vvv "$@"
if test $? != 0 ; then
	echo "### Failed to run pause with no filters applied"
	exit 1
fi
ANSIBLE_CONFIG=no_filters.ini ansible-playbook tempfile.yml  -i ../../inventory -vvv "$@"
if test $? != 0 ; then
	echo "### Failed to run tempfile with no filters applied"
	exit 1
fi

#
# Check that if no modules are rejected then Ansible should not through traceback
#
ANSIBLE_CONFIG=no_rejectlist_module.ini ansible-playbook tempfile.yml  -i ../../inventory -vvv "$@"
if test $? != 0 ; then
	echo "### Failed to run tempfile with no modules rejected"
	exit 1
fi

#
# Check that with these modules filtered out, all of these modules fail to be found
#
ANSIBLE_CONFIG=filter_modules.ini ansible-playbook copy.yml -i ../../inventory -v "$@"
if test $? = 0 ; then
	echo "### Failed to prevent copy from running"
	exit 1
else
	echo "### Copy was prevented from running as expected"
fi
ANSIBLE_CONFIG=filter_modules.ini ansible-playbook pause.yml -i ../../inventory -v "$@"
if test $? = 0 ; then
	echo "### Failed to prevent pause from running"
	exit 1
else
	echo "### pause was prevented from running as expected"
fi
ANSIBLE_CONFIG=filter_modules.ini ansible-playbook tempfile.yml -i ../../inventory -v "$@"
if test $? = 0 ; then
	echo "### Failed to prevent tempfile from running"
	exit 1
else
	echo "### tempfile was prevented from running as expected"
fi

#
# ping is a special module as we test for its existence.  Check it specially
#

# Check that ping runs with no filter
ANSIBLE_CONFIG=no_filters.ini ansible-playbook ping.yml  -i ../../inventory -vvv "$@"
if test $? != 0 ; then
	echo "### Failed to run ping with no filters applied"
	exit 1
fi

# Check that other modules run with ping filtered
ANSIBLE_CONFIG=filter_ping.ini ansible-playbook copy.yml  -i ../../inventory -vvv "$@"
if test $? != 0 ; then
	echo "### Failed to run copy when a filter was applied to ping"
	exit 1
fi
# Check that ping fails to run when it is filtered
ANSIBLE_CONFIG=filter_ping.ini ansible-playbook ping.yml -i ../../inventory -v "$@"
if test $? = 0 ; then
	echo "### Failed to prevent ping from running"
	exit 1
else
	echo "### Ping was prevented from running as expected"
fi

#
# Check that specifying a lookup plugin in the filter has no effect
#

ANSIBLE_CONFIG=filter_lookup.ini ansible-playbook lookup.yml -i ../../inventory -vvv "$@"
if test $? != 0 ; then
	echo "### Failed to use a lookup plugin when it is incorrectly specified in the *module* reject list"
	exit 1
fi

#
# stat is a special module as we use it to run nearly every other module.  Check it specially
#

# Check that stat runs with no filter
ANSIBLE_CONFIG=no_filters.ini ansible-playbook stat.yml  -i ../../inventory -vvv "$@"
if test $? != 0 ; then
	echo "### Failed to run stat with no filters applied"
	exit 1
fi

# Check that running another module when stat is filtered gives us our custom error message
ANSIBLE_CONFIG=filter_stat.ini
export ANSIBLE_CONFIG
CAPTURE=$(ansible-playbook copy.yml  -i ../../inventory -vvv "$@" 2>&1)
if test $? = 0 ; then
	echo "### Copy ran even though stat is in the module reject list"
	exit 1
else
	echo "$CAPTURE" | grep 'The stat module was specified in the module reject list file,.*, but Ansible will not function without the stat module.  Please remove stat from the reject list.'
	if test $? != 0 ; then
		echo "### Stat did not give us our custom error message"
		exit 1
	fi
	echo "### Filtering stat failed with our custom error message as expected"
fi
unset ANSIBLE_CONFIG

# Check that running stat when stat is filtered gives our custom error message
ANSIBLE_CONFIG=filter_stat.ini
export ANSIBLE_CONFIG
CAPTURE=$(ansible-playbook stat.yml  -i ../../inventory -vvv "$@" 2>&1)
if test $? = 0 ; then
	echo "### Stat ran even though it is in the module reject list"
	exit 1
else
	echo "$CAPTURE" | grep 'The stat module was specified in the module reject list file,.*, but Ansible will not function without the stat module.  Please remove stat from the reject list.'
	if test $? != 0 ; then
		echo "### Stat did not give us our custom error message"
		exit 1
	fi
	echo "### Filtering stat failed with our custom error message as expected"
fi
unset ANSIBLE_CONFIG
