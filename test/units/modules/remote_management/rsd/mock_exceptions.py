# -*- coding: utf-8 -*-

#######################################################
# Copyright (c) 2019 Intel Corporation. All rights reserved.
#
# GNU General Public License v3.0+
# (see LICENSE.GPL or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# Authors:
#   - Przemyslaw Szczerbik - <przemyslawx.szczerbik@intel.com>
#######################################################

from __future__ import absolute_import, division, print_function
__metaclass__ = type


class VolumeBackendAPIException(Exception):
    pass


class ResourceNotFoundError(Exception):
    pass


class InvalidParameterValueError(Exception):
    pass


class ConnectionError(Exception):
    pass


class ServerSideError(Exception):
    pass


class HTTPError(Exception):
    pass
