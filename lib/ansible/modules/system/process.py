#!/usr/bin/python
#
# Copyright (c) 2019 Ehab Arman, (@ehabarman)
#
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
module: process
version_added: "2.9.0"
author:
    - Ehab Arman (@ehabarman)
short_description: Manage users processes
description:
    - Manage users processes by performing processes search, kill, suspend
     and resume actions
    - For Linux targets
options:
    action:
        version_added: "2.9.0"
        description:
            - The main action to be performed, it has 4 choices. search, kill,
              suspend and resume.
            - search action finds all processes matching a specific properties
              which passed through the rest of the options. if no option
              passed,then the search will return all processes running
              on the host.
            - kill action will terminate a process using its pid, requires pid
              option to be performed.
            - suspend action will pause a process using its pid, requires pid
              option to be performed.
            - resume action will continue running a process using its pid
              after being stopped, requires pid option to be performed.
        type: str
        default: null
        aliases: []
        choices:
            - search
            - kill"
            - suspend
            - resume
        required: true
    user:
        version_added: "2.9.0"
        description:
            - The effective username of the process.
            - this option used with the search action only, its value will be
              ignored when using other actions.
            - it will force the search action to look for processes with this
              effective username.
            - default value will cause the search action to ignore the
              effective username of each process.
            - passing non-existent effective username value will
              cause the search to return empty list.
        type: str
        default: ""
        aliases:
            - euser
            - uname
        required: false
    not_user:
        version_added: "2.9.0"
        description:
            - The value of this option will be ignored unless the "user"
              option is used.
            - This option will negate the result of "user" option forcing
              the search to return all of the processes,which its effective
              username doesn't equal the passed value of the "user" option.
        type: bool
        default: false
        aliases:
            - not_euser
            - not_uname
        required: false
    ruser:
        version_added: "2.9.0"
        description:
            - The real user ID of the process.
            - this option used with the search action only, its value will be
              ignored when using other actions.
            - it will force the search action to look for processes with
              this real user ID.
            - default value will cause the search action to ignore the real
              user ID of each process.
            - passing non-existent real user ID value will cause the search
              to return empty list.
        type: str
        default: ""
        aliases: []
        required: false
    not_ruser:
        version_added: "2.9.0"
        description:
            - The value of this option will be ignored unless the "ruser"
              option is used.
            - This option will negate the result of "ruser" option forcing
              the search to return all of the processes, which its real user
              ID doesn't equal the passed value of the "ruser" option.
        type: bool
        default: false
        aliases: []
        required: false
    group:
        version_added: "2.9.0"
        description:
            - The effective group ID of the process.
            - this option used with the search action only, its value will be
              ignored when using other actions.
            - it will force the search action to look for processes with this
              effective group ID.
            - default value will cause the search action to ignore the
              effective group ID of each process.
            - passing non-existent effective group ID value will cause
              the search to return empty list.
        type: str
        default: ""
        aliases:
            - egroup
        required: false
    not_group:
        version_added: "2.9.0"
        description:
            - The value of this option will be ignored unless the group
              option is used.
            - This option will negate the result of group option forcing the
              search to return all of the processes.
            - which its effective group ID  doesn't equal the passed value of
              the group option.
        type: bool
        default: false
        aliases:
            - not_egroup
        required: false
    rgroup:
        version_added: "2.9.0"
        description:
            - The real group name of the process
            - this option used with the search action only, its value will be
              ignored when using other actions.
            - it will force the search action to look for processes with this
              real group name.
            - default value will cause the search action to ignore the
              real group name of each process.
            - passing non-existent real group name value will cause the
              search to return empty list.
        type: str
        default: ""
        aliases: []
        required: false
    not_rgroup:
        version_added: "2.9.0"
        description:
            - The value of this option will be ignored unless the group
              option is used.
            - This option will negate the result of group option forcing the
              search to return all of the processes.
            - which its real group name doesn't equal the passed value of
              the group option.
        type: bool
        default: false
        aliases: []
        required: false
    pid:
        version_added: "2.9.0"
        description:
            - a number representing the process ID.
            - pid is the only option that works with the rest of the action
              option choices beside search.
            - When using it with kill, suspend and resume, the pid should be
              passed exactly as in the targeted process.
            - When using search, you can replace digits by "*", the search
              action will look for all possible.
              values of '*", example pid=5* => search will look for processes
              50, 51, 52, 53, 54, 55, 56, 57, 58, 59.
            - the maximum number of digits which can be used is 7 digits.
            - the search action will ignore it will not search for processes
              according to the pid if no value is passed.
            - The other actions will fail the task since they require pid.
        type: str
        default: ""
        aliases:
            - tgid
        required: false
    not_pid:
        version_added: "2.9.0"
        description:
            - The value of this option will be ignored unless the pid option
              is used.
            - This option will negate the result of pid option forcing the
              search to return all of the processes.
            - which its process ID doesn't equal the passed value of the
              pid option.
            - the search action will ignore the option if the default value
              is used.
        type: bool
        default: false
        aliases:
            - not_tgid
        required: false
    pgid:
        version_added: "2.9.0"
        description:
            - a number representing the process group ID.
            - this option used with the search action only, its value will be
              ignored when using other actions.
            - pgid will force the search action to look for processes with
              this process group ID.
            - When using it, you can replace digits by *, the search action
              will look for all possible values of *. example pid=5* =>
              search will look for processes 50, 51, 52, 53, 54, 55, 56, 57,
              58, 59.
            - the maximum number of digits which can be used is 7 digits.
            - the search action will ignore it will not search for processes
              according to the pid if no value is passed.
        type: str
        default: ""
        aliases:
            - pgrp
        required: false
    not_pgid:
        version_added: "2.9.0"
        description:
            - The value of this option will be ignored unless the pgid option
              is used.
            - This option will negate the result of pgid option forcing the
              search to return all of the processes.
            - which its process group ID doesn't equal the passed value of
              the pgid option.
            - the search action will ignore the option if the default value
              is used.
        type: bool
        default: false
        aliases:
            - not_pgrp
        required: false
    ppid:
        version_added: "2.9.0"
        description:
            - The parent process ID
            - this option used with the search action only, its value will be
              ignored when using other actions.
            - pgid will force the search action to look for processes by
              their parents IDs.
            - When using it, you can replace digits by *, the search action
              will look for all possible values of *.
            - example pid=5* => search will look for processes that their
              parents have the values 50, 51, 52, 53, 54, 55, 56, 57, 58, 59.
            - the maximum number of digits which can be used is 7 digits.
            - the search action will ignore it will not search for processes
              according to the parent ID if no value is passed.
        type: str
        default: ""
        aliases: []
        required: false
    not_ppid:
        version_added: "2.9.0"
        description:
            - The value of this option will be ignored unless the ppid option
              is used
            - This option will negate the result of ppid option forcing the
              search to return all of the processes.
            - which its parent process ID doesn't equal the passed value of
              the ppid option.
            - the search action will ignore the option if the default value
              is used.
        type: bool
        default: false
        aliases: []
        required: false
    stat:
        version_added: "2.9.0"
        description:
            - multi-character process state
            - this option used with the search action only, its value will be
              ignored when using other actions.
            - stat will force the search action to look for processes by
              their stat.
            - you can choose one or more of the stat values without
              repetitions.
            - The search will look for processes which has a subset equal
              to the passed value.
            - In order to look for exact stat set use * character.
            - the search action will ignore the option if the default value
              is used.
            - here are the different values of state and its description:-
            -   (D)  uninterruptible sleep (usually IO)
            -   (R)  running or runnable (on run queue)
            -   (S)  interruptible sleep (waiting for an event to complete)
            -   (T)  stopped, either by a job control signal or because it is
                being traced.
            -   (W)  paging (not valid since the 2.6.xx kernel)
            -   (X)  dead (should never be seen)
            -   (Z)  defunct (zombie) process, terminated but not reaped by
                its parent.
            -   (<)  high-priority (not nice to other users)
            -   (N)  low-priority (nice to other users)
            -   (L)  has pages locked into memory (for real-time & custom IO)
            -   (s)  is a session leader
            -   (l)  is multi-threaded (using CLONE_THREAD, like NPTL
                     pthreads do)
            -   (+)  is in the foreground process group
            -   (*)  forces the search to look for an equal stat set
        type: str
        default: ""
        aliases: []
        choices: ['D', 'R', 'S', 'T', 'W', 'X', 'Z', '<', 'N', 'L', 's', 'I',
                  ' +', '*']
        required: false
    not_stat:
        version_added: "2.9.0"
        description:
            - The value of this option will be ignored unless the stat option
              is used.
            - This option will negate the result of stat option forcing the
              search to return all of the processes.
            - which its stat set is not a super set of the passed set of
              the stat option.
            - the search action will ignore the option if the default value
              is used.
        type: bool
        default: false
        aliases: []
        required: false
    rss:
        version_added: "2.9.0"
        description:
            - resident set size, the non-swapped physical memory that a task
              has used (in kilobytes).
            - this option used with the search action only, its value will be
              ignored when using other actions.
            - this option will force the search action to get the processes
              with rss within the passed range.
            - rss accepts only a range value, to positive numbers in the
              form num1-num2.
            - num1 can be equal or smaller than num2.
            - the search action will ignore the range if the default value
              is used.
        type: str
        default: ""
        aliases:
            - rssize
            - rsz
        required: false
    not_rss:
        version_added: "2.9.0"
        description:
            - The value of this option will be ignored unless the rss option
              is used
            - This option will negate the result of rss option forcing the
              search to return all of the processes.
            - which its rss size is not in range of the passed range of the
              rss option.
            - the search action will ignore the option if the default value
              is used.
        type: bool
        default: false
        aliases:
            - not_rssize
            - not_rsz
        required: false
    vsz:
        version_added: "2.9.0"
        description:
            - virtual memory size of the process in KiB (1024-byte units)
            - this option used with the search action only, its value will be
              ignored when using other actions.
            - this option will force the search action to get the processes
              with vsz within the passed range.
            - vsz accepts only a range value, to positive numbers in the form
              num1-num2.
            - num1 can be equal or smaller than num2.
            - the search action will ignore the option if the default value
              is used.
        type: str
        default: ""
        aliases:
            - vsize
        required: false
    not_vsz:
        version_added: "2.9.0"
        description:
            - The value of this option will be ignored unless the vsz option
              is used.
            - This option will negate the result of vsz option forcing the
              search to return all of the processes.
            - which its vsz size is not in range of the passed range of the
              vsz option.
            - the search action will ignore the option if the default value
              is used.
        type: bool
        default: false
        aliases:
            - not_vsz
        required: false
    memory_usage:
        version_added: "2.9.0"
        description:
            - ratio of the process's resident set size to the physical memory
              on the machine, expressed as a percentage.
            - this option used with the search action only, its value will be
              ignored when using other actions.
            - this option will force the search action to get the processes
              with memory_usage% within the passed range.
            - memory_usage accepts only a range value, two positive numbers
              in the form xx.x-xx.x .
            - num1 can be equal or smaller than num2 and can't be lower than
              0.0 or greater than 99.9.
            - the search action will ignore the option if the default value
              is used.
        type: str
        default: ""
        aliases: [ "%mem", "pmem" ]
        required: false
    not_memory_usage:
        version_added: "2.9.0"
        description:
            - The value of this option will be ignored unless the
              memory_usage option is used.
            - This option will negate the result of memory_usage option
              forcing the search to return.
            - all of the processes which its memory_usage% is not in range of
              the passed range of the memory_usage option.
            - the search action will ignore the option if the default value
              is used.
        type: bool
        default: false
        aliases:
            - not_%mem
            - not_pmem
        required: false
    cpu_utilization:
        version_added: "2.9.0"
        description:
            - the CPU time used divided by the time the process has been
              running (cputime/real-time ratio),
            - expressed as a percentage. this option used with the search
              action only, its value will be ignored when using other actions.
            - the option will force the search action to get the processes
              with cpu_utilization% within the passed range.
            - cpu_utilization accepts only a range value, to positive numbers
              in the form xx.x-xx.x .
            - num1 can be equal or smaller than num2 and can't be lower than
              0.0 or greater than 99.9.
            - the search action will ignore the option if the default value
              is used.
        type: str
        default: ""
        aliases: [ "%cpu", "pcpu" ]
        required: false
    not_cpu_utilization:
        version_added: "2.9.0"
        description:
            - The value of this option will be ignored unless the
              cpu_utilization option is used.
            - This option will negate the result of cpu_utilization option
              forcing the search to return.
            - all of the processes which its cpu_utilization% is not in range
              of the passed range of the "cpu_utilization" option.
            - the search action will ignore the option if the default value
              is used.
            - the search action will ignore the option if the default value
              is used.
        type: bool
        default: false
        aliases:
            - not_%cpu
            - not_pcpu
        required: false
    cpu_time:
        version_added: "2.9.0"
        description:
            - cumulative CPU time
            - this option used with the search action only, its value will be
              ignored when using other actions.
            - this option will force the search action to get the processes
              with cumulative CPU time within the passed range.
            - cpu_time accepts only a range value, each value takes the
              format [DD:]hh:mm:ss.
            - the range will look like this, [DD:]hh:mm:ss-[DD:]hh:mm:ss
              with the left value equal or small than the right.
            - the lowest possible value is 00:00:00 (0 sec) while the
              greatest is 99:99:99:99 (100 days).
            - the search action will ignore the option if the default value
              is used.
        type: str
        default: ""
        aliases:
            - cputime
            - time
        required: false
    not_cpu_time:
        version_added: "2.9.0"
        description:
            - The value of this option will be ignored unless the cpu_time
              option is used.
            - This option will negate the result of cpu_time option forcing
              the search to return .
            - all of the processes which its cpu_time is not in range of the
             passed range of the "cpu_time" option.
            - the search action will ignore the option if the default value
              is used.
        type: bool
        default: false
        aliases:
            - not_cputime
            - not_time
        required: false
    elapsed_time:
        version_added: "2.9.0"
        description:
            - elapsed time since the process was started
            - this option used with the search action only, its value will be
              ignored when using other actions.
            - this option will force the search action to get the processes
              with elapsed_time time within the passed range.
            - elapsed_time accepts only a range value, earch value takes the
              format [[DD:]hh]:mm:ss.
            - the range will look like this, [[DD:]hh]:mm:ss-[[DD:]hh]:mm:ss
              with the left value equal or small than the right.
            - the lowest possible value is 00:00:00 (0 sec) while the
              greatest is 99:99:99:99 (100 days).
            - the search action will ignore the option if the default value
              is used.
        type: str
        default: ""
        aliases:
            - etime
        required: false
    not_elapsed_time:
        version_added: "2.9.0"
        description:
            - The value of this option will be ignored unless the elapsed
             _time option is used.
            - This option will negate the result of elapsed_time option
              forcing the search to return.
            - all of the processes which its elapsed_time is not in range
              of the passed range of the "elapsed_time" option.
            - the search action will ignore the option if the default value
              is used.
        type: bool
        default: false
        aliases:
            - etime
        required: false
    command:
        version_added: "2.9.0"
        description:
            - command with all its arguments as a string.
            - command accepts a regex value and force the search to look for
              processes with commands match the regex.
            - the regex can be any correct format regex.
            - the search action will ignore the option if the default value
              is used.
        type: str
        default: ""
        aliases:
            - cmd
            - args
        required: false
    not_command:
        version_added: "2.9.0"
        description:
            - The value of this option will be ignored unless the command
              option is used.
            - This option will negate the result of command option forcing
              the search to return.
            - all of the processes which its command doesn't match the passed
              regex value.
            - the search action will ignore the option if the default value
              is used.
        type: bool
        default: false
        aliases:
            - not_cmd
            - not_args
        required: false
    get_children:
        version_added: "2.9.0"
        description:
            - this option works only with the search action, it will be
              ignored in the rest of the actions.
            - it will force the search action get basic information about
              the children of each process.
            - the information are [ "pid", "name"].
            - the search action will ignore the option if the default value
              is used.
        type: bool
        default: false
        aliases: []
        required: false
    has_children:
        version_added: "2.9.0"
        description:
            - This option requires the get_children to be set to True.
            - It will filter the processes according to their children
            - yes choice will get only the processes which have children
            - no choice will get only the processes which don't have children
            - the search action will ignore the option if the default value
              is used.
        type: str
        default: ""
        aliases: []
        choices:
            - yes
            - no
        required: false
    get_threads:
        version_added: "2.9.0"
        description:
            - this option works only with the search action, it will be
              ignored in the rest of the actions.
            - it will force the search action get basic information about
              the threads of each process.
            - the information are [ 'spid', 'time', 'command'].
            - the search action will ignore the option if the default value
              is used.
        type: bool
        default: false
        aliases: []
        required: false
