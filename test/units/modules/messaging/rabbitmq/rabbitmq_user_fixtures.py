rabbitmq_3_6_status = '''
Status of node rabbit@vagrant
[{pid,5519},
 {running_applications,
     [{rabbit,"RabbitMQ","version_num"},
      {mnesia,"MNESIA  CXC 138 12","4.15.3"},
      {ranch,"Socket acceptor pool for TCP protocols.","1.3.0"},
      {ssl,"Erlang/OTP SSL application","8.2.3"},
      {public_key,"Public key infrastructure","1.5.2"},
      {asn1,"The Erlang ASN1 compiler version 5.0.4","5.0.4"},
      {rabbit_common,
          "Modules shared by rabbitmq-server and rabbitmq-erlang-client",
          "3.6.10"},
      {xmerl,"XML parser","1.3.16"},
      {crypto,"CRYPTO","4.2"},
      {compiler,"ERTS  CXC 138 10","7.1.4"},
      {os_mon,"CPO  CXC 138 46","2.4.4"},
      {syntax_tools,"Syntax tools","2.1.4"},
      {sasl,"SASL  CXC 138 11","3.1.1"},
      {stdlib,"ERTS  CXC 138 10","3.4.3"},
      {kernel,"ERTS  CXC 138 10","5.4.1"}]},
 {os,{unix,linux}},
 {erlang_version,
     "Erlang/OTP 20 [erts-9.2] [source] [64-bit] [smp:1:1] [ds:1:1:10] [async-threads:64] [kernel-poll:true]\n"},
 {memory,
     [{total,49712064},
      {connection_readers,0},
      {connection_writers,0},
      {connection_channels,0},
      {connection_other,0},
      {queue_procs,2744},
      {queue_slave_procs,0},
      {plugins,0},
      {other_proc,17493000},
      {mnesia,65128},
      {metrics,184272},
      {mgmt_db,0},
      {msg_index,41832},
      {other_ets,1766176},
      {binary,43576},
      {code,21390833},
      {atom,891849},
      {other_system,8014118}]},
 {alarms,[]},
 {listeners,[{clustering,25672,"::"},{amqp,5672,"::"}]},
 {vm_memory_high_watermark,0.4},
 {vm_memory_limit,413340467},
 {disk_free_limit,50000000},
 {disk_free,61216505856},
 {file_descriptors,
     [{total_limit,65436},
      {total_used,2},
      {sockets_limit,58890},
      {sockets_used,0}]},
 {processes,[{limit,1048576},{used,153}]},
 {run_queue,0},
 {uptime,1795},
 {kernel,{net_ticktime,60}}]
root@vagrant:/home/vagrant# rabbitmqctl -q status
[{pid,5519},
 {running_applications,
     [{rabbit,"RabbitMQ","3.6.10"},
      {mnesia,"MNESIA  CXC 138 12","4.15.3"},
      {ranch,"Socket acceptor pool for TCP protocols.","1.3.0"},
      {ssl,"Erlang/OTP SSL application","8.2.3"},
      {public_key,"Public key infrastructure","1.5.2"},
      {asn1,"The Erlang ASN1 compiler version 5.0.4","5.0.4"},
      {rabbit_common,
          "Modules shared by rabbitmq-server and rabbitmq-erlang-client",
          "3.6.10"},
      {xmerl,"XML parser","1.3.16"},
      {crypto,"CRYPTO","4.2"},
      {compiler,"ERTS  CXC 138 10","7.1.4"},
      {os_mon,"CPO  CXC 138 46","2.4.4"},
      {syntax_tools,"Syntax tools","2.1.4"},
      {sasl,"SASL  CXC 138 11","3.1.1"},
      {stdlib,"ERTS  CXC 138 10","3.4.3"},
      {kernel,"ERTS  CXC 138 10","5.4.1"}]},
 {os,{unix,linux}},
 {erlang_version,
     "Erlang/OTP 20 [erts-9.2] [source] [64-bit] [smp:1:1] [ds:1:1:10] [async-threads:64] [kernel-poll:true]\n"},
 {memory,
     [{total,49770912},
      {connection_readers,0},
      {connection_writers,0},
      {connection_channels,0},
      {connection_other,0},
      {queue_procs,2744},
      {queue_slave_procs,0},
      {plugins,0},
      {other_proc,17554528},
      {mnesia,65128},
      {metrics,184272},
      {mgmt_db,0},
      {msg_index,41832},
      {other_ets,1766176},
      {binary,42816},
      {code,21390833},
      {atom,891849},
      {other_system,8012198}]},
 {alarms,[]},
 {listeners,[{clustering,25672,"::"},{amqp,5672,"::"}]},
 {vm_memory_high_watermark,0.4},
 {vm_memory_limit,413340467},
 {disk_free_limit,50000000},
 {disk_free,61216497664},
 {file_descriptors,
     [{total_limit,65436},
      {total_used,2},
      {sockets_limit,58890},
      {sockets_used,0}]},
 {processes,[{limit,1048576},{used,153}]},
 {run_queue,0},
 {uptime,17139},
 {kernel,{net_ticktime,60}}]'''

