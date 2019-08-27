#!/bin/sh
#

# LSB header

### BEGIN INIT INFO
# Provides: ansible-test
# Default-Start: 3 4 5
# Default-Stop: 0 1 2 6
# Short-Description: test daemon for ansible
# Description: This is a test daemon used by ansible for testing only
### END INIT INFO

# chkconfig header

# chkconfig: 345 99 99
# description:  This is a test daemon used by ansible for testing only
#
# processname: /usr/sbin/ansible_test_service

# Sanity checks.
[ -x /usr/sbin/ansible_test_service ] || exit 0

DEBIAN_VERSION=/etc/debian_version
SUSE_RELEASE=/etc/SuSE-release
# Source function library.
if [ -f $DEBIAN_VERSION ]; then
    . /lib/lsb/init-functions
elif [ -f $SUSE_RELEASE -a -r /etc/rc.status ]; then
    . /etc/rc.status
else
    . /etc/rc.d/init.d/functions
fi

SERVICE=ansible_test_service
PROCESS=ansible_test_service
CONFIG_ARGS=" "
if [ -f $DEBIAN_VERSION ]; then
    LOCKFILE=/var/lock/$SERVICE
else
    LOCKFILE=/var/lock/subsys/$SERVICE
fi

RETVAL=0

start() {
    echo -n "Starting ansible test daemon: "
    if [ -f $SUSE_RELEASE ]; then
        startproc -p /var/run/${SERVICE}.pid -f /usr/sbin/ansible_test_service
        rc_status -v
    elif [ -e $DEBIAN_VERSION ]; then
        if [ -f $LOCKFILE ]; then
            echo -n "already started, lock file found"
            RETVAL=1
        elif /usr/sbin/ansible_test_service; then
            echo -n "OK"
            RETVAL=0
        fi
    else
        daemon --check $SERVICE $PROCESS --daemonize $CONFIG_ARGS
    fi
    RETVAL=$?
    echo
    [ $RETVAL -eq 0 ] && touch $LOCKFILE
    return $RETVAL
}

stop() {
    echo -n "Stopping ansible test daemon: "
    if [ -f $SUSE_RELEASE ]; then
        killproc -TERM /usr/sbin/ansible_test_service
        rc_status -v
    elif [ -f $DEBIAN_VERSION ]; then
        # Added this since Debian's start-stop-daemon doesn't support spawned processes
        if ps -ef | grep "/usr/sbin/ansible_test_service" | grep -v grep | awk '{print $2}' | xargs kill &> /dev/null; then
            echo -n "OK"
            RETVAL=0
        else
            echo -n "Daemon is not started"
            RETVAL=1
        fi
    else
        killproc -p /var/run/${SERVICE}.pid
    fi
    RETVAL=$?
    echo
    if [ $RETVAL -eq 0 ]; then
        rm -f $LOCKFILE
        rm -f /var/run/$SERVICE.pid
    fi
}

restart() {
   stop
   start
}

# See how we were called.
case "$1" in
    start|stop|restart)
        $1
        ;;
    status)
        if [ -f $SUSE_RELEASE ]; then
            echo -n "Checking for ansible test service "
            checkproc /usr/sbin/ansible_test_service
            rc_status -v
        elif [ -f $DEBIAN_VERSION ]; then
            if [ -f $LOCKFILE ]; then
                RETVAL=0
                echo "ansible test is running."
            else
                RETVAL=1
                echo "ansible test is stopped."
            fi
        else
            status $PROCESS
            RETVAL=$?
        fi
        ;;
    condrestart)
        [ -f $LOCKFILE ] && restart || :
        ;;
    reload)
        echo "ok"
        RETVAL=0
        ;;
    *)
        echo "Usage: $0 {start|stop|status|restart|condrestart|reload}"
        exit 1
        ;;
esac
exit $RETVAL

