from __future__ import annotations as _annotations

from ansible.module_utils._internal._collection_loader import resource_from_fqcr
from ansible.module_utils._internal._collection_loader._collection_config import AnsibleCollectionConfig
from ansible.module_utils._internal._collection_loader._collection_finder import AnsibleCollectionRef

__all__ = [
    'AnsibleCollectionConfig',
    'AnsibleCollectionRef',
    'resource_from_fqcr',
]
