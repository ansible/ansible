#!/bin/sh

# PROVIDE: ansible_test_service
# REQUIRE: FILESYSTEMS devfs
# BEFORE:  LOGIN
# KEYWORD: nojail shutdown

. /etc/rc.subr

name="ansible_test_service"
rcvar="ansible_test_service_enable"
command="/usr/sbin/${name}"
pidfile="/var/run/${name}.pid"
extra_commands=reload
load_rc_config $name
run_rc_command "$1"