notes:
- To use module effectively, you need to have basic understanding of the
  process properties in linux
- This module was tested on linux distributions only
seealso:
  - name: Linux ps command
  description: Complete reference of processes attributes and stats
  link: https://www.computerhope.com/unix/ups.htm
'''

RETURN = r'''
---
msg:
    description:
        - return the general result of the task execution
    returned: always
    type: str
    sample:
        - search action has been performed successfully
        - error during killing the process
        - "bash: kill: (555) No such process"
        - performed suspend action successfully
    version_added: "2.9.0"
result:
    description:
        - contains a list of processes that matches the conditions passed
          through the various options
    returned: on success
    type: list
    sample:
        [
            {
                "children": [],
                "command": "/usr/lib/systemd/systemd-journald",
                "cpu_time": "00:00:00",
                "cpu_utilization": "0.0",
                "elapsed_time": "01:15:25",
                "group": "root",
                "memory_usage": "0.4",
                "nice": "0",
                "pgid": "276",
                "pid": "276",
                "ppid": "1",
                "priority": "19",
                "psr": "0",
                "rgroup": "root",
                "rss": "68044",
                "ruser": "root",
                "stat": "Ss",
                "threads": [
                    {
                        "comm": "systemd-journal",
                        "spid": "276",
                        "time": "00:00:00"
                    }
                ],
                "tty": "?",
                "user": "root",
                "vsz": "155288"
            },
            {
                "children": [
                    {
                        name: llvmpipe,
                        pid: 527
                    }
                ],
                "command": "/usr/lib/Xorg -nolisten tcp -auth
                /var/run/sddm/{0050e749-7119-4dae-8b5c-673fb4cd69b5}
                -background none -noreset -displayfd 17 -seat seat0 vt1",
                "cpu_time": "00:05:43",
                "cpu_utilization": "7.6",
                "elapsed_time": "01:15:11",
                "group": "root",
                "memory_usage": "1.0",
                "nice": "0",
                "pgid": "516",
                "pid": "516",
                "ppid": "497",
                "priority": "19",
                "psr": "7",
                "rgroup": "root",
                "rss": "172904",
                "ruser": "root",
                "stat": "Ssl+",
                "threads": [
                    {
                        "comm": "Xorg",
                        "spid": "516",
                        "time": "00:05:43"
                    },
                    {
                        "comm": "Xorg",
                        "spid": "530",
                        "time": "00:00:00"
                    },
                    {
                        "comm": "Xorg",
                        "spid": "532",
                        "time": "00:00:00"
                    },
                    {
                        "comm": "llvmpipe-0",
                        "spid": "650",
                        "time": "00:00:00"
                    },
                    {
                        "comm": "llvmpipe-1",
                        "spid": "651",
                        "time": "00:00:00"
                    },
                ],
                "tty": "tty1",
                "user": "root",
                "vsz": "917324"
            }
        ]
    version_added: "2.9.0"
    contains:
        children:
            description: list of the children processes
            returned: on successful search when get_children = True
            type: list
            sample:
                [
                    {
                        name: llvmpipe,
                        pid: 527
                    }
                ]
            contains:
                pid:
                    description: process id
                    returned: on successful search when get_children = True
                    type: string
                    sample:
                        - 22
                        - 23
                        - 32
                    version_added: "2.9.0"
                name:
                    description: process name
                    returned: on successful search when get_children = True
                    type: string
                    sample:
                        - llvmpipe
                        - systemd-logind
                        - ModemManager
                    version_added: "2.9.0"
            version_added: "2.9.0"
        command:
            description: the running command of the process
            returned: always on successful search
            type: str
            sample:
              - /sbin/init
              - kworker/u16:1-phy0
            version_added: "2.9.0"
        cpu_time:
            description: the process cumulative cpu time
            returned: always on successful search
            type: str
            sample:
              - 00:00:00
              - 05:36:04
              - 06:06:10
            version_added: "2.9.0"
        cpu_utilization:
            description: the CPU time used divided by the time the process
                         has been running.
            returned: always on successful search.
            type: str
            sample:
              - 0.0
              - 1.1
              - 0.4
            version_added: "2.9.0"
        elapsed_time:
            description: elapsed time since the process was started
            returned: always on successful search.
            type: str
            sample:
              - 00:00:01
              - 02:2:01
              - 03:03:10
            version_added: "2.9.0"
        group:
            description: effective group ID of the process
            returned: always on successful search
            type: str
            sample:
              - root
              - polkitd
              - avahi
            version_added: "2.9.0"
        memory_usage:
            description: ratio of the process's resident set size to the
                         physical memory on the machine.
            returned: always on successful search
            type: str
            sample:
              - 0.1
              - 16.4
              - 8.2
            version_added: "2.9.0"
        nice:
            description: the degree of a process niceness, the the higher
                         the value the lesser time the process will get to
                         use the cpu. highest value is 19 while the lowest
                         is -20.
            returned: always on successful search
            type: str
            sample:
              - 0
              - 1
              - 19
            version_added: "2.9.0"
        pgid:
            description: process group ID
            returned: always on successful search
            type: str
            sample:
              - 1
              - 100
              - 2700
            version_added: "2.9.0"
        pid:
            description: The process ID
            returned: always on successful search
            type: str
            sample:
              - 55
              - 1199
              - 27083
            version_added: "2.9.0"
        ppid:
            description: The ID of the parent process
            returned: always on successful search
            type: str
            sample:
                - 1
                - 3
                - 1000
            version_added: "2.9.0"
        priority:
            description: priority of the process. Higher number means
                         lower priority.
            returned: always on successful search
            type: str
            sample:
              - 19
              - 41
              - 139
            version_added: "2.9.0"
        psr:
            description: processor that process is currently assigned to.
            returned: always on successful search
            type: str
            sample:
              - 0
              - 6
              - 7
            version_added: "2.9.0"
        rgroup:
            description: real group name
            returned: always on successful search
            type: str
            sample:
              - root
              - polkitd
            version_added: "2.9.0"
        rss:
            description: resident set size, the non-swapped physical memory
                         that a task has used.
            returned: always on successful search
            type: str
            sample:
              - 2364
              - 20628
              - 43752
            version_added: "2.9.0"
        ruser:
            description: real user ID
            returned: always on successful search
            type: str
            sample:
              - root
              - rtkit
            version_added: "2.9.0"
        stat:
            description: multi-character process state
            returned: always on successful search
            type: str
            sample:
              - Ss+
              - Z+
              - T
            version_added: "2.9.0"
        threads:
            description: the threads running by the process
            returned: on successful search when get_thread = true
            type: list
            sample:
                [
                    {
                        "comm": "Xorg",
                        "spid": "516",
                        "time": "00:05:43"
                    },
                    {
                        "comm": "Xorg",
                        "spid": "530",
                        "time": "00:00:00"
                    },
                    {
                        "comm": "Xorg",
                        "spid": "532",
                        "time": "00:00:00"
                    },
                ]
            contains:
                comm:
                    description: the command running by the thread
                    returned: on successful search when get_thread = true
                    type: str
                    sample:
                      - Xorg
                      - python
                    version_added: "2.9.0"
                spid:
                    description: the thread id
                    returned: on successful search when get_thread = true
                    type: str
                    sample:
                      - 14707
                      - 14708
                      - 14709
                    version_added: "2.9.0"
                time:
                    description: the thread cumulated CPU time
                    returned: on successful search when get_thread = true
                    type: str
                    sample:
                     - 00:00:00
                     - 00:00:54
                     - 01:58:03
                    version_added: "2.9.0"
            version_added: "2.9.0"
        tty:
            description: controlling terminal
            returned: always on successful search
            type: str
            sample:
              - pts/2
              - tty1
              - ?
            version_added: "2.9.0"
        user:
            description: effective username
            returned: always on successful search
            type: str
            sample:
              - ehab
              - root
              - stack
            version_added: "2.9.0"
        vsz:
            description: virtual memory size of the process in KiB
            returned: always on successful search
            type: str
            sample:
              - 0
              - 7108
              - 497624
            version_added: "2.9.0"


