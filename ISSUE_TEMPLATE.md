##### Issue Type:

"Group managment bug in FreeBSD"

##### Ansible Version:

ansible 1.7.2
Python 2.7.8

##### Environment:

--server
FreeBSD  9.3-RELEASE FreeBSD 9.3-RELEASE #0 r268512: Thu Jul 10 23:44:39 UTC 2014     root@snap.freebsd.org:/usr/obj/usr/src/sys/GENERIC  amd64

--target_client 
FreeBSD  10.0-RELEASE FreeBSD 10.0-RELEASE #0 r260789: Thu Jan 16 22:34:59 UTC 2014     root@snap.freebsd.org:/usr/obj/usr/src/sys/GENERIC  amd64



##### Summary:

I try to change groups for user "test1" in FreeBSD host.
If I am adding a new groups to user (using module "user")- all is working fine , but when I try to "delete" some group for user "test1", I see status " : ok=2    changed=1 ", but realy nothing happens. And every time I see such status.
In Linux host all i working fine.
Please fix it.


--- First time (all is fine) ---
<code>

- hosts: my_servers
  remote_user: root
  tasks:
     - name: Create FreeBSD users
       user: name={{ item.name  }}
             password={{ item.password }}
             groups={{ item.groups }}
             comment={{ item.comment }}
             append=no
       with_items:
             -  { name: 'test1' , groups: 'mysql\,cyrus', password: '11111', comment: 'Vasja' }
             -  { name: 'test2' , groups: 'mysql', password: '22222', comment: 'Kolja' }
       when: ansible_os_family == "FreeBSD"
<code>


--- Second time (bug) ----
<code>

- hosts: my_servers
  remote_user: root
  tasks:
     - name: Create FreeBSD users
       user: name={{ item.name  }}
             password={{ item.password }}
             groups={{ item.groups }}
             comment={{ item.comment }}
             append=no
       with_items:
             -  { name: 'test1' , groups: 'mysql', password: '11111', comment: 'Vasja' }
             -  { name: 'test2' , groups: 'mysql', password: '22222', comment: 'Kolja' }
       when: ansible_os_family == "FreeBSD"


<code>




<output>

root@kris:/home/serg/ansible # ansible-playbook -vvvv run.yml

PLAY [my_servers] ************************************************************* 

GATHERING FACTS *************************************************************** 
<172.29.251.106> ESTABLISH CONNECTION FOR USER: root
<172.29.251.106> REMOTE_MODULE setup
<172.29.251.106> EXEC ['ssh', '-C', '-tt', '-vvv', '-o', 'ControlMaster=auto', '-o', 'ControlPersist=60s', '-o', 'ControlPath=/root/.ansible/cp/ansible-ssh-%h-%p-%r', '-o', 'KbdInteractiveAuthentication=no', '-o', 'PreferredAuthentications=gssapi-with-mic,gssapi-keyex,hostbased,publickey', '-o', 'PasswordAuthentication=no', '-o', 'ConnectTimeout=10', '172.29.251.106', "/bin/sh -c 'mkdir -p $HOME/.ansible/tmp/ansible-tmp-1415297453.89-59397932578099 && echo $HOME/.ansible/tmp/ansible-tmp-1415297453.89-59397932578099'"]
<172.29.251.106> PUT /tmp/tmpyPFA5r TO /root/.ansible/tmp/ansible-tmp-1415297453.89-59397932578099/setup
<172.29.251.106> EXEC ['ssh', '-C', '-tt', '-vvv', '-o', 'ControlMaster=auto', '-o', 'ControlPersist=60s', '-o', 'ControlPath=/root/.ansible/cp/ansible-ssh-%h-%p-%r', '-o', 'KbdInteractiveAuthentication=no', '-o', 'PreferredAuthentications=gssapi-with-mic,gssapi-keyex,hostbased,publickey', '-o', 'PasswordAuthentication=no', '-o', 'ConnectTimeout=10', '172.29.251.106', u"/bin/sh -c 'LANG=en_US.UTF-8 LC_CTYPE=en_US.UTF-8 /usr/local/bin/python /root/.ansible/tmp/ansible-tmp-1415297453.89-59397932578099/setup; rm -rf /root/.ansible/tmp/ansible-tmp-1415297453.89-59397932578099/ >/dev/null 2>&1'"]
ok: [freebsd]

