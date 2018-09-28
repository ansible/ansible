import logging

from ansible.playbook.role import metadata

log = logging.getLogger(__name__)


def test_role_metadata():
    rmd = metadata.RoleMetadata()

    log.debug('rmd: %s', rmd)

    assert isinstance(rmd, metadata.RoleMetadata)