stderr:
    description: details explanation of the error messages on fail return
    returned: on fail
    type: str
    sample:
        - "pid value must be exact during kill action"
        - "'S' occurred more than once, it is not allowed to repeat the same
           stat value more than once"
    version_added: "2.9.0"
rc:
    description: return code of the process, 0 on success and 1 on fail
    returned: always
    type: int
    sample:
        - 0
        - 1
    version_added: "2.9.0"
matches:
    description: number of the processes the matches the conditions passed
                 to the various options.
    returned: on search action success
    type: int
    sample:
        - 0
        - 50
        - 100
    version_added: "2.9.0"
'''

EXAMPLES = r'''
  - name: "get all runnning processes"
    process:
      action: "search"

  - name: "get all runnning processes owned by ruser root"
    process:
      action: "search"
      ruser: "root"

  - name: "get all runnning processes not owned by euser root"
    process:
      action: "search"
      user: "root"
      not_user: True

  - name: "get all running prcesses belong to rgroup foo and owned by ruser
           boo"
    process:
      action: "search"
      ruser: "boo"
      rgroup: "foo"

  - name: "get all processes which pid start with 12 and have a total of
           5 digits"
    process:
      action: "search"
      pid: "12***"

  - name: "get all process which it parent pid is 123456"
    process:
      action: "search"
      ppid: "123456"

  - name: "kill process which pid is 55"
    process:
      action: "kill"
      ppid: "55"

  - name: "suspend process which pid is 55"
    process:
      action: "suspend"
      ppid: "55"

  - name: "resume running process which pid is 55"
    process:
      action: "resume"
      ppid: "55"

  - name: "find all processes which cpu utilization more than 1%"
    process:
      action: "search"
      pcpu: "0.0-1.0"
      not_pcpu: True

  - name: "get all processes which started more than 2 hours ago and its
           cpu time is less than 1 hour"
    process:
      action: "search"
      cputime: "00:00:00-01:00:00"
      etime: "00:00:00-02:00:00"
      not_etime: True

  - name: "get all processes which its rss and vsz greather than 10MB"
    process:
      action: "search"
      rss: "0-10240"
      vsz: "0-10240"
      not_rss: True
      not_vsz: True

  - name: "get all running zombie processes with high priority"
    process:
      action: "search"
      stat: "Z<"

  - name: "get processes running in the foreground and stopped"
    process:
      action: "search"
      stat: "T+"

  - name: "get all processes which have children"
    process:
      action: "search"
      get_children: True
      has_children: "yes"
