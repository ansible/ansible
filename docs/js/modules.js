function AnsibleModules($scope) {
  $scope.modules = [
  {
    "now_date": "2012-10-09", 
    "description": [
      "Manages apt-packages (such as for Debian/Ubuntu)."
    ], 
    "author": "Matthew Williams", 
    "notes": [], 
    "module": "apt", 
    "filename": "library/apt", 
    "examples": [
      {
        "code": "apt pkg=foo update-cache=yes", 
        "description": "Update repositories cache and install C(foo) package"
      }, 
      {
        "code": "apt pkg=foo state=removed", 
        "description": "Remove C(foo) package"
      }, 
      {
        "code": "apt pkg=foo state=installed", 
        "description": "Install the the package C(foo)"
      }, 
      {
        "code": "apt pkg=foo=1.00 state=installed", 
        "description": "Install the version '1.00' of package C(foo)"
      }, 
      {
        "code": "apt pkg=nginx state=latest default-release=squeeze-backports update-cache=yes", 
        "description": "Update the repository cache and update package C(ngnix) to latest version using default release C(squeeze-backport)"
      }, 
      {
        "code": "apt pkg=openjdk-6-jdk state=latest install-recommends=no", 
        "description": "Install latest version of C(openjdk-6-jdk) ignoring C(install-recomands)"
      }
    ], 
    "docuri": "apt", 
    "short_description": "Manages apt-packages", 
    "version_added": "0.0.2", 
    "options": {
      "force": {
        "default": "no", 
        "required": false, 
        "description": [
          "If C(yes), force installs/removes."
        ], 
        "choices": [
          "yes", 
          "no"
        ]
      }, 
      "purge": {
        "default": "no", 
        "required": false, 
        "description": [
          "Will force purging of configuration files if the module state is set to C(absent)."
        ], 
        "choices": [
          "yes", 
          "no"
        ]
      }, 
      "state": {
        "default": "present", 
        "required": false, 
        "description": [
          "Indicates the desired package state"
        ], 
        "choices": [
          "installed", 
          "latest", 
          "remove", 
          "absent", 
          "present"
        ]
      }, 
      "update_cache": {
        "default": "no", 
        "required": false, 
        "description": [
          "Run the equivalent of C(apt-get update) before the operation. Can be run as part of the package installation or as a seperate step"
        ], 
        "choices": [
          "yes", 
          "no"
        ]
      }, 
      "pkg": {
        "default": null, 
        "required": true, 
        "description": [
          "A package name or package specifier with version, like C(foo) or C(foo=1.0)"
        ]
      }, 
      "default_release": {
        "default": null, 
        "required": false, 
        "description": [
          "Corresponds to the C(-t) option for I(apt) and sets pin priorities"
        ]
      }, 
      "install_recommends": {
        "default": "no", 
        "required": false, 
        "description": [
          "Corresponds to the C(--no-install-recommends) option for I(apt), default behavior works as apt's default behavior, C(no) does not install recommended packages. Suggested packages are never installed."
        ], 
        "choices": [
          "yes", 
          "no"
        ]
      }
    }, 
    "ansible_version": "0.8"
  }, 
  {
    "now_date": "2012-10-09", 
    "description": [
      "Manages apt repositores (such as for Debian/Ubuntu)."
    ], 
    "author": "Matt Wright", 
    "notes": [
      "This module works on Debian and Ubuntu only and requires C(apt-add-repository) be available on destination server. To ensure this package is available use the C(apt) module and install the C(python-software-properties) package before using this module.", 
      "A bug in C(apt-add-repository) always adds C(deb) and C(deb-src) types for repositories (see the issue on Launchpad U(https://bugs.launchpad.net/ubuntu/+source/software-properties/+bug/987264)), if a repo doesn't have source information (eg MongoDB repo from 10gen) the system will fail while updating repositories."
    ], 
    "module": "apt_repository", 
    "filename": "library/apt_repository", 
    "examples": [
      {
        "code": "apt_repository repo=ppa://nginx/stable", 
        "description": "Add nginx stable repository from PPA"
      }, 
      {
        "code": "apt_repository repo='deb http://archive.canonical.com/ubuntu hardy partner'", 
        "description": "Add specified repository into sources."
      }
    ], 
    "docuri": "apt-repository", 
    "short_description": "Manages apt repositores", 
    "version_added": "0.7", 
    "options": {
      "repo": {
        "default": null, 
        "required": true, 
        "description": [
          "The repository name/value"
        ]
      }, 
      "state": {
        "default": "present", 
        "required": false, 
        "description": [
          "The repository state"
        ], 
        "choices": [
          "present", 
          "absent"
        ]
      }
    }, 
    "ansible_version": "0.8"
  }, 
  {
    "now_date": "2012-10-09", 
    "description": [
      "Assembles a configuration file from fragments. Often a particular program will take a single configuration file and does not support a C(conf.d) style structure where it is easy to build up the configuration from multiple sources. Assemble will take a directory of files that have already been transferred to the system, and concatenate them together to produce a destination file. Files are assembled in string sorting order. Puppet calls this idea I(fragments)."
    ], 
    "author": "Stephen Fromm", 
    "module": "assemble", 
    "filename": "library/assemble", 
    "examples": [
      {
        "code": "assemble src=/etc/someapp/fragments dest=/etc/someapp/someapp.conf", 
        "description": "Example from Ansible Playbooks"
      }
    ], 
    "docuri": "assemble", 
    "short_description": "Assembles a configuration file from fragments", 
    "version_added": "0.5", 
    "options": {
      "dest": {
        "default": null, 
        "required": true, 
        "description": [
          "A file to create using the concatenation of all of the source files."
        ]
      }, 
      "src": {
        "default": null, 
        "required": true, 
        "description": [
          "An already existing directory full of source files."
        ], 
        "aliases": []
      }, 
      "backup": {
        "default": "no", 
        "required": false, 
        "description": [
          "Create a backup file (if C(yes)), including the timestamp information so you can get the original file back if you somehow clobbered it incorrectly."
        ], 
        "choices": [
          "yes", 
          "no"
        ]
      }, 
      "others": {
        "required": false, 
        "description": [
          "all arguments accepted by the M(file) module also work here"
        ]
      }
    }, 
    "ansible_version": "0.8"
  }, 
  {
    "now_date": "2012-10-09", 
    "requirements": [], 
    "description": [
      "This module gets the status of an asynchronous task. See: U(http://ansible.cc/docs/playbooks2.html#asynchronous-actions-and-polling)"
    ], 
    "author": "Michael DeHaan", 
    "notes": [
      "See U(http://ansible.cc/docs/playbooks2.html#asynchronous-actions-and-polling)"
    ], 
    "module": "async_status", 
    "filename": "library/async_status", 
    "docuri": "async-status", 
    "short_description": "Obtain status of asynchronous task", 
    "version_added": "0.5", 
    "options": {
      "jid": {
        "default": null, 
        "required": true, 
        "description": [
          "Job or task identifier"
        ], 
        "aliases": []
      }, 
      "mode": {
        "default": "status", 
        "required": false, 
        "description": [
          "if C(status), obtain the status; if C(cleanup), clean up the async job cache located in C(~/.ansible_async/) for the specified job I(jid)."
        ], 
        "choices": [
          "status", 
          "cleanup"
        ]
      }
    }, 
    "ansible_version": "0.8"
  }, 
  {
    "now_date": "2012-10-09", 
    "description": [
      "Adds or removes an SSH authorized key for a user from a remote host."
    ], 
    "author": "Brad Olson", 
    "module": "authorized_key", 
    "filename": "library/authorized_key", 
    "examples": [
      {
        "code": "authorized_key user=charlie key=\"ssh-dss ASDF1234L+8BTwaRYr/rycsBF1D8e5pTxEsXHQs4iq+mZdyWqlW++L6pMiam1A8yweP+rKtgjK2httVS6GigVsuWWfOd7/sdWippefq74nppVUELHPKkaIOjJNN1zUHFoL/YMwAAAEBALnAsQN10TNGsRDe5arBsW8cTOjqLyYBcIqgPYTZW8zENErFxt7ij3fW3Jh/sCpnmy8rkS7FyK8ULX0PEy/2yDx8/5rXgMIICbRH/XaBy9Ud5bRBFVkEDu/r+rXP33wFPHjWjwvHAtfci1NRBAudQI/98DbcGQw5HmE89CjgZRo5ktkC5yu/8agEPocVjdHyZr7PaHfxZGUDGKtGRL2QzRYukCmWo1cZbMBHcI5FzImvTHS9/8B3SATjXMPgbfBuEeBwuBK5EjL+CtHY5bWs9kmYjmeo0KfUMH8hY4MAXDoKhQ7DhBPIrcjS5jPtoGxIREZjba67r6/P2XKXaCZH6Fc= charlie@example.org 2011-01-17\"", 
        "description": "Example from Ansible Playbooks"
      }, 
      {
        "code": "authorized_key user=charlie key=$FILE(/home/charlie/.ssh/id_rsa.pub)", 
        "description": "Shorthand available in Ansible 0.8 and later"
      }
    ], 
    "docuri": "authorized-key", 
    "short_description": "Adds or removes an SSH authorized key", 
    "version_added": "0.5", 
    "options": {
      "state": {
        "default": "present", 
        "required": false, 
        "description": [
          "whether the given key should or should not be in the file"
        ], 
        "choices": [
          "present", 
          "absent"
        ]
      }, 
      "user": {
        "default": null, 
        "required": true, 
        "description": [
          "Name of the user who should have access to the remote host"
        ], 
        "aliases": []
      }, 
      "key": {
        "default": null, 
        "required": true, 
        "description": [
          "the SSH public key, as a string"
        ]
      }
    }, 
    "ansible_version": "0.8"
  }, 
  {
    "description": [
      "The command module takes the command name followed by a list of space-delimited arguments.", 
      "The given command will be executed on all selected nodes. It will not be processed through the shell, so variables like C($HOME) and operations like C(\"<\"), C(\">\"), C(\"|\"), and C(\"&\") will not work. As such, all paths to commands must be fully qualified"
    ], 
    "author": "Michael DeHaan", 
    "notes": [
      "If you want to run a command through the shell (say you are using C(<), C(>), C(|), etc), you actually want the M(shell) module instead. The M(command) module is much more secure as it's not affected by the user's environment."
    ], 
    "module": "command", 
    "filename": "library/command", 
    "examples": [
      {
        "code": "command /sbin/shutdown -t now", 
        "description": "Example from Ansible Playbooks"
      }, 
      {
        "code": "command /usr/bin/make_database.sh arg1 arg2 creates=/path/to/database", 
        "description": "I(creates), I(removes), and I(chdir) can be specified after the command. For instance, if you only want to run a command if a certain file does not exist, use this."
      }
    ], 
    "docuri": "command", 
    "short_description": "Executes a command on a remote node", 
    "now_date": "2012-10-09", 
    "options": {
      "creates": {
        "default": null, 
        "required": false, 
        "description": [
          "a filename, when it already exists, this step will B(not) be run."
        ]
      }, 
      "free_form": {
        "default": null, 
        "required": true, 
        "description": [
          "the command module takes a free form command to run"
        ], 
        "aliases": []
      }, 
      "chdir": {
        "default": null, 
        "required": false, 
        "description": [
          "cd into this directory before running the command"
        ], 
        "version_added": "0.6"
      }, 
      "removes": {
        "default": null, 
        "required": false, 
        "description": [
          "a filename, when it does not exist, this step will B(not) be run."
        ], 
        "version_added": "0.8"
      }
    }, 
    "ansible_version": "0.8"
  }, 
  {
    "description": [
      "The M(copy) module copies a file on the local box to remote locations."
    ], 
    "author": "Michael DeHaan", 
    "module": "copy", 
    "filename": "library/copy", 
    "examples": [
      {
        "code": "copy src=/srv/myfiles/foo.conf dest=/etc/foo.conf owner=foo group=foo mode=0644", 
        "description": "Example from Ansible Playbooks"
      }, 
      {
        "code": "copy src=/mine/ntp.conf dest=/etc/ntp.conf owner=root group=root mode=644 backup=yes", 
        "description": "Copy a new C(ntp.conf) file into place, backing up the original if it differs from the copied version"
      }
    ], 
    "docuri": "copy", 
    "short_description": "Copies files to remote locations.", 
    "now_date": "2012-10-09", 
    "options": {
      "dest": {
        "default": null, 
        "required": true, 
        "description": [
          "Remote absolute path where the file should be copied to."
        ]
      }, 
      "src": {
        "default": null, 
        "required": true, 
        "description": [
          "Local path to a file to copy to the remote server; can be absolute or relative."
        ], 
        "aliases": []
      }, 
      "backup": {
        "default": "no", 
        "required": false, 
        "description": [
          "Create a backup file including the timestamp information so you can get the original file back if you somehow clobbered it incorrectly."
        ], 
        "version_added": "0.7", 
        "choices": [
          "yes", 
          "no"
        ]
      }, 
      "others": {
        "required": false, 
        "description": [
          "all arguments accepted by the M(file) module also work here"
        ]
      }
    }, 
    "ansible_version": "0.8"
  }, 
  {
    "now_date": "2012-10-09", 
    "requirements": "cron", 
    "description": [
      "Use this module to manage crontab entries. This module allows you to create named crontab entries, update, or delete them.", 
      "The module include one line with the description of the crontab entry \"#Ansible: <name>\" corresponding to the \"name\" passed to the module, which is used by future ansible/module calls to find/check the state."
    ], 
    "author": "Dane Summers", 
    "module": "cron", 
    "filename": "library/cron", 
    "examples": [
      {
        "code": "cron name=\"check dirs\" hour=\"5,2\" job=\"ls -alh > /dev/null\"", 
        "description": "Ensure a job that runs at 2 and 5 exists. Creates an entry like \"* 5,2 * * ls -alh > /dev/null\""
      }, 
      {
        "code": "name=\"an old job\" cron job=\"/some/dir/job.sh\" state=absent", 
        "description": "Ensure an old job is no longer present. Removes any job that is preceded by \"#Ansible: an old job\" in the crontab"
      }
    ], 
    "docuri": "cron", 
    "short_description": "Manage crontab entries.", 
    "version_added": "0.9", 
    "options": {
      "name": {
        "default": null, 
        "required": true, 
        "description": [
          "Description of a crontab entry."
        ], 
        "aliases": []
      }, 
      "hour": {
        "default": "*", 
        "required": false, 
        "description": [
          "Hour when the job should run ( 0-23, *, */2, etc )"
        ], 
        "aliases": []
      }, 
      "state": {
        "default": "present", 
        "required": false, 
        "description": [
          "Whether to ensure the job is present or absent."
        ], 
        "aliases": []
      }, 
      "month": {
        "default": "*", 
        "required": false, 
        "description": [
          "Month of the year the job should run ( 1-12, *, */2, etc )"
        ], 
        "aliases": []
      }, 
      "job": {
        "default": null, 
        "required": false, 
        "description": [
          "The command to execute.", 
          "Required if state=present."
        ], 
        "aliases": []
      }, 
      "user": {
        "default": "root", 
        "required": false, 
        "description": [
          "The specific user who's crontab should be modified."
        ], 
        "aliases": []
      }, 
      "backup": {
        "default": false, 
        "required": false, 
        "description": [
          "If set, then create a backup of the crontab before it is modified.", 
          "The location of the backup is returned in the 'backup' variable by this module."
        ], 
        "aliases": []
      }, 
      "day": {
        "default": "*", 
        "required": false, 
        "description": [
          "Day of the month the job should run ( 1-31, *, */2, etc )"
        ], 
        "aliases": []
      }, 
      "minute": {
        "default": "*", 
        "required": false, 
        "description": [
          "Minute when the job should run ( 0-59, *, */2, etc )"
        ], 
        "aliases": []
      }, 
      "weekday": {
        "default": "*", 
        "required": false, 
        "description": [
          "Day of the week that the job should run ( 0-7 for Sunday - Saturday, or mon, tue, * etc )"
        ], 
        "aliases": []
      }
    }, 
    "ansible_version": "0.8"
  }, 
  {
    "now_date": "2012-10-09", 
    "description": [
      "This module prints statements during execution and can be useful for debugging variables or expressions without necessarily halting the playbook. Useful for debugging together with the only_if directive.\nIn order to see the debug message, you need to run ansible in verbose mode (using the -v option)."
    ], 
    "author": "Dag Wieers", 
    "module": "debug", 
    "filename": "library/debug", 
    "examples": [
      {
        "code": [
          {
            "local_action": "debug msg=\"System $inventory_hostname has uuid $ansible_product_uuid\""
          }, 
          {
            "only_if": "is_unset('${ansible_default_ipv4.gateway}')", 
            "local_action": "debug msg=\"System $inventory_hostname lacks a gateway\" fail=yes"
          }, 
          {
            "only_if": "is_set('${ansible_default_ipv4.gateway}')", 
            "local_action": "debug msg=\"System $inventory_hostname has gateway ${ansible_default_ipv4.gateway}\""
          }
        ], 
        "description": "Example that prints the loopback address and gateway for each host"
      }
    ], 
    "docuri": "debug", 
    "short_description": "Print statements during execution", 
    "version_added": "0.8", 
    "options": {
      "msg": {
        "default": "Hello world!", 
        "required": false, 
        "description": [
          "The customized message that is printed. If ommited, prints a generic message."
        ]
      }, 
      "fail": {
        "default": "no", 
        "required": false, 
        "description": [
          "A boolean that indicates whether the debug module should fail or not."
        ]
      }, 
      "rc": {
        "default": 0, 
        "required": false, 
        "description": [
          "The return code of the module. If fail=yes, this will default to 1."
        ]
      }
    }, 
    "ansible_version": "0.8"
  }, 
  {
    "now_date": "2012-10-09", 
    "requirements": [
      "virtualenv"
    ], 
    "description": [
      "Installs Python libraries, optionally in a I(virtualenv)"
    ], 
    "author": "Matt Wright", 
    "notes": [
      "Please note that the M(easy_install) module can only install Python libraries. Thus this module is not able to remove libraries. It is generally recommended to use the M(pip) module which you can first install using M(easy_install).", 
      "Also note that I(virtualenv) must be installed on the remote host if the C(virtualenv) parameter is specified."
    ], 
    "module": "easy_install", 
    "filename": "library/easy_install", 
    "examples": [
      {
        "code": "easy_install name=pip", 
        "description": "Examples from Ansible Playbooks"
      }, 
      {
        "code": "easy_install name=flask virtualenv=/webapps/myapp/venv", 
        "description": "Install I(Flask) (U(http://flask.pocoo.org/)) into the specified I(virtualenv)"
      }
    ], 
    "docuri": "easy-install", 
    "short_description": "Installs Python libraries", 
    "version_added": "0.7", 
    "options": {
      "virtualenv": {
        "default": null, 
        "required": false, 
        "description": [
          "an optional I(virtualenv) directory path to install into. If the I(virtualenv) does not exist, it is created automatically"
        ]
      }, 
      "name": {
        "default": null, 
        "required": true, 
        "description": [
          "A Python library name"
        ], 
        "aliases": []
      }
    }, 
    "ansible_version": "0.8"
  }, 
  {
    "now_date": "2012-10-09", 
    "requirements": [
      "facter", 
      "ruby-json"
    ], 
    "description": [
      "Runs the I(facter) discovery program (U(https://github.com/puppetlabs/facter)) on the remote system, returning JSON data that can be useful for inventory purposes."
    ], 
    "author": "Michael DeHaan", 
    "notes": [], 
    "module": "facter", 
    "filename": "library/facter", 
    "examples": [
      {
        "code": "ansible  www.example.net -m facter", 
        "description": "Example command-line invocation"
      }
    ], 
    "docuri": "facter", 
    "short_description": "Runs the discovery program I(facter) on the remote system", 
    "version_added": "0.2", 
    "options": [], 
    "ansible_version": "0.8"
  }, 
  {
    "now_date": "2012-10-09", 
    "description": [
      "This module fails the progress with a custom message. It can be useful for bailing out when a certain condition is met using only_if."
    ], 
    "author": "Dag Wieers", 
    "module": "fail", 
    "filename": "library/fail", 
    "examples": [
      {
        "code": "action: fail msg=\"The system may not be provisioned according to the CMDB status.\" rc=100\nonly_if: \"'$cmdb_status' != 'to-be-staged'\"\n", 
        "description": "Example playbook using fail and only_if together"
      }
    ], 
    "docuri": "fail", 
    "short_description": "Fail with custom message", 
    "version_added": "0.8", 
    "options": {
      "msg": {
        "default": "'Failed because only_if condition is true'", 
        "required": false, 
        "description": [
          "The customized message used for failing execution. If ommited, fail will simple bail out with a generic message."
        ]
      }, 
      "rc": {
        "default": 1, 
        "required": false, 
        "description": [
          "The return code of the failure. This is currently not used by Ansible, but might be used in the future."
        ]
      }
    }, 
    "ansible_version": "0.8"
  }, 
  {
    "now_date": "2012-10-09", 
    "requirements": [], 
    "description": [
      "This module works like M(copy), but in reverse. It is used for fetching files from remote machines and storing them locally in a file tree, organized by hostname."
    ], 
    "author": "Michael DeHaan", 
    "module": "fetch", 
    "filename": "library/fetch", 
    "examples": [
      {
        "code": "fetch src=/var/log/messages dest=/home/logtree", 
        "description": "Example from Ansible Playbooks"
      }
    ], 
    "docuri": "fetch", 
    "short_description": "Fetches a file from remote nodes", 
    "version_added": "0.2", 
    "options": {
      "dest": {
        "default": null, 
        "required": true, 
        "description": [
          "A directory to save the file into. For example, if the I(dest) directory is C(/backup) a src file named C(/etc/profile) on host C(host.example.com), would be saved into C(/backup/host.example.com/etc/profile)"
        ]
      }, 
      "src": {
        "default": null, 
        "required": true, 
        "description": [
          "The file on the remote system to fetch. This must be a file, not a directory. Recursive fetching may be supported in a later release."
        ], 
        "aliases": []
      }
    }, 
    "ansible_version": "0.8"
  }, 
  {
    "requirements": [], 
    "description": [
      "Sets attributes of files, symlinks, and directories, or removes files/symlinks/directories. Many other modules support the same options as the file module - including M(copy), M(template), and M(assmeble)."
    ], 
    "author": "Michael DeHaan", 
    "notes": [
      "See also M(copy), M(template), M(assemble)"
    ], 
    "module": "file", 
    "filename": "library/file", 
    "examples": [
      {
        "code": "file path=/etc/foo.conf owner=foo group=foo mode=0644", 
        "description": "Example from Ansible Playbooks"
      }, 
      {
        "code": "file src=/file/to/link/to dest=/path/to/symlink owner=foo group=foo state=link"
      }
    ], 
    "docuri": "file", 
    "short_description": "Sets attributes of files", 
    "now_date": "2012-10-09", 
    "options": {
      "src": {
        "default": null, 
        "required": false, 
        "description": [
          "path of the file to link to (applies only to C(state=link))."
        ], 
        "choices": []
      }, 
      "group": {
        "default": null, 
        "required": false, 
        "description": [
          "name of the group that should own the file/directory, as would be fed to I(chown)"
        ], 
        "choices": []
      }, 
      "dest": {
        "default": [], 
        "required": true, 
        "description": [
          "defines the file being managed, unless when used with I(state=link), and then sets the destination to create a symbolic link to using I(src)"
        ], 
        "aliases": []
      }, 
      "selevel": {
        "default": "s0", 
        "required": false, 
        "description": [
          "level part of the SELinux file context. This is the MLS/MCS attribute, sometimes known as the C(range). C(_default) feature works as for I(seuser)."
        ], 
        "choices": []
      }, 
      "seuser": {
        "default": null, 
        "required": false, 
        "description": [
          "user part of SELinux file context. Will default to system policy, if applicable. If set to C(_default), it will use the C(user) portion of the the policy if available"
        ], 
        "choices": []
      }, 
      "serole": {
        "default": null, 
        "required": false, 
        "description": [
          "role part of SELinux file context, C(_default) feature works as for I(seuser)."
        ], 
        "choices": []
      }, 
      "state": {
        "default": "file", 
        "required": false, 
        "description": [
          "If C(directory), all immediate subdirectories will be created if they do not exist. If C(file), the file will NOT be created if it does not exist, see the M(copy) or M(template) module if you want that behavior. If C(link), the symbolic link will be created or changed. If C(absent), directories will be recursively deleted, and files or symlinks will be unlinked."
        ], 
        "choices": [
          "file", 
          "link", 
          "directory", 
          "absent"
        ]
      }, 
      "mode": {
        "default": null, 
        "required": false, 
        "description": [
          "mode the file or directory should be, such as 0644 as would be fed to"
        ], 
        "choices": []
      }, 
      "context": {
        "default": null, 
        "required": false, 
        "description": [
          "accepts only C(default) as value. This will restore a file's SELinux context in the policy. Does nothing if no default value is available."
        ], 
        "choices": [
          "default"
        ]
      }, 
      "owner": {
        "default": null, 
        "required": false, 
        "description": [
          "name of the user that should own the file/directory, as would be fed to I(chown)"
        ], 
        "choices": []
      }, 
      "force": {
        "default": null, 
        "required": false, 
        "description": [
          "force is required when changing an existing file to a directory, or a link to a directory, and so on.  Use this with caution."
        ], 
        "choices": []
      }, 
      "setype": {
        "default": null, 
        "required": false, 
        "description": [
          "type part of SELinux file context, C(_default) feature works as for I(seuser)."
        ], 
        "choices": []
      }
    }, 
    "ansible_version": "0.8"
  }, 
  {
    "now_date": "2012-10-09", 
    "requirements": [
      "zmq", 
      "keyczar"
    ], 
    "description": [
      "This modules launches an ephemeral I(fireball) ZeroMQ message bus daemon on the remote node which Ansible can to communicate with nodes at high speed.", 
      "The daemon listens on a configurable port for a configurable amount of time.", 
      "Starting a new fireball as a given user terminates any existing user fireballs.", 
      "Fireball mode is AES encrypted"
    ], 
    "author": "Michael DeHaan", 
    "notes": [
      "See the advanced playbooks chapter for more about using fireball mode."
    ], 
    "module": "fireball", 
    "filename": "library/fireball", 
    "examples": [
      {
        "code": "- hosts: devservers\n      gather_facts: false\n      connection: ssh\n      sudo: yes\n      tasks:\n          - action: fireball \n\n    - hosts: devservers\n      connection: fireball\n      tasks:\n          - action: command /usr/bin/anything\n", 
        "description": "This example playbook has two plays: the first launches I(fireball) mode on all hosts via SSH, and the second actually starts using I(fireball) node for subsequent management over the fireball interface"
      }
    ], 
    "docuri": "fireball", 
    "short_description": "Enable fireball mode on remote node", 
    "version_added": "0.9", 
    "options": {
      "minutes": {
        "default": 30, 
        "required": false, 
        "description": [
          "The I(fireball) listener daemon is started on nodes and will stay around for this number of minutes before turning itself off."
        ]
      }, 
      "port": {
        "default": 5099, 
        "required": false, 
        "description": [
          "TCP port for ZeroMQ"
        ], 
        "aliases": []
      }
    }, 
    "ansible_version": "0.8"
  }, 
  {
    "now_date": "2012-10-09", 
    "requirements": [
      "urllib2", 
      "urlparse"
    ], 
    "description": [
      "Downloads files from HTTP, HTTPS, or FTP to the remote server. The remote server must have direct access to the remote resource."
    ], 
    "author": "Jan-Piet Mens", 
    "notes": [
      "This module doesn't yet support configuration for proxies or passwords."
    ], 
    "module": "get_url", 
    "filename": "library/get_url", 
    "examples": [
      {
        "code": "get_url url=http://example.com/path/file.conf dest=/etc/foo.conf mode=0440", 
        "description": "Example from Ansible Playbooks"
      }
    ], 
    "docuri": "get-url", 
    "short_description": "Downloads files from HTTP, HTTPS, or FTP to node", 
    "version_added": "0.6", 
    "options": {
      "url": {
        "default": null, 
        "required": true, 
        "description": [
          "HTTP, HTTPS, or FTP URL"
        ], 
        "aliases": []
      }, 
      "dest": {
        "default": null, 
        "required": true, 
        "description": [
          "absolute path of where to download the file to.", 
          "If I(dest) is a directory, the basename of the file on the remote server will be used. If a directory, I(thirsty=yes) must also be set."
        ]
      }, 
      "thirsty": {
        "default": "no", 
        "required": false, 
        "description": [
          "if C(yes), will download the file every time and replace the file if the contents change. if C(no), the file will only be downloaded if the destination does not exist. Generally should be C(yes) only for small local files. prior to 0.6, acts if C(yes) by default."
        ], 
        "version_added": "0.7", 
        "choices": [
          "yes", 
          "no"
        ]
      }, 
      "others": {
        "required": false, 
        "description": [
          "all arguments accepted by the M(file) module also work here"
        ]
      }
    }, 
    "ansible_version": "0.8"
  }, 
  {
    "now_date": "2012-10-09", 
    "description": [
      "Manage git checkouts of repositories to deploy files or software."
    ], 
    "author": "Michael DeHaan", 
    "module": "git", 
    "filename": "library/git", 
    "examples": [
      {
        "code": "git repo=git://foosball.example.org/path/to/repo.git dest=/srv/checkout version=release-0.22", 
        "description": "Example git checkout from Ansible Playbooks"
      }
    ], 
    "docuri": "git", 
    "short_description": "Deploy software (or files) from git checkouts", 
    "version_added": "0.0.1", 
    "options": {
      "repo": {
        "required": true, 
        "description": [
          "git, ssh, or http protocol address of the git repository."
        ], 
        "aliases": [
          "name"
        ]
      }, 
      "dest": {
        "required": true, 
        "description": [
          "Absolute path of where the repository should be checked out to."
        ]
      }, 
      "version": {
        "default": "HEAD", 
        "required": false, 
        "description": [
          "What version of the repository to check out.  This can be the git I(SHA), the literal string I(HEAD), branch name, or a tag name."
        ]
      }, 
      "force": {
        "default": "yes", 
        "required": false, 
        "description": [
          "(New in 0.7)  If yes, any modified files in the working repository will be discarded.  Prior to 0.7, this was always 'yes' and could not be disabled."
        ], 
        "choices": [
          true, 
          false
        ]
      }, 
      "remote": {
        "default": "origin", 
        "required": false, 
        "description": [
          "Name of the remote branch."
        ]
      }
    }, 
    "ansible_version": "0.8"
  }, 
  {
    "now_date": "2012-10-09", 
    "requirements": [
      "groupadd", 
      "groupdel", 
      "groupmod"
    ], 
    "description": [
      "Manage presence of groups on a host."
    ], 
    "author": "Stephen Fromm", 
    "module": "group", 
    "filename": "library/group", 
    "examples": [
      {
        "code": "group name=somegroup state=present", 
        "description": "Example group command from Ansible Playbooks"
      }
    ], 
    "docuri": "group", 
    "short_description": "Add or remove groups", 
    "version_added": "0.0.2", 
    "options": {
      "state": {
        "default": "present", 
        "required": false, 
        "description": [
          "Whether the group should be present or not on the remote host."
        ], 
        "choices": [
          "present", 
          "absent"
        ]
      }, 
      "gid": {
        "required": false, 
        "description": [
          "Optional I(GID) to set for the group."
        ]
      }, 
      "name": {
        "required": true, 
        "description": [
          "Name of the group to manage."
        ]
      }, 
      "system": {
        "default": "no", 
        "required": false, 
        "description": [
          "If I(yes), indicates that the group created is a system group."
        ], 
        "choices": [
          true, 
          false
        ]
      }
    }, 
    "ansible_version": "0.8"
  }, 
  {
    "now_date": "2012-10-09", 
    "description": [
      "This module boots a system through its HP iLO interface. The boot media can be one of: cdrom, floppy, hdd, network or usb.", 
      "This module requires the hpilo python module."
    ], 
    "author": "Dag Wieers", 
    "notes": [
      "To use a USB key image you need to specify floppy as boot media.", 
      "This module ought to be run from a system that can access the HP iLO interface directly, either by using C(local_action) or C(using delegate)_to."
    ], 
    "module": "hpilo_boot", 
    "filename": "library/hpilo_boot", 
    "examples": [
      {
        "code": "local_action: hpilo_boot host=$ilo_address login=$ilo_login password=$ilo_password match=$inventory_hostname_short media=cdrom image=$iso_url\nonly_if: \"'$cmdb_hwmodel'.startswith('HP ')\n", 
        "description": "Task to boot a system using an ISO from an HP iLO interface only if the system is an HP server"
      }
    ], 
    "docuri": "hpilo-boot", 
    "short_description": "Boot system using specific media through HP iLO interface", 
    "version_added": "0.8", 
    "options": {
      "force": {
        "default": false, 
        "required": false, 
        "description": [
          "Whether to force a reboot (even when the system is already booted)"
        ], 
        "choices": [
          "yes", 
          "no"
        ]
      }, 
      "media": {
        "default": "network", 
        "required": false, 
        "description": [
          "The boot media to boot the system from"
        ], 
        "choices": [
          "cdrom", 
          "floppy", 
          "hdd", 
          "network", 
          "normal", 
          "usb"
        ]
      }, 
      "image": {
        "required": false, 
        "description": [
          "The URL of a cdrom, floppy or usb boot media image. C(protocol://username:password@hostname:port/filename)", 
          "protocol is either C(http) or C(https)", 
          "username:password is optional", 
          "port is optional"
        ]
      }, 
      "state": {
        "default": "boot_once", 
        "required": true, 
        "description": [
          "The state of the boot media.", 
          "no_boot: Do not boot from the device", 
          "boot_once: Boot from the device once and then notthereafter", 
          "boot_always: Boot from the device each time the serveris rebooted", 
          "connect: Connect the virtual media device and set to boot_always", 
          "disconnect: Disconnects the virtual media device and set to no_boot"
        ], 
        "choices": [
          "boot_always", 
          "boot_once", 
          "connect", 
          "disconnect", 
          "no_boot"
        ]
      }, 
      "host": {
        "required": true, 
        "description": [
          "The HP iLO hostname/address that is linked to the physical system."
        ]
      }, 
      "login": {
        "default": "Administrator", 
        "required": false, 
        "description": [
          "The login name to authenticate to the HP iLO interface."
        ]
      }, 
      "password": {
        "default": "admin", 
        "required": false, 
        "description": [
          "The password to authenticate to the HP iLO interface."
        ]
      }, 
      "match": {
        "required": false, 
        "description": [
          "An optional string to match against the iLO server name.", 
          "This is a safety measure to prevent accidentally using the wrong HP iLO interface with dire consequences."
        ]
      }
    }, 
    "ansible_version": "0.8"
  }, 
  {
    "now_date": "2012-10-09", 
    "description": [
      "This module gathers facts for a specific system using its HP iLO interface. These facts include hardware and network related information useful for provisioning (e.g. macaddress, uuid).", 
      "This module requires the hpilo python module."
    ], 
    "author": "Dag Wieers", 
    "notes": [
      "This module ought to be run from a system that can access the HP iLO interface directly, either by using C(local_action) or C(using delegate)_to."
    ], 
    "module": "hpilo_facts", 
    "filename": "library/hpilo_facts", 
    "examples": [
      {
        "code": "local_action: hpilo_facts host=$ilo_address login=$ilo_login password=$ilo_password match=$inventory_hostname_short\nonly_if: \"'$cmdb_hwmodel'.startswith('HP ')\n", 
        "description": "Task to gather facts from a HP iLO interface only if the system is an HP server"
      }, 
      {
        "code": "- hw_bios_date: \"05/05/2011\"\n  hw_bios_version: \"P68\"\n  hw_eth0:\n  - macaddress: \"00:11:22:33:44:55\"\n    macaddress_dash: \"00-11-22-33-44-55\"\n  hw_eth1:\n  - macaddress: \"00:11:22:33:44:57\"\n    macaddress_dash: \"00-11-22-33-44-57\"\n  hw_eth2:\n  - macaddress: \"00:11:22:33:44:5A\"\n    macaddress_dash: \"00-11-22-33-44-5A\"\n  hw_eth3:\n  - macaddress: \"00:11:22:33:44:5C\"\n    macaddress_dash: \"00-11-22-33-44-5C\"\n  hw_eth_ilo:\n  - macaddress: \"00:11:22:33:44:BA\"\n    macaddress_dash: \"00-11-22-33-44-BA\"\n  hw_product_name: \"ProLiant DL360 G7\"\n  hw_product_uuid: \"ef50bac8-2845-40ff-81d9-675315501dac\"\n  hw_system_serial: \"ABC12345D6\"\n  hw_uuid: \"123456ABC78901D2\"\n", 
        "description": "Typical output of HP iLO_facts for a physical system"
      }
    ], 
    "docuri": "hpilo-facts", 
    "short_description": "Gather facts through an HP iLO interface", 
    "version_added": "0.8", 
    "options": {
      "host": {
        "required": true, 
        "description": [
          "The HP iLO hostname/address that is linked to the physical system."
        ]
      }, 
      "password": {
        "default": "admin", 
        "required": false, 
        "description": [
          "The password to authenticate to the HP iLO interface."
        ]
      }, 
      "login": {
        "default": "Administrator", 
        "required": false, 
        "description": [
          "The login name to authenticate to the HP iLO interface."
        ]
      }, 
      "match": {
        "required": false, 
        "description": [
          "An optional string to match against the iLO server name.", 
          "This is a safety measure to prevent accidentally using the wrong HP iLO interface with dire consequences."
        ]
      }
    }, 
    "ansible_version": "0.8"
  }, 
  {
    "now_date": "2012-10-09", 
    "requirements": [
      "ConfigParser"
    ], 
    "description": [
      "Manage (add, remove, change) individual settings in an INI-style file without having to manage the file as a whole with, say, M(template) or M(assemble). Adds missing sections if they don't exist."
    ], 
    "author": "Jan-Piet Mens", 
    "notes": [
      "While it is possible to add an I(option) without specifying a I(value), this makes no sense."
    ], 
    "module": "ini_file", 
    "filename": "library/ini_file", 
    "examples": [
      {
        "code": "ini_file dest=/etc/conf section=drinks option=fav value=lemonade mode=0600 backup=true", 
        "description": "Ensure C(fav=lemonade) is in section C([drinks]) in said file"
      }, 
      {
        "code": "ini_file dest=/etc/anotherconf\n         section=drinks\n         option=temperature\n         value=cold\n         backup=true\n"
      }
    ], 
    "docuri": "ini-file", 
    "short_description": "Tweak settings in INI files", 
    "version_added": "0.9", 
    "options": {
      "option": {
        "default": null, 
        "required": false, 
        "description": [
          "if set (required for changing a I(value)), this is the name of the option.", 
          "May be omitted if adding/removing a whole I(section)."
        ]
      }, 
      "dest": {
        "default": null, 
        "required": true, 
        "description": [
          "Path to the INI-style file; this file is created if required"
        ]
      }, 
      "section": {
        "default": null, 
        "required": true, 
        "description": [
          "Section name in INI file. This is added if C(state=present) automatically when a single value is being set."
        ]
      }, 
      "value": {
        "default": null, 
        "required": false, 
        "description": [
          "the string value to be associated with an I(option). May be omitted when removing an I(option)."
        ]
      }, 
      "others": {
        "required": false, 
        "description": [
          "all arguments accepted by the M(file) module also work here"
        ]
      }, 
      "backup": {
        "default": false, 
        "required": false, 
        "description": [
          "Create a backup file including the timestamp information so you can get the original file back if you somehow clobbered it incorrectly."
        ], 
        "choices": [
          "yes", 
          "no"
        ]
      }
    }, 
    "ansible_version": "0.8"
  }, 
  {
    "now_date": "2012-10-09", 
    "description": [
      "This module will search a file for a line, and ensure that it is present or absent.", 
      "This is primarily useful when you want to change a single line in a file only. For other cases, see the M(copy) or M(template) modules."
    ], 
    "author": "Daniel Hokka Zakrisson", 
    "module": "lineinfile", 
    "filename": "library/lineinfile", 
    "examples": [
      {
        "code": "lineinfile dest=/etc/selinux/config regexp=^SELINUX= line=SELINUX=disabled"
      }, 
      {
        "code": "lineinfile dest=/etc/sudoers state=absent regexp=\"^%wheel\""
      }
    ], 
    "docuri": "lineinfile", 
    "short_description": "Ensure a particular line is in a file", 
    "version_added": "0.7", 
    "options": {
      "dest": {
        "required": true, 
        "description": [
          "The file to modify"
        ], 
        "aliases": [
          "name", 
          "destfile"
        ]
      }, 
      "state": {
        "default": "present", 
        "aliases": [], 
        "required": false, 
        "description": [
          "Whether the line should be there or not."
        ], 
        "choices": [
          "present", 
          "absent"
        ]
      }, 
      "insertafter": {
        "default": "EOF", 
        "required": false, 
        "description": [
          "Used with C(state=present). If specified, the line will be inserted after the specified regular expression. Two special values are available; C(BOF) for inserting the line at the beginning of the file, and C(EOF) for inserting the line at the end of the file."
        ], 
        "choices": [
          "BOF", 
          "EOF"
        ]
      }, 
      "regexp": {
        "required": true, 
        "description": [
          "The regular expression to look for in the file. For C(state=present), the pattern to replace. For C(state=absent), the pattern of the line to remove."
        ]
      }, 
      "line": {
        "required": false, 
        "description": [
          "Required for C(state=present). The line to insert/replace into the file. Must match the value given to C(regexp)."
        ]
      }, 
      "backup": {
        "default": false, 
        "required": false, 
        "description": [
          "Create a backup file including the timestamp information so you can get the original file back if you somehow clobbered it incorrectly."
        ]
      }
    }, 
    "ansible_version": "0.8"
  }, 
  {
    "now_date": "2012-10-09", 
    "requirements": [], 
    "description": [
      "This module controls active and configured mount points in C(/etc/fstab)."
    ], 
    "author": "Seth Vidal", 
    "notes": [], 
    "module": "mount", 
    "filename": "library/mount", 
    "examples": [
      {
        "code": "mount name=/mnt/dvd src=/dev/sr0 fstype=iso9660 opts=ro", 
        "description": "Mount DVD read-only"
      }
    ], 
    "docuri": "mount", 
    "short_description": "Control active and configured mount points", 
    "version_added": "0.6", 
    "options": {
      "src": {
        "default": null, 
        "required": true, 
        "description": [
          "device to be mounted on I(name)."
        ]
      }, 
      "name": {
        "default": null, 
        "required": true, 
        "description": [
          "path to the mount point, eg: C(/mnt/files)"
        ], 
        "aliases": []
      }, 
      "dump": {
        "default": null, 
        "required": false, 
        "description": [
          "dump (see fstab(8))"
        ]
      }, 
      "passno": {
        "default": null, 
        "required": false, 
        "description": [
          "passno (see fstab(8))"
        ]
      }, 
      "fstype": {
        "default": null, 
        "required": true, 
        "description": [
          "file-system type"
        ]
      }, 
      "state": {
        "default": null, 
        "required": true, 
        "description": [
          "If C(mounted) or C(unmounted), the device will be actively mounted or unmounted as well as just configured in I(fstab). C(absent) and C(present) only deal with I(fstab)."
        ], 
        "choices": [
          "present", 
          "absent", 
          "mounted", 
          "unmounted"
        ]
      }, 
      "opts": {
        "default": null, 
        "required": false, 
        "description": [
          "mount options (see fstab(8))"
        ]
      }
    }, 
    "ansible_version": "0.8"
  }, 
  {
    "now_date": "2012-10-09", 
    "requirements": [
      "ConfigParser"
    ], 
    "description": [
      "Add or remove MySQL databases from a remote host."
    ], 
    "author": "Mark Theunissen", 
    "notes": [
      "Requires the MySQLdb Python package on the remote host. For Ubuntu, this is as easy as apt-get install python-mysqldb.", 
      "Both C(login_password) and C(login_username) are required when you are passing credentials. If none are present, the module will attempt to read the credentials from C(~/.my.cnf), and finally fall back to using the MySQL default login of 'root' with no password."
    ], 
    "module": "mysql_db", 
    "filename": "library/mysql_db", 
    "examples": [
      {
        "code": "mysql_db db=bobdata state=present", 
        "description": "Create a new database with name 'bobdata'"
      }
    ], 
    "docuri": "mysql-db", 
    "short_description": "Add or remove MySQL databases from a remote host.", 
    "version_added": "0.6", 
    "options": {
      "name": {
        "default": null, 
        "required": true, 
        "description": [
          "name of the database to add or remove"
        ]
      }, 
      "encoding": {
        "default": null, 
        "required": false, 
        "description": [
          "Encoding mode"
        ]
      }, 
      "login_user": {
        "default": null, 
        "required": false, 
        "description": [
          "The username used to authenticate with"
        ]
      }, 
      "login_host": {
        "default": "localhost", 
        "required": false, 
        "description": [
          "Host running the database"
        ]
      }, 
      "state": {
        "default": "present", 
        "required": false, 
        "description": [
          "The database state"
        ], 
        "choices": [
          "present", 
          "absent"
        ]
      }, 
      "login_password": {
        "default": null, 
        "required": false, 
        "description": [
          "The password used to authenticate with"
        ]
      }, 
      "collation": {
        "default": null, 
        "required": false, 
        "description": [
          "Collation mode"
        ]
      }
    }, 
    "ansible_version": "0.8"
  }, 
  {
    "now_date": "2012-10-09", 
    "requirements": [
      "ConfigParser", 
      "MySQLdb"
    ], 
    "description": [
      "Adds or removes a user from a MySQL database."
    ], 
    "author": "Mark Theunissen", 
    "notes": [
      "Requires the MySQLdb Python package on the remote host. For Ubuntu, this is as easy as apt-get install python-mysqldb.", 
      "Both C(login_password) and C(login_username) are required when you are passing credentials. If none are present, the module will attempt to read the credentials from C(~/.my.cnf), and finally fall back to using the MySQL default login of 'root' with no password."
    ], 
    "module": "mysql_user", 
    "filename": "library/mysql_user", 
    "examples": [
      {
        "code": "mysql_user name=bob password=12345 priv=*.*:ALL state=present", 
        "description": "Create database user with name 'bob' and password '12345' with all database privileges"
      }, 
      {
        "code": "mysql_user login_user=root login_password=123456 name=sally state=absent", 
        "description": "Ensure no user named 'sally' exists, also passing in the auth credentials."
      }, 
      {
        "code": "mydb.*:INSERT,UPDATE/anotherdb.*:SELECT/yetanotherdb.*:ALL", 
        "description": "Example privileges string format"
      }
    ], 
    "docuri": "mysql-user", 
    "short_description": "Adds or removes a user from a MySQL database.", 
    "version_added": "0.6", 
    "options": {
      "name": {
        "default": null, 
        "required": true, 
        "description": [
          "name of the user (role) to add or remove"
        ]
      }, 
      "login_user": {
        "default": null, 
        "required": false, 
        "description": [
          "The username used to authenticate with"
        ]
      }, 
      "login_host": {
        "default": "localhost", 
        "required": false, 
        "description": [
          "Host running the database"
        ]
      }, 
      "state": {
        "default": "present", 
        "required": false, 
        "description": [
          "The database state"
        ], 
        "choices": [
          "present", 
          "absent"
        ]
      }, 
      "host": {
        "default": "localhost", 
        "required": false, 
        "description": [
          "the 'host' part of the MySQL username"
        ]
      }, 
      "login_password": {
        "default": null, 
        "required": false, 
        "description": [
          "The password used to authenticate with"
        ]
      }, 
      "password": {
        "default": null, 
        "required": false, 
        "description": [
          "set the user's password"
        ]
      }, 
      "priv": {
        "default": null, 
        "required": false, 
        "description": [
          "MySQL privileges string in the format: C(db.table:priv1,priv2)"
        ]
      }
    }, 
    "ansible_version": "0.8"
  }, 
  {
    "now_date": "2012-10-09", 
    "requirements": [
      "Nagios"
    ], 
    "description": [
      "The M(nagios) module has two basic functions: scheduling downtime and toggling alerts for services or hosts.", 
      "All actions require the C(host) parameter to be given explicitly. In playbooks you can use the C($inventory_hostname) variable to refer to the host the playbook is currently running on.", 
      "You can specify multiple services at once by separating them with commas, .e.g., C(services=httpd,nfs,puppet).", 
      "When specifying what service to handle there is a special service value, I(host), which will handle alerts/downtime for the I(host itself), e.g., C(service=host). This keyword may not be given with other services at the same time. I(Setting alerts/downtime for a host does not affect alerts/downtime for any of the services running on it.)", 
      "When using the M(nagios) module you will need to specify your nagios server using the C(delegate_to) parameter."
    ], 
    "author": "Tim Bielawa", 
    "module": "nagios", 
    "filename": "library/nagios", 
    "examples": [
      {
        "code": "nagios action=downtime minutes=30 service=httpd host=$inventory_hostname", 
        "description": "set 30 minutes of apache downtime"
      }, 
      {
        "code": "nagios action=downtime minutes=60 service=host host=$inventory_hostname", 
        "description": "schedule an hour of HOST downtime"
      }, 
      {
        "code": "nagios action=downtime services=frob,foobar,qeuz host=$inventory_hostname", 
        "description": "schedule downtime for a few services"
      }, 
      {
        "code": "nagios action=enable_alerts service=smart host=$inventory_hostname", 
        "description": "enable SMART disk alerts"
      }, 
      {
        "code": "nagios action=disable_alerts service=httpd,nfs host=$inventory_hostname", 
        "description": "two services at once: disable httpd and nfs alerts"
      }, 
      {
        "code": "nagios action=disable_alerts service=host host=$inventory_hostname", 
        "description": "disable HOST alerts"
      }, 
      {
        "code": "nagios action=silence host=$inventory_hostname", 
        "description": "silence ALL alerts"
      }, 
      {
        "code": "nagios action=unsilence host=$inventory_hostname", 
        "description": "unsilence all alerts"
      }
    ], 
    "docuri": "nagios", 
    "short_description": "Perform common tasks in Nagios related to downtime and notifications.", 
    "version_added": 0.7, 
    "options": {
      "author": {
        "default": "Ansible", 
        "required": false, 
        "description": [
          "Author to leave downtime comments as. - Only useable with the C(downtime) action."
        ]
      }, 
      "services": {
        "default": null, 
        "required": true, 
        "description": [
          "What to manage downtime/alerts for. Separate multiple services with commas.", 
          "C(service) is an alias for C(services).", 
          "B(Required) option when using the C(downtime), C(enable_alerts), and C(disable_alerts) actions."
        ], 
        "aliases": [
          "service"
        ]
      }, 
      "host": {
        "default": null, 
        "required": true, 
        "description": [
          "Host to operate on in Nagios."
        ]
      }, 
      "action": {
        "default": null, 
        "required": true, 
        "description": [
          "Action to take."
        ], 
        "choices": [
          "downtime", 
          "enable_alerts", 
          "disable_alerts", 
          "silence", 
          "unsilence"
        ]
      }, 
      "minutes": {
        "default": 30, 
        "required": false, 
        "description": [
          "Minutes to schedule downtime for.", 
          "Only useable with the C(downtime) action."
        ]
      }, 
      "cmdfile": {
        "default": "auto-detected", 
        "required": false, 
        "description": [
          "Path to the nagios I(command file) (FIFO pipe).", 
          "Only required if auto-detection fails."
        ]
      }
    }, 
    "ansible_version": "0.8"
  }, 
  {
    "now_date": "2012-10-09", 
    "requirements": [
      "ohai"
    ], 
    "description": [
      "Similar to the M(facter) module, this runs the I(ohai) discovery program (U(http://wiki.opscode.com/display/chef/Ohai)) on the remote host and returns JSON inventory data. I(Ohai) data is a bit more verbose and nested than I(facter)."
    ], 
    "author": "Michael DeHaan", 
    "notes": [], 
    "module": "ohai", 
    "filename": "library/ohai", 
    "examples": [
      {
        "code": "ansible webservers -m ohai --tree=/tmp/ohaidata", 
        "description": "Retrieve I(ohai) data from all Web servers and store in one-file per host"
      }
    ], 
    "docuri": "ohai", 
    "short_description": "Returns inventory data from I(ohai)", 
    "version_added": "0.6", 
    "options": [], 
    "ansible_version": "0.8"
  }, 
  {
    "now_date": "2012-10-09", 
    "description": [
      "Pauses playbook execution for a set amount of time, or until a prompt is acknowledged. All parameters are optional. The default behavior is to pause with a prompt.", 
      "You can use C(ctrl+c) if you wish to advance a pause earlier than it is set to expire or if you need to abort a playbook run entirely. To continue early: press C(ctrl+c) and then C(c). To abort a playbook: press C(ctrl+c) and then C(a).", 
      "The pause module integrates into async/parallelized playbooks without any special considerations (see also: Rolling Updates). When using pauses with the C(serial) playbook parameter (as in rolling updates) you are only prompted once for the current group of hosts."
    ], 
    "author": "Tim Bielawa", 
    "module": "pause", 
    "filename": "library/pause", 
    "examples": [
      {
        "code": "pause minutes=5", 
        "description": "Pause for 5 minutes to build app cache."
      }, 
      {
        "code": "pause", 
        "description": "Pause until you can verify updates to an application were successful."
      }, 
      {
        "code": "pause prompt=Make sure org.foo.FooOverload exception is not present", 
        "description": "A helpful reminder of what to look out for post-update."
      }
    ], 
    "docuri": "pause", 
    "short_description": "Pause playbook execution", 
    "version_added": 0.8, 
    "options": {
      "seconds": {
        "default": null, 
        "required": false, 
        "description": [
          "Number of minutes to pause for."
        ]
      }, 
      "prompt": {
        "default": null, 
        "required": false, 
        "description": [
          "Optional text to use for the prompt message."
        ]
      }, 
      "minutes": {
        "default": null, 
        "required": false, 
        "description": [
          "Number of minutes to pause for."
        ]
      }
    }, 
    "ansible_version": "0.8"
  }, 
  {
    "description": [
      "A trivial test module, this module always returns 'pong' on successful contact. It does not make sense in playbooks, but is useful from C(/usr/bin/ansible)"
    ], 
    "author": "Michael DeHaan", 
    "module": "ping", 
    "filename": "library/ping", 
    "examples": [
      {
        "code": "ansible webservers -m ping", 
        "description": "Test 'webservers' status"
      }
    ], 
    "docuri": "ping", 
    "short_description": "Try to connect to host and return pong on success.", 
    "now_date": "2012-10-09", 
    "ansible_version": "0.8"
  }, 
  {
    "now_date": "2012-10-09", 
    "requirements": [
      "virtualenv", 
      "pip"
    ], 
    "description": [
      "Manage Python library dependencies."
    ], 
    "author": "Matt Wright", 
    "notes": [
      "Please note that U(http://www.virtualenv.org/, virtualenv) must be installed on the remote host if the virtualenv parameter is specified."
    ], 
    "module": "pip", 
    "filename": "library/pip", 
    "examples": [
      {
        "code": "pip name=flask", 
        "description": "Install I(flask) python package."
      }, 
      {
        "code": "pip name=flask version=0.8", 
        "description": "Install I(flask) python package on version 0.8."
      }, 
      {
        "code": "pip name=flask virtualenv=/srv/webapps/my_app/venv", 
        "description": "Install I(Flask) (U(http://flask.pocoo.org/)) into the specified I(virtualenv)"
      }, 
      {
        "code": "pip requirements=/srv/webapps/my_app/src/requirements.txt", 
        "description": "Install specified python requirements."
      }, 
      {
        "code": "pip requirements=/srv/webapps/my_app/src/requirements.txt virtualenv=/srv/webapps/my_app/venv", 
        "description": "Install specified python requirements in indicated virtualenv."
      }
    ], 
    "docuri": "pip", 
    "short_description": "Manages Python library dependencies.", 
    "version_added": "0.7", 
    "options": {
      "virtualenv": {
        "default": null, 
        "required": false, 
        "description": [
          "An optional path to a virtualenv directory to install into"
        ]
      }, 
      "state": {
        "default": "present", 
        "required": false, 
        "description": [
          "The state of module"
        ], 
        "choices": [
          "present", 
          "absent", 
          "latest"
        ]
      }, 
      "version": {
        "default": null, 
        "required": false, 
        "description": [
          "The version number to install of the Python library specified in the 'name' parameter"
        ]
      }, 
      "requirements": {
        "default": null, 
        "required": false, 
        "description": [
          "The path to a pip requirements file"
        ]
      }, 
      "name": {
        "default": null, 
        "required": true, 
        "description": [
          "The name of a Python library to install"
        ]
      }
    }, 
    "ansible_version": "0.8"
  }, 
  {
    "now_date": "2012-10-09", 
    "requirements": [
      "psycopg2"
    ], 
    "description": [
      "Add or remove PostgreSQL databases from a remote host."
    ], 
    "author": "Lorin Hochstein", 
    "notes": [
      "The default authentication assumes that you are either logging in as or sudo'ing to the postgres account on the host.", 
      "This module uses psycopg2, a Python PostgreSQL database adapter. You must ensure that psycopg2 is installed on the host before using this module. If the remote host is the PostgreSQL server (which is the default case), then PostgreSQL must also be installed on the remote host. For Ubuntu-based systems, install the postgresql, libpq-dev, and python-psycopg2 packages on the remote host before using this module."
    ], 
    "module": "postgresql_db", 
    "filename": "library/postgresql_db", 
    "examples": [
      {
        "code": "postgresql_db db=acme", 
        "description": "Create a new database with name 'acme'"
      }
    ], 
    "docuri": "postgresql-db", 
    "short_description": "Add or remove PostgreSQL databases from a remote host.", 
    "version_added": "0.6", 
    "options": {
      "name": {
        "default": null, 
        "required": true, 
        "description": [
          "name of the database to add or remove"
        ]
      }, 
      "login_user": {
        "default": null, 
        "required": false, 
        "description": [
          "The username used to authenticate with"
        ]
      }, 
      "login_host": {
        "default": "localhost", 
        "required": false, 
        "description": [
          "Host running the database"
        ]
      }, 
      "state": {
        "default": "present", 
        "required": false, 
        "description": [
          "The database state"
        ], 
        "choices": [
          "present", 
          "absent"
        ]
      }, 
      "login_password": {
        "default": null, 
        "required": false, 
        "description": [
          "The password used to authenticate with"
        ]
      }, 
      "owner": {
        "default": null, 
        "required": false, 
        "description": [
          "Name of the role to set as owner of the database"
        ]
      }
    }, 
    "ansible_version": "0.8"
  }, 
  {
    "now_date": "2012-10-09", 
    "requirements": [
      "psycopg2"
    ], 
    "description": [
      "Add or remove PostgreSQL users (roles) from a remote host and, optionally, grant the users access to an existing database or tables.", 
      "The fundamental function of the module is to create, or delete, roles from a PostgreSQL cluster. Privilege assignment, or removal, is an optional step, which works on one database at a time. This allows for the module to be called several times in the same module to modify the permissions on different databases, or to grant permissions to already existing users.", 
      "A user cannot be removed untill all the privileges have been stripped from the user. In such situation, if the module tries to remove the user it will fail. To avoid this from happening the fail_on_user option signals the module to try to remove the user, but if not possible keep going; the module will report if changes happened and separately if the user was removed or not."
    ], 
    "author": "Lorin Hochstein", 
    "notes": [
      "The default authentication assumes that you are either logging in as or sudo'ing to the postgres account on the host.", 
      "This module uses psycopg2, a Python PostgreSQL database adapter. You must ensure that psycopg2 is installed on the host before using this module. If the remote host is the PostgreSQL server (which is the default case), then PostgreSQL must also be installed on the remote host. For Ubuntu-based systems, install the postgresql, libpq-dev, and python-psycopg2 packages on the remote host before using this module."
    ], 
    "module": "postgresql_user", 
    "filename": "library/postgresql_user", 
    "examples": [
      {
        "code": "postgresql_user db=acme user=django password=ceec4eif7ya priv=CONNECT/products:ALL", 
        "description": "Create django user and grant access to database and products table"
      }, 
      {
        "code": "postgresql_user db=acme user=test priv=ALL/products:ALL state=absent fail_on_user=no", 
        "description": "Remove test user privileges from acme"
      }, 
      {
        "code": "postgresql_user db=test user=test priv=ALL state=absent", 
        "description": "Remove test user from test database and the cluster"
      }, 
      {
        "code": "INSERT,UPDATE/table:SELECT/anothertable:ALL", 
        "description": "Example privileges string format"
      }
    ], 
    "docuri": "postgresql-user", 
    "short_description": "Adds or removes a users (roles) from a PostgreSQL database.", 
    "version_added": "0.6", 
    "options": {
      "name": {
        "default": null, 
        "required": true, 
        "description": [
          "name of the user (role) to add or remove"
        ]
      }, 
      "login_user": {
        "default": "postgres", 
        "required": false, 
        "description": [
          "User (role) used to authenticate with PostgreSQL"
        ]
      }, 
      "login_host": {
        "default": "localhost", 
        "required": false, 
        "description": [
          "Host running PostgreSQL."
        ]
      }, 
      "db": {
        "default": null, 
        "required": false, 
        "description": [
          "name of database where permissions will be granted"
        ]
      }, 
      "state": {
        "default": "present", 
        "required": false, 
        "description": [
          "The database state"
        ], 
        "choices": [
          "present", 
          "absent"
        ]
      }, 
      "login_password": {
        "default": null, 
        "required": false, 
        "description": [
          "Password used to authenticate with PostgreSQL"
        ]
      }, 
      "password": {
        "default": null, 
        "required": true, 
        "description": [
          "set the user's password"
        ]
      }, 
      "fail_on_user": {
        "default": true, 
        "required": false, 
        "description": [
          "if yes, fail when user can't be removed. Otherwise just log and continue"
        ], 
        "choices": [
          "yes", 
          "no"
        ]
      }, 
      "priv": {
        "default": null, 
        "required": false, 
        "description": [
          "PostgreSQL privileges string in the format: C(table:priv1,priv2)"
        ]
      }
    }, 
    "ansible_version": "0.8"
  }, 
  {
    "description": [
      "Executes a low-down and dirty SSH command, not going through the module subsystem. This is useful and should only be done in two cases. The first case is installing python-simplejson on older (Python 2.4 and before) hosts that need it as a dependency to run modules, since nearly all core modules require it. Another is speaking to any devices such as routers that do not have any Python installed. In any other case, using the M(shell) or M(command) module is much more appropriate. Arguments given to M(raw) are run directly through the configured remote shell and only output is returned. There is no error detection or change handler support for this module"
    ], 
    "author": "Michael DeHaan", 
    "module": "raw", 
    "filename": "library/raw", 
    "examples": [
      {
        "code": "ansible newhost.example.com -m raw -a \"yum -y install python-simplejson\"", 
        "description": "Example from /usr/bin/ansible to bootstrap a legacy python 2.4 host"
      }
    ], 
    "docuri": "raw", 
    "short_description": "Executes a low-down and dirty SSH command", 
    "now_date": "2012-10-09", 
    "ansible_version": "0.8"
  }, 
  {
    "now_date": "2012-10-09", 
    "requirements": [], 
    "description": [
      "Toggles SELinux booleans."
    ], 
    "author": "Stephen Fromm", 
    "notes": [
      "Not tested on any debian based system"
    ], 
    "module": "seboolean", 
    "filename": "library/seboolean", 
    "examples": [
      {
        "code": "seboolean name=httpd_can_network_connect state=true persistent=yes", 
        "description": "Set I(httpd_can_network_connect) SELinux flag to I(true) and I(persistent)"
      }
    ], 
    "docuri": "seboolean", 
    "short_description": "Toggles SELinux booleans.", 
    "version_added": "0.7", 
    "options": {
      "state": {
        "default": null, 
        "required": true, 
        "description": [
          "Desired boolean value"
        ], 
        "choices": [
          "true", 
          "false"
        ]
      }, 
      "name": {
        "default": null, 
        "required": true, 
        "description": [
          "Name of the boolean to configure"
        ]
      }, 
      "persistent": {
        "default": false, 
        "required": false, 
        "description": [
          "Set to 'yes' if the boolean setting should survive a reboot"
        ], 
        "choices": [
          "yes", 
          "no"
        ]
      }
    }, 
    "ansible_version": "0.8"
  }, 
  {
    "now_date": "2012-10-09", 
    "requirements": [], 
    "description": [
      "Configures the SELinux mode and policy. A reboot may be required after usage. Ansible will not issue this reboot but will let you know when it is required."
    ], 
    "author": "Derek Carter", 
    "notes": [
      "Not tested on any debian based system"
    ], 
    "module": "selinux", 
    "filename": "library/selinux", 
    "examples": [
      {
        "code": "selinux policy=targeted state=enforcing"
      }, 
      {
        "code": "selinux policy=targeted state=disabled"
      }
    ], 
    "docuri": "selinux", 
    "short_description": "Change policy and state of SELinux", 
    "version_added": "0.7", 
    "options": {
      "policy": {
        "default": null, 
        "required": true, 
        "description": [
          "name of the SELinux policy to use (example: 'targeted')"
        ]
      }, 
      "state": {
        "default": null, 
        "required": true, 
        "description": [
          "The SELinux mode"
        ], 
        "choices": [
          "enforcing", 
          "permissive", 
          "disabled"
        ]
      }, 
      "conf": {
        "default": "/etc/selinux/config", 
        "required": false, 
        "description": [
          "path to the SELinux configuration file, if non-standard"
        ]
      }
    }, 
    "ansible_version": "0.8"
  }, 
  {
    "now_date": "2012-10-09", 
    "description": [
      "Controls services on remote hosts."
    ], 
    "author": "Michael DeHaan", 
    "module": "service", 
    "filename": "library/service", 
    "examples": [
      {
        "code": "service name=httpd state=started", 
        "description": "Example action from Ansible Playbooks"
      }, 
      {
        "code": "service name=httpd state=stopped", 
        "description": "Example action from Ansible Playbooks"
      }, 
      {
        "code": "service name=httpd state=restarted", 
        "description": "Example action from Ansible Playbooks"
      }, 
      {
        "code": "service name=httpd state=reloaded", 
        "description": "Example action from Ansible Playbooks"
      }, 
      {
        "code": "service name=foo pattern=/usr/bin/foo state=started", 
        "description": "Example action from Ansible Playbooks"
      }
    ], 
    "docuri": "service", 
    "short_description": "Manage services.", 
    "version_added": 0.1, 
    "options": {
      "pattern": {
        "required": false, 
        "description": [
          "If the service does not respond to the status command, name a substring to look for as would be found in the output of the I(ps) command as a stand-in for a status result.  If the string is found, the service will be assumed to be running."
        ], 
        "version_added": "0.7"
      }, 
      "state": {
        "required": false, 
        "description": [
          "I(started), I(stopped), I(reloaded), I(restarted). I(Started)/I(stopped) are idempotent actions that will not run commands unless necessary.  I(restarted) will always bounce the service.  I(reloaded) will always reload."
        ], 
        "choices": [
          "running", 
          "started", 
          "stopped", 
          "restarted", 
          "reloaded"
        ]
      }, 
      "enabled": {
        "required": false, 
        "description": [
          "Whether the service should start on boot."
        ], 
        "choices": [
          "yes", 
          "no"
        ]
      }, 
      "name": {
        "required": true, 
        "description": [
          "Name of the service."
        ]
      }
    }, 
    "ansible_version": "0.8"
  }, 
  {
    "description": [
      "This module is automatically called by playbooks to gather useful variables about remote hosts that can be used in playbooks. It can also be executed directly by C(/usr/bin/ansible) to check what variables are available to a host. Ansible provides many I(facts) about the system, automatically."
    ], 
    "author": "Michael DeHaan", 
    "notes": [
      "More ansible facts will be added with successive releases. If I(facter) or I(ohai) are installed, variables from these programs will also be snapshotted into the JSON file for usage in templating. These variables are prefixed with C(facter_) and C(ohai_) so it's easy to tell their source. All variables are bubbled up to the caller. Using the ansible facts and choosing to not install I(facter) and I(ohai) means you can avoid Ruby-dependencies on your remote systems."
    ], 
    "module": "setup", 
    "filename": "library/setup", 
    "examples": [
      {
        "code": "ansible all -m setup -tree /tmp/facts", 
        "description": "Obtain facts from all hosts and store them indexed by hostname at /tmp/facts."
      }
    ], 
    "docuri": "setup", 
    "short_description": "Gathers facts about remote hosts", 
    "now_date": "2012-10-09", 
    "ansible_version": "0.8"
  }, 
  {
    "now_date": "2012-10-09", 
    "requirements": [], 
    "description": [
      "The shell module takes the command name followed by a list of arguments, space delimited. It is almost exactly like the M(command) module but runs the command through a shell (C(/bin/sh)) on the remote node."
    ], 
    "author": "Michael DeHaan", 
    "notes": [
      "If you want to execute a command securely and predicably, it may be better to use the M(command) module instead. Best practices when writing playbooks will follow the trend of using M(command) unless M(shell) is explicitly required. When running ad-hoc commands, use your best judgement."
    ], 
    "module": "shell", 
    "filename": "library/shell", 
    "examples": [
      {
        "code": "shell somescript.sh >> somelog.txt", 
        "description": "Execute the command in remote shell"
      }
    ], 
    "docuri": "shell", 
    "short_description": "Execute commands in nodes.", 
    "version_added": "0.2", 
    "options": {
      "creates": {
        "default": null, 
        "required": false, 
        "description": [
          "a filename, when it already exists, this step will NOT be run"
        ]
      }, 
      "chdir": {
        "default": null, 
        "required": false, 
        "description": [
          "cd into this directory before running the command (0.6 and later)"
        ]
      }, 
      "(free form)": {
        "default": null, 
        "required": null, 
        "description": [
          "The command module takes a free form command to run"
        ]
      }
    }, 
    "ansible_version": "0.8"
  }, 
  {
    "requirements": [], 
    "description": [
      "This module works like M(fetch). It is used for fetching a base64- encoded blob containing the data in a remote file."
    ], 
    "author": "Michael DeHaan", 
    "notes": [
      "See also: M(fetch)"
    ], 
    "module": "slurp", 
    "filename": "library/slurp", 
    "examples": [
      {
        "code": "ansible host -m slurp -a 'src=/tmp/xx'\n    host | success >> {\n       \"content\": \"aGVsbG8gQW5zaWJsZSB3b3JsZAo=\", \n       \"encoding\": \"base64\"\n    }\n", 
        "description": "Example using C(/usr/bin/ansible)"
      }
    ], 
    "docuri": "slurp", 
    "short_description": "Slurps a file from remote nodes", 
    "now_date": "2012-10-09", 
    "options": {
      "src": {
        "default": null, 
        "required": true, 
        "description": [
          "The file on the remote system to fetch. This must be a file, not a directory."
        ], 
        "aliases": []
      }
    }, 
    "ansible_version": "0.8"
  }, 
  {
    "now_date": "2012-10-09", 
    "requirements": [], 
    "description": [
      "This module is really simple, so for now this checks out from the given branch of a repo at a particular SHA or tag. Latest is not supported, you should not be doing that."
    ], 
    "author": "Dane Summers", 
    "notes": [
      "Requires subversion and grep on the client."
    ], 
    "module": "subversion", 
    "filename": "library/subversion", 
    "examples": [
      {
        "code": "subversion repo=svn+ssh://an.example.org/path/to/repo dest=/src/checkout", 
        "description": "Export subversion repository in a specified folder"
      }
    ], 
    "docuri": "subversion", 
    "short_description": "Deploys a subversion repository.", 
    "version_added": "0.7", 
    "options": {
      "repo": {
        "default": null, 
        "required": true, 
        "description": [
          "The subversion URL to the repository."
        ]
      }, 
      "dest": {
        "default": null, 
        "required": true, 
        "description": [
          "Absolute path where the repository should be deployed."
        ]
      }, 
      "force": {
        "default": true, 
        "required": false, 
        "description": [
          "If yes, any modified files in the working repository will be discarded. If no, this module will fail if it encounters modified files."
        ], 
        "choices": [
          "yes", 
          "no"
        ]
      }
    }, 
    "ansible_version": "0.8"
  }, 
  {
    "now_date": "2012-10-09", 
    "requirements": [], 
    "description": [
      "Manage the state of a program or group of programs running via Supervisord"
    ], 
    "author": "Matt Wright", 
    "module": "supervisorctl", 
    "filename": "library/supervisorctl", 
    "examples": [
      {
        "code": "supervisorctl name=my_app state=started", 
        "description": "Manage the state of program I(my_app) to be in I(started) state."
      }
    ], 
    "docuri": "supervisorctl", 
    "short_description": "Manage the state of a program or group of programs running via Supervisord", 
    "version_added": "0.7", 
    "options": {
      "state": {
        "default": null, 
        "required": true, 
        "description": [
          "The state of service"
        ], 
        "choices": [
          "started", 
          "stopped", 
          "restarted"
        ]
      }, 
      "name": {
        "default": null, 
        "required": true, 
        "description": [
          "The name of the supervisord program/process to manage"
        ]
      }
    }, 
    "ansible_version": "0.8"
  }, 
  {
    "requirements": null, 
    "description": [
      "Templates are processed by the Jinja2 templating language (U(http://jinja.pocoo.org/docs/)) - documentation on the template formatting can be found in the Template Designer Documentation (U(http://jinja.pocoo.org/docs/templates/))."
    ], 
    "author": "Michael DeHaan", 
    "notes": [
      "Since Ansible version 0.9, templates are loaded with C(trim_blocks=True)."
    ], 
    "module": "template", 
    "filename": "library/template", 
    "examples": [
      {
        "code": "template src=/mytemplates/foo.j2 dest=/etc/file.conf owner=bin group=wheel mode=0644", 
        "description": "Example from Ansible Playbooks"
      }
    ], 
    "docuri": "template", 
    "short_description": "Templates a file out to a remote server.", 
    "now_date": "2012-10-09", 
    "options": {
      "dest": {
        "default": null, 
        "required": true, 
        "description": [
          "Location to render the template to on the remote machine."
        ]
      }, 
      "src": {
        "default": null, 
        "required": true, 
        "description": [
          "Path of a Jinja2 formatted template on the local server. This can be a relative or absolute path."
        ], 
        "aliases": []
      }, 
      "backup": {
        "default": "no", 
        "required": false, 
        "description": [
          "Create a backup file including the timestamp information so you can get the original file back if you somehow clobbered it incorrectly."
        ], 
        "choices": [
          "yes", 
          "no"
        ]
      }, 
      "others": {
        "required": false, 
        "description": [
          "all arguments accepted by the M(file) module also work here"
        ]
      }
    }, 
    "ansible_version": "0.8"
  }, 
  {
    "now_date": "2012-10-09", 
    "requirements": [
      "useradd", 
      "userdel", 
      "usermod"
    ], 
    "description": [
      "Manage user accounts and user attributes."
    ], 
    "author": "Stephen Fromm", 
    "module": "user", 
    "filename": "library/user", 
    "docuri": "user", 
    "short_description": "Manage user accounts", 
    "version_added": 0.2, 
    "options": {
      "comment": {
        "required": false, 
        "description": [
          "Optionally sets the description (aka I(GECOS)) of user account."
        ]
      }, 
      "shell": {
        "required": false, 
        "description": [
          "Optionally set the user's shell."
        ]
      }, 
      "force": {
        "default": "no", 
        "required": false, 
        "description": [
          "When used with I(state=absent), behavior is as with I(userdel --force)."
        ], 
        "choices": [
          true, 
          false
        ]
      }, 
      "name": {
        "required": true, 
        "description": [
          "Name of the user to create, remove or modify."
        ]
      }, 
      "createhome": {
        "default": "yes", 
        "required": false, 
        "description": [
          "Unless set to I(no), a home directory will be made for the user when the account is created."
        ], 
        "choices": [
          true, 
          false
        ]
      }, 
      "system": {
        "default": "no", 
        "required": false, 
        "description": [
          "When creating an account, setting this to I(yes) makes the user a system account.  This setting cannot be changed on existing users."
        ], 
        "choices": [
          true, 
          false
        ]
      }, 
      "remove": {
        "default": "no", 
        "required": false, 
        "description": [
          "When used with I(state=absent), behavior is as with I(userdel --remove)."
        ], 
        "choices": [
          true, 
          false
        ]
      }, 
      "group": {
        "required": false, 
        "description": [
          "Optionally sets the user's primary group (takes a group name)."
        ]
      }, 
      "state": {
        "default": "present", 
        "required": false, 
        "description": [
          "Whether the account should exist.  When I(absent), removes the user account."
        ], 
        "choices": [
          "present", 
          "absent"
        ]
      }, 
      "groups": {
        "required": false, 
        "description": [
          "Puts the user in this comma-delimited list of groups."
        ]
      }, 
      "home": {
        "required": false, 
        "description": [
          "Optionally set the user's home directory."
        ]
      }, 
      "password": {
        "required": false, 
        "description": [
          "Optionally set the user's password to this crypted value.  See the user example in the github examples directory for what this looks like in a playbook."
        ]
      }, 
      "append": {
        "required": false, 
        "description": [
          "If I(yes), will only add groups, not set them to just the list in I(groups)."
        ]
      }, 
      "uid": {
        "required": false, 
        "description": [
          "Optionally sets the I(UID) of the user."
        ]
      }
    }, 
    "ansible_version": "0.8"
  }, 
  {
    "now_date": "2012-10-09", 
    "requirements": [
      "libvirt"
    ], 
    "description": [
      "Manages virtual machines supported by I(libvirt)."
    ], 
    "author": "Michael DeHaan, Seth Vidal", 
    "notes": [
      "Other non-idempotent commands are: C(status), C(pause), C(unpause), C(get_xml), C(autostart), C(freemem), C(list_vms), C(info), C(nodeinfo), C(virttype)"
    ], 
    "module": "virt", 
    "filename": "library/virt", 
    "examples": [
      {
        "code": "virt guest=alpha state=running", 
        "description": "Example from Ansible Playbooks"
      }, 
      {
        "code": "ansible host -m virt -a \"guest=alpha command=status\"", 
        "description": "Example guest management with C(/usr/bin/ansible)"
      }
    ], 
    "docuri": "virt", 
    "short_description": "Manages virtual machines supported by libvirt", 
    "version_added": "0.2", 
    "options": {
      "state": {
        "default": "no", 
        "required": false, 
        "description": [
          "Note that there may be some lag for state requests like C(shutdown) since these refer only to VM states. After starting a guest, it may not be immediately accessible."
        ], 
        "choices": [
          "running", 
          "shutdown", 
          "destroyed", 
          "undefined"
        ]
      }, 
      "command": {
        "required": false, 
        "description": [
          "in addition to state management, various non-idempotent commands are available. See examples"
        ]
      }, 
      "name": {
        "default": null, 
        "required": true, 
        "description": [
          "name of the guest VM being managed"
        ], 
        "aliases": []
      }
    }, 
    "ansible_version": "0.8"
  }, 
  {
    "now_date": "2012-10-09", 
    "description": [
      "This module gathers facts for a specific guest on VMWare vSphere. These facts include hardware and network related information useful for provisioning (e.g. macaddress, uuid).", 
      "This module requires the pysphere python module."
    ], 
    "author": "Dag Wieers", 
    "notes": [
      "This module ought to be run from a system that can access vSphere directly. Either by using C(local_action), or C(using delegate)_to."
    ], 
    "module": "vsphere_facts", 
    "filename": "library/vsphere_facts", 
    "examples": [
      {
        "code": "local_action: vsphere_facts host=$esxserver login=$esxlogin password=$esxpassword guest=$inventory_hostname_short\nonly_if: \"'$cmdb_hwmodel'.startswith('VMWare ')\n", 
        "description": "Task to gather facts from a vSphere cluster only if the system is a VMWare guest"
      }, 
      {
        "code": [
          {
            "hw_name": "centos6", 
            "hw_processor_count": 1, 
            "hw_memtotal_mb": 2048, 
            "hw_guest_full_name": "Red Hat Enterprise Linux 6 (64-bit)", 
            "hw_guest_id": "rhel6_64Guest", 
            "hw_eth0": [
              {
                "macaddress": "00:11:22:33:44:55", 
                "macaddress_dash": "00-11-22-33-44-55", 
                "addresstype": "assigned", 
                "summary": "VLAN-321", 
                "label": "Network adapter 1"
              }
            ], 
            "hw_product_uuid": "ef50bac8-2845-40ff-81d9-675315501dac"
          }
        ], 
        "description": "Typical output of a vsphere_facts run on a guest"
      }
    ], 
    "docuri": "vsphere-facts", 
    "short_description": "Gather facts for a guest on VMWare vSphere", 
    "version_added": "0.8", 
    "options": {
      "host": {
        "required": true, 
        "description": [
          "The vSphere server from the cluster the virtual server is located on."
        ]
      }, 
      "password": {
        "required": true, 
        "description": [
          "The password to authenticate on the vSphere cluster."
        ]
      }, 
      "login": {
        "required": true, 
        "description": [
          "The login name to authenticate on the vSphere cluster."
        ]
      }, 
      "guest": {
        "required": true, 
        "description": [
          "The virtual server to gather facts for on the vSphere cluster."
        ]
      }
    }, 
    "ansible_version": "0.8"
  }, 
  {
    "now_date": "2012-10-09", 
    "requirements": null, 
    "description": [
      "This is useful for when services are not immediately available after their init scripts return - which is true of certain Java application servers. It is also useful when starting guests with the M(virt) module and needing to pause until they are ready."
    ], 
    "author": "Jeroen Hoekx", 
    "notes": [], 
    "module": "wait_for", 
    "filename": "library/wait_for", 
    "examples": [
      {
        "code": "wait_for port=8000 delay=10", 
        "description": "Example from Ansible Playbooks"
      }
    ], 
    "docuri": "wait-for", 
    "short_description": "Waits for a given port to become accessible on a server.", 
    "version_added": "0.7", 
    "options": {
      "delay": {
        "default": 0, 
        "required": false, 
        "description": [
          "number of seconds to wait before starting to poll"
        ]
      }, 
      "host": {
        "default": "127.0.0.1", 
        "required": false, 
        "description": [
          "hostname or IP address to wait for"
        ], 
        "aliases": []
      }, 
      "port": {
        "required": true, 
        "description": [
          "port number to poll"
        ]
      }, 
      "timeout": {
        "default": 300, 
        "required": false, 
        "description": [
          "maximum number of seconds to wait for"
        ]
      }, 
      "state": {
        "default": "started", 
        "description": [
          "either C(started), or C(stopped) depending on whether the module should poll for the port being open or closed."
        ], 
        "choices": [
          "started", 
          "stopped"
        ]
      }
    }, 
    "ansible_version": "0.8"
  }, 
  {
    "requirements": [
      "yum", 
      "rpm"
    ], 
    "description": [
      "Will install, upgrade, remove, and list packages with the I(yum) package manager."
    ], 
    "author": "Seth Vidal", 
    "notes": [], 
    "module": "yum", 
    "filename": "library/yum", 
    "examples": [
      {
        "code": "yum name=httpd state=latest"
      }, 
      {
        "code": "yum name=httpd state=removed"
      }, 
      {
        "code": "yum name=httpd state=installed"
      }
    ], 
    "docuri": "yum", 
    "short_description": "Manages packages with the I(yum) package manager", 
    "now_date": "2012-10-09", 
    "options": {
      "state": {
        "default": "present", 
        "required": false, 
        "description": [
          "whether to install (C(present), C(latest)), or remove (C(absent)) a package."
        ], 
        "choices": [
          "present", 
          "latest", 
          "absent"
        ]
      }, 
      "list": {
        "default": null, 
        "required": false, 
        "description": [
          "various non-idempotent commands for usage with C(/usr/bin/ansible) and I(not) playbooks. See examples."
        ]
      }, 
      "name": {
        "default": null, 
        "required": true, 
        "description": [
          "package name, or package specifier with version, like C(name-1.0)."
        ], 
        "aliases": []
      }
    }, 
    "ansible_version": "0.8"
  }
];

  $scope.orderProp = "module";
}