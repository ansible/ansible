Config Encoder Filters
======================

.. versionadded:: 2.2


Motivation
----------

Ansible Galaxy contains a lot of useful roles. Some of them exist in
many variations which differ only by their parameterization. The
parameterization is often used mainly in templates which generate the
configuration file. A good example such issues are roles for Nginx of
which you can find almost 200 in the Ansible Galaxy.

Nginx is possible to configure in infinite number of ways and therefore
is almost impossible to create an Ansible template file which would
capture all possible variations of the configuration. Even if a suitable
roles is found, users often want to customize even more. This is where
people normally clone the role and add parameters they are missing. Some
people try to get the change back into the original role by creating a
pull request (PR) but sometimes such change is not accepted by the
maintainer of the original role and the user ends up maintaining his/her
own clone forever.

This is why the Config Encoder filters were developed to facilitate the
creation of Ansible roles with universal configuration. The structure of
the configuration file is described as a YAML data structure stored in a
variable. The variable together with he Config Encoder filter is then
used in the template file which is used to generate the final
configuration file. This approach allows to shift the paradigm of
thinking about configuration files as templates to thinking about them as
data structures. The data structure can be dynamically generated which
allows to create truly universal configuration.


Example
-------

Imagine the following INI file::

    [section1]
    option11=value11
    option12=value12

Such configuration file can be described as a YAML data structure::

    myapp_config:
      section1:
        option11: value11
        option12: value12

The variable is then used together with the ``encode_ini`` Config Encoder
filter in the template file ``myapp.cfg.j2`` like this::

    {{ myapp_config | encode_ini }}

And finally, the template file is used in a task like this::

    - name: Create config file
      template:
        src: myapp.cfg.j2
        dest: /etc/myapp/myapp.cfg

When the task is executed, it creates exactly the same file as the
original INI file.

So we can describe the configuration as a data structure which is then
converted into the final configuration file format with the Config
Encoder filter.

In order to change the above configuration, we would have to overwrite
the ``myapp_config`` which is not very practical. Therefore we break the
monolithic variable into a set of variables which will allow us to change
any part of the configuration without the need to overwrite the whole
data structure::

    myapp_config_section1_option11: value11
    myapp_config_section1_option12: value12

    myapp_config_section1__default:
      option11: "{{ myapp_config_section1_option11 }}"
      option12: "{{ myapp_config_section1_option12 }}"

    myapp_config_section1__custom: {}

    myapp_config_default:
      section1: "{{
        myapp_config_section1__default.update(myapp_config_section1__custom) }}{{
        myapp_config_section1__default }}"

    myapp_config__custom: {}

    myapp_config: "{{
      myapp_config__default.update(myapp_config__custom) }}{{
      myapp_config__default }}"

Like this, if we want to change the value of the ``option11``, we only
override the variable ``myapp_config_section1_option11``::

    myapp_config_section1_option11: My new value

If we want to add a new option into the ``section1``, we add it into the
variable ``myapp_config_section1__custom`` which is then merged with the
default list of options::

    myapp_config_section1__custom:
      section13: value13

And if we want to add a new section, we add it into the variable
``myapp_config__custom`` which is then merged with the default list of
sections::

    myapp_config__custom:
      section2:
        option21: value21

The above is showing an example for INI configuration files only but the
same principle is possible to use for all the supported Config Encoders
listed bellow.


Supported encoders
------------------

The following is the list of supported Config Encoder filters. Each
filter requires special data structure as its input. Each filter also has
a set of parameters which can modify the behaviour of the filter.


encode_apache
^^^^^^^^^^^^^

This filter helps to create configuration in the format used by Apache
web server. The expected data structure is the following::

    my_apache_vhost:
      content:
        - sections:
          - name: VirtualHost
            param: "*:80"
            content:
              - options:
                - DocumentRoot: /www/example1
                - ServerName: www.example.com
                - ErrorLog: /var/log/httpd/www.example.com-error_log
                - CustomLog:
                  - /var/log/httpd/www.example.com-access_log
                  - common
                - "#": Other directives here ...