'''


import json
import re
from subprocess import Popen, PIPE
from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

ACTIONS = ["search", "kill", "suspend", "resume"]
INTEGER_RANGE_PATTERN = r"^\d+-\d+$"
DOUBLE_RANGE_PATTERN = r"((^[0-9]{1,2}.[0-9])|(^[0-9]{1,2}))-(([0-9]{1,2}." \
                       r"[0-9])|([0-9]{1,2}))$"
VALIDATE_CPU_TIME_LEFT_SIDE = r"^(([0-9]{2}:[0-2][0-9]:[0-5][0-9]:[0-5]" \
                              r"[0-9])|([0-2][0-9]:[0-5][0-9]:[0-5][0-9]))"
VALIDATE_CPU_TIME_RIGHT_SIDE = r"(([0-9]{2}:[0-2][0-9]:[0-5][0-9]:[0-5][" \
                               r"0-9])|([0-2][0-9]:[0-5][0-9]:[0-5][0-9]))$"
VALIDATE_CPU_TIME_PATTERN = VALIDATE_CPU_TIME_LEFT_SIDE + "-" + \
                            VALIDATE_CPU_TIME_RIGHT_SIDE
VALIDATE_ELAPSED_TIME_LEFT_SIDE = r"^(([0-9]{2}:[0-2][0-9]:[0-5][0-9]:[0-5]" \
                                  r"[0-9])|([0-2][0-9]:[0-5][0-9]:[0-5]" \
                                  r"[0-9])|[0-5][0-9]:[0-5][0-9])"
VALIDATE_ELAPSED_TIME_RIGHT_SIDE = r"(([0-9]{2}:[0-2][0-9]:[0-5][0-9]:[" \
                                   r"0-5][0-9])|([0-2][0-9]:[0-5][0-9]:" \
                                   r"[0-5][0-9])|[0-5][0-9]:[0-5][0-9])$"
VALIDATE_ELAPSED_TIME_PATTERN = VALIDATE_ELAPSED_TIME_LEFT_SIDE + "-" + \
                                VALIDATE_ELAPSED_TIME_RIGHT_SIDE
INTEGER_RANGE_FORMAT = "integer-integer"
DOUBLE_RANGE_FORMAT = "xx.x-xx.x"
CPU_TIME_RANGE_FORMAT = "[DD:]hh:mm:ss-[DD:]hh:mm:ss"
ELAPSED_TIME_RANGE_FORMAT = "[[DD:]hh]:mm:ss-[[DD:]hh]:mm:ss"

FIELDS = {
    "action": {"required": True, "type": "str"},
    "user": {"required": False, "type": "str", "default": "",
             "aliases": ["euser", "uname"]},
    "ruser": {"required": False, "type": "str", "default": ""},
    "group": {"required": False, "type": "str", "default": "",
              "aliases": ["egroup"]},
    "rgroup": {"required": False, "type": "str", "default": ""},
    "not_user": {"required": False, "type": "bool", "default": False,
                 "aliases": ["not_euser", "not_uname"]},
    "not_ruser": {"required": False, "type": "bool", "default": False},
    "not_group": {"required": False, "type": "bool", "default": False,
                  "aliases": ["not_egroup"]},
    "not_rgroup": {"required": False, "type": "bool", "default": False},
    "pid": {"required": False, "type": "str", "default": "",
            "aliases": ["tgid"]},
    "pgid": {"required": False, "type": "str", "default": "",
             "aliases": ["pgrp"]},
    "ppid": {"required": False, "type": "str", "default": ""},
    "not_pid": {"required": False, "type": "bool", "default": False,
                "aliases": ["not_tgid"]},
    "not_pgid": {"required": False, "type": "bool", "default": False,
                 "aliases": ["not_pgrp"]},
    "not_ppid": {"required": False, "type": "bool", "default": False},
    "stat": {"required": False, "type": "str", "default": ""},
    "not_stat": {"required": False, "type": "bool", "default": False},
    "rss": {"required": False, "type": "str", "default": "",
            "aliases": ["rssize", "rsz"]},
    "not_rss": {"required": False, "type": "bool", "default": False,
                "aliases": ["not_rssize", "not_rsz"]},
    "vsz": {"required": False, "type": "str", "default": "",
            "aliases": ["vsize"]},
    "not_vsz": {"required": False, "type": "bool", "default": False,
                "aliases": ["not_vsize"]},
    "memory_usage": {"required": False, "type": "str", "default": "",
                     "aliases": ["%mem", "pmem"]},
    "not_memory_usage": {"required": False, "type": "bool", "default": False,
                         "aliases": ["not_%mem", "not_pmem"]},
    "cpu_utilization": {"required": False, "type": "str", "default": "",
                        "aliases": ["%cpu", "pcpu"]},
    "not_cpu_utilization": {"required": False, "type": "bool",
                            "default": False,
                            "aliases": ["not_%cpu", "not_pcpu"]},
    "cpu_time": {"required": False, "type": "str", "default": "",
                 "aliases": ["cputime", "time"]},
    "not_cpu_time": {"required": False, "type": "bool", "default": False,
                     "aliases": ["not_cputime", "not_time"]},
    "elapsed_time": {"required": False, "type": "str", "default": "",
                     "aliases": ["etime"]},
    "not_elapsed_time": {"required": False, "type": "bool", "default": False,
                         "aliases": ["not_etime"]},
    "command": {"required": False, "type": "str", "default": "",
                "aliases": ["cmd", "args"]},
    "not_command": {"required": False, "type": "bool", "default": False,
                    "aliases": ["not_cmd", "not_args"]},
    "get_children": {"required": False, "type": "bool", "default": False},
    "has_children": {"required": False, "type": "str", "default": ""},
    "get_threads": {"required": False, "type": "bool", "default": False},
}


def main(ansible_module):
    ansible_check_mode = ansible_module.check_mode
    params = ansible_module.params
    common_validators_result = validate_common_passed_fields_values(params)
    did_the_task_fail(ansible_module, common_validators_result)

    execution_result = {'msg': '', 'rc': 0}

    action = params['action']
    if action == "search":
        search_validators_result = validate_search_passed_fields_values(params)
        did_the_task_fail(ansible_module, search_validators_result)
        execution_result = search(params)
    elif action == "kill":
        execution_result = execute_action(params, "9", ansible_check_mode)
    elif action == "suspend":
        execution_result = execute_action(params, "STOP", ansible_check_mode)
    elif action == "resume":
        execution_result = execute_action(params, "CONT", ansible_check_mode)

    # return final result
    did_the_task_fail(ansible_module, execution_result)
    ansible_module.exit_json(**execution_result)


def search(params):
    result = {'msg': '', 'rc': 0}

    # get process list
    headers = ["cpu_utilization", "cpu_time", "group", "ppid", "user",
               "rgroup", "nice", "pid", "pgid", "elapsed_time",
               "ruser",
               "tty", "vsz", "memory_usage", "priority", "rss", "stat", "psr",
               "command"]
    get_processes_list_command = 'ps -eo "%cpu cputime group ppid user' \
                                 ' rgroup nice pid pgid etime ruser tty vsz' \
                                 ' %mem pri rss stat psr args" '
    output, stderr, rc = run_shell_cmd(get_processes_list_command)

    if rc:
        result['msg'] = "failed to get processes list"
        result['stderr'] = stderr
        result['rc'] = rc
        return result

    raw_processes_list = output.strip().split("\n")[1:]
    processes_list = parse_process_list_into_dictionaries(raw_processes_list,
                                                          headers)

    # module fields values
    user = params['user']
    ruser = params['ruser']
    group = params['group']
    rgroup = params['rgroup']
    not_user = params['not_user']
    not_ruser = params['not_ruser']
    not_group = params['not_group']
    not_rgroup = params['not_rgroup']
    pid = params['pid']
    pgid = params['pgid']
    ppid = params['ppid']
    not_pid = params['not_pid']
    not_pgid = params['not_pgid']
    not_ppid = params['not_ppid']
    stat = params['stat']
    not_stat = params['not_stat']
    rss = params['rss']
    not_rss = params['not_rss']
    vsz = params['vsz']
    not_vsz = params['not_vsz']
    cpu_utilization = params['cpu_utilization']
    not_cpu_utilization = params['not_cpu_utilization']
    memory_usage = params['memory_usage']
    not_memory_usage = params['not_memory_usage']
    cpu_time = params['cpu_time']
    not_cpu_time = params['not_cpu_time']
    elapsed_time = params['elapsed_time']
    not_elapsed_time = params['not_elapsed_time']
    command = params['command']
    not_command = params['not_command']
    get_children = params['get_children']
    has_children = params['has_children']
    get_threads = params['get_threads']

    # filter process_list according to the passed fields values
    processes_list = filter_list_by_exact_name(user, not_user, processes_list,
                                               "user")
    processes_list = filter_list_by_exact_name(ruser, not_ruser,
                                               processes_list, "ruser")
    processes_list = filter_list_by_exact_name(group, not_group,
                                               processes_list, "group")
    processes_list = filter_list_by_exact_name(rgroup, not_rgroup,
                                               processes_list, "rgroup")
    processes_list = filter_list_by_regex_id(pid, not_pid, processes_list,
                                             "pid")
    processes_list = filter_list_by_regex_id(ppid, not_ppid, processes_list,
                                             "ppid")
    processes_list = filter_list_by_regex_id(pgid, not_pgid, processes_list,
                                             "pgid")
    processes_list = filter_list_by_stat(stat, not_stat, processes_list)
    processes_list = filter_list_by_number_range(rss, not_rss, processes_list,
                                                 "rss")
    processes_list = filter_list_by_number_range(vsz, not_vsz, processes_list,
                                                 "vsz")
    processes_list = filter_list_by_number_range(memory_usage,
                                                 not_memory_usage,
                                                 processes_list,
                                                 "memory_usage")
    processes_list = filter_list_by_number_range(cpu_utilization,
                                                 not_cpu_utilization,
                                                 processes_list,
                                                 "cpu_utilization")
    processes_list = filter_list_by_time_range(cpu_time, not_cpu_time,
                                               processes_list, "cpu_time")
    processes_list = filter_list_by_time_range(elapsed_time, not_elapsed_time,
                                               processes_list, "elapsed_time")
    processes_list = filter_list_by_regex(command, not_command, processes_list,
                                          "command")

    # get threads list for the remaining processes
    if get_threads:
        headers = ["spid", "time", "comm"]
        get_process_threads_command = 'ps -T -p {} -o "spid time comm"'
        for process in processes_list:
            output, stderr, rc = run_shell_cmd(
                get_process_threads_command.format(process["pid"]))
            raw_threads_list = output.strip().split("\n")[1:]
            process["threads"] = parse_process_list_into_dictionaries(
                raw_threads_list, headers)

    # get children processes list for the remaining porocesses
    if get_children:
        get_process_children_command = 'pgrep -l -P {}'
        headers = ["pid", "name"]
        for process in processes_list:
            output, stderr, rc = run_shell_cmd(
                get_process_children_command.format(process["pid"]))
            raw_children_list = output.strip().split("\n")[:]
            process["children"] = parse_process_list_into_dictionaries(
                raw_children_list, headers)

        # filter process according to has_children
        if has_children == "yes":
            processes_list = list(
                filter(lambda parent_process: len(process["children"]) != 0,
                       processes_list))
        elif has_children == "no":
            processes_list = list(
                filter(lambda parent_process: len(process["children"]) == 0,
                       processes_list))

    # return final result
    result['msg'] = "search action has been performed successfully"
    result['result'] = processes_list
    result['rc'] = 0
    result['matches'] = len(processes_list)
    return result


def execute_action(params, action_signal, check_mode):
    result = {'msg': '', 'rc': 0}
    pid = params["pid"]
    required_action = params['action']

    if not pid:
        result["msg"] = "pid value is needed to execute {} action".format(
            required_action)
        result["stderr"] = "set pid value"
        result["rc"] = 1
    if "*" in pid:
        result["msg"] = "error during killing the process"
        result["stderr"] = "pid value must be exact during kill action"
        result["rc"] = 1

    if result["rc"]:
        return result

    if not check_mode:
        action_command = "kill -{} {}".format(action_signal, pid)
        output, stderr, rc = run_shell_cmd(action_command)
    else:
        action_command = 'ps -eo "pid" | grep -Po "^{}$"'.format(pid)
        output, stderr, rc = run_shell_cmd(action_command)
        if rc:
            stderr = "-bash: kill: ({}) - No such process".format(pid)

    result["rc"] = rc
    if rc:
        result["msg"] = "failed to execute {} action".format(required_action)
        result["stderr"] = stderr
    else:
        result["msg"] = "performed {} action successfully".format(
            required_action)
        result["result"] = output

    return result


def filter_list_by_regex(command, reverse, processes_list, key):
    if command:
        return list(filter(lambda process: (has_regex_match(command, process[
            key])) != reverse, processes_list))
    return processes_list


def filter_list_by_time_range(time_range, reverse, processes_list, key):
    if time_range:
        left_side, right_side = [convert_time_to_seconds(side) for side in
                                 time_range.split("-")]
        return list(
            filter(lambda process: (left_side <= convert_time_to_seconds(
                process[key]) <= right_side) != reverse,
                processes_list))
    return processes_list


def filter_list_by_number_range(integer_range, reverse, processes_list, key):
    if integer_range:
        lower, upper = [float(num) for num in integer_range.split("-")]
        return list(filter(
            lambda process: (lower <= float(process[key]) <= upper) != reverse,
            processes_list))
    return processes_list


def filter_list_by_exact_name(name, reverse, processes_list, key):
    if name:
        return list(filter(lambda process: (process[key] == name) != reverse,
                           processes_list))
    return processes_list


def filter_list_by_regex_id(id_raw_pattern, reverse, processes_list, key):
    if id_raw_pattern:
        pattern = "^" + id_raw_pattern.lstrip().replace("*", "[0-9]") + "$"
        return list(filter(lambda process: (has_regex_match(pattern, process[
            key])) != reverse, processes_list))
    return processes_list


def filter_list_by_stat(stat, reverse, processes_list):
    # for exact stat use "*"
    if not stat:
        return processes_list

    exact_state = False
    if "*" in stat:
        exact_state = True
        stat = stat.replace("*", "")

    if exact_state:
        stat = sorted(stat)
        return list(filter(
            lambda process: (stat == sorted(process['stat'])) != reverse,
            processes_list))
    else:
        stat = set(stat)
        return list(filter(
            lambda process: (stat.issubset(set(process["stat"]))) != reverse,
            processes_list))


def parse_process_list_into_dictionaries(processes_list, headers):
    if not processes_list:
        return json.dumps([])

    json_processes_list = []

    for process in processes_list:
        columns = process.strip().split()
        if not columns:
            continue
        headers_index = 0
        json_obj = dict([])
        for headers_index in range(len(headers) - 1):
            json_obj[headers[headers_index]] = columns[headers_index].strip()
            headers_index += 1

        json_obj[headers[headers_index]] = " ".join(columns[headers_index:])
        json_processes_list.append(json_obj)

    return json_processes_list


def run_shell_cmd(cmd):
    p = Popen([cmd], stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True)
    output, err = p.communicate()
    re_code = p.returncode

    # work around for newer python versions which returns bytes sequences
    # instead of a string
    if isinstance(output, bytes):
        output = output.decode("utf-8")
    if isinstance(err, bytes):
        err = err.decode("utf-8")

    return output.strip(), err.strip(), re_code


def validate_common_passed_fields_values(params):
    validators = [
        validate_id_field_pattern(params, "pid"),
    ]
    result = {'msg': '', 'rc': 0, 'stderr': ''}

    for validator_result in validators:
        if validator_result['rc']:
            result = validator_result
            break
    return result


def validate_search_passed_fields_values(params):
    result = {'msg': '', 'rc': 0, 'stderr': ''}

    validators = [
        validate_choice_field(params, ACTIONS, "action"),
        validate_id_field_pattern(params, "pgid"),
        validate_id_field_pattern(params, "ppid"),
        validate_stat_field(params),
        validate_number_range(params, "rss", INTEGER_RANGE_PATTERN,
                              INTEGER_RANGE_FORMAT),
        validate_number_range(params, "vsz", INTEGER_RANGE_PATTERN,
                              INTEGER_RANGE_FORMAT),
        validate_number_range(params, "cpu_utilization", DOUBLE_RANGE_PATTERN,
                              DOUBLE_RANGE_FORMAT),
        validate_number_range(params, "memory_usage", DOUBLE_RANGE_PATTERN,
                              DOUBLE_RANGE_FORMAT),
        validate_time_range(params, "cpu_time", VALIDATE_CPU_TIME_PATTERN,
                            CPU_TIME_RANGE_FORMAT),
        validate_time_range(params, "elapsed_time",
                            VALIDATE_ELAPSED_TIME_PATTERN,
                            ELAPSED_TIME_RANGE_FORMAT),
        validate_command_regex(params),
        validate_children_parameters(params)
    ]

    for validator_result in validators:
        if validator_result['rc']:
            result = validator_result
            break

    return result


def validate_command_regex(params):
    pattern = params["command"]
    result = {'msg': '', 'rc': 0, 'stderr': ''}

    try:
        has_regex_match(pattern, "")

    except re.error:
        result['msg'] = "command field regex value"
        result['stderr'] = "passed regex is not valid"
        result['rc'] = 1

    finally:
        return result


def validate_children_parameters(params):
    result = {'msg': '', 'rc': 0, 'stderr': ''}

    if not params["get_children"] and params["has_children"] != "":
        result[
            'msg'] = "to use has_children, get_children must be set to " \
                     "True first"
        result[
            'stderr'] = "has_children must be used with get_children set" \
                        " to True"
        result['rc'] = 1
    elif params["get_children"] and params["has_children"] != "":
        result = validate_choice_field(params, ["yes", "no"], "has_children")

    return result


def validate_time_range(params, key, range_pattern, range_format):
    result = {'msg': '', 'rc': 0, 'stderr': ''}
    value = params[key]

    if value:
        if has_regex_match(range_pattern, value):
            lower, upper = [side for side in value.split("-")]
            lower_hours = list(reversed(lower.split(":")))
            upper_hours = list(reversed(upper.split(":")))
            if len(lower_hours) > 2 and int(lower_hours[2]) > 23 or \
                    len(upper_hours) > 2 and int(upper_hours[2]) > 23:
                result['msg'] = "error in {} field value".format(key)
                result[
                    'stderr'] = "'{}' is not a valid range. hours must be" \
                                " within range [0-23]".format(
                    value, key)
                result['rc'] = 1
                return result

            if convert_time_to_seconds(lower) > convert_time_to_seconds(upper):
                result['msg'] = "error in {} field value".format(key)
                result[
                    'stderr'] = "'{}' is not a valid range. lower boundary" \
                                " can't be greater than upper " \
                                "boundary".format(value)
                result['rc'] = 1
        else:
            result['msg'] = "error in {} field value".format(key)
            result[
                'stderr'] = "'{}' is not a valid range. Range must be in" \
                            " the form {}".format(
                value, range_format)
            result['rc'] = 1

    return result


def validate_number_range(params, key, range_pattern, range_format):
    result = {'msg': '', 'rc': 0, 'stderr': ''}
    value = params[key]

    if value:
        if has_regex_match(range_pattern, value):
            lower, upper = [float(number) for number in value.split("-")]
            if lower > upper:
                result['msg'] = "error in {} field value".format(key)
                result[
                    'stderr'] = "{} is not allowed because {} > {}, the" \
                                " lower boundary value must be smaller or " \
                                "equal to the upper boundary".format(value,
                                                                     lower,
                                                                     upper)
                result['rc'] = 1
        else:
            result['msg'] = "error in {} field value".format(key)
            result[
                'stderr'] = "'{}' is not a valid range . Range must be" \
                            " in the form {} where both numbers have " \
                            "positive values".format(value, range_format)
            result['rc'] = 1

    return result


def validate_choice_field(params, choices, key):
    result = {'msg': '', 'rc': 0, 'stderr': ''}

    if params[key]:
        if not (params[key] in choices):
            result[
                'msg'] = "{} value can be only one of the following" \
                         " options:{}".format(
                key, choices)
            result['stderr'] = "wrong " + key + " value"
            result['rc'] = 1

    return result


def validate_id_field_pattern(params, field):
    id_pattern = r'^[0-9*]{1,7}$'
    result = {'msg': '', 'rc': 0, 'stderr': ''}
    value = params[field]

    if value:
        if not has_regex_match(id_pattern, value):
            result['msg'] = "{field} field value is not valid".format(
                field=field)
            result[
                'stderr'] = "{field} value can consist of numbers or * " \
                            "and up to 7 digits".format(
                field=field)
            result['rc'] = 1
        if not value.lstrip("0"):
            result['msg'] = "{field} is not allowed to equal 0".format(
                field=field)
            result['stderr'] = "wrong parameter format"
            result['rc'] = 1

    return result


def validate_stat_field(params):
    stat = params["stat"]
    result = {'msg': '', 'rc': 0, 'stderr': ''}

    for letter in stat:
        if not (letter in ['D', 'R', 'S', 'T', 'W', 'X', 'Z', '<', 'N', 'L',
                           's', 'I', ' +', '*']):
            result['msg'] = "stat field value is not valid"
            result[
                'stderr'] = "'{}' is not permitted. stat can have any" \
                            " combination of the following values: " \
                            "['D', 'R', 'S', 'T', 'W', 'X', 'Z', '<'," \
                            " 'N', 'L', 's', 'I', ' +', '*']".format(
                letter)
            result['rc'] = 1
            break
        if stat.count(letter) != 1:
            result['msg'] = "stat field value is not valid"
            result[
                'stderr'] = "'{}' occurred more than once, it is not" \
                            " allowed to repeat the same stat value " \
                            "more than once".format(letter)
            result['rc'] = 1
            break

    return result


def has_regex_match(pattern, value):
    regexp = re.compile(pattern)
    if regexp.search(value):
        return True
    return False


def convert_time_to_seconds(standard_format):
    standard_format_list = list((reversed(standard_format.split(":"))))
    multiplier = [1, 60, 3600, 86400]
    return sum(
        [int(x) * int(y) for x, y in zip(standard_format_list, multiplier)])


def did_the_task_fail(module, result):
    if result['rc']:
        module.fail_json(**result)


if __name__ == '__main__':
    module = AnsibleModule(argument_spec=FIELDS,
                           supports_check_mode=True)
    main(module)