rabbitmq_3_7_status = \
    '{"pid":31701,"running_applications":[' \
    '["rabbit",[82,97,98,98,105,116,77,81],version_num],' \
    '["rabbit_common",[77,111,100,117,108,101,115,32,115,104,97,114,101,100,32,98,121,32,114,97,98,98,105,116,109,' \
    '113,45,115,101,114,118,101,114,32,97,110,100,32,114,97,98,98,105,116,109,113,45,101,114,108,97,110,103,45,99,' \
    '108,105,101,110,116],[51,46,55,46,54]],' \
    '["ranch_proxy_protocol",[82,97,110,99,104,32,80,114,111,120,121,32,80,114,111,116,111,99,111,108,32,84,114,97,' \
    '110,115,112,111,114,116],[49,46,53,46,48]],' \
    '["ranch",[83,111,99,107,101,116,32,97,99,99,101,112,116,111,114,32,112,111,111,108,32,102,111,114,32,84,67,80,' \
    '32,112,114,111,116,111,99,111,108,115,46],[49,46,53,46,48]],["ssl",[69,114,108,97,110,103,47,79,84,80,32,83,83,' \
    '76,32,97,112,112,108,105,99,97,116,105,111,110],[56,46,50,46,51]],' \
    '["public_key",[80,117,98,108,105,99,32,107,101,121,32,105,110,102,114,97,115,116,114,117,99,116,117,114,101],' \
    '[49,46,53,46,50]],' \
    '["asn1",[84,104,101,32,69,114,108,97,110,103,32,65,83,78,49,32,99,111,109,112,105,108,101,114,32,118,101,114,' \
    '115,105,111,110,32,53,46,48,46,52],[53,46,48,46,52]],' \
    '["crypto",[67,82,89,80,84,79],[52,46,50]],["xmerl",[88,77,76,32,112,97,114,115,101,114],[49,46,51,46,49,54]],' \
    '["recon",[68,105,97,103,110,111,115,116,105,99,32,116,111,111,108,115,32,102,111,114,32,112,114,111,100,117,99,' \
    '116,105,111,110,32,117,115,101],[50,46,51,46,50]],' \
    '["inets",[73,78,69,84,83,32,32,67,88,67,32,49,51,56,32,52,57],[54,46,52,46,53]],' \
    '["jsx",[97,32,115,116,114,101,97,109,105,110,103,44,32,101,118,101,110,116,101,100,32,106,115,111,110,32,112,97,' \
    '114,115,105,110,103,32,116,111,111,108,107,105,116],[50,46,56,46,50]],["os_mon",[67,80,79,32,32,67,88,67,32,49,' \
    '51,56,32,52,54],[50,46,52,46,52]],' \
    '["mnesia",[77,78,69,83,73,65,32,32,67,88,67,32,49,51,56,32,49,50],[52,46,49,53,46,51]],' \
    '["lager",[69,114,108,97,110,103,32,108,111,103,103,105,110,103,32,102,114,97,109,101,119,111,114,107],' \
    '[51,46,53,46,49]],' \
    '["goldrush",[69,114,108,97,110,103,32,101,118,101,110,116,32,115,116,114,101,97,109,32,112,114,111,99,101,115,' \
    '115,111,114],[48,46,49,46,57]],["compiler",[69,82,84,83,32,32,67,88,67,32,49,51,56,32,49,48],[55,46,49,46,52]],' \
    '["syntax_tools",[83,121,110,116,97,120,32,116,111,111,108,115],[50,46,49,46,52]],' \
    '["syslog",[65,110,32,82,70,67,32,51,49,54,52,32,97,110,100,32,82,70,67,32,53,52,50,52,32,99,111,109,112,108,' \
    '105,97,110,116,32,108,111,103,103,105,110,103,32,102,114,97,109,101,119,111,114,107,46],[51,46,52,46,50]],' \
    '["sasl",[83,65,83,76,32,32,67,88,67,32,49,51,56,32,49,49],[51,46,49,46,49]],' \
    '["stdlib",[69,82,84,83,32,32,67,88,67,32,49,51,56,32,49,48],[51,46,52,46,51]],' \
    '["kernel",[69,82,84,83,32,32,67,88,67,32,49,51,56,32,49,48],[53,46,52,46,49]]],' \
    '"os":["unix","linux"],"erlang_version":[69,114,108,97,110,103,47,79,84,80,32,50,48,32,91,101,114,116,115,45,57,' \
    '46,50,93,32,91,115,111,117,114,99,101,93,32,91,54,52,45,98,105,116,93,32,91,115,109,112,58,49,58,49,93,32,91,' \
    '100,115,58,49,58,49,58,49,48,93,32,91,97,115,121,110,99,45,116,104,114,101,97,100,115,58,54,52,93,32,91,107,' \
    '101,114,110,101,108,45,112,111,108,108,58,116,114,117,101,93,10],' \
    '"memory":{"connection_readers":0,"connection_writers":0,"connection_channels":0,' \
    '"connection_other":0,"queue_procs":0,"queue_slave_procs":0,"plugins":5736,"other_proc":23159832,' \
    '"metrics":184608,"mgmt_db":0,"mnesia":76896,"other_ets":1882856,"binary":64120,"msg_index":57184,' \
    '"code":24981937,"atom":1041593,"other_system":8993494,"allocated_unused":13066752,"reserved_unallocated":0,' \
    '"strategy":"rss","total":{"erlang":60448256,"rss":72720384,"allocated":73515008}},"alarms":[],' \
    '"listeners":[["clustering",25672,[58,58]],["amqp",5672,[58,58]]],"vm_memory_calculation_strategy":"rss",' \
    '"vm_memory_high_watermark":0.4,"vm_memory_limit":413340467,"disk_free_limit":50000000,"disk_free":61108576256,' \
    '"file_descriptors":{"total_limit":924,"total_used":4,"sockets_limit":829,"sockets_used":0},' \
    '"processes":{"limit":1048576,"used":214},"run_queue":0,"uptime":173,"kernel":["net_ticktime",60]}'

