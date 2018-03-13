#!/usr/bin/env python

# Only needed until we can enable a pylint test for this.  We may have to write
# one or add it to another existing test (like the one to warn on inappropriate
# variable names).  Adding to an existing test may be hard as we may have many
# other things that are not compliant with that test.

import os
import re
import sys


def main():
    skip = set([
        'test/sanity/code-smell/%s' % os.path.basename(__file__),
        # These files currently use _ as a variable.  Fix them and then remove them
        # from this list. Note that we're not sure if we'll translate module return
        # values.  If we decide never to do that, then we can stop checking for those.
        'contrib/inventory/gce.py',
        'lib/ansible/cli/console.py',
        'lib/ansible/compat/selectors/_selectors2.py',
        'lib/ansible/executor/playbook_executor.py',
        'lib/ansible/executor/task_queue_manager.py',
        'lib/ansible/module_utils/facts/network/linux.py',
        'lib/ansible/module_utils/urls.py',
        'lib/ansible/modules/cloud/amazon/data_pipeline.py',
        'lib/ansible/modules/cloud/amazon/ec2_group_facts.py',
        'lib/ansible/modules/cloud/amazon/ec2_vpc_nat_gateway.py',
        'lib/ansible/modules/cloud/amazon/ec2_vpc_vpn.py',
        'lib/ansible/modules/cloud/amazon/efs.py',
        'lib/ansible/modules/cloud/amazon/efs_facts.py',
        'lib/ansible/modules/cloud/amazon/kinesis_stream.py',
        'lib/ansible/modules/cloud/amazon/route53_zone.py',
        'lib/ansible/modules/cloud/amazon/s3_sync.py',
        'lib/ansible/modules/cloud/azure/azure_rm_loadbalancer.py',
        'lib/ansible/modules/cloud/docker/docker_container.py',
        'lib/ansible/modules/cloud/docker/docker_service.py',
        'lib/ansible/modules/cloud/google/gce.py',
        'lib/ansible/modules/cloud/google/gce_eip.py',
        'lib/ansible/modules/cloud/google/gce_img.py',
        'lib/ansible/modules/cloud/google/gce_instance_template.py',
        'lib/ansible/modules/cloud/google/gce_lb.py',
        'lib/ansible/modules/cloud/google/gce_mig.py',
        'lib/ansible/modules/cloud/google/gce_net.py',
        'lib/ansible/modules/cloud/google/gce_pd.py',
        'lib/ansible/modules/cloud/google/gce_snapshot.py',
        'lib/ansible/modules/cloud/google/gce_tag.py',
        'lib/ansible/modules/cloud/google/gcp_backend_service.py',
        'lib/ansible/modules/cloud/google/gcp_healthcheck.py',
        'lib/ansible/modules/cloud/lxc/lxc_container.py',
        'lib/ansible/modules/files/copy.py',
        'lib/ansible/modules/files/patch.py',
        'lib/ansible/modules/files/synchronize.py',
        'lib/ansible/modules/monitoring/statusio_maintenance.py',
        'lib/ansible/modules/monitoring/zabbix/zabbix_maintenance.py',
        'lib/ansible/modules/net_tools/basics/uri.py',
        'lib/ansible/modules/network/cloudengine/ce_acl.py',
        'lib/ansible/modules/network/cloudengine/ce_command.py',
        'lib/ansible/modules/network/cloudengine/ce_dldp_interface.py',
        'lib/ansible/modules/network/cloudengine/ce_mlag_interface.py',
        'lib/ansible/modules/network/cloudvision/cv_server_provision.py',
        'lib/ansible/modules/network/f5/bigip_remote_syslog.py',
        'lib/ansible/modules/network/illumos/dladm_etherstub.py',
        'lib/ansible/modules/network/illumos/dladm_iptun.py',
        'lib/ansible/modules/network/illumos/dladm_linkprop.py',
        'lib/ansible/modules/network/illumos/dladm_vlan.py',
        'lib/ansible/modules/network/illumos/dladm_vnic.py',
        'lib/ansible/modules/network/illumos/flowadm.py',
        'lib/ansible/modules/network/illumos/ipadm_addr.py',
        'lib/ansible/modules/network/illumos/ipadm_addrprop.py',
        'lib/ansible/modules/network/illumos/ipadm_if.py',
        'lib/ansible/modules/network/illumos/ipadm_ifprop.py',
        'lib/ansible/modules/network/illumos/ipadm_prop.py',
        'lib/ansible/modules/network/vyos/vyos_command.py',
        'lib/ansible/modules/packaging/language/pip.py',
        'lib/ansible/modules/packaging/os/yum.py',
        'lib/ansible/modules/source_control/git.py',
        'lib/ansible/modules/system/alternatives.py',
        'lib/ansible/modules/system/beadm.py',
        'lib/ansible/modules/system/cronvar.py',
        'lib/ansible/modules/system/dconf.py',
        'lib/ansible/modules/system/filesystem.py',
        'lib/ansible/modules/system/gconftool2.py',
        'lib/ansible/modules/system/interfaces_file.py',
        'lib/ansible/modules/system/iptables.py',
        'lib/ansible/modules/system/java_cert.py',
        'lib/ansible/modules/system/lvg.py',
        'lib/ansible/modules/system/lvol.py',
        'lib/ansible/modules/system/parted.py',
        'lib/ansible/modules/system/timezone.py',
        'lib/ansible/modules/system/ufw.py',
        'lib/ansible/modules/utilities/logic/wait_for.py',
        'lib/ansible/modules/web_infrastructure/rundeck_acl_policy.py',
        'lib/ansible/parsing/vault/__init__.py',
        'lib/ansible/playbook/base.py',
        'lib/ansible/playbook/helpers.py',
        'lib/ansible/playbook/role/__init__.py',
        'lib/ansible/playbook/taggable.py',
        'lib/ansible/plugins/callback/hipchat.py',
        'lib/ansible/plugins/connection/lxc.py',
        'lib/ansible/plugins/filter/core.py',
        'lib/ansible/plugins/lookup/sequence.py',
        'lib/ansible/plugins/strategy/__init__.py',
        'lib/ansible/plugins/strategy/linear.py',
        'test/legacy/cleanup_gce.py',
        'test/legacy/gce_credentials.py',
        'test/runner/lib/cloud/cs.py',
        'test/runner/lib/core_ci.py',
        'test/runner/lib/delegation.py',
        'test/runner/lib/docker_util.py',
        'test/runner/lib/executor.py',
        'test/runner/lib/http.py',
        'test/runner/lib/import_analysis.py',
        'test/runner/lib/manage_ci.py',
        'test/runner/lib/target.py',
        'test/runner/lib/util.py',
        'test/sanity/import/importer.py',
        'test/sanity/validate-modules/main.py',
        'test/units/executor/test_play_iterator.py',
        'test/units/module_utils/basic/test_run_command.py',
        'test/units/modules/cloud/amazon/test_ec2_vpc_nat_gateway.py',
        'test/units/modules/cloud/amazon/test_ec2_vpc_vpn.py',
        'test/units/modules/system/interfaces_file/test_interfaces_file.py',
    ])

    for path in sys.argv[1:] or sys.stdin.read().splitlines():
        if path in skip:
            continue

        with open(path, 'r') as path_fd:
            for line, text in enumerate(path_fd.readlines()):
                match = re.search(r'(?: |[^C]\()(_)(?: |,|\))', text)

                if match:
                    print('%s:%d:%d: use `dummy` instead of `_` for a variable name' % (
                        path, line + 1, match.start(1) + 1))


if __name__ == '__main__':
    main()