TASK: [Create FreeBSD users] ************************************************** 
<172.29.251.106> ESTABLISH CONNECTION FOR USER: root
<172.29.251.106> REMOTE_MODULE user name=test1 password=VALUE_HIDDEN groups=mysql comment=Vasja append=no
<172.29.251.106> EXEC ['ssh', '-C', '-tt', '-vvv', '-o', 'ControlMaster=auto', '-o', 'ControlPersist=60s', '-o', 'ControlPath=/root/.ansible/cp/ansible-ssh-%h-%p-%r', '-o', 'KbdInteractiveAuthentication=no', '-o', 'PreferredAuthentications=gssapi-with-mic,gssapi-keyex,hostbased,publickey', '-o', 'PasswordAuthentication=no', '-o', 'ConnectTimeout=10', '172.29.251.106', "/bin/sh -c 'mkdir -p $HOME/.ansible/tmp/ansible-tmp-1415297454.25-201202690342400 && echo $HOME/.ansible/tmp/ansible-tmp-1415297454.25-201202690342400'"]
<172.29.251.106> PUT /tmp/tmpDSK0ET TO /root/.ansible/tmp/ansible-tmp-1415297454.25-201202690342400/user
<172.29.251.106> EXEC ['ssh', '-C', '-tt', '-vvv', '-o', 'ControlMaster=auto', '-o', 'ControlPersist=60s', '-o', 'ControlPath=/root/.ansible/cp/ansible-ssh-%h-%p-%r', '-o', 'KbdInteractiveAuthentication=no', '-o', 'PreferredAuthentications=gssapi-with-mic,gssapi-keyex,hostbased,publickey', '-o', 'PasswordAuthentication=no', '-o', 'ConnectTimeout=10', '172.29.251.106', u"/bin/sh -c 'LANG=en_US.UTF-8 LC_CTYPE=en_US.UTF-8 /usr/local/bin/python /root/.ansible/tmp/ansible-tmp-1415297454.25-201202690342400/user; rm -rf /root/.ansible/tmp/ansible-tmp-1415297454.25-201202690342400/ >/dev/null 2>&1'"]
changed: [freebsd] => (item={'comment': 'Vasja', 'password': '11111', 'name': 'test1', 'groups': 'mysql'}) => {"append": false, "changed": true, "comment": "Vasja", "group": 1002, "groups": "mysql", "home": "/home/test1", "item": {"comment": "Vasja", "groups": "mysql", "name": "test1", "password": "11111"}, "move_home": false, "name": "test1", "password": "NOT_LOGGING_PASSWORD", "shell": "/bin/sh", "state": "present", "uid": 1002}
<172.29.251.106> ESTABLISH CONNECTION FOR USER: root
<172.29.251.106> REMOTE_MODULE user name=test2 password=VALUE_HIDDEN groups=mysql comment=Kolja append=no
<172.29.251.106> EXEC ['ssh', '-C', '-tt', '-vvv', '-o', 'ControlMaster=auto', '-o', 'ControlPersist=60s', '-o', 'ControlPath=/root/.ansible/cp/ansible-ssh-%h-%p-%r', '-o', 'KbdInteractiveAuthentication=no', '-o', 'PreferredAuthentications=gssapi-with-mic,gssapi-keyex,hostbased,publickey', '-o', 'PasswordAuthentication=no', '-o', 'ConnectTimeout=10', '172.29.251.106', "/bin/sh -c 'mkdir -p $HOME/.ansible/tmp/ansible-tmp-1415297454.45-101295486595285 && echo $HOME/.ansible/tmp/ansible-tmp-1415297454.45-101295486595285'"]
<172.29.251.106> PUT /tmp/tmpSb6Sfc TO /root/.ansible/tmp/ansible-tmp-1415297454.45-101295486595285/user
<172.29.251.106> EXEC ['ssh', '-C', '-tt', '-vvv', '-o', 'ControlMaster=auto', '-o', 'ControlPersist=60s', '-o', 'ControlPath=/root/.ansible/cp/ansible-ssh-%h-%p-%r', '-o', 'KbdInteractiveAuthentication=no', '-o', 'PreferredAuthentications=gssapi-with-mic,gssapi-keyex,hostbased,publickey', '-o', 'PasswordAuthentication=no', '-o', 'ConnectTimeout=10', '172.29.251.106', u"/bin/sh -c 'LANG=en_US.UTF-8 LC_CTYPE=en_US.UTF-8 /usr/local/bin/python /root/.ansible/tmp/ansible-tmp-1415297454.45-101295486595285/user; rm -rf /root/.ansible/tmp/ansible-tmp-1415297454.45-101295486595285/ >/dev/null 2>&1'"]
ok: [freebsd] => (item={'comment': 'Kolja', 'password': '22222', 'name': 'test2', 'groups': 'mysql'}) => {"append": false, "changed": false, "comment": "Kolja", "group": 1003, "groups": "mysql", "home": "/home/test2", "item": {"comment": "Kolja", "groups": "mysql", "name": "test2", "password": "22222"}, "move_home": false, "name": "test2", "password": "NOT_LOGGING_PASSWORD", "shell": "/bin/sh", "state": "present", "uid": 1003}

PLAY RECAP ******************************************************************** 
freebsd                    : ok=2    changed=1    unreachable=0    failed=0   


<output>



##### Steps To Reproduce:

 Just run my playbook
# ansible-playbook run.yml

##### Expected Results:

Change user group for user "test1" from groups=1002(test1),88(mysql),60(cyrus) to  groups=1002(test1),88(mysql)

##### Actual Results:

Still all old groups for user "test1"  
uid=1002(test1) gid=1002(test1) groups=1002(test1),88(mysql),60(cyrus)


