# Copyright (c) 2018, Oracle and/or its affiliates.
# This software is made available to you under the terms of the GPL 3.0 license or the Apache 2.0 license.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# Apache License v2.0
# See LICENSE.TXT for details.


class ModuleDocFragment(object):
    DOCUMENTATION = """
    options:
        force_create:
            description: Whether to attempt non-idempotent creation of a resource. By default, create resource is an
                         idempotent operation, and doesn't create the resource if it already exists. Setting this option
                         to true, forcefully creates a copy of the resource, even if it already exists.This option is
                         mutually exclusive with I(key_by).
            default: False
            type: bool
        key_by:
            description: The list of comma-separated attributes of this resource which should be used to uniquely
                         identify an instance of the resource. By default, all the attributes of a resource except
                         I(freeform_tags) are used to uniquely identify a resource.
            type: list
    """