rabbitmq_3_8_status = \
    '{"active_plugins":[],"alarms":[],"config_files":[],"data_directory":"/var/lib/rabbitmq/mnesia/rabbit@vagrant",' \
    '"disk_free":60898615296,"disk_free_limit":50000000,"enabled_plugin_file":"/etc/rabbitmq/enabled_plugins",' \
    '"erlang_version":"Erlang/OTP 21 [erts-10.3.5.8] [source] [64-bit] [smp:1:1] [ds:1:1:10] [async-threads:64]",' \
    '"file_descriptors":{"sockets_limit":29399,"sockets_used":0,"total_limit":32668,"total_used":4},' \
    '"listeners":[{"interface":"[::]","node":"rabbit@vagrant","port":25672,"protocol":"clustering",' \
    '"purpose":"inter-node and CLI tool communication"},{"interface":"[::]","node":"rabbit@vagrant",' \
    '"port":5672,"protocol":"amqp","purpose":"AMQP 0-9-1 and AMQP 1.0"}],' \
    '"log_files":["/var/log/rabbitmq/rabbit@vagrant.log","/var/log/rabbitmq/rabbit@vagrant_upgrade.log"],' \
    '"memory":{"allocated_unused":14962432,"atom":1180881,"binary":82304,"code":26631176,"connection_channels":0,' \
    '"connection_other":0,"connection_readers":0,"connection_writers":0,"metrics":195308,"mgmt_db":0,"mnesia":76896,' \
    '"msg_index":57088,"other_ets":2666736,"other_proc":25333896,"other_system":10068879,"plugins":11732,' \
    '"queue_procs":0,"queue_slave_procs":0,"quorum_ets":42368,"quorum_queue_procs":0,"reserved_unallocated":0,' \
    '"strategy":"rss","total":{"erlang":66347264,"rss":80506880,"allocated":81309696}},"net_ticktime":60,' \
    '"os":"Linux","pid":9829,"processes":{"limit":1048576,"used":259},"rabbitmq_version":"version_num","run_queue":1,' \
    '"totals":{"virtual_host_count":2,"connection_count":0,"queue_count":0},"uptime":66,' \
    '"vm_memory_calculation_strategy":"rss","vm_memory_high_watermark_limit":413340467,' \
    '"vm_memory_high_watermark_setting":{"relative":0.4}}'
