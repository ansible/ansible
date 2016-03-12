Ansible Changes By Release
==========================

## 2.1 TBD - ACTIVE DEVELOPMENT

###Major Changes:

* added facility for modules to send back 'diff' for display when ansible is called with --diff, updated several modules to return this info
* added ansible-console tool, a REPL shell that allows running adhoc tasks against a chosen inventory (based on  https://github.com/dominis/ansible-shell )

####New Modules:
- aws
  * ec2_vol_facts
  * ec2_vpc_dhcp_options
  * ec2_vpc_net_facts
- cloudstack
  * cs_cluster
  * cs_configuration
  * cs_instance_facts
  * cs_pod
  * cs_resourcelimit
  * cs_volume
  * cs_zone
- windows
  * win_regmerge
  * win_timezone
- yum_repository


####New Filters:
* extract

####New Callbacks:
* actionable (only shows changed and failed)
* slack
* json

####New Inventory scripts:
* rackhd

###Minor Changes:

* callbacks now have access to the options with which the CLI was called
* debug is now controlable with verbosity
* modules now get verbosity, diff and other flags as passed to ansible

## 2.0.1 "Over the Hills and Far Away"

* Fixes a major compatibility break in the synchronize module shipped with
  2.0.0.x.  That version of synchronize ran sudo on the controller prior to
  running rsync.  In 1.9.x and previous, sudo was run on the host that rsync
  connected to.  2.0.1 restores the 1.9.x behaviour.
* Additionally, several other problems with where synchronize chose to run when
  combined with delegate_to were fixed.  In particular, if a playbook targetted
  localhost and then delegated_to a remote host the prior behavior (in 1.9.x
  and 2.0.0.x) was to copy files between the src and destination directories on
  the delegated host.  This has now been fixed to copy between localhost and
  the delegated host.
* Fix a regression where synchronize was unable to deal with unicode paths.
* Fix a regression where synchronize deals with inventory hosts that use
  localhost but with an alternate port.
* Fixes a regression where the retry files feature was not implemented.
* Fixes a regression where the any_errors_fatal option was implemented in 2.0
  incorrectly, and also adds a feature where any_errors_fatal can be set at
  the block level.
* Fix tracebacks when playbooks or ansible itself were located in directories
  with unicode characters.
* Fix bug when sending unicode characters to an external pager for display.
* Fix a bug with squashing loops for special modules (mostly package managers).
  The optimization was squashing when the loop did not apply to the selection
  of packages.  This has now been fixed.
* Temp files created when using vault are now "shredded" using the unix shred
  program which overwrites the file with random data.
* Some fixes to cloudstack modules for case sensitivity
* Fix non-newstyle modules (non-python modules and old-style modules) to
  disabled pipelining.
* Fix fetch module failing even if fail_on_missing is set to False
* Fix for cornercase when local connections, sudo, and raw were used together.
* Fix dnf module to remove dependent packages when state=absent is specified.
  This was a feature of the 1.9.x version that was left out by mistake when the
  module was rewritten for 2.0.
* Fix bugs with non-english locales in yum, git, and apt modules
* Fix a bug with the dnf module where state=latest could only upgrade, not install.
* Fix to make implicit fact gathering task correctly inherit settings from play,
  this might cause an error if settings environment on play depending on 'ansible_env'
  which was previouslly ignored

## 2.0 "Over the Hills and Far Away" - Jan 12, 2016

###Major Changes:

* Releases are now named after Led Zeppelin songs, 1.9 will be the last Van Halen named release.
* The new block/rescue/always directives allow for making task blocks and exception-like semantics
* New strategy plugins (e.g. `free`) allow control over the flow of task execution per play. The default (`linear`) will be the same as before.
* Improved error handling, with more detailed parser messages. General exception handling and display has been revamped.
* Task includes are now evaluated during execution, allowing more dynamic includes and options. Play includes are unchanged both still use the `include` directive.
* "with\_<lookup>" loops can now be used with task includes since they are dynamic.
* Callback, connection, cache and lookup plugin APIs have changed. Existing plugins might require modification to work with the new versions.
* Callbacks are now shipped in the active directory and don't need to be copied, just whitelisted in ansible.cfg.
* Many API changes. Those integrating directly with Ansible's API will encounter breaking changes, but the new API is much easier to use and test.
* Settings are now more inheritable; what you set at play, block or role will be automatically inherited by the contained tasks.
  This allows for new features to automatically be settable at all levels, previously we had to manually code this.
* Vars are now settable at play, block, role and task level with the `vars` directive and scoped to the tasks contained.
* Template code now retains types for bools and numbers instead of turning them into strings.
  If you need the old behaviour, quote the value and it will get passed around as a string
* Empty variables and variables set to null in yaml will no longer be converted to empty strings.  They will retain the value of `None`.
  To go back to the old behaviour, you can override the `null_representation` setting to an empty string in your config file or
  by setting the `ANSIBLE_NULL_REPRESENTATION` environment variable.
* Added `meta: refresh_inventory` to force rereading the inventory in a play.
  This re-executes inventory scripts, but does not force them to ignore any cache they might use.
* New delegate_facts directive, a boolean that allows you to apply facts to the delegated host (true/yes) instead of the inventory_hostname (no/false) which is the default and previous behaviour.
* local connections now work with 'su' as a privilege escalation method
* Ansible 2.0 has deprecated the “ssh” from ansible_ssh_user, ansible_ssh_host, and ansible_ssh_port to become ansible_user, ansible_host, and ansible_port.
* New ssh configuration variables (`ansible_ssh_common_args`, `ansible_ssh_extra_args`) can be used to configure a
  per-group or per-host ssh ProxyCommand or set any other ssh options.
  `ansible_ssh_extra_args` is used to set options that are accepted only by ssh (not sftp or scp, which have their own analogous settings).
* ansible-pull can now verify the code it runs when using git as a source repository, using git's code signing and verification features.
* Backslashes used when specifying parameters in jinja2 expressions in YAML dicts sometimes needed to be escaped twice.
  This has been fixed so that escaping once works. Here's an example of how playbooks need to be modified:

    ```
    # Syntax in 1.9.x
    - debug:
        msg: "{{ 'test1_junk 1\\\\3' | regex_replace('(.*)_junk (.*)', '\\\\1 \\\\2') }}"
    # Syntax in 2.0.x
    - debug:
        msg: "{{ 'test1_junk 1\\3' | regex_replace('(.*)_junk (.*)', '\\1 \\2') }}"

    # Output:
    "msg": "test1 1\\3"
    ```

* When a string with a trailing newline was specified in the playbook via yaml
dict format, the trailing newline was stripped. When specified in key=value
format the trailing newlines were kept. In v2, both methods of specifying the
string will keep the trailing newlines. If you relied on the trailing
newline being stripped you can change your playbook like this:

    ```
    # Syntax in 1.9.2
    vars:
      message: >
        Testing
        some things
    tasks:
    - debug:
        msg: "{{ message }}"

    # Syntax in 2.0.x
    vars:
      old_message: >
        Testing
        some things
      message: "{{ old_messsage[:-1] }}"
    - debug:
        msg: "{{ message }}"
    # Output
    "msg": "Testing some things"
    ```

* When specifying complex args as a variable, the variable must use the full jinja2
variable syntax ('{{var_name}}') - bare variable names there are no longer accepted.
In fact, even specifying args with variables has been deprecated, and will not be
allowed in future versions:

    ```
    ---
    - hosts: localhost
      connection: local
      gather_facts: false
      vars:
        my_dirs:
          - { path: /tmp/3a, state: directory, mode: 0755 }
          - { path: /tmp/3b, state: directory, mode: 0700 }
      tasks:
        - file:
          args: "{{item}}"
          with_items: my_dirs
    ```

###Plugins

* Rewritten dnf module that should be faster and less prone to encountering bugs in cornercases
* WinRM connection plugin passes all vars named `ansible_winrm_*` to the underlying pywinrm client. This allows, for instance, `ansible_winrm_server_cert_validation=ignore` to be used with newer versions of pywinrm to disable certificate validation on Python 2.7.9+.
* WinRM connection plugin put_file is significantly faster and no longer has file size limitations. 

####Deprecated Modules (new ones in parens):

* ec2_ami_search (ec2_ami_find)
* quantum_network (os_network)
* glance_image
* nova_compute   (os_server)
* quantum_floating_ip (os_floating_ip)
* quantum_router (os_router)
* quantum_router_gateway (os_router)
* quantum_router_interface (os_router)

####New Modules:

- amazon
  * ec2_ami_copy
  * ec2_ami_find
  * ec2_elb_facts
  * ec2_eni
  * ec2_eni_facts
  * ec2_remote_facts
  * ec2_vpc_igw
  * ec2_vpc_net
  * ec2_vpc_net_facts
  * ec2_vpc_route_table
  * ec2_vpc_route_table_facts
  * ec2_vpc_subnet
  * ec2_vpc_subnet_facts
  * ec2_win_password
  * ecs_cluster
  * ecs_task
  * ecs_taskdefinition
  * elasticache_subnet_group_facts
  * iam
  * iam_cert
  * iam_policy
  * route53_facts
  * route53_health_check
  * route53_zone
  * s3_bucket
  * s3_lifecycle
  * s3_logging
  * sns_topic
  * sqs_queue
  * sts_assume_role
- apk
- bigip_gtm_wide_ip
- bundler
- centurylink
  * clc_aa_policy
  * clc_alert_policy
  * clc_blueprint_package
  * clc_firewall_policy
  * clc_group
  * clc_loadbalancer
  * clc_modify_server
  * clc_publicip
  * clc_server
  * clc_server_snapshot
- circonus_annotation
- consul
  * consul
  * consul_acl
  * consul_kv
  * consul_session
- cloudtrail
- cloudstack
  * cs_account
  * cs_affinitygroup
  * cs_domain
  * cs_facts
  * cs_firewall
  * cs_iso
  * cs_instance
  * cs_instancegroup
  * cs_ip_address
  * cs_loadbalancer_rule
  * cs_loadbalancer_rule_member
  * cs_network
  * cs_portforward
  * cs_project
  * cs_securitygroup
  * cs_securitygroup_rule
  * cs_sshkeypair
  * cs_staticnat
  * cs_template
  * cs_user
  * cs_vmsnapshot
- cronvar
- datadog_monitor
- deploy_helper
- docker
  * docker_login
- dpkg_selections
- elasticsearch_plugin
- expect
- find
- google
  * gce_tag
- hall
- ipify_facts
- iptables
- libvirt
  * virt_net
  * virt_pool
- maven_artifact
- openstack
  * os_auth
  * os_client_config
  * os_image
  * os_image_facts
  * os_floating_ip
  * os_ironic
  * os_ironic_node
  * os_keypair
  * os_network
  * os_network_facts
  * os_nova_flavor
  * os_object
  * os_port
  * os_project
  * os_router
  * os_security_group
  * os_security_group_rule
  * os_server
  * os_server_actions
  * os_server_facts
  * os_server_volume
  * os_subnet
  * os_subnet_facts
  * os_user
  * os_user_group
  * os_volume
- openvswitch_db
- osx_defaults
- pagerduty_alert
- pam_limits
- pear
- profitbricks
  * profitbricks
  * profitbricks_datacenter
  * profitbricks_nic
  * profitbricks_snapshot
  * profitbricks_volume
  * profitbricks_volume_attachments
- proxmox
  * proxmox
  * proxmox_template
- puppet
- pushover
- pushbullet
- rax
  * rax_clb_ssl
  * rax_mon_alarm
  * rax_mon_check
  * rax_mon_entity
  * rax_mon_notification
  * rax_mon_notification_plan
- rabbitmq
  * rabbitmq_binding
  * rabbitmq_exchange
  * rabbitmq_queue
- selinux_permissive
- sendgrid
- sensu
  * sensu_check
  * sensu_subscription
- seport
- slackpkg
- solaris_zone
- taiga_issue
- vertica
  * vertica_configuration
  * vertica_facts
  * vertica_role
  * vertica_schema
  * vertica_user
- vmware
  * vca_fw
  * vca_nat
  * vmware_cluster
  * vmware_datacenter
  * vmware_dns_config
  * vmware_dvs_host
  * vmware_dvs_portgroup
  * vmware_dvswitch
  * vmware_host
  * vmware_migrate_vmk
  * vmware_portgroup
  * vmware_target_canonical_facts
  * vmware_vm_facts
  * vmware_vm_vss_dvs_migrate
  * vmware_vmkernel
  * vmware_vmkernel_ip_config
  * vmware_vsan_cluster
  * vmware_vswitch
  * vsphere_copy
- webfaction
  * webfaction_app
  * webfaction_db
  * webfaction_domain
  * webfaction_mailbox
  * webfaction_site
- windows
  * win_acl
  * win_dotnet_ngen
  * win_environment
  * win_firewall_rule
  * win_iis_virtualdirectory
  * win_iis_webapplication
  * win_iis_webapppool
  * win_iis_webbinding
  * win_iis_website
  * win_lineinfile
  * win_nssm
  * win_package
  * win_regedit
  * win_scheduled_task
  * win_unzip
  * win_updates
  * win_webpicmd
- xenserver_facts
- zabbbix
  * zabbix_host
  * zabbix_hostmacro
  * zabbix_screen
- znode

####New Inventory scripts:

* cloudstack
* fleetctl
* openvz
* nagios_ndo
* nsot
* proxmox
* rudder
* serf

####New Lookups:

* credstash
* hashi_vault
* ini
* shelvefile

####New Filters:

* combine

####New Connection:

* docker: for talking to docker containers on the ansible controller machine without using ssh.

####New Callbacks:

* logentries: plugin to send play data to logentries service
* skippy: same as default but does not display skip messages

###Minor changes:

* Many more tests. The new API makes things more testable and we took advantage of it.
* big_ip modules now support turning off ssl certificate validation (use only for self-signed certificates).
* Consolidated code from modules using urllib2 to normalize features, TLS and SNI support.
* synchronize module's dest_port parameter now takes precedence over the ansible_ssh_port inventory setting.
* Play output is now dynamically sized to terminal with a minimum of 80 coluumns (old default).
* vars_prompt and pause are now skipped with a warning if the play is called noninteractively (i.e. pull from cron).
* Support for OpenBSD's 'doas' privilege escalation method.
* Most vault operations can now be done over multilple files.
* ansible-vault encrypt/decrypt read from stdin if no other input file is given, and can write to a given ``--output file`` (including stdout, '-').
  This lets you avoid ever writing sensitive plaintext to disk.
* ansible-vault rekey accepts the --new-vault-password-file option.
* ansible-vault now preserves file permissions on edit and rekey and defaults to restrictive permissions for other options.
* Configuration items defined as paths (local only) now all support shell style interpolations.
* Many fixes and new options added to modules, too many to list here.
* Now you can see task file and line number when using verbosity of 3 or above.
* The ``[x-y]`` host range syntax is no longer supported. Note that ``[0:1]`` matches two hosts, i.e. the range is inclusive of its endpoints.
* We now recommend the use of `pattern1,pattern2` to combine host matching patterns.
  * The use of ':' as a separator conflicts with IPv6 addresses and host ranges. It will be deprecated in the future.
  * The undocumented use of ';' as a separator is now deprecated.
* modules and callbacks have been extended to support no_log to avoid data disclosure.
* new managed_syslog option has been added to control output to syslog on managed machines, no_log supersedes this settings.
* Lookup, vars and action plugin pathing has been normalized, all now follow the same sequence to find relative files.
* We do not ignore the explicitly set login user for ssh when it matches the 'current user' anymore, this allows overriding .ssh/config when it is set
  explicitly. Leaving it unset will still use the same user and respect .ssh/config. This also means ansible_ssh_user can now return a None value.
* environment variables passed to remote shells now default to 'controller' settings, with fallback to en_US.UTF8 which was the previous default.
* add_hosts is much stricter about host name and will prevent invalid names from being added.
* ansible-pull now defaults to doing shallow checkouts with git, use `--full` to return to previous behaviour.
* random cows are more random
* when: now gets the registered var after the first iteration, making it possible to break out of item loops
* Handling of undefined variables has changed.  In most places they will now raise an error instead of silently injecting an empty string.  Use the default filter if you want to approximate the old behaviour:

    ```
    - debug: msg="The error message was: {{error_code |default('') }}"
    ```

## 1.9.4 "Dancing In the Street" - Oct 9, 2015

* Fixes a bug where yum state=latest would error if there were no updates to install.
* Fixes a bug where yum state=latest did not work with wildcard package names.
* Fixes a bug in lineinfile relating to escape sequences.
* Fixes a bug where vars_prompt was not keeping passwords private by default.
* Fix ansible-galaxy and the hipchat callback plugin to check that the host it
  is contacting matches its TLS Certificate.

## 1.9.3 "Dancing In the Street" - Sep 3, 2015

* Fixes a bug related to keyczar messing up encodings internally, resulting in decrypted
  messages coming out as empty strings.
* AES Keys generated for use in accelerated mode are now 256-bit by default instead of 128.
* Fix url fetching for SNI with python-2.7.9 or greater.  SNI does not work
  with python < 2.7.9.  The best workaround is probably to use the command
  module with curl or wget.
* Fix url fetching to allow tls-1.1 and tls-1.2 if the system's openssl library
  supports those protocols
* Fix ec2_ami_search module to check TLS Certificates
* Fix the following extras modules to check TLS Certificates:
  * campfire
  * layman
  * librarto_annotate
  * twilio
  * typetalk
* Fix docker module's parsing of docker-py version for dev checkouts
* Fix docker module to work with docker server api 1.19
* Change yum module's state=latest feature to update all packages specified in
  a single transaction.  This is the same type of fix as was made for yum's
  state=installed in 1.9.2 and both solves the same problems and with the same caveats.
* Fixed a bug where stdout from a module might be blank when there were were non-printable
  ASCII characters contained within it

## 1.9.2 "Dancing In the Street" - Jun 26, 2015

* Security fixes to check that hostnames match certificates with https urls (CVE-2015-3908)
  - get_url and uri modules
  - url and etcd lookup plugins
* Security fixes to the zone (Solaris containers), jail (bsd containers),
  and chroot connection plugins.  These plugins can be used to connect to
  their respective container types in leiu of the standard ssh connection.
  Prior to this fix being applied these connection plugins didn't properly
  handle symlinks within the containers which could lead to files intended to
  be written to or read from the container being written to or read from the
  host system instead. (CVE pending)
* Fixed a bug in the service module where init scripts were being incorrectly used instead of upstart/systemd.
* Fixed a bug where sudo/su settings were not inherited from ansible.cfg correctly.
* Fixed a bug in the rds module where a traceback may occur due to an unbound variable.
* Fixed a bug where certain remote file systems where the SELinux context was not being properly set.
* Re-enabled several windows modules which had been partially merged (via action plugins):
  - win_copy.ps1
  - win_copy.py
  - win_file.ps1
  - win_file.py
  - win_template.py
* Fix bug using with_sequence and a count that is zero.  Also allows counting backwards isntead of forwards
* Fix get_url module bug preventing use of custom ports with https urls
* Fix bug disabling repositories in the yum module.
* Fix giving yum module a url to install a package from on RHEL/CENTOS5
* Fix bug in dnf module preventing it from working when yum-utils was not already installed

## 1.9.1 "Dancing In the Street" - Apr 27, 2015

* Fixed a bug related to Kerberos auth when using winrm with a domain account.
* Fixing several bugs in the s3 module.
* Fixed a bug with upstart service detection in the service module.
* Fixed several bugs with the user module when used on OSX.
* Fixed unicode handling in some module situations (assert and shell/command execution).
* Fixed a bug in redhat_subscription when using the activationkey parameter.
* Fixed a traceback in the gce module on EL6 distros when multiple pycrypto installations are available.
* Added support for PostgreSQL 9.4 in rds_param_group
* Several other minor fixes.

## 1.9 "Dancing In the Street" - Mar 25, 2015

Major changes:

* Added kerberos support to winrm connection plugin.
* Tags rehaul: added 'all', 'always', 'untagged' and 'tagged' special tags and normalized
  tag resolution. Added tag information to --list-tasks and new --list-tags option.
* Privilege Escalation generalization, new 'Become' system and variables  now will
  handle existing and new methods. Sudo and su have been kept for backwards compatibility.
  New methods pbrun and pfexec in 'alpha' state, planned adding 'runas' for winrm connection plugin.
* Improved ssh connection error reporting, now you get back the specific message from ssh.
* Added facility to document task module return values for registered vars, both for
  ansible-doc and the docsite. Documented copy, stats and acl modules, the rest must be
  updated individually (we will start doing so incrementally).
* Optimize the plugin loader to cache available plugins much more efficiently.
  For some use cases this can lead to dramatic improvements in startup time.
* Overhaul of the checksum system, now supports more systems and more cases more reliably and uniformly.
* Fix skipped tasks to not display their parameters if no_log is specified.
* Many fixes to unicode support, standarized functions to make it easier to add to input/output boundaries.
* Added travis integration to github for basic tests, this should speed up ticket triage and merging.
* environment: directive now can also be applied to play and is inhertited by tasks, which can still override it.
* expanded facts and OS/distribution support for existing facts and improved performance with pypy.
* new 'wantlist' option to lookups allows for selecting a list typed variable vs a comma delimited string as the return.
* the shared module code for file backups now uses a timestamp resolution of seconds (previouslly minutes).
* allow for empty inventories, this is now a warning and not an error (for those using localhost and cloud modules).
* sped up YAML parsing in ansible by up to 25% by switching to CParser loader.

New Modules:

* cryptab *-- manages linux encrypted block devices*
* gce_img *-- for utilizing GCE image resources*
* gluster_volume *-- manage glusterfs volumes*
* haproxy *-- for the load balancer of same name*
* known_hosts *-- manages the ssh known_hosts file*
* lxc_container *-- manage lxc containers*
* patch *-- allows for patching files on target systems*
* pkg5 *-- installing and uninstalling packages on Solaris*
* pkg5_publisher *-- manages Solaris pkg5 repository configuration*
* postgresql_ext *-- manage postgresql extensions*
* snmp_facts *-- gather facts via snmp*
* svc *-- manages daemontools based services*
* uptimerobot *-- manage monitoring with this service*

New Filters:

* ternary: allows for trueval/falseval assignment dependent on conditional
* cartesian: returns the Cartesian product of 2 lists
* to_uuid: given a string it will return an ansible domain specific UUID
* checksum: uses the ansible internal checksum to return a hash from a string
* hash: get a hash from a string (md5, sha1, etc)
* password_hash: get a hash form as string that can be used as a password in the user module (and others)
* A whole set of ip/network manipulation filters: ipaddr,ipwrap,ipv4,ipv6ipsubnet,nthhost,hwaddr,macaddr

Other Notable Changes:

* New lookup plugins:
  * dig: does dns resolution and returns IPs.
  * url: allows pulling data from a url.

* New callback plugins:
  * syslog_json: allows logging play output to a syslog network server using json format

* Many new enhancements to the amazon web service modules:
  * ec2 now applies all specified security groups when creating a new instance.  Previously it was only applying one
  * ec2_vol gained the ability to specify the EBS volume type
  * ec2_vol can now detach volumes by specifying instance=None
  * Fix ec2_group to purge specific grants rather than whole rules
  * Added tenancy support for the ec2 module
  * rds module has gained the ability to manage tags and set charset and public accessibility
  * ec2_snapshot module gained the capability to remove snapshots
  * Add alias support for route53
  * Add private_zones support to route53
  * ec2_asg: Add wait_for_instances parameter that waits until an instance is ready before ending the ansible task
* Many new docker improvements:
  * restart_policy parameters to configure when the container automatically restarts
  * If the docker client or server doesn't support an option, the task will now fail instead of silently ignoring the option
  * Add insecure_registry parameter for connecting to registries via http
  * New parameter to set a container's domain name
  * Undeprecated docker_image module until there's replacement functionality
  * Allow setting the container's pid namespace
  * Add a pull parameter that chooses when ansible will look for more recent images in the registry
  * docker module states have been greatly enhanced.  The reworked and new states are:
    * present now creates but does not start containers
    * restarted always restarts a container
    * reloaded restarts a container if ansible detects that the configuration is different than what is specified
      * reloaded accounts for exposed ports, env vars, and volumes
  * Can now connect to the docker server using TLS
* Several source control modules had force parameters that defaulted to true.
  These have been changed to default to false so as not to accidentally lose
  work.  Playbooks that depended on the former behaviour simply need to add
  force=True to the task that needs it.  Affected modules:
  * bzr: When local modifications exist in a checkout, the bzr module used to
    default to removing the modifications on any operation.  Now the module
    will not remove the modifications unless force=yes is specified.
    Operations that depend on a clean working tree may fail unless force=yes is
    added.
  * git: When local modifications exist in a checkout, the git module will now
    fail unless force is explicitly specified.  Specifying force=yes will allow
    the module to revert and overwrite local modifications to make git actions
    succeed.
  * hg: When local modifications exist in a checkout, the hg module used to
    default to removing the modifications on any operation.  Now the module
    will not remove the modifications unless force=yes is specified.
  * subversion: When updating a checkout with local modifications, you now need
    to add force=yes so the module will revert the modifications before updating.
* New inventory scripts:
  * vbox: virtualbox
  * consul: use consul as an inventory source
* gce gained the ip_forward parameter to forward ip packets
* disk_auto_delete parameter to gce that will remove the boot disk after an instance is destroyed
* gce can now spawn instances with no external ip
* gce_pd gained the ability to choose a disk type
* gce_net gained target_tags parameter for creating firewall rules
* rax module has new parameters for making use of a boot volume
* Add scheduler_hints to the nova_compute module for optional parameters
* vsphere_guest now supports deploying guests from a template
* Many fixes for hardlink and softlink handling in file-related modules
* Implement user, group, mode, and selinux parameters for the unarchive module
* authorized_keys can now use url as a key source
* authorized_keys has a new exclusive parameter that determines if keys that weren't specified in the task
* The selinux module now sets the current running state to permissive if state='disabled'
* Can now set accounts to expire via the user module
* Overhaul of the service module to make code simpler and behave better for systems running several popular init systems
* yum module now has a parameter to refresh its cache of package metadata
* apt module gained a build_dep parameter to install a package's build dependencies
* Add parameters to the postgres modules to specify a unix socket to connect to the db
* The mount module now supports bind mounts
* Add a clone parameter to git module that allows you to get information about a remote repo even if it doesn't exist locally.
* Add a refspec argument to the git module that allows pulling commits that aren't part of a branch
* Many documentation additions and fixes.

## 1.8.4 "You Really Got Me" - Feb 19, 2015

* Fixed regressions in ec2 and mount modules, introduced in 1.8.3

## 1.8.3 "You Really Got Me" - Feb 17, 2015

* Fixing a security bug related to the default permissions set on a temporary file created when using "ansible-vault view <filename>".
* Many bug fixes, for both core code and core modules.

## 1.8.2 "You Really Got Me" - Dec 04, 2014

* Various bug fixes for packaging issues related to modules.
* Various bug fixes for lookup plugins.
* Various bug fixes for some modules (continued cleanup of postgresql issues, etc.).

* Add a clone parameter to git module that allows you to get information about a remote repo even if it doesn't exist locally.

## 1.8.1 "You Really Got Me" - Nov 26, 2014

* Various bug fixes in postgresql and mysql modules.
* Fixed a bug related to lookup plugins used within roles not finding files based on the relative paths to the roles files/ directory.
* Fixed a bug related to vars specified in plays being templated too early, resulting in incorrect variable interpolation.
* Fixed a bug related to git submodules in bare repos.

## 1.8 "You Really Got Me" - Nov 25, 2014

Major changes:

* fact caching support, pluggable, initially supports Redis (DOCS pending)
* 'serial' size in a rolling update can be specified as a percentage
* added new Jinja2 filters, 'min' and 'max' that take lists
* new 'ansible_version' variable available contains a dictionary of version info
* For ec2 dynamic inventory, ec2.ini can has various new configuration options
* 'ansible vault view filename.yml' opens filename.yml decrypted in a pager.
* no_log parameter now surpressess data from callbacks/output as well as syslog
* ansible-galaxy install -f requirements.yml allows advanced options and installs from non-galaxy SCM sources and tarballs.
* command_warnings feature will warn about when usage of the shell/command module can be simplified to use core modules - this can be enabled in ansible.cfg
* new omit value can be used to leave off a parameter when not set, like so module_name: a=1 b={{ c | default(omit) }}, would not pass value for b (not even an empty value) if c was not set.
* developers: 'baby JSON' in module responses, originally intended for writing modules in bash, is removed as a feature to simplify logic, script module remains available for running bash scripts.
* async jobs started in "fire & forget" mode can now be checked on at a later time.
* added ability to subcategorize modules for docs.ansible.com
* added ability for shipped modules to have aliases with symlinks
* added ability to deprecate older modules by starting with "_" and including "deprecated: message why" in module docs

New Modules:

- cloud
  * rax_cdb *-- manages Rackspace Cloud Database instances*
  * rax_cdb_database *-- manages Rackspace Cloud Databases*
  * rax_cdb_user *-- manages Rackspace Cloud Database users*
- monitoring
  * bigpanda *-- support for bigpanda*
  * zabbix_maintaince *-- handles outage windows with Zabbix*
- net_infrastructure
  * a10_server *-- manages server objects on A10 devices*
  * a10_service_group *-- manages service group objects on A10 devices*
  * a10_virtual_server *-- manages virtual server objects on A10 devices*
- system
  * getent  *-- read getent databases*

Some other notable changes:

* added the ability to set "instance filters" in the ec2.ini to limit results from the inventory plugin.
* upgrades for various variable precedence items and parsing related items
* added a new "follow" parameter to the file and copy modules, which allows actions to be taken on the target of a symlink rather than the symlink itself.
* if a module should ever traceback, it will return a standard error, catchable by ignore_errors, versus an 'unreachable'
* ec2_lc: added support for multiple new parameters like kernel_id, ramdisk_id and ebs_optimized.
* ec2_elb_lb: added support for the connection_draining_timeout and cross_az_load_balancing options.
* support for symbolic representations (ie. u+rw) for file permission modes (file/copy/template modules etc.).
* docker: Added support for specifying the net type of the container.
* docker: support for specifying read-only volumes.
* docker: support for specifying the API version to use for the remote connection.
* openstack modules: various improvements
* irc: ssl support for the notification module
* npm: fix flags passed to package installation
* windows: improved error handling
* setup: additional facts on System Z
* apt_repository: certificate validation can be disabled if requested
* pagerduty module: misc improvements
* ec2_lc: public_ip boolean configurable in launch configurations
* ec2_asg: fixes related to proper termination of an autoscaling group
* win_setup: total memory fact correction
* ec2_vol: ability to list existing volumes
* ec2: can set optimized flag
* various parser improvements
* produce a friendly error message if the SSH key is too permissive
* ec2_ami_search: support for SSD and IOPS provisioned EBS images
* can set ansible_sudo_exe as an inventory variable which allows specifying
  a different sudo (or equivalent) command
* git module: Submodule handling has changed.  Previously if you used the
  ``recursive`` parameter to handle submodules, ansible would track the
  submodule upstream's head revision.  This has been changed to checkout the
  version of the submodule specified in the superproject's git repository.
  This is inline with what git submodule update does.  If you want the old
  behaviour use the new module parameter track_submodules=yes
* Checksumming of transferred files has been made more portable and now uses
  the sha1 algorithm instead of md5 to be compatible with FIPS-140.
  - As a small side effect, the fetch module no longer returns a useful value
    in remote_md5.  If you need a replacement, switch to using remote_checksum
    which returns the sha1sum of the remote file.
* ansible-doc CLI tool contains various improvements for working with different terminals

And various other bug fixes and improvements ...


## 1.7.2 "Summer Nights" - Sep 24, 2014

- Fixes a bug in accelerate mode which caused a traceback when trying to use that connection method.
- Fixes a bug in vault where the password file option was not being used correctly internally.
- Improved multi-line parsing when using YAML literal blocks (using > or |).
- Fixed a bug with the file module and the creation of relative symlinks.
- Fixed a bug where checkmode was not being honoured during the templating of files.
- Other various bug fixes.

## 1.7.1 "Summer Nights" - Aug 14, 2014

- Security fix to disallow specifying 'args:' as a string, which could allow the insertion of extra module parameters through variables.
- Performance enhancements related to previous security fixes, which could cause slowness when modules returned very large JSON results. This specifically impacted the unarchive module frequently, which returns the details of all unarchived files in the result.
- Docker module bug fixes:
  * Fixed support for specifying rw/ro bind modes for volumes
  * Fixed support for allowing the tag in the image parameter
- Various other bug fixes

## 1.7 "Summer Nights" - Aug 06, 2014

Major new features:

* Windows support (alpha) using native PowerShell remoting
* Tasks can now specify `run_once: true`, meaning they will be executed exactly once. This can be combined with delegate_to to trigger actions you want done just the one time versus for every host in inventory.

New inventory scripts:

* SoftLayer
* Windows Azure

New Modules:

- cloud
  * azure
  * rax_meta
  * rax_scaling_group
  * rax_scaling_policy
- windows
  * *version of setup module*
  * *version of slurp module*
  * win_feature
  * win_get_url
  * win_group
  * win_msi
  * win_ping
  * win_service
  * win_user

Other notable changes:

* Security fixes
  - Prevent the use of lookups when using legacy "{{ }}" syntax around variables and with_* loops.
  - Remove relative paths in TAR-archived file names used by ansible-galaxy.
* Inventory speed improvements for very large inventories.
* Vault password files can now be executable, to support scripts that fetch the vault password.


## 1.6.10 "And the Cradle Will Rock" - Jul 25, 2014

- Fixes an issue with the copy module when copying a directory that fails when changing file attributes and the target file already exists
- Improved unicode handling when splitting args

## 1.6.9 "And the Cradle Will Rock" - Jul 24, 2014

- Further improvements to module parameter parsing to address additional regressions caused by security fixes

## 1.6.8 "And the Cradle Will Rock" - Jul 22, 2014

- Corrects a regression in the way shell and command parameters were being parsed

## 1.6.7 "And the Cradle Will Rock" - Jul 21, 2014

- Security fixes:
  * Strip lookup calls out of inventory variables and clean unsafe data
    returned from lookup plugins (CVE-2014-4966)
  * Make sure vars don't insert extra parameters into module args and prevent
    duplicate params from superseding previous params (CVE-2014-4967)

## 1.6.6 "And the Cradle Will Rock" - Jul 01, 2014

- Security updates to further protect against the incorrect execution of untrusted data

## 1.6.4, 1.6.5 "And the Cradle Will Rock" - Jun 25, 2014

- Security updates related to evaluation of untrusted remote inputs

## 1.6.3 "And the Cradle Will Rock" - Jun 09, 2014

- Corrects a regression where handlers were run across all hosts, not just those that triggered the handler.
- Fixed a bug in which modules did not support properly moving a file atomically when su was in use.
- Fixed two bugs related to symlinks with directories when using the file module.
- Fixed a bug related to MySQL master replication syntax.
- Corrects a regression in the order of variable merging done by the internal runner code.
- Various other minor bug fixes.

## 1.6.2 "And the Cradle Will Rock" - May 23, 2014

- If an improper locale is specified, core modules will now automatically revert to using the 'C' locale.
- Modules using the fetch_url utility will now obey proxy environment variables.
- The SSL validation step in fetch_url will likewise obey proxy settings, however only proxies using the http protocol are supported.
- Fixed multiple bugs in docker module related to version changes upstream.
- Fixed a bug in the ec2_group module where egress rules were lost when a VPC was specified.
- Fixed two bugs in the synchronize module:
  * a trailing slash might be lost when calculating relative paths, resulting in an incorrect destination.
  * the sync might use the inventory directory incorrectly instead of the playbook or role directory.
- Files will now only be chown'd on an atomic move if the src/dest uid/gid do not match.

## 1.6.1 "And the Cradle Will Rock" - May 7, 2014

- Fixed a bug in group_by, where systems were being grouped incorrectly.
- Fixed a bug where file descriptors may leak to a child process when using accelerate.
- Fixed a bug in apt_repository triggered when python-apt not being installed/available.
- Fixed a bug in the apache2_module module, where modules were not being disabled correctly.

## 1.6 "And the Cradle Will Rock" - May 5, 2014

Major features/changes:

* The deprecated legacy variable templating system has been finally removed.  Use {{ foo }} always not $foo or ${foo}.
* Any data file can also be JSON.  Use sparingly -- with great power comes great responsibility.  Starting file with "{" or "[" denotes JSON.
* Added 'gathering' param for ansible.cfg to change the default gather_facts policy.
* Accelerate improvements:
  - multiple users can connect with different keys, when `accelerate_multi_key = yes` is specified in the ansible.cfg.
  - daemon lifetime is now based on the time from the last activity, not the time from the daemon's launch.
* ansible-playbook now accepts --force-handlers to run handlers even if tasks result in failures.
* Added VMWare support with the vsphere_guest module.

New Modules:

- files
  * replace
- packaging
  * apt_rpm
  * composer *(PHP)*
  * cpanm *(Perl)*
  * homebrew_cask *(OS X)*
  * homebrew_tap *(OS X)*
  * layman
  * portage
- monitoring
  * librato_annotation
  * logentries
  * rollbar_deployment
- notification
  * nexmo *(SMS)*
  * slack *(Slack.com)*
  * sns *(Amazon)*
  * twilio *(SMS)*
  * typetalk *(Typetalk.in)*
- system
  * alternatives
  * capabilities
  * debconf
  * locale_gen
  * ufw
- net_infrastructure
  * bigip_facts
  * dnssimple
  * lldp
- web_infrastructure
  * apache2_module
- cloud
  * digital_ocean_domain
  * digital_ocean_sshkey 
  * ec2_asg *(configure autoscaling groups)*
  * ec2_metric_alarm
  * ec2_scaling_policy
  * rax_identity
  * rax_cbs *(cloud block storage)*
  * rax_cbs_attachments
  * vsphere_guest

Other notable changes:

* example callback plugin added for hipchat
* added example inventory plugin for vcenter/vsphere
* added example inventory plugin for doing really trivial inventory from SSH config files
* libvirt module now supports destroyed and paused as states
* s3 module can specify metadata
* security token additions to ec2 modules
* setup module code moved into module_utils/, facts now accessible by other modules  
* synchronize module sets relative dirs based on inventory or role path
* misc bugfixes and other parameters
* the ec2_key module now has wait/wait_timeout parameters
* added version_compare filter (see docs)
* added ability for module documentation YAML to utilize shared module snippets for common args
* apt module now accepts "deb" parameter to install local dpkg files
* regex_replace filter plugin added
* added an inventory script for Docker
* added an inventory script for Abiquo
* the get_url module now accepts url_username and url_password as parameters, so sites which require
  authentication no longer need to have them embedded in the url
* ... to be filled in from changelogs ...

## 1.5.5 "Love Walks In" - April 18, 2014

- Security fix for vault, to ensure the umask is set to a restrictive mode before creating/editing vault files.
- Backported apt_repository security fixes relating to filename/mode upon sources list file creation.

## 1.5.4 "Love Walks In" - April 1, 2014

- Security fix for safe_eval, which further hardens the checking of the evaluation function.
- Changing order of variable precedence for system facts, to ensure that inventory variables take precedence over any facts that may be set on a host.

## 1.5.3 "Love Walks In" - March 13, 2014

- Fix validate_certs and run_command errors from previous release
- Fixes to the git module related to host key checking

## 1.5.2 "Love Walks In" - March 11, 2014

- Fix module errors in airbrake and apt from previous release

## 1.5.1 "Love Walks In" - March 10, 2014

- Force command action to not be executed by the shell unless specifically enabled.
- Validate SSL certs accessed through urllib*.
- Implement new default cipher class AES256 in ansible-vault.
- Misc bug fixes.

## 1.5 "Love Walks In" - February 28, 2014

Major features/changes:

* when_foo which was previously deprecated is now removed, use "when:" instead.  Code generates appropriate error suggestion.
* include + with_items which was previously deprecated is now removed, ditto.  Use with_nested / with_together, etc.
* only_if, which is much older than when_foo and was deprecated, is similarly removed.
* ssh connection plugin is now more efficient if you add 'pipelining=True' in ansible.cfg under [ssh_connection], see example.cfg
* localhost/127.0.0.1 is not required to be in inventory if referenced, if not in inventory, it does not implicitly appear in the 'all' group.
* git module has new parameters (accept_hostkey, key_file, ssh_opts) to ease the usage of git and ssh protocols. 
* when using accelerate mode, the daemon will now be restarted when specifying a different remote_user between plays.
* added no_log: option for tasks. When used, no logging information will be sent to syslog during the module execution.
* acl module now handles 'default' and allows for either shorthand entry or specific fields per entry section
* play_hosts is a new magic variable to provide a list of hosts in scope for the current play.
* ec2 module now accepts 'exact_count' and 'count_tag' as a way to enforce a running number of nodes by tags.
* all ec2 modules that work with Eucalyptus also now support a 'validate_certs' option, which can be set to 'off' for installations using self-signed certs.
* Start of new integration test infrastructure (WIP, more details TBD)
* if repoquery is unavailable, the yum module will automatically attempt to install yum-utils
* ansible-vault: a framework for encrypting your playbooks and variable files 
* added support for privilege escalation via 'su' into bin/ansible and bin/ansible-playbook and associated keywords 'su', 'su_user', 'su_pass' for tasks/plays

New modules:

- cloud
  * docker_image
  * ec2_elb_lb
  * ec2_key
  * ec2_snapshot
  * rax_dns
  * rax_dns_record
  * rax_files
  * rax_files_objects
  * rax_keypair
  * rax_queue
- messaging
  * rabbitmq_policy
- system
  * at
- utilities
  * assert

Other notable changes (many new module params & bugfixes may not be listed):

* no_reboot is now defaulted to "no" in the ec2_ami module to ensure filesystem consistency in the resulting AMI.
* sysctl module overhauled
* authorized_key module overhauled
* synchronized module now handles local transport better
* apt_key module now ignores case on keys
* zypper_repository now skips on check mode
* file module now responds to force behavior when dealing with hardlinks
* new lookup plugin 'csvfile'
* fixes to allow hash_merge behavior to work with dynamic inventory
* mysql module will use port argument on dump/import
* subversion module now ignores locale to better intercept status messages
* rax api_key argument is no longer logged
* backwards/forwards compatibility for OpenStack modules, 'quantum' modules grok neutron renaming
* hosts properly uniqueified if appearing in redundant groups
* hostname module support added for ScientificLinux
* ansible-pull can now show live stdout and pass verbosity levels to ansible-playbook
* ec2 instances can now be stopped or started
* additional volumes can be created when creating new ec2 instances
* user module can move a home directory
* significant enhancement and cleanup of rackspace modules
* ansible_ssh_private_key_file can be templated
* docker module updated to support docker-py 0.3.0
* various other bug fixes
* md5 logic improved during sudo operation
* support for ed25519 keys in authorized_key module
* ability to set directory permissions during a recursive copy (directory_mode parameter)

## 1.4.5 "Could This Be Magic" - February 12, 2014

- fixed issue with permissions being incorrect on fireball/accelerate keys when the umask setting was too loose.

## 1.4.4 "Could This Be Magic" - January 6, 2014

- fixed a minor issue with newer versions of pip dropping the "use-mirrors" parameter.

## 1.4.3 "Could This Be Magic" - December 20, 2013

- Fixed role_path parsing from ansible.cfg
- Fixed default role templates

## 1.4.2 "Could This Be Magic" - December 18, 2013

* Fixed a few bugs related to unicode
* Fixed errors in the ssh connection method with large data returns
* Miscellaneous fixes for a few modules
* Add the ansible-galaxy command

## 1.4.1 "Could This Be Magic" - November 27, 2013

* Misc fixes to accelerate mode and various modules.

## 1.4 "Could This Be Magic" - November 21, 2013

Highlighted new features:

* Added do-until feature, which can be used to retry a failed task a specified number of times with a delay in-between the retries.
* Added failed_when option for tasks, which can be used to specify logical statements that make it easier to determine when a task has failed, or to make it easier to ignore certain non-zero return codes for some commands.
* Added the "subelement" lookup plugin, which allows iteration of the keys of a dictionary or items in a list.
* Added the capability to use either paramiko or ssh for the initial setup connection of an accelerated playbook.
* Automatically provide advice on common parser errors users encounter.
* Deprecation warnings are now shown for legacy features: when_integer/etc, only_if, include+with_items, etc.  Can be disabled in ansible.cfg
* The system will now provide helpful tips around possible YAML syntax errors increasing ease of use for new users.
* warnings are now shown for using {{ foo }} in loops and conditionals, and suggest leaving the variable expressions bare as per docs.
* The roles search path is now configurable in ansible.cfg.  'roles_path' in the config setting.
* Includes with parameters can now be done like roles for consistency:  - { include: song.yml, year:1984, song:'jump' }
* The name of each role is now shown before each task if roles are being used
* Adds a "var=" option to the debug module for debugging variable data.  "debug: var=hostvars['hostname']" and "debug: var=foo" are all valid syntax.
* Variables in {{ format }} can be used as references even if they are structured data
* Can force binding of accelerate to ipv6 ports.
* the apt module will auto-install python-apt if not present rather than requiring a manual installation
* the copy module is now recursive if the local 'src' parameter is a directory.
* syntax checks now scan included task and variable files as well as main files

New modules and plugins.

- cloud
  * docker *- instantiates/removes/manages docker containers*
  * ec2_eip *-- manage AWS elastic IPs*
  * ec2_vpc *-- manage ec2 virtual private clouds*
  * elasticcache *-- Manages clusters in Amazon Elasticache*
  * ovirt *-- VM lifecycle controls for ovirt*
  * rax_network *-- sets up Rackspace networks*
  * rax_facts *-- retrieve facts about a Rackspace Cloud Server*
  * rax_clb_nodes *-- manage Rackspace cloud load balanced nodes*
  * rax_clb *-- manages Rackspace cloud load balancers*
- files
  * acl *-- set or get acls on a file*
  * synchronize *-- a useful wraper around rsyncing trees of files*
  * unarchive *-- pushes and extracts tarballs*
- system
  * blacklist *-- add or remove modules from the kernel blacklist*
  * firewalld *-- manage the firewalld configuration*
  * hostname *-- sets the systems hostname*
  * modprobe *-- manage kernel modules on systems that support modprobe/rmmod*
  * open_iscsi *-- manage targets on an initiator using open-iscsi*
- utilities
  * include_vars *-- dynamically load variables based on conditions.*
- packaging
  * swdepot *-- a module for working with swdepot*
  * urpmi *-- work with urpmi packages*
  * zypper_repository *-- adds or removes Zypper repositories*
- notification
  * grove *-- notifies to Grove hosted IRC channels*
- web_infrastructure
  * ejabberd_user *-- add and remove users to ejabberd*
  * jboss *-- deploys or undeploys apps to jboss*
- source_control
  * github_hooks *-- manages GitHub service hooks*
- net_infrastructure
  * bigip_monitor_http *-- manages F5 BIG-IP LTM http monitors*
  * bigip_monitor_tcp *-- manages F5 BIG-IP LTM TCP monitors*
  * bigip_node *-- manages F5 BIG-IP LTM nodes*
  * bigip_pool_member *-- manages F5 BIG-IP LTM pool members*
  * openvswitch_port
  * openvswitch_bridge

Plugins:

* jail connection module (FreeBSD)
* lxc connection module
* added inventory script for listing FreeBSD jails 
* added md5 as a Jinja2 filter:  {{ path | md5 }}
* added a fileglob filter that will return files matching a glob pattern.  with_items: "/foo/pattern/*.txt | fileglob"
* 'changed' filter returns whether a previous step was changed easier.  when: registered_result | changed
* DOCS NEEDED: 'unique' and 'intersect' filters are added for dealing with lists.
* DOCS NEEDED: new lookup plugin added for etcd
* a 'func' connection type to help people migrating from func/certmaster.

Misc changes (all module additions/fixes may not listed):

* (docs pending) New features for accelerate mode: configurable timeouts and a keepalives for long running tasks.
* Added a `delimiter` field to the assemble module.
* Added `ansible_env` to the list of facts returned by the setup module.
* Added `state=touch` to the file module, which functions similarly to the command-line version of `touch`.
* Added a -vvvv level, which will show SSH client debugging information in the event of a failure.
* Includes now support the more standard syntax, similar to that of role includes and dependencies. 
* Changed the `user:` parameter on plays to `remote_user:` to prevent confusion with the module of the same name.  Still backwards compatible on play parameters.
* Added parameter to allow the fetch module to skip the md5 validation step ('validate_md5=false'). This is useful when fetching files that are actively being written to, such as live log files.
* Inventory hosts are used in the order they appear in the inventory.
* in hosts: foo[2-5] type syntax, the iterators now are zero indexed and the last index is non-inclusive, to match Python standards.
* There is now a way for a callback plugin to disable itself.  See osx_say example code for an example.
* Many bugfixes to modules of all types.
* Complex arguments now can be used with async tasks
* SSH ControlPath is now configurable in ansible.cfg.  There is a limit to the lengths of these paths, see how to shorten them in ansible.cfg.
* md5sum support on AIX with csum.
* Extremely large documentation refactor into subchapters
* Added 'append_privs' option to the mysql_user module
* Can now update (temporarily change) host variables using the "add_host" module for existing hosts.
* Fixes for IPv6 addresses in inventory text files
* name of executable can be passed to pip/gem etc, for installing under *different* interpreters
* copy of ./hacking/env-setup added for fish users, ./hacking/env-setup.fish
* file module more tolerant of non-absolute paths in softlinks.
* miscellaneous fixes/upgrades to async polling logic.
* conditions on roles now pass to dependent roles
* ansible_sudo_pass can be set in a host variable if desired
* misc fixes for the pip an easy_install modules
* support for running handlers that have parameterized names based on role parameters
* added support for compressing MySQL dumps and extracting during import
* Boto version compatibility fixes for the EC2 inventory script
* in the EC2 inventory script, a group 'EC2' and 'RDS' contains EC2 and RDS hosts.
* umask is enforced by the cron module
* apt packages that are not-removed and not-upgraded do not count as changes
* the assemble module can now use src files from the local server and copy them over dynamically
* authorization code has been standardized between Amazon cloud modules
* the wait_for module can now also wait for files to exist or a regex string to exist in a file
* leading ranges are now allowed in ranged hostname patterns, ex: [000-250].example.com
* pager support added to ansible-doc (so it will auto-invoke less, etc)
* misc fixes to the cron module
* get_url module now understands content-disposition headers for deciding filenames
* it is possible to have subdirectories in between group_vars/ and host_vars/ and the final filename, like host_vars/rack42/asdf for the variables for host 'asdf'.  The intermediate directories are ignored, and do not put a file in there twice.

## 1.3.4 "Top of the World" (reprise) - October 29, 2013

* Fixed a bug in the copy module, where a filename containing the string "raw" was handled incorrectly
* Fixed a bug in accelerate mode, where copying a zero-length file out would fail

## 1.3.3 "Top of the World" (reprise) - October 9, 2013

Additional fixes for accelerate mode.

## 1.3.2 "Top of the World" (reprise) - September 19th, 2013

Multiple accelerate mode fixes:

* Make packet reception less greedy, so multiple frames of data are not consumed by one call.
* Adding two timeout values (one for connection and one for data reception timeout).
* Added keepalive packets, so async mode is no longer required for long-running tasks.
* Modified accelerate daemon to use the verbose logging level of the ansible command that started it.
* Fixed bug where accelerate would not work in check-mode.
* Added a -vvvv level, which will show SSH client debugging information in the event of a failure.
* Fixed bug in apt_repository module where the repository cache was not being updated.
* Fixed bug where "too many open files" errors would be encountered due to pseudo TTY's not being closed properly.

## 1.3.1 "Top of the World" (reprise) - September 16th, 2013

Fixing a bug in accelerate mode whereby the gather_facts step would always be run via sudo regardless of the play settings.

## 1.3 "Top of the World" - September 13th, 2013

Highlighted new features:

* accelerated mode: An enhanced fireball mode that requires zero bootstrapping and fewer requirements plus adds capabilities like sudo commands.
* role defaults: Allows roles to define a set of variables at the lowest priority. These variables can be overridden by any other variable.
* new /etc/ansible/facts.d allows JSON or INI-style facts to be provided from the remote node, and supports executable fact programs in this dir. Files must end in *.fact.
* added the ability to make undefined template variables raise errors (see ansible.cfg)
* (DOCS PENDING) sudo: True/False and sudo_user: True/False can be set at include and role level
* added changed_when: (expression) which allows overriding whether a result is changed or not and can work with registered expressions
* --extra-vars can now take a file as input, e.g., "-e @filename" and can also be formatted as YAML
* external inventory scripts may now return host variables in one pass, which allows them to be much more efficient for large numbers of hosts
* if --forks exceeds the numbers of hosts, it will be automatically reduced. Set forks to 0 and you get "as many forks as I have hosts" out of the box.
* enabled error_on_undefined_vars by default, which will make errors in playbooks more obvious
* role dependencies -- one role can now pull in another, with parameters of its own.
* added the ability to have tasks execute even during a check run (always_run).
* added the ability to set the maximum failure percentage for a group of hosts.

New modules:

- notifications
  * datadog_event *-- send data to datadog*
- cloud
  * digital_ocean *-- module for DigitalOcean provisioning that also includes inventory support*
  * rds *-- Amazon Relational Database Service*
  * linode *-- modules for Linode provisioning that also includes inventory support*
  * route53 *-- manage Amazon DNS entries*
  * ec2_ami *-- manages (and creates!) ec2 AMIs*
- database
  * mysql_replication *-- manages mysql replication settings for masters/slaves*
  * mysql_variables *-- manages mysql runtime variables*
  * redis *-- manages redis databases (slave mode and flushing data)*
- net_infrastructure
  * arista_interface
  * arista_l2interface
  * arista_lag
  * arista_vlan
  * dnsmadeeasy *-- manipulate DNS Made Easy records*
- system
  * stat *-- reports on stat(istics) of remote files, for use with 'register'*
- web_infrastructure
  * htpasswd *-- manipulate htpasswd files*
- packaging
  * apt_repository *-- rewritten to remove dependencies*
  * rpm_key *-- adds or removes RPM signing keys*
- monitoring
  * boundary_meter *-- adds or removes boundary.com meters*
- files
  * xattr *-- manages extended attributes on files*

Misc changes:

* return 3 when there are hosts that were unreachable during a run
* the yum module now supports wildcard values for the enablerepo argument
* added an inventory script to pull host information from Zabbix
* async mode no longer allows with_* lookup plugins due to incompatibilities
* Added OpenRC support (Gentoo) to the service module
* ansible_ssh_user value is available to templates
* added placement_group parameter to ec2 module
* new sha256sum parameter added to get_url module for checksum validation
* search for mount binaries in system path and sbin vs assuming path
* allowed inventory file to be read from a pipe
* added Solaris distribution facts
* fixed bug along error path in quantum_network module
* user password update mode is controllable in user module now (at creation vs. every time)
* added check mode support to the OpenBSD package module
* Fix for MySQL 5.6 compatibility
* HP UX virtualization facts
* fixed some executable bits in git
* made rhn_register module compatible with EL5
* fix for setup module epoch time on Solaris
* sudo_user is now expanded later, allowing it to be set at inventory scope
* mongodb_user module changed to also support MongoDB 2.2
* new state=hard option added to the file module for hardlinks vs softlinks
* fixes to apt module purging option behavior
* fixes for device facts with multiple PCI domains
* added "with_inventory_hostnames" lookup plugin, which can take a pattern and loop over hostnames matching the pattern and is great for use with delegate_to and so on
* ec2 module supports adding to multiple security groups
* cloudformation module includes fixes for the error path, and the 'wait_for' parameter was removed
* added --only-if-changed to ansible-pull, which runs only if the repo has changes (not default)
* added 'mandatory', a Jinja2 filter that checks if a variable is defined: {{ foo|mandatory }}
* added support for multiple size formats to the lvol module
* timing reporting on wait_for module now includes the delay time
* IRC module can now send a server password
* "~" now expanded on each component of configured plugin paths
* fix for easy_install module when dealing with virtualenv
* rackspace module now explicitly indicates rackspace vs vanilla openstack
* add_host module does not report changed=True any longer
* explanatory error message when using fireball with sudo has been improved
* git module now automatically pulls down git submodules
* negated patterns do not require "all:!foo", you can just say "!foo" now to select all not foos
* fix for Debian services always reporting changed when toggling enablement bit
* roles files now tolerate files named 'main.yaml' and 'main' in addition to main.yml
* some help cleanup to command line flags on scripts
* force option reinstated for file module so it can create symlinks to non-existent files, etc.
* added termination support to ec2 module
* --ask-sudo-pass or --sudo-user does not enable all options to use sudo in ansible-playbook
* include/role conditionals are added ahead of task conditionals so they can short circuit properly
* added pipes.quote in various places so paths with spaces are better tolerated
* error handling while executing Jinja2 filters has been improved
* upgrades to atomic replacement logic when copying files across partitions/etc
* mysql user module can try to login before requiring explicit password
* various additional options added to supervisorctl module
* only add non unique parameter on group creation when required
* allow rabbitmq_plugin to specify a non-standard RabbitMQ path
* authentication fixes to keystone_user module
* added IAM role support to EC2 module
* fixes for OpenBSD package module to avoid shell expansion
* git module upgrades to allow --depth and --version to be used together
* new lookup plugin, "with_flattened"
* extra vars (-e) variables can be used in playbook include paths
* improved reporting for invalid sudo passwords
* improved reporting for inability to find a suitable tmp location
* require libselinux-python to perform file operations if SELinux is operational
* ZFS module fixes for byte display constants and handling paths with spaces
* setup module more tolerant of gathering facts against things it does not have permission to read
* can specify name=* state=latest to update all yum modules
* major speedups to the yum module for default cases
* ec2_facts module will now run in check mode
* sleep option on service module for sleeping between stop/restart
* fix for IPv6 facts on BSD
* added Jinja2 filters: skipped, whether a result was skipped
* added Jinja2 filters: quote, quotes a string if it needs to be quoted
* allow force=yes to affect apt upgrades
* fix for saving conditionals in variable names
* support for multiple host ranges in INI inventory, e.g., db[01:10:3]node-[01:10]
* fixes/improvements to cron module
* add user_install=no option to gem module to install gems system wide
* added raw=yes to allow copying without python on remote machines
* added with_indexed_items lookup plugin
* Linode inventory plugin now significantly faster
* added recurse=yes parameter to pacman module for package removal
* apt_key module can now target specific keyrings (keyring=filename)
* ec2 module change reporting improved
* hg module now expands user paths (~)
* SSH connection type known host checking now can process hashed known_host files
* lvg module now checks for executables in more correct locations
* copy module now works correctly with sudo_user
* region parameter added to ec2_elb module
* better default XMPP module message types
* fixed conditional tests against raw booleans
* mysql module grant removal is now smarter
* apt-remove is now forced to be non-interactive
* support ; comments in INI file module
* fixes to callbacks WRT async output (fire and forget tasks now trigger callbacks!)
* folder support for s3 module
* added new example inventory plugin for Red Hat OpenShift
* and other misc. bugfixes

## 1.2.3 "Hear About It Later" (reprise) -- Aug 21, 2013

* Local security fixes for predictable file locations for ControlPersist and retry file paths on shared machines
on operating systems without kernel symlink/hardlink protections.

## 1.2.2 "Hear About It Later" (reprise) -- July 4, 2013

* Added a configuration file option [paramiko_connection] record_host_keys which allows the code that paramiko uses
to update known_hosts to be disabled.  This is done because paramiko can be very slow at doing this if you have a
large number of hosts and some folks may not want this behavior.  This can be toggled independently of host key checking
and does not affect the ssh transport plugin.  Use of the ssh transport plugin is preferred if you have ControlPersist
capability, and Ansible by default in 1.2.1 and later will autodetect.

## 1.2.1 "Hear About It Later" -- July 4, 2013

* Connection default is now "smart", which discovers if the system openssh can support ControlPersist, and uses
  it if so, if not falls back to paramiko.
* Host key checking is on by default.  Disable it if you like by adding host_key_checking=False in the [default]
  section of /etc/ansible/ansible.cfg or ~/ansible.cfg or by exporting ANSIBLE_HOST_KEY_CHECKING=False
* Paramiko now records host keys it was in contact with host key checking is on.  It is somewhat sluggish when doing this,
  so switch to the 'ssh' transport if this concerns you.

## 1.2 "Right Now" -- June 10, 2013

Core Features:

* capability to set 'all_errors_fatal: True' in a playbook to force any error to stop execution versus
  a whole group or serial block needing to fail
  usable, without breaking the ability to override in ansible
* ability to use variables from {{ }} syntax in mainline playbooks, new 'when' conditional, as detailed
  in documentation.  Can disable old style replacements in ansible.cfg if so desired, but are still active
  by default.
* can set ansible_ssh_private_key_file as an inventory variable (similar to ansible_ssh_host, etc)
* 'when' statement can be affixed to task includes to auto-affix the conditional to each task therein
* cosmetic: "*****" banners in ansible-playbook output are now constant width
* --limit can now be given a filename (--limit @filename) to constrain a run to a host list on disk
* failed playbook runs will create a retry file in /var/tmp/ansible usable with --limit
* roles allow easy arrangement of reusable tasks/handlers/files/templates
* pre_tasks and post_tasks allow for separating tasks into blocks where handlers will fire around them automatically
* "meta: flush_handler" task capability added for when you really need to force handlers to run
* new --start-at-task option to ansible playbook allows starting at a specific task name in a long playbook
* added a log file for ansible/ansible-playbook, set 'log_path' in the configuration file or ANSIBLE_LOG_PATH in environment
* debug mode always outputs debug in playbooks, without needing to specify -v
* external inventory script added for Spacewalk / Red Hat Satellite servers
* It is now possible to feed JSON structures to --extra-vars.  Pass in a JSON dictionary/hash to feed in complex data.
* group_vars/ and host_vars/ directories can now be kept alongside the playbook as well as inventory (or both!)
* more filters: ability to say {{ foo|success }} and {{ foo|failed }} and when: foo|success and when: foo|failed
* more filters: {{ path|basename }} and {{ path|dirname }}
* lookup plugins now use the basedir of the file they have included from, avoiding needs of ../../../ in places and
increasing the ease at which things can be reorganized.

Modules added:

- cloud
  * rax *-- module for creating instances in the rackspace cloud (uses pyrax)*
- packages
  * npm *-- node.js package management*
  * pkgng *-- next-gen package manager for FreeBSD*
  * redhat_subscription *-- manage Red Hat subscription usage*
  * rhn_register *-- basic RHN registration*
  * zypper *(SuSE)*
- database
  * postgresql_priv *-- manages postgresql privileges*
- networking
  * bigip_pool *-- load balancing with F5s*
  * ec2_elb *-- add and remove machines from ec2 elastic load balancers*
- notification
  * hipchat *-- send notification events to hipchat*
  * flowdock *-- send messages to flowdock during playbook runs*
  * campfire *-- send messages to campfire during playbook runs*
  * mqtt *-- send messages to the Mosquitto message bus*
  * irc *-- send messages to IRC channels*
  * filesystem *-- a wrapper around mkfs*
  * jabber *-- send jabber chat messages*
  * osx_say *-- make OS X say things out loud*
- openstack
  * glance_image
  * nova_compute
  * nova_keypair
  * keystone_user
  * quantum_floating_ip
  * quantum_floating_ip_associate
  * quantum_network
  * quantum_router
  * quantum_router_gateway
  * quantum_router_interface
  * quantum_subnet
- monitoring
  * airbrake_deployment *-- notify airbrake of new deployments*
  * monit
  * newrelic_deployment *-- notifies newrelic of new deployments*
  * pagerduty
  * pingdom
- utility
  * set_fact *-- sets a variable, which can be the result of a template evaluation*

Modules removed

* vagrant -- can't be compatible with both versions at once, just run things though the vagrant provisioner in vagrant core

Bugfixes and Misc Changes:

* service module happier if only enabled=yes|no specified and no state
* mysql_db: use --password= instead of -p in dump/import so it doesn't go interactive if no pass set
* when using -c ssh and the ansible user is the current user, don't pass a -o to allow SSH config to be
* overwrite parameter added to the s3 module
* private_ip parameter added to the ec2 module
* $FILE and $PIPE now tolerate unicode
* various plugin loading operations have been made more efficient
* hostname now uses platform.node versus socket.gethostname to be more consistent with Unix 'hostname'
* fix for SELinux operations on Unicode path names
* inventory directory locations now ignore files with .ini extensions, making hybrid inventory easier
* copy module in check-mode now reports back correct changed status when used with force=no
* added avail. zone to ec2 module
* fixes to the hash variable merging logic if so enabled in the main settings file (default is to replace, not merge hashes)
* group_vars and host_vars files can now end in a .yaml or .yml extension, (previously required no extension, still favored)
* ec2vol module improvements
* if the user module is told to generate the ssh key, the key generated is now returned in the results
* misc fixes to the Riak module
* make template module slightly more efficient
* base64encode / decode filters are now available to templates
* libvirt module can now work with multiple different libvirt connection URIs
* fix for postgresql password escaping
* unicode fix for shlex.split in some cases
* apt module upgrade logic improved
* URI module now can follow redirects
* yum module can now install off http URLs
* sudo password now defaults to ssh password if you ask for both and just hit enter on the second prompt
* validate feature on copy and template module, for example, running visudo prior to copying the file over
* network facts upgraded to return advanced configs (bonding, etc)
* region support added to ec2 module
* riak module gets a wait for ring option
* improved check mode support in the file module
* exception handling added to handle scenario when attempt to log to systemd journal fails
* fix for upstart handling when toggling the enablement and running bits at the same time
* when registering a task with a conditional attached, and the task is skipped by the conditional,
the variable is still registered for the host, with the attribute skipped: True.
* delegate_to tasks can look up ansible_ssh_private_key_file variable from inventory correctly now
* s3 module takes a 'dest' parameter to change the destination for uploads
* apt module gets a cache_valid_time option to avoid redundant cache updates
* ec2 module better understands security groups
* fix for postgresql codec usage
* setup module now tolerant of OpenVZ interfaces
* check mode reporting improved for files and directories
* doc system now reports on module requirements
* group_by module can now also make use of globally scoped variables
* localhost and 127.0.0.1 are now fuzzy matched in inventory (are now more or less interchangeable)
* AIX improvements/fixes for users, groups, facts
* lineinfile now does atomic file replacements
* fix to not pass PasswordAuthentication=no in the config file unnecessarily for SSH connection type
* for authorized_key on Debian Squeeze
* fixes for apt_repository module reporting changed incorrectly on certain repository types
* allow the virtualenv argument to the pip module to be a pathname
* service pattern argument now correctly read for BSD services
* fetch location can now be controlled more directly via the 'flat' parameter.
* added basename and dirname as Jinja2 filters available to all templates
* pip works better when sudoing from unprivileged users
* fix for user creation with groups specification reporting 'changed' incorrectly in some cases
* fix for some unicode encoding errors in outputing some data in verbose mode
* improved FreeBSD, NetBSD and Solaris facts
* debug module always outputs data without having to specify -v
* fix for sysctl module creating new keys (must specify checks=none)
* NetBSD and OpenBSD support for the user and groups modules
* Add encrypted password support to password lookup

## 1.1 "Mean Street" -- 4/2/2013

Core Features

* added --check option for "dry run" mode
* added --diff option to show how templates or copied files change, or might change
* --list-tasks for the playbook will list the tasks without running them
* able to set the environment by setting "environment:" as a dictionary on any task (go proxy support!)
* added ansible_ssh_user and ansible_ssh_pass for per-host/group username and password
* jinja2 extensions can now be loaded from the config file
* support for complex arguments to modules (within reason)
* can specify ansible_connection=X to define the connection type in inventory variables
* a new chroot connection type
* module common code now has basic type checking (and casting) capability
* module common now supports a 'no_log' attribute to mark a field as not to be syslogged
* inventory can now point to a directory containing multiple scripts/hosts files, if using this, put group_vars/host_vars directories inside this directory
* added configurable crypt scheme for 'vars_prompt'
* password generating lookup plugin -- $PASSWORD(path/to/save/data/in)
* added --step option to ansible-playbook, works just like Linux interactive startup!

Modules Added:

* bzr *(bazaar version control)*
* cloudformation
* django-manage
* gem *(ruby gems)*
* homebrew
* lvg *(logical volume groups)*
* lvol *(LVM logical volumes)*
* macports
* mongodb_user
* netscaler
* okg
* openbsd_pkg
* rabbit_mq_parameter
* rabbit_mq_plugin
* rabbit_mq_user
* rabbit_mq_vhost
* rhn_channel
* s3 *-- allows putting file contents in buckets for sharing over s3*
* uri module *-- can get/put/post/etc*
* vagrant *-- launching VMs with vagrant, this is different from existing vagrant plugin*
* zfs

Bugfixes and Misc Changes:

* stderr shown when commands fail to parse
* uses yaml.safe_dump in filter plugins
* authentication Q&A no longer happens before --syntax-check, but after
* ability to get hostvars data for nodes not in the setup cache yet
* SSH timeout now correctly passed to native SSH connection plugin
* raise an error when multiple when_ statements are provided
* --list-hosts applies host limit selections better
* (internals) template engine specifications to use template_ds everywhere
* better error message when your host file can not be found
* end of line comments now work in the inventory file
* directory destinations now work better with remote md5 code
* lookup plugin macros like $FILE and $ENV now work without returning arrays in variable definitions/playbooks
* uses yaml.safe_load everywhere
* able to add EXAMPLES to documentation via EXAMPLES docstring, rather than just in main documentation YAML
* can set ANSIBLE_COW_SELECTION to pick other cowsay types (including random)
* to_nice_yaml and to_nice_json available as Jinja2 filters that indent and sort
* cowsay able to run out of macports (very important!)
* improved logging for fireball mode
* nicer error message when talking to an older system that needs a JSON module installed
* 'magic' variable 'inventory_dir' now gives path to inventory file
* 'magic' variable 'vars' works like 'hostvars' but gives global scope variables, useful for debugging in templates mostly
* conditionals can be used on plugins like add_host
* developers: all callbacks now have access to a ".runner" and ".playbook", ".play", and ".task" object (use getattr, they may not always be set!)

Facts:

* block device facts for the setup module
* facts for AIX
* fact detection for OS type on Amazon Linux
* device fact gathering stability improvements
* ansible_os_family fact added
* user_id (remote user name)
* a whole series of current time information under the 'datetime' hash
* more OS X facts
* support for detecting Alpine Linux
* added facts for OpenBSD

Module Changes/Fixes:

* ansible module common code (and ONLY that) which is mixed in with modules, is now BSD licensed.  App remains GPLv3.
* service code works better on platforms that mix upstart, systemd, and system-v
* service enablement idempotence fixes for systemd and upstart
* service status 4 is also 'not running'
* supervisorctl restart fix
* increased error handling for ec2 module
* can recursively set permissions on directories
* ec2: change to the way AMI tags are handled
* cron module can now also manipulate cron.d files
* virtualenv module can now inherit system site packages (or not)
* lineinfile module now has an insertbefore option
* NetBSD service module support
* fixes to sysctl module where item has multiple values
* AIX support for the user and group modules
* able to specify a different hg repo to pull from than the original set
* add_host module can set ports and other inventory variables
* add_host module can add modules to multiple groups (groups=a,b,c), groups now alias for groupname
* subnet ID can be set on EC2 module
* MySQL module password handling improvements
* added new virtualenv flags to pip and easy_install modules
* various improvements to lineinfile module, now accepts common arguments from file
* force= now replaces thirsty where used before, thirsty remains an alias
* setup module can take a 'filter=<wildcard>' parameter to just return a few facts (not used by playbooks)
* cron module works even if no crontab is present (for cron.d)
* security group ID settable on EC2 module
* misc fixes to sysctl module
* fix to apt module so packages not in cache are still removable
* charset fix to mail module
* postresql db module now does not try to create the 'PUBLIC' user
* SVN module now works correctly with self signed certs
* apt module now has an upgrade parameter (values=yes, no, or 'dist')
* nagios module gets new silence/unsilence commands
* ability to disable proxy usage in get_url (use_proxy=no)
* more OS X facts
* added a 'fail_on_missing' (default no) option to fetch
* added timeout to the uri module (default 30 seconds, adjustable)
* ec2 now has a 'wait' parameter to wait for the instance to be active, eliminates need for separate wait_for call.
* allow regex backreferences in lineinfile
* id attribute on ec2 module can be used to set idempotent-do-not-recreate launches
* icinga support for nagios module
* fix default logins when no my.conf for MySQL module
* option to create users with non-unique UIDs (user module)
* macports module can enable/disable packages
* quotes in my.cnf are stripped by the MySQL modules
* Solaris Service management added
* service module will attempt to auto-add unmanaged chkconfig services when needed
* service module supports systemd service unit files

Plugins:

* added 'with_random_choice' filter plugin
* fixed ~ expansion for fileglob
* with_nested allows for nested loops (see examples in examples/playbooks)

## 1.0 "Eruption" -- Feb 1 2013

New modules:

* apt_key
* ec2_facts
* hg *(now in core)*
* pacman *(Arch linux)*
* pkgin *(Joyent SmartOS)*
* sysctl

New config settings:

* sudo_exe parameter can be set in config to use sudo alternatives
* sudo_flags parameter can alter the flags used with sudo

New playbook/language features:

* added when_failed and when_changed
* task includes can now be of infinite depth
* when_set and when_unset can take more than one var (when_set: $a and $b and $c)
* added the with_sequence lookup plugin
* can override "connection:" on an individual task
* parameterized playbook includes can now define complex variables (not just all on one line)
* making inventory variables available for use in vars_files paths
* messages when skipping plays are now more clear
* --extra-vars now has maximum precedence (as intended)

Module fixes and new flags:

* ability to use raw module without python on remote system
* fix for service status checking on Ubuntu
* service module now responds to additional exit code for SERVICE_UNAVAILABLE
* fix for raw module with '-c local'
* various fixes to git module
* ec2 module now reports the public DNS name
* can pass executable= to the raw module to specify alternative shells
* fix for postgres module when user contains a "-"
* added additional template variables -- $template_fullpath and $template_run_date
* raise errors on invalid arguments used with a task include statement
* shell/command module takes a executable= parameter to specify a different shell than /bin/sh
* added return code and error output to the raw module
* added support for @reboot to the cron module
* misc fixes to the pip module
* nagios module can schedule downtime for all services on the host
* various subversion module improvements
* various mail module improvements
* SELinux fix for files created by authorized_key module
* "template override" ??
* get_url module can now send user/password authorization
* ec2 module can now deploy multiple simultaneous instances
* fix for apt_key modules stalling in some situations
* fix to enable Jinja2 {% include %} to work again in template
* ec2 module is now powered by Boto
* setup module can now detect if package manager is using pacman
* fix for yum module with enablerepo in use on EL 6

Core fixes and new behaviors:

* various fixes for variable resolution in playbooks
* fixes for handling of "~" in some paths
* various fixes to DWIM'ing of relative paths
* /bin/ansible now takes a --list-hosts just like ansible-playbook did
* various patterns can now take a regex vs a glob if they start with "~" (need docs on which!) - also /usr/bin/ansible
* allow intersecting host patterns by using "&" ("webservers:!debian:&datacenter1")
* handle tilde shell character for --private-key
* hash merging policy is now selectable in the config file, can choose to override or merge
* environment variables now available for setting all plugin paths (ANSIBLE_CALLBACK_PLUGINS, etc)
* added packaging file for macports (not upstreamed yet)
* hacking/test-module script now uses /usr/bin/env properly
* fixed error formatting for certain classes of playbook syntax errors
* fix for processing returns with large volumes of output

Inventory files/scripts:

* hostname patterns in the inventory file can now use alphabetic ranges
* whitespace is now allowed around group variables in the inventory file
* inventory scripts can now define groups of groups and group vars (need example for docs?)

## 0.9 "Dreams" -- Nov 30 2012

Highlighted core changes:

* various performance tweaks, ansible executes dramatically less SSH ops per unit of work
* close paramiko SFTP connections less often on copy/template operations (speed increase)
* change the way we use multiprocessing (speed/RAM usage improvements)
* able to set default for asking password & sudo password in config file
* ansible now installs nicely if running inside a virtualenv
* flag to allow SSH connection to move files by scp vs sftp (in config file)
* additional RPM subpackages for easily installing fireball mode deps (server and node)
* group_vars/host_vars now available to ansible, not just playbooks
* native ssh connection type (-c ssh) now supports passwords as well as keys
* ansible-doc program to show details

Other core changes:

* fix for template calls when last character is '$'
* if ansible_python_interpreter is set on a delegated host, it now works as intended
* --limit can now take "," as separator as well as ";" or ":"
* msg is now displaced with newlines when a task fails
* if any with_ plugin has no results in a list (empty list for with_items, etc), the task is now skipped
* various output formatting fixes/improvements
* fix for Xen dom0/domU detection in default facts
* 'ansible_domain' fact now available (ex value: example.com)
* configured remote temp file location is now always used even for root
* 'register'-ed variables are not recorded for skipped hosts (for example, using only_if/when)
* duplicate host records for the same host can no longer result when a host is listed in multiple groups
* ansible-pull now passes --limit to prevent running on multiple hosts when used with generic playbooks
* remote md5sum check fixes for Solaris 10
* ability to configure syslog facility used by remote module calls
* in templating, stray '$' characters are now handled more correctly

Playbook changes:

* relative paths now work for 'first_available_file'
* various templating engine fixes
* 'when' is an easier form of only if
* --list-hosts on the playbook command now supports multiple playbooks on the same command line
* playbook includes can now be parameterized

Module additions:

* (addhost) new module for adding a temporary host record (used for creating new guests)
* (group_by) module allows partitioning hosts based on group data
* (ec2) new module for creating ec2 hosts
* (script) added 'script' module for pushing and running self-deleting remote scripts
* (svr4pkg) solaris svr4pkg module

Module changes:

* (authorized key) module uses temp file now to prevent failure on full disk
* (fetch) now uses the 'slurp' internal code to work as you would expect under sudo'ed accounts
* (fetch) internal usage of md5 sums fixed for BSD
* (get_url) thirsty is no longer required for directory destinations
* (git) various git module improvements/tweaks
* (group) now subclassed for various platforms, includes SunOS support
* (lineinfile) create= option on lineinfile can create the file when it does not exist
* (mysql_db) module takes new grant options
* (postgresql_db) module now takes role_attr_flags
* (service) further upgrades to service module service status reporting
* (service) tweaks to get service module to play nice with BSD style service systems (rc.conf)
* (service) possible to pass additional arguments to services
* (shell) and command module now take an 'executable=' flag for specifying an alternate shell than /bin/sh
* (user) ability to create SSH keys for users when using user module to create users
* (user) atomic replacement of files preserves permissions of original file
* (user) module can create SSH keys
* (user) module now does Solaris and BSD
* (yum) module takes enablerepo= and disablerepo=
* (yum) misc yum module fixing for various corner cases

Plugin changes:

* EC2 inventory script now produces nicer failure message if AWS is down (or similar)
* plugin loading code now more streamlined
* lookup plugins for DNS text records, environment variables, and redis
* added a template lookup plugin $TEMPLATE('filename.j2')
* various tweaks to the EC2 inventory plugin
* jinja2 filters are now pluggable so it's easy to write your own (to_json/etc, are now impl. as such)

## 0.8 "Cathedral" -- Oct 19, 2012

Highlighted Core Changes:

* fireball mode -- ansible can bootstrap a ephemeral 0mq (zeromq) daemon that runs as a given user and expires after X period of time.  It is very fast.
* playbooks with errors now return 2 on failure.  1 indicates a more fatal syntax error.  Similar for /usr/bin/ansible
* server side action code (template, etc) are now fully pluggable
* ability to write lookup plugins, like the code powering "with_fileglob" (see below)

Other Core Changes:

* ansible config file can also go in 'ansible.cfg' in cwd in addition to ~/.ansible.cfg and /etc/ansible/ansible.cfg
* fix for inventory hosts at API level when hosts spec is a list and not a colon delimited string
* ansible-pull example now sets up logrotate for the ansible-pull cron job log
* negative host matching (!hosts) fixed for external inventory script usage
* internals: os.executable check replaced with utils function so it plays nice on AIX
* Debian packaging now includes ansible-pull manpage
* magic variable 'ansible_ssh_host' can override the hostname (great for usage with tunnels)
* date command usage in build scripts fixed for OS X
* don't use SSH agent with paramiko if a password is specified
* make output be cleaner on multi-line command/shell errors
* /usr/bin/ansible now prints things when tasks are skipped, like when creates= is used with -m command and /usr/bin/ansible
* when trying to async a module that is not a 'normal' asyncable module, ansible will now let you know
* ability to access inventory variables via 'hostvars' for hosts not yet included in any play, using on demand lookups
* merged ansible-plugins, ansible-resources, and ansible-docs into the main project
* you can set ANSIBLE_NOCOWS=1 if you want to disable cowsay if it is installed.  Though no one should ever want to do this!  Cows are great!
* you can set ANSIBLE_FORCE_COLOR=1 to force color mode even when running without a TTY
* fatal errors are now properly colored red.
* skipped messages are now cyan, to differentiate them from unchanged messages.
* extensive documentation upgrades
* delegate_action to localhost (aka local_action) will always use the local connection type

Highlighted playbook changes:

* is_set is available for use inside of an only_if expression:  is_set('ansible_eth0').  We intend to further upgrade this with a 'when'
  keyword providing better options to 'only_if' in the next release.   Also is_unset('ansible_eth0')
* playbooks can import playbooks in other directories and then be able to import tasks relative to them
* FILE($path) now allows access of contents of file in a path, very good for use with SSH keys
* similarly PIPE($command) will run a local command and return the results of executing this command
* if all hosts in a play fail, stop the playbook, rather than letting the console log spool on by
* only_if using register variables that are booleans now works in a boolean way like you'd expect
* task includes now work with with_items (such as: include: path/to/wordpress.yml user=$item)
* when using a $list variable with $var or ${var} syntax it will automatically join with commas
* setup is not run more than once when we know it is has already been run in a play that included another play, etc
* can set/override sudo and sudo_user on individual tasks in a play, defaults to what is set in the play if not present
* ability to use with_fileglob to iterate over local file patterns
* templates now use Jinja2's 'trim_blocks=True' to avoid stray newlines, small changes to templates may
be required in rare cases.

Other playbook changes:

* to_yaml and from_yaml are available as Jinja2 filters
* $group and $group_names are now accessible in with_items
* where 'stdout' is provided a new 'stdout_lines' variable (type == list) is now generated and usable with with_items
* when local_action is used the transport is automatically overridden to the local type
* output on failed playbook commands is now nicely split for stderr/stdout and syntax errors
* if local_action is not used and delegate_to was 127.0.0.1 or localhost, use local connection regardless
* when running a playbook, and the statement has changed, prints 'changed:' now versus 'ok:' so it is obvious without colored mode
* variables now usable within vars_prompt (just not host/group vars)
* setup facts are now retained across plays (dictionary just gets updated as needed)
* --sudo-user now works with --extra-vars
* fix for multi_line strings with only_if

New Modules:

* ini_file module for manipulating INI files
* new LSB facts (release, distro, etc)
* pause module -- (pause seconds=10) (pause minutes=1) (pause prompt=foo) -- it's an action plugin
* a module for adding entries to the main crontab (though you may still wish to just drop template files into cron.d)
* debug module can be used for outputing messages without using 'shell echo'
* a fail module is now available for causing errors, you might want to use it with only_if to fail in certain conditions

Other module Changes, Upgrades, and Fixes:

* removes= exists on command just like creates=
* postgresql modules now take an optional port= parameter
* /proc/cmdline info is now available in Linux facts
* public host key detection for OS X
* lineinfile module now uses 'search' not exact 'match' in regexes, making it much more intuitive and not needing regex syntax most of the time
* added force=yes|no (default no) option for file module, which allows transition between files to directories and so on
* additional facts for SunOS virtualization
* copy module is now atomic when used across volumes
* url_get module now returns 'dest' with the location of the file saved
* fix for yum module when using local RPMs vs downloading
* cleaner error messages with copy if destination directory does not exist
* setup module now still works if PATH is not set
* service module status now correct for services with 'subsys locked' status
* misc fixes/upgrades to the wait_for module
* git module now expands any "~" in provided destination paths
* ignore stop error code failure for service module with state=restarted, always try to start
* inline documentation for modules allows documentation source to built without pull requests to the ansible-docs project, among other things
* variable '$ansible_managed' is now great to include at the top of your templates and includes useful information and a warning that it will be replaced
* "~" now expanded in command module when using creates/removes
* mysql module can do dumps and imports
* selinux policy is only required if setting to not disabled
* various fixes for yum module when working with packages not in any present repo

## 0.7 "Panama" -- Sept 6 2012

Module changes:

* login_unix_socket option for mysql user and database modules (see PR #781 for doc notes)
* new modules -- pip, easy_install, apt_repository, supervisorctl
* error handling for setup module when SELinux is in a weird state
* misc yum module fixes
* better changed=True/False detection in user module on older Linux distros
* nicer errors from modules when arguments are not key=value
* backup option on copy (backup=yes), as well as template, assemble, and lineinfile
* file module will not recurse on directory properties
* yum module now workable without having repoquery installed, but doesn't support comparisons or list= if so
* setup module now detects interfaces with aliases
* better handling of VM guest type detection in setup module
* new module boilerplate code to check for mutually required arguments, arguments required together, exclusive args
* add pattern= as a parameter to the service module (for init scripts that don't do status, or do poor status)
* various fixes to mysql & postresql modules
* added a thirsty= option (boolean, default no) to the get_url module to decide to download the file every time or not
* added a wait_for module to poll for ports being open
* added a nagios module for controlling outage windows and alert statuses
* added a seboolean module for getsebool/setsebool type operations
* added a selinux module for controlling overall SELinux policy
* added a subversion module
* added lineinfile for adding and removing lines from basic files
* added facts for ARM-based CPUs
* support for systemd in the service module
* git moduleforce reset behavior is now controllable
* file module can now operate on special files (block devices, etc)

Core changes:

* ansible --version will now give branch/SHA information if running from git
* better sudo permissions when encountering different umasks
* when using paramiko and SFTP is not accessible, do not traceback, but return a nice human readable msg
* use -vvv for extreme debug levels. -v gives more playbook output as before
* -vv shows module arguments to all module calls (and maybe some other things later)
* don not pass "--" to sudo to work on older EL5
* make remote_md5 internal function work with non-bash shells
* allow user to be passed in via --extra-vars (regression)
* add --limit option, which can be used to further confine the pattern given in ansible-playbooks
* adds ranged patterns like dbservers[0-49] for usage with patterns or --limit
* -u and user: defaults to current user, rather than root, override as before
* /etc/ansible/ansible.cfg and ~/ansible.cfg now available to set default values and other things
* (developers) ANSIBLE_KEEP_REMOTE_FILES=1 can be used in debugging (envrionment variable)
* (developers) connection types are now plugins
* (developers) callbacks can now be extended via plugins
* added FreeBSD ports packaging scripts
* check for terminal properties prior to engaging color modes
* explicitly disable password auth with -c ssh, as it is not used anyway

Playbooks:

* YAML syntax errors detected and show where the problem is
* if you ctrl+c a playbook it will not traceback (usually)
* vars_prompt now has encryption options (see examples/playbooks/prompts.yml)
* allow variables in parameterized task include parameters (regression)
* add ability to store the result of any command in a register (see examples/playbooks/register_logic.yml)
* --list-hosts to show what hosts are included in each play of a playbook
* fix a variable ordering issue that could affect vars_files with selective file source lists
* adds 'delegate_to' for a task, which can be used to signal outage windows and load balancers on behalf of hosts
* adds 'serial' to playbook, allowing you to specify how many hosts can be processing a playbook at one time (default 0=all)
* adds 'local_action: <action parameters>' as an alias to 'delegate_to: 127.0.0.1'

## 0.6 "Cabo" -- August 6, 2012

playbooks:

* support to tag tasks and includes and use --tags in playbook CLI
* playbooks can now include other playbooks (example/playbooks/nested_playbooks.yml)
* vars_files now usable with with_items, provided file paths don't contain host specific facts
* error reporting if with_items value is unbound
* with_items no longer creates lots of tasks, creates one task that makes multiple calls
* can use host_specific facts inside with_items (see above)
* at the top level of a playbook, set 'gather_facts: no' to skip fact gathering
* first_available_file and with_items used together will now raise an error
* to catch typos, like 'var' for 'vars', playbooks and tasks now yell on invalid parameters
* automatically load (directory_of_inventory_file)/group_vars/groupname and /host_vars/hostname in vars_files
* playbook is now colorized, set ANSIBLE_NOCOLOR=1 if you do not like this, does not colorize if not a TTY
* hostvars now preserved between plays (regression in 0.5 from 0.4), useful for sharing vars in multinode configs
* ignore_errors: yes on a task can be used to allow a task to fail and not stop the play
* with_items with the apt/yum module will install/remove/update everything in a single command

inventory:

* groups variable available as a hash to return the hosts in each group name
* in YAML inventory, hosts can list their groups in inverted order now also (see tests/yaml_hosts)
* YAML inventory is deprecated and will be removed in 0.7
* ec2 inventory script
* support ranges of hosts in the host file, like www[001-100].example.com (supports leading zeros and also not)

modules:

* fetch module now does not fail a system when requesting file paths (ex: logs) that don't exist
* apt module now takes an optional install-recommends=yes|no (default yes)
* fixes to the return codes of the copy module
* copy module takes a remote md5sum to avoid large file transfer
* various user and group module fixes (error handling, etc)
* apt module now takes an optional force parameter
* slightly better psychic service status handling for the service module
* fetch module fixes for SSH connection type
* modules now consistently all take yes/no for boolean parameters (and DWIM on true/false/1/0/y/n/etc)
* setup module no longer saves to disk, template module now only used in playbooks
* setup module no longer needs to run twice per playbook
* apt module now passes DEBIAN_FRONTEND=noninteractive
* mount module (manages active mounts + fstab)
* setup module fixes if no ipv6 support
* internals: template in common module boilerplate, also causes less SSH operations when used
* git module fixes
* setup module overhaul, more modular
* minor caching logic added to inventory to reduce hammering of inventory scripts.
* MySQL and PostgreSQL modules for user and db management
* vars_prompt now supports private password entry (see examples/playbooks/prompts.yml)
* yum module modified to be more tolerant of plugins spewing random console messages (ex: RHN)

internals:

* when sudoing to root, still use /etc/ansible/setup as the metadata path, as if root
* paramiko is now only imported if needed when running from source checkout
* cowsay support on Ubuntu
* various ssh connection fixes for old Ubuntu clients
* ./hacking/test-module now supports options like ansible takes and has a debugger mode
* sudoing to a user other than root now works more seamlessly (uses /tmp, avoids umask issues)

## 0.5 "Amsterdam" ------- July 04, 2012

* Service module gets more accurate service states when running with upstart
* Jinja2 usage in playbooks (not templates), reinstated, supports %include directive
* support for --connection ssh (supports Kerberos, bastion hosts, etc), requires ControlMaster
* misc tracebacks replaced with error messages
* various API/internals refactoring
* vars can be built from other variables
* support for exclusion of hosts/groups with "!groupname"
* various changes to support md5 tool differences for FreeBSD nodes & OS X clients
* "unparseable" command output shows in command output for easier debugging
* mktemp is no longer required on remotes (not available on BSD)
* support for older versions of python-apt in the apt module
* a new "assemble" module, for constructing files from pieces of files (inspired by Puppet "fragments" idiom)
* ability to override most default values with ANSIBLE_FOO environment variables
* --module-path parameter can support multiple directories separated with the OS path separator
* with_items can take a variable of type list
* ansible_python_interpreter variable available for systems with more than one Python
* BIOS and VMware "fact" upgrades
* cowsay is used by ansible-playbook if installed to improve output legibility (try installing it)
* authorized_key module
* SELinux facts now sourced from the python selinux library
* removed module debug option -D
* added --verbose, which shows output from successful playbook operations
* print the output of the raw command inside /usr/bin/ansible as with command/shell
* basic setup module support for Solaris
* ./library relative to the playbook is always in path so modules can be included in tarballs with playbooks

## 0.4 "Unchained" ------- May 23, 2012

Internals/Core
* internal inventory API now more object oriented, parsers decoupled
* async handling improvements
* misc fixes for running ansible on OS X (overlord only)
* sudo improvements, now works much more smoothly
* sudo to a particular user with -U/--sudo-user, or using 'sudo_user: foo' in a playbook
* --private-key CLI option to work with pem files

Inventory
* can use -i host1,host2,host3:port to specify hosts not in inventory (replaces --override-hosts)
* ansible INI style format can do groups of groups [groupname:children] and group vars [groupname:vars]
* groups and users module takes an optional system=yes|no on creation (default no)
* list of hosts in playbooks can be expressed as a YAML list in addition to ; delimited

Playbooks
* variables can be replaced like ${foo.nested_hash_key.nested_subkey[array_index]}
* unicode now ok in templates (assumes utf8)
* able to pass host specifier or group name in to "hosts:" with --extra-vars
* ansible-pull script and example playbook (extreme scaling, remediation)
* inventory_hostname variable available that contains the value of the host as ansible knows it
* variables in the 'all' section can be used to define other variables based on those values
* 'group_names' is now a variable made available to templates
* first_available_file feature, see selective_file_sources.yml in examples/playbooks for info
* --extra-vars="a=2 b=3" etc, now available to inject parameters into playbooks from CLI

Incompatible Changes
* jinja2 is only usable in templates, not playbooks, use $foo instead
* --override-hosts removed, can use -i with comma notation (-i "ahost,bhost")
* modules can no longer include stderr output (paramiko limitation from sudo)

Module Changes
* tweaks to SELinux implementation for file module
* fixes for yum module corner cases on EL5
* file module now correctly returns the mode in octal
* fix for symlink handling in the file module
* service takes an enable=yes|no which works with chkconfig or updates-rc.d as appropriate
* service module works better on Ubuntu
* git module now does resets and such to work more smoothly on updates
* modules all now log to syslog
* enabled=yes|no on a service can be used to toggle chkconfig & updates-rc.d states
* git module supports branch=
* service fixes to better detect status using return codes of the service script
* custom facts provided by the setup module mean no dependency on Ruby, facter, or ohai
* service now has a state=reloaded
* raw module for bootstrapping and talking to routers w/o Python, etc

Misc Bugfixes
* fixes for variable parsing in only_if lines
* misc fixes to key=value parsing
* variables with mixed case now legal
* fix to internals of hacking/test-module development script


## 0.3 "Baluchitherium" -- April 23, 2012

* Packaging for Debian, Gentoo, and Arch
* Improvements to the apt and yum modules
* A virt module
* SELinux support for the file module
* Ability to use facts from other systems in templates (aka exported
resources like support)
* Built in Ansible facts so you don't need ohai, facter, or Ruby
* tempdir selections that work with noexec mounted /tmp
* templates happen locally, not remotely, so no dependency on
python-jinja2 for remote computers
* advanced inventory format in YAML allows more control over variables
per host and per group
* variables in playbooks can be structured/nested versus just a flat namespace
* manpage upgrades (docs)
* various bugfixes
* can specify a default --user for playbooks rather than specifying it
in the playbook file
* able to specify ansible port in ansible host file (see docs)
* refactored Inventory API to make it easier to write scripts using Ansible
* looping capability for playbooks (with_items)
* support for using sudo with a password
* module arguments can be unicode
* A local connection type, --connection=local,  for use with cron or
in kickstarts
* better module debugging with -D
* fetch module for pulling in files from remote hosts
* command task supports creates=foo for idempotent semantics, won't run if file foo already exists

## 0.0.2 and 0.0.1

* Initial stages of project
