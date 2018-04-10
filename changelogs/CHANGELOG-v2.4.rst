========================================
Ansible 2.4 "Dancing Days" Release Notes
========================================
2.4.4 "Dancing Days" - TBD
--------------------------

Bugfixes
~~~~~~~~

-  Fix python 3 dictionary runtime error in ios\_confg and eos\_config
   (https://github.com/ansible/ansible/issues/36717)
-  Fix ``win_script`` to work with large arguments and removed uneeded
   function that produces errors and was not needed
   (https://github.com/ansible/ansible/pull/33855)
-  Fix timeout when using piped ssh transfer with become
   https://github.com/ansible/ansible/issues/34523
-  Fix win\_scheduled\_task docs to correctly reflect what is required
   and when (https://github.com/ansible/ansible/issues/35072)
-  Updated copy test to create recursive symlink during the test and not
   have it located in the git repo
   (https://github.com/ansible/ansible/pull/35073)
-  Fix Digital Ocean tags data type due to backend API changes no longer
   acceping integers (https://github.com/ansible/ansible/pull/33486)
-  Fix for nxos\_vxlan\_vtep\_vni issues:
   https://github.com/ansible/ansible/pull/34946
-  Fixes for nxos\_bgp: https://github.com/ansible/ansible/pull/34590
-  Enable nxapi nxos\_banner test:
   https://github.com/ansible/ansible/pull/35033
-  fix vxlan idempotent issue in nxos\_vxlan\_vtep:
   https://github.com/ansible/ansible/pull/34750
-  Fix win\_dns\_client to allow setting dynamic IP from static IP
   (https://github.com/ansible/ansible/pull/35149)
-  Fix azure\_rm\_subnet absent idempotency issues
   (https://github.com/ansible/ansible/pull/35037)
-  Fix azure\_rm\_virtualmachine creating VM with vnet in another
   resource group (https://github.com/ansible/ansible/pull/35038)
-  Fix nxos terminal plugin regex to support certain commands
   (https://github.com/ansible/ansible/pull/35186)
-  Fix network os\_config modules backward diff
   (https://github.com/ansible/ansible/pull/35332)
-  Fix nxos\_snmp\_user removing encryption from user on subsequent runs
   of the task (https://github.com/ansible/ansible/pull/35433)
-  Fix traceback in winrm module when the ipaddress module is not
   installed https://github.com/ansible/ansible/pull/35723/files
-  Fix bug in ``lineinfile`` where the line would not be inserted when
   using ``insertbefore`` or ``insertafter`` if the pattern occured
   anywhere in the file.
   (https://github.com/ansible/ansible/issues/28721)
-  Fix connection local getting overridden by network\_cli for transport
   nxapi,eapi for platform agnostic modules
   (https://github.com/ansible/ansible/pull/35590)
-  Include dest i nthe results from file copy:
   https://github.com/ansible/ansible/pull/35702/
-  Fix eos\_config second-level indent idempotece
   https://github.com/ansible/ansible/pull/35588
-  Fix the removed\_in\_version to 2.6 ios\_config force option
   https://github.com/ansible/ansible/pull/35853
-  Fix memory ballooning caused as a result of task caching changes
   https://github.com/ansible/ansible/pull/35921
-  Fix nxos\_igmp\_interface for diff nxos versions
   (https://github.com/ansible/ansible/pull/35959)
-  Fix recursion error with many flat includes
   (https://github.com/ansible/ansible/pull/36075)
-  Fix win\_uri to work with ``creates`` and ``removed`` option
   (https://github.com/ansible/ansible/pull/36016)
-  Fix the oom\_killer parameter to docker\_container not being honored
   https://github.com/ansible/ansible/pull/34130
-  Fix docker\_service so a build is not triggered every time
   https://github.com/ansible/ansible/issues/36145
-  Be more tolerant about spaces when gathering virtual facts
   (https://github.com/ansible/ansible/pull/36042)
-  validate add\_host name parameter
   (https://github.com/ansible/ansible/pull/36055)
-  spelling fixes (https://github.com/ansible/ansible/pull/36007)
-  avoid needles vault prompt on ansible-console
   (https://github.com/ansible/ansible/pull/36244)
-  fix callback function signatures
   (https://github.com/ansible/ansible/pull/35664)
-  Clarify error message from convert\_bool()
   https://github.com/ansible/ansible/pull/36041
-  Fix EC2 C5 instance\_type fact to be kvm:
   https://github.com/ansible/ansible/pull/35063
-  Fix templating of loop\_control properties:
   https://github.com/ansible/ansible/pull/36124
-  Fix dependency in the deb package on Ubuntu-12.04:
   https://github.com/ansible/ansible/pull/36407
-  Fix WinRM Python 3 encoding when getting Kerberos ticket
   (https://github.com/ansible/ansible/issues/36255)
-  Always show custom prompt in pause module
   (https://github.com/ansible/ansible/issues/36057)
-  Improve performance and recursion depth in include\_role
   (https://github.com/ansible/ansible/pull/36470)
-  Fix using ansible\_\*\_interpreter on Python3 with non-new-style
   modules (old-style ansible python modules, modules written in another
   language, etc) https://github.com/ansible/ansible/pull/36541
-  Fix vyos\_config IndexError in sanitize\_config
   (https://github.com/ansible/ansible/issues/36351)
-  Fix vyos\_l3\_interface multiple address assignment to interfaces
   (https://github.com/ansible/ansible/pull/36721)
-  Protect from inventory plugins using verify incorrectly
   https://github.com/ansible/ansible/pull/36591
-  loop control templating https://github.com/ansible/ansible/pull/36124
-  fix debug output https://github.com/ansible/ansible/pull/36307
-  Fix credentials for Ansible Tower modules to work with v1 and v2 of
   the API (https://github.com/ansible/ansible/pull/36587)
   (https://github.com/ansible/ansible/pull/36662)
-  Python3 fixes:
-  Fix for the znode zookeeper module:
   https://github.com/ansible/ansible/pull/36999
-  Fix for the maven\_artifact module:
   https://github.com/ansible/ansible/pull/37035
-  Add changes to get docker\_container, docker\_common, and
   docker\_network working with Docker SDK 3.x:
   https://github.com/ansible/ansible/pull/36973
-  Ensure we install ansible-config and ansible-inventory with
   ``pip install -e`` (https://github.com/ansible/ansible/pull/37151)
-  Fix for unarchive when users use the --strip-components extra\_opt to
   tar causing ansible to set permissions on the wrong directory.
   https://github.com/ansible/ansible/pull/37048
-  Fix powershell plugin to handle special chars in environment keys as
   well as int and bool values
   (https://github.com/ansible/ansible/pull/37215)
-  Fix error messages to not be inappropriately templated:
   https://github.com/ansible/ansible/pull/37329
-  Fix Python 3 error in the openssl\_certificate module:
   https://github.com/ansible/ansible/pull/35143
-  Fix traceback when creating or stopping ovirt vms
   (https://github.com/ansible/ansible/pull/37249)
-  Connection error messages may contain characters that jinja2 would
   interpret as a template. Wrap the error string so this doesn't happen
   (https://github.com/ansible/ansible/pull/37329)

2.4.3 "Dancing Days" - 2018-01-31
---------------------------------

Bugfixes
~~~~~~~~

-  Fix ``pamd`` rule args regexp to match file paths
   (https://github.com/ansible/ansible/pull/33432)
-  Check if SELinux policy exists before setting
   (https://github.com/ansible/ansible/pull/31834)
-  Set locale to ``C`` in ``letsencrypt`` module to fix date parsing
   errors (https://github.com/ansible/ansible/pull/31339)
-  Fix include in loop when stategy=free
   (https://github.com/ansible/ansible/pull/33094)
-  Fix save parameter in asa\_config
   (https://github.com/ansible/ansible/pull/32761)
-  Fix --vault-id support in ansible-pull
   (https://github.com/ansible/ansible/pull/33629)
-  In nxos\_interface\_ospf, fail nicely if loopback is used with
   passive\_interface: (https://github.com/ansible/ansible/pull/33252)
-  Fix quote filter when given an integer to quote
   (https://github.com/ansible/ansible/issues/33272)
-  nxos\_vrf\_interface fix when validating the interface
   (https://github.com/ansible/ansible/issues/33227)
-  Fix for win\_copy when sourcing files from an SMBv1 share
   (https://github.com/ansible/ansible/pull/33576)
-  correctly report callback plugin file
-  restrict revaulting to vault cli
   https://github.com/ansible/ansible/pull/33656
-  Fix python3 tracebacks in letsencrypt module
   (https://github.com/ansible/ansible/pull/32734)
-  Fix ansible\_\*\_interpreter variables to be templated prior to being
   used: https://github.com/ansible/ansible/pull/33698
-  Fix setting of environment in a task that uses a loop:
   https://github.com/ansible/ansible/issues/32685
-  Fix fetch on Windows failing to fetch files or particular block size
   (https://github.com/ansible/ansible/pull/33697)
-  preserve certain fields during no log.
   https://github.com/ansible/ansible/pull/33637
-  fix issue with order of declaration of sections in ini inventory
   https://github.com/ansible/ansible/pull/33781
-  Fix win\_iis\_webapppool to correctly stop a apppool
   (https://github.com/ansible/ansible/pull/33777)
-  Fix CloudEngine host failed
   (https://github.com/ansible/ansible/pull/27876)
-  Fix ios\_config save issue
   (https://github.com/ansible/ansible/pull/33791)
-  Handle vault filenames with nonascii chars when displaying messages
   (https://github.com/ansible/ansible/pull/33926)
-  Fix win\_iis\_webapppool to not return passwords
   (https://github.com/ansible/ansible/pull/33931)
-  Fix extended file attributes detection and changing:
   (https://github.com/ansible/ansible/pull/18731)
-  correctly ensure 'ungrouped' membership rules
   (https://github.com/ansible/ansible/pull/33878)
-  made warnings less noisy when empty/no inventory is supplied
   (https://github.com/ansible/ansible/pull/32806)
-  Fixes a failure which prevents to create servers in module
   cloudscale\_server
-  Fix win\_firewall\_rule "Specified cast is invalid" error when
   modifying a rule with all of Domain/Public/Private profiles set
   (https://github.com/ansible/ansible/pull/34383)
-  Fix case for multilib when installing from a file in the yum module
   (https://github.com/ansible/ansible/pull/32236)
-  Fix WinRM parsing/escaping of IPv6 addresses
   (https://github.com/ansible/ansible/pull/34072)
-  Fix win\_package to detect MSI regardless of the extension case
   (https://github.com/ansible/ansible/issues/34465)
-  Updated win\_mapped\_drive docs to clarify what it is used for
   (https://github.com/ansible/ansible/pull/34478)
-  Fix file related modules run in check\_mode when the file being
   operated on does not exist
   (https://github.com/ansible/ansible/pull/33967)
-  Make eos\_vlan idempotent
   (https://github.com/ansible/ansible/pull/34443)
-  Fix win\_iis\_website to properly check attributes before setting
   (https://github.com/ansible/ansible/pull/34501)
-  Fixed the removal date for ios\_config save and force parameters
   (https://github.com/ansible/ansible/pull/33885)
-  cloudstack: fix timeout from ini config file being ignored
   https://github.com/ansible/ansible/pull/34854
-  fixes memory usage issues with many blocks/includes
   https://github.com/ansible/ansible/issues/31673
   https://github.com/ansible/ansible/pull/34461
-  Fixes maximum recursion depth exceeded with include\_role
   https://github.com/ansible/ansible/issues/23609
-  Fix to win\_dns\_client module to take ordering of DNS servers to
   resolve into account: https://github.com/ansible/ansible/pull/34656
-  Fix for the nxos\_banner module where some nxos images nest the
   output inside of an additional dict:
   https://github.com/ansible/ansible/pull/34695
-  Fix failure message "got multiple values for keyword argument id" in
   the azure\_rm\_securitygroup module (caused by changes to the azure
   python API): https://github.com/ansible/ansible/pull/34810
-  Bump Azure storage client minimum to 1.5.0 to fix deserialization
   issues. This will break Azure Stack until it receives storage API
   version 2017-10-01 or changes are made to support multiple versions.
   (https://github.com/ansible/ansible/pull/34442)
-  Flush stdin when passing the become password. Fixes some cases of
   timeout on Python 3 with the ssh connection plugin:
   https://github.com/ansible/ansible/pull/35049

2.4.2 "Dancing Days" - 2017-11-29
---------------------------------

Bugfixes
~~~~~~~~

-  Fix formatting typo in panos\_security\_rule.py docs.
   (https://github.com/ansible/ansible/commit/c0fc797a06451d2fe1ac4fc077fc64f3a1666447)
-  Fix rpm spec file to build on RHEL6 without EPEL packages
   (https://github.com/ansible/ansible/pull/31653)
-  Keep hosts in play vars if inside of a rescue task
   (https://github.com/ansible/ansible/pull/31710)
-  Fix wait\_for module to treat broken connections as unready so that
   the connection continues to be retried:
   https://github.com/ansible/ansible/pull/28839
-  Python3 fixes:
-  windows\_azure, clc\_firewall\_policy, and ce\_template modules fixed
   for imports of urllib which changed between Python2 and Python3
   lookup plugin for consul\_kv.py fixed for imports of urllib
   (https://github.com/ansible/ansible/issues/31240)
-  Make internal hashing of hostvars use bytes on both python2 and
   python3 (https://github.com/ansible/ansible/pull/31788)
-  Fix logging inside of KubernetesAnsibleModule() to not use
   self.helper.logging. the Ansible builtin log() method will strip out
   parameters marked no\_log and will not log if no\_log was set in the
   playbook. self.helper.log() circumvents that
   (https://github.com/ansible/ansible/pull/31789)
-  Correct task results display so that it more closely matches what was
   present in 2.3.x and previous.
-  Warn when a group has a bad key (Should be one of vars, children, or
   hosts) https://github.com/ansible/ansible/pull/31495
-  Use controller configured ansible\_shell\_executable to run commands
   in the module (https://github.com/ansible/ansible/pull/31361)
-  Add documentation about writing unittests for Ansible
-  Fix bugs in get\_url/uri's SNI and TLS version handling when used on
   systems that have Python-2.7.9+ and urllib3 installed.
-  Have ansible-pull process inventory in its own way. Fixes issues with
   ansible-pull not using the correct inventory, especially for
   localhost (https://github.com/ansible/ansible/pull/32135)
-  Fix for implicit localhost receiving too many variables from the all
   group (https://github.com/ansible/ansible/pull/31959)
-  Fix the service module to correctly detect which type of init system
   is present on the host.
   (https://github.com/ansible/ansible/pull/32086)
-  Fix inventory patterns to convert to strings before processing:
   (https://github.com/ansible/ansible/issues/31978)
-  Fix traceback in firewalld module instead of a nice error message:
   (https://github.com/ansible/ansible/pull/31949)
-  Fix for entering privileged mode using eos network modules:
   (https://github.com/ansible/ansible/issues/30802)
-  Validate that the destination for ansible-pull is a valid.directory:
   (https://github.com/ansible/ansible/pull/31499)
-  Document how to preserve strings of digits as strings in the ini
   inventory: (https://github.com/ansible/ansible/pull/32047)
-  Make sure we return ansible\_distribution\_major\_version to macOS:
   (https://github.com/ansible/ansible/pull/31708)
-  Fix to ansible-doc -l to list custom inventory plugins:
   (https://github.com/ansible/ansible/pull/31996)
-  Fix win\_chocolatey to respect case sensitivity in URLs:
   (https://github.com/ansible/ansible/pull/31983)
-  Fix config\_format json in the junos\_facts module:
   (https://github.com/ansible/ansible/pull/31818)
-  Allow the apt module's autoremove parameter to take effect in
   upgrades: (https://github.com/ansible/ansible/pull/30747)
-  When creating a new use via eos\_user, create the user before setting
   the user's privilege level:
   (https://github.com/ansible/ansible/pull/32162)
-  Fixes nxos\_portchannel idempotence failure on N1 images:
   (https://github.com/ansible/ansible/pull/31057)
-  Remove provider from prepare\_ios\_tests integration test:
   (https://github.com/ansible/ansible/pull/31038)
-  Fix nxos\_acl change ports to non well known ports and drop
   time\_range for N1: (https://github.com/ansible/ansible/pull/31261)
-  Fix nxos\_banner removal idempotence issue in N1 images:
   (https://github.com/ansible/ansible/pull/31259)
-  Return error message back to the module
   (https://github.com/ansible/ansible/pull/31035)
-  Fix nxos\_igmp\_snooping idempotence:
   (https://github.com/ansible/ansible/pull/31688)
-  NXOS integration test nxos\_file\_copy, nxos\_igmp,
   nxos\_igmp\_interface nxos\_igmp\_snooping, nxos\_ntp\_auth,
   nxos\_ntp\_options: (https://github.com/ansible/ansible/pull/29030)
-  Fix elb\_target\_group module traceback when ports were specified
   inside of the targets parameter:
   (https://github.com/ansible/ansible/pull/32202)
-  Fix creation of empty virtual directories in aws\_s3 module:
   (https://github.com/ansible/ansible/pull/32169)
-  Enable echo for ``pause`` module:
   (https://github.com/ansible/ansible/issues/14160)
-  Fix for ``hashi_vault`` lookup to return all keys at a given path
   when no key is specified
   (https://github.com/ansible/ansible/pull/32182)
-  Fix for ``win_package`` to allow TLS 1.1 and 1.2 on web requests:
   (https://github.com/ansible/ansible/pull/32184)
-  Remove provider from ios integration test:
   (https://github.com/ansible/ansible/pull/31037)
-  Fix eos\_user tests (https://github.com/ansible/ansible/pull/32261)
-  Fix ansible-galaxy --force with installed roles:
   (https://github.com/ansible/ansible/pull/32282)
-  ios\_interface testfix:
   (https://github.com/ansible/ansible/pull/32335)
-  Fix ios integration tests:
   (https://github.com/ansible/ansible/pull/32342)
-  Ensure there is always a basdir so we always pickup group/host\_vars
   https://github.com/ansible/ansible/pull/32269
-  Fix vars placement in ansible-inventory
   https://github.com/ansible/ansible/pull/32276
-  Correct options for luseradd in user module
   https://github.com/ansible/ansible/pull/32262
-  Clarified package docs on 'latest' state
   https://github.com/ansible/ansible/pull/32397
-  Fix issue with user module when local is true
   (https://github.com/ansible/ansible/pull/32262 and
   https://github.com/ansible/ansible/pull/32411)
-  Fix for max\_fail\_percentage being inaccurate:
   (https://github.com/ansible/ansible/issues/32255)
-  Fix check mode when deleting ACS instance in azure\_rm\_acs module:
   (https://github.com/ansible/ansible/pull/32063)
-  Fix ios\_logging smaller issues and make default size for buffered
   work: (https://github.com/ansible/ansible/pull/32321)
-  Fix ios\_logging module issue where facility is being deleted along
   with host: (https://github.com/ansible/ansible/pull/32234)
-  Fix wrong prompt issue for network modules
   (https://github.com/ansible/ansible/pull/32426)
-  Fix eos\_eapi to enable non-default vrfs if the default vrf is
   already configured (https://github.com/ansible/ansible/pull/32112)
-  Fix network parse\_cli filter in case of single match is not caught
   when using start\_block and end\_block
   (https://github.com/ansible/ansible/pull/31092)
-  Fix win\_find failing on files it can't access, change behaviour to
   be more like the find module
   (https://github.com/ansible/ansible/issues/31898)
-  Amended tracking of 'changed'
   https://github.com/ansible/ansible/pull/31812
-  Fix label assignment in ovirt\_host\_networks
   (https://github.com/ansible/ansible/pull/31973)
-  Fix fencing and kuma usage in ovirt\_cluster module
   (https://github.com/ansible/ansible/pull/32190)
-  Fix failure during upgrade due to NON\_RESPONSIVE state for
   ovirt\_hosts module (https://github.com/ansible/ansible/pull/32192)
-  ini inventory format now correclty handles group creation w/o need
   for specific orders https://github.com/ansible/ansible/pull/32471
-  Fix for quoted paths in win\_service
   (https://github.com/ansible/ansible/issues/32368)
-  Fix tracebacks for non-ascii paths when parsing inventory
   (https://github.com/ansible/ansible/pull/32511)
-  Fix git archive when update is set to no
   (https://github.com/ansible/ansible/pull/31829)
-  Fix locale when screen scraping in the yum module
   (https://github.com/ansible/ansible/pull/32203)
-  Fix for validating proxy results on Python3 for modules making http
   requests: (https://github.com/ansible/ansible/pull/32596)
-  Fix unreferenced variable in SNS topic module
   (https://github.com/ansible/ansible/pull/29117)
-  Handle ignore\_errors in loops
   (https://github.com/ansible/ansible/pull/32546)
-  Fix running with closed stdin on python 3
   (https://github.com/ansible/ansible/pull/31695)
-  Fix undefined variable in script inventory plugin
   (https://github.com/ansible/ansible/pull/31381)
-  Fix win\_copy on Python 2.x to support files greater than 4GB
   (https://github.com/ansible/ansible/pull/32682)
-  Add extra error handling for wmare connect to correctly detect
   scenarios where username does not have the required logon permissions
   (https://github.com/ansible/ansible/pull/32613)
-  Fix ios\_config file prompt issue while using save\_when
   (https://github.com/ansible/ansible/pull/32744)
-  Prevent host\_group\_vars plugin load errors when using 'path as
   inventory hostname' https://github.com/ansible/ansible/issues/32764
-  Better errors when loading malformed vault envelopes
   (https://github.com/ansible/ansible/issues/28038)
-  nxos\_interface error handling
   (https://github.com/ansible/ansible/pull/32846)
-  Fix snmp bugs on Nexus 3500 platform
   (https://github.com/ansible/ansible/pull/32773)
-  nxos\_config and nxos\_facts - fixes for N35 platform
   (https://github.com/ansible/ansible/pull/32762)
-  fix dci failure nxos (https://github.com/ansible/ansible/pull/32877)
-  Do not execute ``script`` tasks is check mode
   (https://github.com/ansible/ansible/issues/30676)
-  Keep newlines when reading LXC container config file
   (https://github.com/ansible/ansible/pull/32219)
-  Fix a traceback in os\_floating\_ip when required instance is already
   present in the cloud: https://github.com/ansible/ansible/pull/32887
-  Fix for modifying existing application load balancers using
   certificates (https://github.com/ansible/ansible/pull/28217)
-  Fix --ask-vault-pass with no tty and password from stdin
   (https://github.com/ansible/ansible/issues/30993)
-  Fix for IIS windows modules to use hashtables instead of
   PSCustomObject (https://github.com/ansible/ansible/pull/32710)
-  Fix nxos\_snmp\_host bug
   (https://github.com/ansible/ansible/pull/32916)
-  Make IOS devices consistent ios\_logging
   (https://github.com/ansible/ansible/pull/33100)
-  restore error on orphan group:vars delcaration for ini inventories
   https://github.com/ansible/ansible/pull/32866
-  restore host/group\_vars merge order
   https://github.com/ansible/ansible/pull/32963
-  use correct loop var when delegating
   https://github.com/ansible/ansible/pull/32986
-  Handle sets and datetime objects in inventory sources fixing
   tracebacks https://github.com/ansible/ansible/pull/32990
-  Fix for breaking change to Azure Python SDK DNS RecordSet constructor
   in azure-mgmt-dns==1.2.0
   https://github.com/ansible/ansible/pull/33165
-  Fix for breaking change to Azure Python SDK that prevented some
   members from being returned in facts modules
   https://github.com/ansible/ansible/pull/33169
-  restored glob/regex host pattern matching to traverse groups and
   hosts and not return after first found
   https://github.com/ansible/ansible/pull/33158
-  change nxos\_interface module to use "show interface" to support more
   platforms https://github.com/ansible/ansible/pull/33037

2.4.1 "Dancing Days" - 2017-10-25
---------------------------------

Bugfixes
~~~~~~~~

-  Security fix for CVE-2017-7550 the jenkins\_plugin module was logging
   the jenkins server password if the url\_password was passed via the
   params field: https://github.com/ansible/ansible/pull/30875
-  Update openssl\* module documentation to show openssl-0.16 is the
   minimum version
-  Fix openssl\_certificate's csr handling
-  Python-3 fixes
-  Fix openssl\_certificate parameter assertion on Python3
-  Fix for python3 and nonascii strings in inventory plugins
   (https://github.com/ansible/ansible/pull/30666)
-  Fix missing urllib in iam\_policy
-  Fix crypttab module for bytes<=>text string mismatch (
   https://github.com/ansible/ansible/pull/30457 )
-  Fix lxc\_container module combining bytes with text (
   https://github.com/ansible/ansible/pull/30572 )
-  Fix map doesn't return a list on python3 in ec2\_snapshot\_facts
   module (https://github.com/ansible/ansible/pull/30606)
-  Fix uri (and other url retrieving) modules when used with a proxy.
   (https://github.com/ansible/ansible/issues/31109)
-  Fix azure\_rm dynamic inventory script ConfigParser usage.
-  Fix for win\_file to respect check mode when deleting directories
-  Fix for Ansible.ModuleUtils.Legacy.psm1 to return list params
   correctly
-  Fix for a proper logout in the module ovirt\_vms
-  Fixed docs for 'password' lookup
-  Corrected and added missing feature and porting docs for 2.4
-  Fix for Ansible.ModuleUtils.CamelConversion to handle empty lists and
   lists with one entry
-  Fix nxos terminal regex to parse username correctly.
-  Fix colors for selective callback
-  Fix for 'New password' prompt on 'ansible-vault edit'
   (https://github.com/ansible/ansible/issues/30491)
-  Fix for 'ansible-vault encrypt' with vault\_password\_file in config
   and --ask-vault-pass cli
   (https://github.com/ansible/ansible/pull/30514#pullrequestreview-63395903)
-  updated porting guide with notes for callbacks and config
-  Added backwards compatiblity shim for callbacks that do not inherit
   from CallbackBase
-  Corrected issue with configuration and multiple ini entries being
   overwriten even when not set.
-  backported fix for doc generation (plugin\_formatter)
-  Fix ec2\_lc module for an unknown parameter name
   (https://github.com/ansible/ansible/pull/30573)
-  Change configuration of defaults to use standard jinja2 instead of
   custom eval() for using variables in the default field of config
   (https://github.com/ansible/ansible/pull/30650)
-  added missing entry in chlog deprecation
-  Fixed precedence and values for become flags and executable settings
-  Fix for win\_domain\_membership to throw more helpful error messages
   and check/fix when calling WMI function after changing workgroup
-  Fix for win\_power\_plan to compare the OS version's correctly and
   work on Windows 10/Server 2016
-  Fix module doc for typo in telnet command option
-  Fix OpenBSD pkg\_mgr fact
   (https://github.com/ansible/ansible/issues/30623)
-  Fix encoding error when there are nonascii values in the path to the
   ssh binary
-  removed YAML inventory group name validation, broke existing setups
   and should be global in any case, and configurable
-  performance improvment for inventory, had slown down considerably
   from 2.3
-  Fix cpu facts on sparc64
   (https://github.com/ansible/ansible/pull/30261)
-  Fix ansible\_distribution fact for Arch linux
   (https://github.com/ansible/ansible/issues/30600)
-  remove print statements from play\_context/become
-  Fix vault errors after 'ansible-vault edit'
   (https://github.com/ansible/ansible/issues/30575)
-  updated api doc example to match api changes
-  corrected issues with slack callback plugin
-  it is import\_playbook, not import\_plays, docs now reflect this
-  fixed typo and missed include/import conversion in import\_tasks docs
-  updated porting docs with note about inventory\_dir
-  removed extension requirement for yaml inventory plugin to restore
   previous behaviour
-  fixed ansible-pull to now correctly deal with inventory
-  corrected dig lookup docs
-  fix type handling for sensu\_silence so the module works
-  added fix for win\_iis\_webapppool to correctly handle array elements
-  Fix bugs caused by lack of collector ordering like service\_mgr being
   incorrect (https://github.com/ansible/ansible/issues/30753)
-  Fix os\_image when the id parameter is not set in the task. (
   https://github.com/ansible/ansible/pull/29147 )
-  Fix for the winrm connection to use proper task vars
-  removed typo from dig lookup docs
-  Updated win\_chocolatey example to be clearer around what should be
   used with become
-  Fix for copy module when permissions are changed but the file
   contents are not ( https://github.com/ansible/ansible/issues/30556 )
-  corrected YAML\_FILENAME\_EXTENSIONS ini setter as key/section were
   swapped
-  Better error message when a yaml inventory is invalid
-  avoid include\_Xs conflating vars with options
-  Fix aws\_s3 module handling ``encrypt`` option
   (https://github.com/ansible/ansible/pull/31203)
-  Fix for win\_msg to document and show error when message is greater
   than 255 characters
-  Fix for win\_dotnet\_ngen to work after recent regression
-  fixed backwards compat method for config
-  removed docs for prematurely added ssh specific pipelining settings
-  fixed redis cache typo
-  Fix AttributeError during inventory group deserialization
   (https://github.com/ansible/ansible/issues/30903)
-  Fix 'ansible-vault encrypt --output=-'
   (https://github.com/ansible/ansible/issues/30550)
-  restore pre 2.4 pipeline configuration options (env and ini)
-  Fix win\_copy regression: handling of vault-encrypted source files
   (https://github.com/ansible/ansible/pull/31084)
-  Updated return values for win\_reg\_stat to correctly show what is
   being returned (https://github.com/ansible/ansible/pull/31252)
-  reduced normal error redundancy and verbosity, display on increased
   and when needed
-  Give an informative error instead of a traceback if include\_vars dir
   is file instead of directory
   (https://github.com/ansible/ansible/pull/31157)
-  Fix monit module's version check for color support
   (https://github.com/ansible/ansible/pull/31212)
-  Make ``elasticsearch_plugin`` module work with both 2.x and 5.x
   (https://github.com/ansible/ansible/issues/21989)
-  Fix for become on Windows to handle ignored errors
   (https://github.com/ansible/ansible/issues/30468)
-  Fix removal of newlines when writing SELinux config
   (https://github.com/ansible/ansible/issues/30618)
-  clarified extension requirement for constructed inv plugin
-  really turn off inventory caching, toggle will be added in 2.5
-  for inventory sources, dont follow symlinks to calculate base
   directory, used for group/host\_vars
-  Port the uptime.py example script to the new inventory API.
-  inventory\_file variable again returns full path, not just basename
-  added info about cwd group/host vars to porting guide
-  Fix name parsing out of envra in the yum module
-  give user friendly error on badly formatted yaml inventory source
-  Fix any\_errors\_fatal setting in playbooks.
-  Fix setting of ssh-extra-args from the cli
   (https://github.com/ansible/ansible/pull/31326)
-  Change SELinux fact behavior to always return a dictionary.
   (https://github.com/ansible/ansible/issues/18692)
-  Revert a fix for using non /bin/sh shells for modules' running
   commands as this was causing output from commands to change, thus
   breaking playbooks. See the original bug for details and links to the
   eventual fix: https://github.com/ansible/ansible/issues/24169
-  Do not log data field in ``docker_secrets`` module
   (https://github.com/ansible/ansible/pull/31366)
-  Fix rpm\_key taking the wrong 8 chars from the keyid
   (https://github.com/ansible/ansible/pull/31045)
-  chown errors now more informative
-  Fix for win\_copy to copy a source file that has invalid windows
   characters in the filename, the dest still must be have valid windows
   characters
   (https://github.com/ansible/ansible/issues/31336#issuecomment-334649927)
-  Fix systemd module to not run daemon-reload in check mode.
-  fixed some parsing and selection issues with inventory manager, fixed
   minor bugs in yaml and constructed plugins
-  Fix the ping module documentation to reference win\_ping instead of
   itself: https://github.com/ansible/ansible/pull/31444
-  Fix for ec2\_win\_password to allow blank key\_passphrase again
   (https://github.com/ansible/ansible/pull/28791)
-  added toggle for vars\_plugin behaviour to execute relative to
   playbook, set default to revert to previous way.
-  Fix for win\_copy to not remove destination file on change when in
   check mode (https://github.com/ansible/ansible/pull/31469)
-  Fix include\_role usage of role\_name
   (https://github.com/ansible/ansible/pull/31463)
-  Fix service and package forcing a second run of the setup module to
   function (https://github.com/ansible/ansible/issues/31485)
-  Better error message when attempting to use include or import with
   /usr/bin/ansible (https://github.com/ansible/ansible/pull/31492/)
-  Fix ``sysctl`` module to remove etries when ``state=absent``
   (https://github.com/ansible/ansible/issues/29920)
-  Fix for ec2\_group to avoid trying to iterate over None
   (https://github.com/ansible/ansible/pull/31531)
-  Fix for ec2\_group for a possible KeyError bug
   (https://github.com/ansible/ansible/pull/31540)
-  Fix for the rpm\_key module when importing the first gpg key on a
   system (https://github.com/ansible/ansible/pull/31514)
-  Fix for aws\_s3 metadata to use the correct parameters when uploading
   a file (https://github.com/ansible/ansible/issues/31232)
-  Fix for the yum module when installing from file/url crashes
   (https://github.com/ansible/ansible/pull/31529)
-  Improved error messaging for Windows become/runas when username is
   bogus (https://github.com/ansible/ansible/pull/31551)
-  Fix rollback feature in junos\_config to now allow configuration
   rollback on device (https://github.com/ansible/ansible/pull/31424)
-  Remove command executed log from ansible-connection
   (https://github.com/ansible/ansible/pull/31581)
-  Fix relative paths to be relative to config file when there is no
   playbook available (https://github.com/ansible/ansible/issues/31533)
-  Fix Inventory plugins to use the configured inventory plugin path
   (https://github.com/ansible/ansible/issues/31605)
-  Fix include task to be dynamic
   (https://github.com/ansible/ansible/issues/31593)
-  A couple fixes to the test process to account for new testing
   resources in our ci system and an upstream cryptography update that
   didn't work with pip-8.x
-  Document backup\_path in a few dellos modules and vyos\_config
   (https://github.com/ansible/ansible/issues/31844)
-  Fix for vmware\_vm\_facts with dangling inaccessible VM which don't
   have MAC addresses (https://github.com/ansible/ansible/pull/31629)
-  Fix for win\_regedit sending extra data that could confuse ansible's
   result parsing (https://github.com/ansible/ansible/pull/31813)
-  Fix git module to correctly cleanup temporary dirs
   (https://github.com/ansible/ansible/pull/31541)
-  Fix for modules which use atomic\_move() to rename files raising an
   exception if a file could not be opened. Fix will return a nice error
   message instead: https://github.com/ansible/ansible/issues/31786
-  Fix ansible-doc and ansible-console module-path option
   (https://github.com/ansible/ansible/pull/31744)
-  Fix for hostname module on RHEL 7.5
   (https://github.com/ansible/ansible/issues/31811)
-  Fix provider password leak in logs for asa modules
   (https://github.com/ansible/ansible/issues/32343)
-  Fix tagging for dynamodb\_table if region is not explicitly passed to
   the module (https://github.com/ansible/ansible/pull/32557)
-  Fix Python 3 decode error in ``cloudflare_dns``
   (https://github.com/ansible/ansible/pull/32065)

Known Bugs
~~~~~~~~~~

-  Implicit localhost is getting ansible\_connection from all:vars
   instead of from the implicit localhost definition
   (https://github.com/ansible/ansible/issues/31420)

2.4 "Dancing Days" - 2017/09/18
-------------------------------

Major Changes
~~~~~~~~~~~~~

-  Support for Python-2.4 and Python-2.5 on the managed system's side
   was dropped. If you need to manage a system that ships with
   Python-2.4 or Python-2.5, you'll need to install Python-2.6 or better
   on the managed system or run Ansible-2.3 until you can upgrade the
   system.
-  New import/include keywords to replace the old bare ``include``
   directives. The use of ``static: {yes|no}`` on such includes is now
   deprecated.

   -  Using ``import_*`` (``import_playbook``, ``import_tasks``,
      ``import_role``) directives are static.
   -  Using ``include_*`` (``include_tasks``, ``include_role``)
      directives are dynamic. This is done to avoid collisions and
      possible security issues as facts come from the remote targets and
      they might be compromised.

-  New ``order`` play level keyword that allows the user to change the
   order in which Ansible processes hosts when dispatching tasks.
-  Users can now set group merge priority for groups of the same depth
   (parent child relationship), using the new ``ansible_group_priority``
   variable, when values are the same or don't exist it will fallback to
   the previous sorting by name'.
-  Inventory has been revamped:
-  Inventory classes have been split to allow for better management and
   deduplication
-  Logic that each inventory source duplicated is now common and pushed
   up to reconciliation
-  VariableManager has been updated for better interaction with
   inventory
-  Updated CLI with helper method to initialize base objects for plays
-  New inventory plugins for creating inventory
-  Old inventory formats are still supported via plugins
-  Inline host\_list is also an inventory plugin, an example alternative
   ``advanced_host_list`` is also provided (it supports ranges)
-  New configuration option to list enabled plugins and precedence order
   ``[inventory]enable_plugins`` in ansible.cfg
-  vars\_plugins have been reworked, they are now run from Vars manager
   and API has changed (need docs)
-  Loading group\_vars/host\_vars is now a vars plugin and can be
   overridden
-  It is now possible to specify multiple inventory sources in the
   command line (-i /etc/hosts1 -i /opt/hosts2)
-  Inventory plugins can use the cache plugin (i.e. virtualbox) and is
   affected by ``meta: refresh_inventory``
-  Group variable precedence is now configurable via new 'precedence'
   option in ansible.cfg (needs docs)
-  Improved warnings and error messages across the board
-  Configuration has been changed from a hardcoded listing in the
   constants module to dynamically loaded from yaml definitions
-  Also added an ansible-config CLI to allow for listing config options
   and dumping current config (including origin)
-  TODO: build upon this to add many features detailed in ansible-config
   proposal https://github.com/ansible/proposals/issues/35
-  Windows modules now support the use of multiple shared module\_utils
   files in the form of Powershell modules (.psm1), via
   ``#Requires -Module Ansible.ModuleUtils.Whatever.psm1``
-  Python module argument\_spec now supports custom validation logic by
   accepting a callable as the ``type`` argument.
-  Windows become\_method: runas is no longer marked ``experimental``
-  Windows become\_method: runas now works across all authtypes and will
   auto-elevate under UAC if WinRM user has "Act as part of the
   operating system" privilege
-  Do not escape backslashes in the template lookup plugin to mirror
   what the template module does
   https://github.com/ansible/ansible/issues/26397

Deprecations
~~~~~~~~~~~~

-  The behaviour when specifying ``--tags`` (or ``--skip-tags``)
   multiple times on the command line has changed so that the tags are
   merged together by default. See the documentation for how to
   temporarily use the old behaviour if needed:
   https://docs.ansible.com/ansible/intro\_configuration.html#merge-multiple-cli-tags
-  The ``fetch`` module's ``validate_md5`` parameter has been deprecated
   and will be removed in 2.8. If you wish to disable post-validation of
   the downloaded file, use validate\_checksum instead.
-  Those using ansible as a library should note that the
   ``ansible.vars.unsafe_proxy`` module is deprecated and slated to go
   away in 2.8. The functionality has been moved to
   ``ansible.utils.unsafe_proxy`` to avoid a circular import.
-  The win\_get\_url module has the dictionary 'win\_get\_url' in its
   results deprecated, its content is now also available directly in the
   resulting output, like other modules.
-  Previously deprecated 'hostfile' config settings have been
   're-deprecated' as before the code did not warn about deprecated
   configuration settings, but it does now.

Deprecated Modules (to be removed in 2.8):
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

-  azure: use M(azure\_rm\_virtualmachine) instead
-  cs\_nic: replaced by cs\_instance\_nic\_secondaryip, also see new
   module cs\_instance\_nic for managing nics
-  ec2\_facts: replaced by ec2\_metadata\_facts
-  ec2\_remote\_facts: replaced by ec2\_instance\_facts
-  panos\_address: use M(panos\_object) instead
-  panos\_nat\_policy: use M(panos\_nat\_rule) instead
-  panos\_security\_policy: use M(panos\_security\_rule) instead
-  panos\_service: use M(panos\_object) instead
-  s3: replaced by aws\_s3
-  win\_msi: use M(win\_package) instead

Removed Modules (previously deprecated):
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

-  eos\_template: use eos\_config instead
-  ios\_template: use ios\_config instead
-  iosxr\_template: use iosxr\_config instead
-  junos\_template: use junos\_config instead
-  nxos\_template: use nxos\_config instead
-  openswitch
-  ops\_template: use ops\_config instead

Minor Changes
~~~~~~~~~~~~~

-  Now deprecated configuration options issue warnings when set.
-  Removed unused and deprecated config option ``pattern``
-  Updated the copy of six bundled for modules to use from 1.4.1 to
   1.10.0
-  The ``inventory_dir`` var is not a global anymore, as we now allow
   multiple inventory sources, it is now host dependant. This means it
   cannot be used wherever host vars are not permitted, for example in
   task/handler names.
-  Fixed a cornercase with ini inventory vars. Previously, if an
   inventory var was a quoted string with hash marks ("#") in it then
   the parsed string included the quotes. Now the string will not be
   quoted. Previously, if the quoting ended before the string finished
   and then the hash mark appeared, the hash mark was included as part
   of the string. Now it is treated as a trailing comment:

   # Before: var1="string#comment" ===> var1: ""string#comment""
   var1="string" #comment ===> var1: ""string" #comment" # After:
   var1="string#comment" ===> var1: "string#comment" var1="string"
   #comment ===> var1: "string"

The new behaviour mirrors how the variables would appear if there was no
hash mark in the string. \* As of 2.4.0, the fetch module fails if there
are errors reading the remote file. Use ``ignore_errors`` or
``failed_when`` in playbooks if you wish to ignore errors. \*
Experimentally added pmrun become method. \* Enable the docker
connection plugin to use su as a become method \* Add an encoding
parameter for the replace module so that it can operate on non-utf-8
files \* By default, Ansible now uses the cryptography module to
implement vault instead of the older pycrypto module. \* Changed task
state resulting from both ``rc`` and ``failed`` fields returned, 'rc' no
longer overrides 'failed'. Test plugins have also been updated
accordingly. \* The win\_unzip module no longer includes dictionary
'win\_unzip' in its results, the content is now directly in the
resulting output, like pretty much every other module. \* Rewrite of the
copy module so that it handles cornercases with symbolic links and empty
directories. The copy module has a new parameter, ``local_follow`` which
controls how links on the source system are treated. (The older
parameter, follow is for links on the remote system.) \* Update the
handling of symbolic file permissions in file-related mode parameters to
deal with multiple operators. For instance, ``mode='u=rw+x-X'`` to set
the execute bit on directories, remove it from filea, and set read-write
on both is now supported \* Added better cookie parsing to
fetch\_url/open\_url. Cookies are now in a dictionary named ``cookies``
in the fetch\_url result. Anything using ``open_url`` directly can pass
a cookie object as a named arg (``cookies``), and then parse/format the
cookies in the result. \* The bundled copy of six in
lib/ansible/module\_utils/six is now used unconditionally. The code to
fallback on a system six interfered with static analysis of the code so
the cost of using the fallback code became too high. Distributions which
wish to unbundle may do so by replacing the bundled six in
ansible/module\_utils/six/\ **init**.py. Six is tricky to unbundle,
however, so they may want to base their efforts off the code we were
using: \*
https://github.com/ansible/ansible/blob/2fff690caab6a1c6a81973f704be3fbd0bde2c2f/lib/ansible/module\_utils/six/\ **init**.py
\* Update ipaddr Jinja filters to replace existing non RFC compliant
ones. Added additional filters for easier use of handling IP addresses.
(PR #26566) \* datetime filter updated to use default format of
datetime.datetime (ISO8601) \* The junit plugin now has an option to
report a junit test failure on changes for idempotent testing. \* New
'diff' keyword allows setting diff mode on playbook objects, overriding
command line option and config. \* New config settings for inventory to:
- control inventory plugins used - extensions of files to ignore when
using inventory directory - patterns of files to ignore when using
inventory directory - option to toggle failed inventory source parsing
between an error or a warning \* More fixes for Python 3 across the code
base. \* win\_shell and win\_command modules now properly preserve
quoted arguments passed on the command-line. Tasks that attempted to
work around the issue by adding extra quotes/escaping may need to be
reworked. See https://github.com/ansible/ansible/issues/23019 for
additional detail. \* All configuration paths are now relative to the
``ansible.cfg`` file used. \* By user request, a 'configuration macro'
(``CWD``) is available to force configured paths to be relative to the
current working directory. Please note that this is unsafe and not
recommended.

New Callbacks:
^^^^^^^^^^^^^^

-  full\_skip
-  profile\_roles
-  stderr

New Connection plugins:
^^^^^^^^^^^^^^^^^^^^^^^

-  buildah
-  saltstack

New Filters:
^^^^^^^^^^^^

-  ipaddr filter gained several new suboptions
-  first\_usable
-  ip/prefix
-  ip\_netmask
-  last\_usable
-  next\_usable
-  network\_id
-  network/prefix
-  network\_netmask
-  network\_wildcard
-  previous\_usable
-  range\_usable
-  size\_usable
-  wildcard
-  next\_nth\_usable
-  network\_in\_network
-  network\_in\_usable
-  previous\_nth\_usable
-  parse\_cli
-  parse\_cli\_textfsm
-  strftime
-  urlsplit

New Inventory Plugins:
^^^^^^^^^^^^^^^^^^^^^^

-  advanced\_host\_list
-  constructed
-  host\_list
-  ini
-  openstack
-  script
-  virtualbox
-  yaml

New Inventory scripts:
^^^^^^^^^^^^^^^^^^^^^^

-  lxd

New Lookups:
^^^^^^^^^^^^

-  chef\_databag
-  cyberarkpassword
-  hiera

New Tests:
^^^^^^^^^^

-  any : true if any element is true
-  all: true if all elements are true

Module Notes
~~~~~~~~~~~~

-  By mistake, an early version of elb\_classic\_lb, elb\_instance, and
   elb\_classic\_lb\_facts modules were released and marked as
   stableinterface. These are now marked as preview in 2.4.1 and their
   parameters and return values may change in 2.5.0. Part of this
   mistake included deprecating the ec2\_elb\_lb, ec2\_lb, and
   ec2\_elb\_facts modules prematurely. These modules won't be
   deprecated until the replacements above have a stableinterface and
   the erroneous deprecation has been fixed in 2.4.1.
-  The docker\_container module has gained a new option, ``working_dir``
   which allows specifying the working directory for the command being
   run in the image.
-  The ec2\_win\_password module now requires the cryptography python
   module be installed to run
-  The stat module added a field, lnk\_target. When the file being
   stated is a symlink, lnk\_target will contain the target of the link.
   This differs from lnk\_source when the target is specified relative
   to the symlink. In this case, lnk\_target will remain relative while
   lnk\_source will be expanded to an absolute path.
-  The archive module has a new parameter exclude\_path which lists
   paths to exclude from the archive
-  The yum module has a new parameter security which limits state=latest
   to security updates
-  The template module gained a follow parameter to match with copy and
   file. Like those modules, template defaults this parameter to False.
   Previously, template hardcoded this to true.
-  Added a new parameter to command module that lets users specify data
   to pipe into the command's stdin.
-  The azure\_rm modules now accept a ``cloud_environment`` arg to
   access regional and private clouds.
-  The azure\_rm modules and inventory script now require at least
   version 2.0.0 of the Azure Python SDK.

New Modules
~~~~~~~~~~~

Cloud
^^^^^

-  amazon
-  aws\_api\_gateway
-  aws\_direct\_connect\_connection
-  aws\_direct\_connect\_link\_aggregation\_group
-  aws\_s3
-  aws\_s3\_bucket\_facts
-  aws\_waf\_facts
-  data\_pipeline
-  dynamodb\_ttl
-  ec2\_instance\_facts
-  ec2\_metadata\_facts
-  ec2\_vpc\_dhcp\_option\_facts
-  ec2\_vpc\_endpoint
-  ec2\_vpc\_endpoint\_facts
-  ec2\_vpc\_peering\_facts
-  ecs\_attribute
-  elb\_application\_lb
-  elb\_application\_lb\_facts
-  elb\_target\_group
-  elb\_target\_group\_facts
-  iam\_group
-  iam\_managed\_policy
-  lightsail
-  redshift\_facts
-  azure
-  azure\_rm\_acs
-  azure\_rm\_availabilityset
-  azure\_rm\_availabilityset\_facts
-  azure\_rm\_dnsrecordset
-  azure\_rm\_dnsrecordset\_facts
-  azure\_rm\_dnszone
-  azure\_rm\_dnszone\_facts
-  azure\_rm\_functionapp
-  azure\_rm\_functionapp\_facts
-  azure\_rm\_loadbalancer
-  azure\_rm\_loadbalancer\_facts
-  azure\_rm\_managed\_disk
-  azure\_rm\_managed\_disk\_facts
-  azure\_rm\_virtualmachine\_extension
-  azure\_rm\_virtualmachine\_scaleset
-  azure\_rm\_virtualmachine\_scaleset\_facts
-  atomic
-  atomic\_container
-  cloudstack
-  cs\_instance\_nic
-  cs\_instance\_nic\_secondaryip
-  cs\_network\_acl
-  cs\_network\_acl\_rule
-  cs\_storage\_pool
-  cs\_vpn\_gateway
-  digital\_ocean
-  digital\_ocean\_floating\_ip
-  docker
-  docker\_secret
-  docker\_volume
-  google
-  gce\_labels
-  gcp\_backend\_service
-  gcp\_forwarding\_rule
-  gcp\_healthcheck
-  gcp\_target\_proxy
-  gcp\_url\_map
-  misc
-  helm
-  ovirt
-  ovirt\_host\_storage\_facts
-  ovirt\_scheduling\_policies\_facts
-  ovirt\_storage\_connections
-  vmware
-  vcenter\_license
-  vmware\_guest\_find
-  vmware\_guest\_tools\_wait
-  vmware\_resource\_pool

Commands
^^^^^^^^

-  telnet

Crypto
^^^^^^

-  openssl\_certificate
-  openssl\_csr

Files
^^^^^

-  xml

Identity
^^^^^^^^

-  cyberark
-  cyberark\_authentication
-  cyberark\_user
-  ipa
-  ipa\_dnsrecord

Monitoring
^^^^^^^^^^

-  sensu\_client
-  sensu\_handler
-  sensu\_silence

Network
^^^^^^^

-  aci
-  aci\_aep
-  aci\_ap
-  aci\_bd
-  aci\_bd\_subnet
-  aci\_bd\_to\_l3out
-  aci\_contract
-  aci\_contract\_subject\_to\_filter
-  aci\_epg
-  aci\_epg\_monitoring\_policy
-  aci\_epg\_to\_contract
-  aci\_epg\_to\_domain
-  aci\_filter
-  aci\_filter\_entry
-  aci\_intf\_policy\_fc
-  aci\_intf\_policy\_l2
-  aci\_intf\_policy\_lldp
-  aci\_intf\_policy\_mcp
-  aci\_intf\_policy\_port\_channel
-  aci\_intf\_policy\_port\_security
-  aci\_l3out\_route\_tag\_policy
-  aci\_rest
-  aci\_taboo\_contract
-  aci\_tenant
-  aci\_tenant\_action\_rule\_profile
-  aci\_tenant\_span\_dst\_group
-  aci\_vrf
-  aireos
-  aireos\_command
-  aireos\_config
-  aruba
-  aruba\_command
-  aruba\_config
-  avi
-  avi\_actiongroupconfig
-  avi\_alertconfig
-  avi\_alertemailconfig
-  avi\_alertscriptconfig
-  avi\_alertsyslogconfig
-  avi\_authprofile
-  avi\_backup
-  avi\_backupconfiguration
-  avi\_cloud
-  avi\_cloudconnectoruser
-  avi\_cloudproperties
-  avi\_cluster
-  avi\_controllerproperties
-  avi\_dnspolicy
-  avi\_gslb
-  avi\_gslbapplicationpersistenceprofile
-  avi\_gslbgeodbprofile
-  avi\_gslbhealthmonitor
-  avi\_gslbservice
-  avi\_hardwaresecuritymodulegroup
-  avi\_httppolicyset
-  avi\_ipaddrgroup
-  avi\_ipamdnsproviderprofile
-  avi\_microservicegroup
-  avi\_network
-  avi\_networksecuritypolicy
-  avi\_poolgroupdeploymentpolicy
-  avi\_prioritylabels
-  avi\_scheduler
-  avi\_seproperties
-  avi\_serverautoscalepolicy
-  avi\_serviceengine
-  avi\_serviceenginegroup
-  avi\_snmptrapprofile
-  avi\_stringgroup
-  avi\_trafficcloneprofile
-  avi\_useraccountprofile
-  avi\_vrfcontext
-  avi\_vsdatascriptset
-  avi\_vsvip
-  avi\_webhook
-  bigswitch
-  bcf\_switch
-  cloudengine
-  ce\_aaa\_server
-  ce\_aaa\_server\_host
-  ce\_acl
-  ce\_acl\_advance
-  ce\_acl\_interface
-  ce\_bfd\_global
-  ce\_bfd\_session
-  ce\_bfd\_view
-  ce\_bgp
-  ce\_bgp\_af
-  ce\_bgp\_neighbor
-  ce\_bgp\_neighbor\_af
-  ce\_config
-  ce\_dldp
-  ce\_dldp\_interface
-  ce\_eth\_trunk
-  ce\_evpn\_bd\_vni
-  ce\_evpn\_bgp
-  ce\_evpn\_bgp\_rr
-  ce\_evpn\_global
-  ce\_facts
-  ce\_file\_copy
-  ce\_info\_center\_debug
-  ce\_info\_center\_global
-  ce\_info\_center\_log
-  ce\_info\_center\_trap
-  ce\_interface
-  ce\_interface\_ospf
-  ce\_ip\_interface
-  ce\_link\_status
-  ce\_mlag\_config
-  ce\_mlag\_interface
-  ce\_mtu
-  ce\_netconf
-  ce\_netstream\_aging
-  ce\_netstream\_export
-  ce\_netstream\_global
-  ce\_netstream\_template
-  ce\_ntp
-  ce\_ntp\_auth
-  ce\_ospf
-  ce\_ospf\_vrf
-  ce\_reboot
-  ce\_rollback
-  ce\_sflow
-  ce\_snmp\_community
-  ce\_snmp\_contact
-  ce\_snmp\_location
-  ce\_snmp\_target\_host
-  ce\_snmp\_traps
-  ce\_snmp\_user
-  ce\_startup
-  ce\_static\_route
-  ce\_stp
-  ce\_switchport
-  ce\_vlan
-  ce\_vrf
-  ce\_vrf\_af
-  ce\_vrf\_interface
-  ce\_vrrp
-  ce\_vxlan\_arp
-  ce\_vxlan\_gateway
-  ce\_vxlan\_global
-  ce\_vxlan\_tunnel
-  ce\_vxlan\_vap
-  cloudvision
-  cv\_server\_provision
-  eos
-  eos\_logging
-  eos\_vlan
-  eos\_vrf
-  f5
-  bigip\_command
-  bigip\_config
-  bigip\_configsync\_actions
-  bigip\_gtm\_pool
-  bigip\_iapp\_service
-  bigip\_iapp\_template
-  bigip\_monitor\_tcp\_echo
-  bigip\_monitor\_tcp\_half\_open
-  bigip\_provision
-  bigip\_qkview
-  bigip\_snmp
-  bigip\_snmp\_trap
-  bigip\_ucs
-  bigip\_user
-  bigip\_virtual\_address
-  fortios
-  fortios\_address
-  interface
-  net\_interface
-  net\_linkagg
-  net\_lldp\_interface
-  ios
-  ios\_interface
-  ios\_logging
-  ios\_static\_route
-  ios\_user
-  iosxr
-  iosxr\_banner
-  iosxr\_interface
-  iosxr\_logging
-  iosxr\_user
-  junos
-  junos\_banner
-  junos\_interface
-  junos\_l3\_interface
-  junos\_linkagg
-  junos\_lldp
-  junos\_lldp\_interface
-  junos\_logging
-  junos\_static\_route
-  junos\_system
-  junos\_vlan
-  junos\_vrf
-  layer2
-  net\_l2\_interface
-  net\_vlan
-  layer3
-  net\_l3\_interface
-  net\_vrf
-  netscaler
-  netscaler\_cs\_action
-  netscaler\_cs\_policy
-  netscaler\_cs\_vserver
-  netscaler\_gslb\_service
-  netscaler\_gslb\_site
-  netscaler\_gslb\_vserver
-  netscaler\_lb\_monitor
-  netscaler\_lb\_vserver
-  netscaler\_save\_config
-  netscaler\_server
-  netscaler\_service
-  netscaler\_servicegroup
-  netscaler\_ssl\_certkey
-  nuage
-  nuage\_vspk
-  nxos
-  nxos\_banner
-  nxos\_logging
-  panos
-  panos\_nat\_rule
-  panos\_object
-  panos\_security\_rule
-  protocol
-  net\_lldp
-  routing
-  net\_static\_route
-  system
-  net\_banner
-  net\_logging
-  net\_system
-  net\_user
-  vyos
-  vyos\_banner
-  vyos\_interface
-  vyos\_l3\_interface
-  vyos\_linkagg
-  vyos\_lldp
-  vyos\_lldp\_interface
-  vyos\_logging
-  vyos\_static\_route
-  vyos\_user

Notification
^^^^^^^^^^^^

-  bearychat
-  catapult
-  office\_365\_connector\_card

Remote Management
^^^^^^^^^^^^^^^^^

-  hpe
-  oneview\_fc\_network
-  imc
-  imc\_rest
-  manageiq
-  manageiq\_user

Source Control
^^^^^^^^^^^^^^

-  github\_deploy\_key
-  github\_issue

Storage
^^^^^^^

-  nuage\_vpsk
-  panos
-  panos\_sag
-  purestorage
-  purefa\_hg
-  purefa\_host
-  purefa\_pg
-  purefa\_snap
-  purefa\_volume

System
^^^^^^

-  aix\_lvol
-  awall
-  dconf
-  interfaces\_file

Web Infrastructure
^^^^^^^^^^^^^^^^^^

-  gunicorn
-  rundeck\_acl\_policy
-  rundeck\_project

Windows
^^^^^^^

-  win\_defrag
-  win\_domain\_group
-  win\_domain\_user
-  win\_dsc
-  win\_eventlog
-  win\_eventlog\_entry
-  win\_firewall
-  win\_group\_membership
-  win\_hotfix
-  win\_mapped\_drive
-  win\_pagefile
-  win\_power\_plan
-  win\_psmodule
-  win\_rabbitmq\_plugin
-  win\_route
-  win\_security\_policy
-  win\_toast
-  win\_user\_right
-  win\_wait\_for
-  win\_wakeonlan