The variable starts with ``content`` which can contain list of
``sections`` or ``options``. ``sections`` then contain list of individual
sections which has the ``name``, ``param`` and ``content`` parameter. The
``content`` can again contain a list of `sections`` or ``options``.

The above variable can be used in the template file like this::

    {{ my_apache_vhost | encode_apache }}

The output of such template would be::

    <VirtualHost *:80>
      DocumentRoot /www/example1
      ServerName www.example.com
      ErrorLog /var/log/httpd/www.example.com-error_log
      CustomLog /var/log/httpd/www.example.com-access_log common
      # "Other directives here ..."
    </VirtualHost>

The filter can have the following parameters:

- ``convert_bools=false``

  Indicates whether Boolean values presented as a string should be
  converted to a real Boolean value. For example ``var1: 'True'`` would
  be represented as a string but by using the ``convert_bools=true`` it
  will be converted into Boolean like it would be defined like ``var1:
  true``.

- ``convert_nums=false``

  Indicates whether number presented as a string should be converted to
  number. For example ``var1: '123'`` would be represented as a string
  but by using the ``convert_nums=true`` it will be converted it to a
  number like it would be defined like ``var1: 123``. It's also possible
  to use the YAML type casting to convert string to number (e.g. ``!!int
  "1234"``, ``!!float "3.14"``).

- ``indent="  "``

  Defines the indentation unit.

- ``level=0``

  Indicates the initial level of the indentation. Value ``0`` starts
  indenting from the beginning of the line. Setting the value to higher
  than ``0`` indents the content by ``indent * level``.

- ``quote_all_nums=false``

  Number values are not quoted by default. This parameter will force to
  quote all numbers.

- ``quote_all_strings=false``

  String values are quoted only if they contain a space. This parameter
  will force to quote all strings regardless if the they contain the
  space or not.


encode_erlang
^^^^^^^^^^^^^

This filter helps to create configuration in the Erlang format. The
expected data structure is the following::

    my_rabbitmq_config:
      - rabbit:
        - tcp_listeners:
          - '"127.0.0.1"': 5672
        - ssl_listeners:
          - 5671
        - ssl_options:
          - cacertfile: /path/to/testca/cacert.pem
          - certfile: /path/to/server/cert.pem
          - keyfile: /path/to/server/key.pem
          - verify: verify_peer
          - fail_if_no_peer_cert: true

The variable consists of a lists of dictionaries. The value of the key-value
pair can be another list or simple value like a string or a number. Erlang
tuples can be enforced by prepending the value with the special character
specified in the ``atom_value_indicator``.

The above variable can be used in the template file like this::

    {{ my_rabbitmq_config | encode_erlang }}

The output of such template would be::

    [
      {rabbit, [
          {tcp_listeners, [
              {"127.0.0.1", 5672}
          ]},
          {ssl_listeners, [
            5671
          ]},
          {ssl_options, [
              {cacertfile, "/path/to/testca/cacert.pem"},
              {certfile, "/path/to/server/cert.pem"},
              {keyfile, "/path/to/server/key.pem"},
              {verify, "verify_peer"},
              {fail_if_no_peer_cert, true}
          ]}
      ]}
    ].

The filter can have the following parameters:

- ``atom_value_indicator=":"``

  The value of this parameter indicates the string which must be
  prepended to a string value to treat it as an atom value.

- ``convert_bools=false``

  Indicates whether Boolean values presented as a string should be
  converted to a real Boolean value. For example ``var1: 'True'`` would
  be represented as a string but by using the ``convert_bools=true`` it
  will be converted into Boolean like it would be defined like ``var1:
  true``.

- ``convert_nums=false``

  Indicates whether number presented as a string should be converted to
  number. For example ``var1: '123'`` would be represented as a string
  but by using the ``convert_nums=true`` it will be converted it to a
  number like it would be defined like ``var1: 123``. It's also possible
  to use the YAML type casting to convert string to number (e.g. ``!!int
  "1234"``, ``!!float "3.14"``).

- ``indent="  "``

  Defines the indentation unit.

- ``level=0``

  Indicates the initial level of the indentation. Value ``0`` starts
  indenting from the beginning of the line. Setting the value to higher
  than ``0`` indents the content by ``indent * level``.


encode_haproxy
^^^^^^^^^^^^^^

This filter helps to create configuration in the format used in Haproxy.
The expected data structure is the following::

    my_haproxy_config:
      - global:
        - daemon
        - maxconn 256
      - "# This is the default section"
      - defaults:
        - mode http
        - timeout connect 5000ms
        - timeout client 50000ms
        - timeout server 50000ms
      - frontend http-in:
        - "# This is the bind address/port"
        - bind *:80
        - default_backend servers
        - backend servers
        - server server1 127.0.0.1:8000 maxconn 32

The variable is a list which can contain a simple string value or a dictionary
which indicates a section.

The above variable can be used in the template file like this::

    {{ my_haproxy_config | encode_haproxy }}

The output of such template would be::

    global
      daemon
      maxconn 256

    # This is the default section
    defaults
      mode http
      timeout connect 5000ms
      timeout client 50000ms
      timeout server 50000ms

    frontend http-in
      # This is the bind address/port
      bind *:80
      default_backend servers
      backend servers
      server server1 127.0.0.1:8000 maxconn 32

The filter can have the following parameters:

- ``indent="  "``

  Defines the indentation unit.


encode_ini
^^^^^^^^^^

This filter helps to create configuration in the INI format. The expected
data structure is the following::

    my_rsyncd_config:
      uid: nobody
      gid: nobody
      use chroot: no
      max connections: 4
      syslog facility: local5
      pid file: /run/rsyncd.pid
      ftp:
        path: /srv/ftp
        comment: ftp area

The variable consist of dictionaries which can be nested. If the value of the
key-value pair on the first level is of a simple type (string, number, boolean),
such pair is considered to be global and gets processed first. If the value of
the key-value pair on the first level is another dictionary, the key is
considered to be the name of the section and the inner dictionary as properties
of the section.

The above variable can be used in the template file like this::

    {{ my_rsyncd_config | encode_ini }}

The output of such template would be::

    gid=nobody
    max connections=4
    pid file=/run/rsyncd.pid
    syslog facility=local5
    uid=nobody
    use chroot=False

    [ftp]
    comment=ftp area
    path=/srv/ftp

The filter can have the following parameters:

- ``delimiter="="``

  Sign separating the *property* and the *value*. By default it's set to
  ``'='`` but it can also be set for example to ``' = '``.

- ``quote=""``

  Sets the quoting of the value. Use ``quote="'"`` or ``quote='"'``.

- ``section_is_comment=false``

  If this parameter is set to ``true``, the section value will be used as
  a comment for the following properties of the section.

- ``ucase_prop=false``

  Indicates whether the *property* should be made upper case.


encode_json
^^^^^^^^^^^

This filter helps to create configuration in the JSON format. The
expected data structure is the following::

    my_sensu_client_config:
      client:
        name: localhost
        address: 127.0.0.1
        subscriptions:
          - test

Because JSON is very similar to YAML, the variable consists of
dictionaries of which value can be either an simple type (number, string,
boolean), list or another dictionary. All can be nested in any number of
levels.

The above variable can be used in the template file like this::

    {{ my_sensu_client_config | encode_json }}

The output of such template would be::

    {
      "client": {
        "address": "127.0.0.1",
        "name": "localhost",
        "subscriptions": [
          "test"
        ]
      }
    }

The filter can have the following parameters:

- ``convert_bools=false``

  Indicates whether Boolean values presented as a string should be
  converted to a real Boolean value. For example ``var1: 'True'`` would
  be represented as a string but by using the ``convert_bools=true`` it
  will be converted into Boolean like it would be defined like ``var1:
  true``.

- ``convert_nums=false``

  Indicates whether number presented as a string should be converted to
  number. For example ``var1: '123'`` would be represented as a string
  but by using the ``convert_nums=true`` it will be converted it to a
  number like it would be defined like ``var1: 123``. It's also possible
  to use the YAML type casting to convert string to number (e.g. ``!!int
  "1234"``, ``!!float "3.14"``).

- ``indent="  "``

  Defines the indentation unit.

- ``level=0``

  Indicates the initial level of the indentation. Value ``0`` starts
  indenting from the beginning of the line. Setting the value to higher
  than ``0`` indents the content by ``indent * level``.


encode_logstash
^^^^^^^^^^^^^^^

This filter helps to create configuration in the format used by Logstash.
The expected data structure is the following::

    my_logstash_config:
      - :input:
          - :file:
              path: /tmp/access_log
              start_position: beginning
      - :filter:
          - ':if [path] =~ "access"':
              - :mutate:
                  replace:
                    type: apache_access
              - :grok:
                  match:
                    message: "%{COMBINEDAPACHELOG}"
      - :date:
          - match:
              - timestamp
              - dd/MMM/yyyy:HH:mm:ss Z
      - :output:
          - :elasticsearch:
              hosts:
                - localhost:9200
          - :stdout:
              codec: rubydebug

The variable consists of a list of sections where each section is
prefixed by a special character specified by the ``section_prefix``
(``:`` by default). The value of the top level sections can be either
another section or a dictionary. The value of the dictionary can be a
simple value, list or another dictionary.

The above variable can be used in the template file like this::

    {{ my_logstash_config | encode_logstash }}

The output of such template would be::

    input {
      file {
        path => "/tmp/access_log"
        start_position => "beginning"
      }
    }
    filter {
      if [path] =~ "access" {
        mutate {
          replace => {
            "type" => "apache_access"
          }
        }
        grok {
          match => {
            "message" => "%{COMBINEDAPACHELOG}"
          }
        }
      }
    }
    date {
      match => [
        "timestamp",
        "dd/MMM/yyyy:HH:mm:ss Z"
      ]
    }
    output {
      elasticsearch {
        hosts => [
          "localhost:9200"
        ]
      }
      stdout {
        codec => "rubydebug"
      }
    }

The filter can have the following parameters:

- ``convert_bools=false``

  Indicates whether Boolean values presented as a string should be
  converted to a real Boolean value. For example ``var1: 'True'`` would
  be represented as a string but by using the ``convert_bools=true`` it
  will be converted into Boolean like it would be defined like ``var1:
  true``.

- ``convert_nums=false``

  Indicates whether number presented as a string should be converted to
  number. For example ``var1: '123'`` would be represented as a string
  but by using the ``convert_nums=true`` it will be converted it to a
  number like it would be defined like ``var1: 123``. It's also possible
  to use the YAML type casting to convert string to number (e.g. ``!!int
  "1234"``, ``!!float "3.14"``).

- ``indent="  "``

  Defines the indentation unit.

- ``level=0``

  Indicates the initial level of the indentation. Value ``0`` starts
  indenting from the beginning of the line. Setting the value to higher
  than ``0`` indents the content by ``indent * level``.

- ``section_prefix=":"``

  This parameter specifies which character will be used to identify the
  Logstash section.


encode_nginx
^^^^^^^^^^^^

This filter helps to create configuration in the format used by Nginx
wweb server. The expected data structure is the following::

    my_nginx_vhost_config:
      - server:
        - listen 80
        - server_name $hostname
        - "location /":
          - root /srv/www/myapp
          - index index.html

As Nginx configuration is order sensitive, the all configuration is
defined as a nested list. As it would be difficult to recognize how many
elements each configuration definition has, the list item value is no
further separated into key/value dictionary. Every line of the
configuration is treated either as a key indicating another nested list
or simply as a string.

The above variable can be used in the template file like this::

    {{ my_nginx_vhost | encode_nginx }}

The output of such template would be::

    server {
      listen 80;
      server_name $hostname;

      location / {
        root /srv/www/myapp;
        index index.html;
      }
    }

The filter can have the following parameters:

- ``indent="  "``

  Defines the indentation unit.

- ``level=0``

  Indicates the initial level of the indentation. Value ``0`` starts
  indenting from the beginning of the line. Setting the value to higher
  than ``0`` indents the content by ``indent * level``.


encode_pam
^^^^^^^^^^

This filter helps to create configuration in the format user by Linux
Pluggable Authentication Modules (PAM). The expected data structure is
the following::

    my_system_auth_config:
      aa:
        type: auth
        control: required
        path: pam_unix.so
        args:
          - try_first_pass
          - nullok
      bb:
        type: auth
        control: optional
        path: pam_permit.so
      cc:
        type: auth
        control: required
        path: pam_env.so
      dd:
        type: account
        control: required
        path: pam_unix.so
      ee:
        type: account
        control: optional
        path: pam_permit.so
      ff:
        type: account
        control: required
        path: pam_time.so
      gg:
        type: password
        control: required
        path: pam_unix.so
        args:
          - try_first_pass
          - nullok
          - sha512
          - shadow
      hh:
        type: password
        control: optional
        path: pam_permit.so
        args:
      ii:
        type: session
        control: required
        path: pam_limits.so
      jj:
        type: session
        control: required
        path: pam_unix.so
      kk:
        type: session
        control: optional
        path: pam_permit.so

The variable is a dictionary of which the key is a labels and the value
is the PAM rule. The label is used to order the PAM rules. Using labels
with even number of characters allows to insert another rule in between
of any two rules.

The above variable can be used in the template file like this::

    {{ my_system_auth_config | encode_pam }}

The output of such template would be::

    auth  required  pam_unix.so  try_first_pass nullok
    auth  optional  pam_permit.so
    auth  required  pam_env.so

    account  required  pam_unix.so
    account  optional  pam_permit.so
    account  required  pam_time.so

    password  required  pam_unix.so  try_first_pass nullok sha512 shadow
    password  optional  pam_permit.so

    session  required  pam_limits.so
    session  required  pam_unix.so
    session  optional  pam_permit.so

The filter can have the following parameters:

- ``print_label=false``

  Print labels as a comment in the output.

- ``separate_types=true``

  Add a newline between the groups of types.

- ``separator="  "``

  Separator between the collection of tokens.


encode_toml
^^^^^^^^^^^

This filter helps to create configuration in the TOML format. The
expected data structure is the following::

    my_grafana_ldap_config:
      verbose_logging: false
      servers:
        - host: 127.0.0.1
          port: 389
          use_ssl: false
          ssl_skip_verify: false
          bind_dn: cn=admin,dc=grafana,dc=org
          bind_password: grafana
          search_filter: "(cn=%s)"
          search_base_dns:
            - dc=grafana,dc=org
      servers.attributes:
        name: givenName
        surname: sn
        username: cn
        member_of: memberOf
        email: email
      servers.group_mappings:
        - group_dn: cn=admins,dc=grafana,dc=org
          org_role: Admin
        - group_dn: cn=users,dc=grafana,dc=org
          org_role: Editor
        - group_dn: "*"
          org_role: Viewer

The variable is a dictionary of which value can be either a simple type
(number, string, boolean), list or another dictionary. The dictionaries
and lists can be nested.

The above variable can be used in the template file like this::

    {{ my_grafana_ldap_config | encode_toml }}

The output of such template would be::

    verbose_logging = false

      [[servers]]
      bind_dn = "cn=admin,dc=grafana,dc=org"
      bind_password = "grafana"
      host = "127.0.0.1"
      port = 389
      search_base_dns = ["dc=grafana,dc=org"]
      search_filter = "(cn=%s)"
      ssl_skip_verify = false
      use_ssl = false

    [servers.attributes]
    email = "email"
    member_of = "memberOf"
    name = "givenName"
    surname = "sn"
    username = "cn"

      [[servers.group_mappings]]
      group_dn = "cn=admins,dc=grafana,dc=org"
      org_role = "Admin"

      [[servers.group_mappings]]
      group_dn = "cn=users,dc=grafana,dc=org"
      org_role = "Editor"

      [[servers.group_mappings]]
      group_dn = "*"
      org_role = "Viewer"

The filter can have the following parameters:

- ``convert_bools=false``

  Indicates whether Boolean values presented as a string should be
  converted to a real Boolean value. For example ``var1: 'True'`` would
  be represented as a string but by using the ``convert_bools=true`` it
  will be converted into Boolean like it would be defined like ``var1:
  true``.

- ``convert_nums=false``

  Indicates whether number presented as a string should be converted to
  number. For example ``var1: '123'`` would be represented as a string
  but by using the ``convert_nums=true`` it will be converted it to a
  number like it would be defined like ``var1: 123``. It's also possible
  to use the YAML type casting to convert string to number (e.g. ``!!int
  "1234"``, ``!!float "3.14"``).

- ``indent="  "``

  Defines the indentation unit.

- ``level=0``

  Indicates the initial level of the indentation. Value ``0`` starts
  indenting from the beginning of the line. Setting the value to higher
  than ``0`` indents the content by ``indent * level``.

- ``quote='"'``

  Sets the quoting of the value. Use ``quote="'"`` or ``quote='"'``.


encode_xml
^^^^^^^^^^

This filter helps to create configuration in the XML format. The expected
data structure is the following::

    my_oddjob_config:
      - oddjobconfig:
        - service:
          - ^name: com.redhat.oddjob
          - object:
            - ^name: /com/redhat/oddjob
            - interface:
              - ^name: com.redhat.oddjob
              - method:
                - ^name: listall
                - allow:
                  - ^min_uid: 0
                  - ^max_uid: 0
              - method:
                - ^name: list
                - allow: null
              - method:
                - ^name: quit
                - allow:
                  - ^user: root
              - method:
                - ^name: reload
                - allow:
                  - ^user: root
        - include:
          - ^ignore_missing: "yes"
          - /etc/oddjobd.conf.d/*.conf
        - include:
          - ^ignore_missing: "yes"
          - /etc/oddjobd-local.conf

The variable can be a list of dictionaries, lists or strings. This config
encoder does not handle mixed content very well so the safest way how to
include mixed content is to define it as a string and use the parameter
``escape_xml=false``. This config encoder also produces no XML declaration.
Any XML declaration or DOCTYPE must be a part of the template file.

The above variable can be used in the template file like this::

    {{ my_oddjob_config | encode_xml }}

The output of such template would be::

    <oddjobconfig>
      <service name="com.redhat.oddjob">
        <object name="/com/redhat/oddjob">
          <interface name="com.redhat.oddjob">
            <method name="listall">
              <allow min_uid="0" max_uid="0" />
            </method>
            <method name="list">
              <allow />
            </method>
            <method name="quit">
              <allow user="root" />
            </method>
            <method name="reload">
              <allow user="root" />
            </method>
          </interface>
        </object>
      </service>
      <include ignore_missing="yes">/etc/oddjobd.conf.d/*.conf</include>
      <include ignore_missing="yes">/etc/oddjobd-local.conf</include>
    </oddjobconfig>

The filter can have the following parameters:

- ``attribute_sign="^"``

  XML attribute indicator.

- ``indent="  "``

  Defines the indentation unit.

- ``level=0``

  Indicates the initial level of the indentation. Value ``0`` starts
  indenting from the beginning of the line. Setting the value to higher
  than ``0`` indents the content by ``indent * level``.


encode_yaml
^^^^^^^^^^^

This filter helps to create configuration in the YAML format. The
expected data structure is the following::

    my_mongodb_config:
      systemLog:
        destination: file
        logAppend: true
        path: /var/log/mongodb/mongod.log
      storage:
        dbPath: /var/lib/mongo
        journal:
          enabled: true
      processManagement:
        fork: true
        pidFilePath: /var/run/mongodb/mongod.pid
      net:
        port: 27017
        bindIp: 127.0.0.1

The variable is ordinary YAML. The only purpose of this encoder filter is
to be able to convert YAML data structure into the string in a template
file in unified way compatible with the other config encoders.

The above variable can be used in the template file like this::

    {{ my_mongodb_config | encode_yaml }}

The output of such template would be::

    net:
      bindIp: "127.0.0.1"
      port: 27017
    processManagement:
      fork: true
      pidFilePath: "/var/run/mongodb/mongod.pid"
    storage:
      dbPath: "/var/lib/mongo"
      journal:
        enabled: true
    systemLog:
      destination: "file"
      logAppend: true
      path: "/var/log/mongodb/mongod.log"

The filter can have the following parameters:

- ``convert_bools=false``

  Indicates whether Boolean values presented as a string should be
  converted to a real Boolean value. For example ``var1: 'True'`` would
  be represented as a string but by using the ``convert_bools=true`` it
  will be converted into Boolean like it would be defined like ``var1:
  true``.

- ``convert_nums=false``

  Indicates whether number presented as a string should be converted to
  number. For example ``var1: '123'`` would be represented as a string
  but by using the ``convert_nums=true`` it will be converted it to a
  number like it would be defined like ``var1: 123``. It's also possible
  to use the YAML type casting to convert string to number (e.g. ``!!int
  "1234"``, ``!!float "3.14"``).

- ``indent="  "``

  Defines the indentation unit.

- ``level=0``

  Indicates the initial level of the indentation. Value ``0`` starts
  indenting from the beginning of the line. Setting the value to higher
  than ``0`` indents the content by ``indent * level``.

- ``quote='"'``

  Sets the quoting of the value. Use ``quote="'"`` or ``quote='"'``.


Utilities
---------

The followng is a list of utilities that can be used in conjunction with the
Config Encoder filters.


template_replace
^^^^^^^^^^^^^^^^

This filter allows to use extra templating layer which gets processed during
the template file processing. That can be useful if it's necessary to create
repetitive but slightly different definitions inside the template file.

The extra templating layer is represented by a templating variable which
contains specially decorated variables which get replaced by its real value at
the time of template file processing. The template variable can be composed
dynamically which provides extra flexibility that would otherwise have to be
hardcoded in the template file.

The filter expects the template variable containing the specially decorated
variables as its input. The filter has one parameter which is used to replaced
the specially decorated variables in the template variable.

Let's have a look at an example of such usage::

    # The variable used as the replacement in the template variable
    my_clients:
      - host: myclient01
        jobdefs: Default
        password: Passw0rd1
        file_retention: 30 days
      - host: myclient02
        jobdefs: HomeOnly
        password: Passw0rd2
        file_retention: 90 days

    # The actual template variable used in the template file
    bacula_director_config_job_client:
      # First template variable containing the specially decorated variables
      - template:
          - Job:
            - Name = Job-{[{ item['jobdefs'] }]}-{[{ item['host'] }]}
            - Client = {[{ item['host'] }]}-fd
            - JobDefs = {[{ item['jobdefs'] }]}
        # Variable used to replace the specially decorated variables
        items: "{{ my_clients }}"
      # Second template and its items
      - template:
          - Client:
            - Name = {[{ item['host'] }]}-fd
            - Address = {[{ item['host'] }]}
            - FD Port = 9102
            - Catalog = Default
            - Password = {[{ item['password'] }]}
            - File Retention = {[{ item['file_retention'] }]}
            - Job Retention = 3 months
            - AutoPrune = yes
        items: "{{ my_clients }}"

The above variable can be used together with the `template_replace` filter in
the template file (``bacula-dir.conf.j2``) like this::

    {% for record in bacula_director_config_job_client %}
      {%- for item in record['items'] -%}
        {{ record['template'] | template_replace(item) | encode_nginx }}{{ "\n" }}
      {%- endfor -%}
    {% endfor %}

The template file can be called from the playbook/role like this::

    - name: Configure Bacula Director
      template:
        src: bacula-dir.conf.j2
        dest: /etc/bacula/bacula-dir.conf

And the result of such usage is the following::

    Job {
      Name = Job-Default-myclient01;
      Client = myclient01-fd;
      JobDefs = Default;
    }

    Job {
      Name = Job-HomeOnly-myclient02;
      Client = myclient02-fd;
      JobDefs = HomeOnly;
    }

    Client {
      Name = myclient01-fd;
      Address = myclient01;
      FD Port = 9102;
      Catalog = Default;
      Password = Passw0rd1;
      File Retention = 30 days;
      Job Retention = 3 months;
      AutoPrune = yes;
    }

    Client {
      Name = myclient02-fd;
      Address = myclient02;
      FD Port = 9102;
      Catalog = Default;
      Password = Passw0rd2;
      File Retention = 90 days;
      Job Retention = 3 months;
      AutoPrune = yes;
    }


.. seealso::

   :doc:`playbooks`
       An introduction to playbooks
   :doc:`playbooks_filters`
       Introduction to Jinja2 filters and their uses
   :doc:`playbooks_conditionals`
       Conditional statements in playbooks
   :doc:`playbooks_variables`
       All about variables
   :doc:`playbooks_loops`
       Looping in playbooks
   :doc:`playbooks_roles`
       Playbook organization by roles
   :doc:`playbooks_best_practices`
       Best practices in playbooks
   `User Mailing List <http://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
