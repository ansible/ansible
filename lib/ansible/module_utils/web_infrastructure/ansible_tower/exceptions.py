# Copyright 2018, Ansible, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


class TowerExceptionError(Exception):
    """Base exception class for problems raised within Tower CLI.
    This class adds coloring to exceptions.
    """
    message = "An unknown exception occurred."

    def __init__(self, **kwargs):
        super(TowerExceptionError, self).__init__(self.message % kwargs)
        self.msg = self.message % kwargs


class BadRequest(TowerExceptionError):
    """An exception class for reporting unexpected error codes from Ansible
    Tower such that 400 <= code < 500.

    In theory, we should never, ever get these.
    """
    message = ("Tower Unexpected error failed with: %(reason)")


class AuthError(TowerExceptionError):
    """An exception class for reporting when a request failed due to an
    authorization failure.
    """
    message = ("Tower Authorization failure failed with: %(reason)")


class Forbidden(TowerExceptionError):
    """An exception class for reporting when a user doesn't have permission
    to do something.
    """
    message = ("Tower Permission failure failed with: %(reason)")


class NotFound(TowerExceptionError):
    """An exception class for reporting when a request went through without
    incident, but the requested content could not be found.
    """
    message = ("Tower Incident failure failed with: %(reason)")


class MethodNotAllowed(TowerExceptionError):
    """An exception class for sending a request to a URL where the URL doesn't
    accept that method at all.
    """
    message = ("Tower Method failure failed with: %(reason)")


class ServerError(TowerExceptionError):
    """An exception class for reporting server-side errors which are expected
    to be ephemeral.
    """
    message = ("Tower Server-side failure failed with: %(reason)")


class Found(TowerExceptionError):
    """An exception class for when a record already exists, and we were
    explicitly told that it shouldn't.
    """
    message = ("Tower Record failure failed with: %(reason)")


class RelatedError(TowerExceptionError):
    """An exception class for errors where we can't find related objects
    that we expect to find.
    """
    message = ("Tower Related object failure failed with: %(reason)")


class MultipleRelatedError(RelatedError):
    """An exception class for errors where we try to find a single related
    object, and get more than one.
    """
    message = ("Tower Related object failure failed with: %(reason)")


class ValidationError(TowerExceptionError):
    """An exception class for invalid values being sent as option
    switches to Tower CLI.
    """
    message = ("Tower Validation failure failed with: %(reason)")


class CannotStartJob(TowerExceptionError):
    """An exception class for jobs that cannot be started within Tower
    for whatever reason.
    """
    message = ("Tower Job failure failed with: %(reason)")


class Timeout(TowerExceptionError):
    """An exception class for timeouts encountered within Tower CLI,
    usually for monitoring.
    """
    message = ("Tower Timeouts failure failed with: %(reason)")


class JobFailure(TowerExceptionError):
    """An exception class for job failures that require error codes within
    the Tower CLI.
    """
    message = ("Tower Job failure failed with: %(reason)")


class ConnectionError(TowerExceptionError):
    """An exception class to bubble requests errors more nicely,
    and communicate connection issues to the user.
    """
    message = ("Tower HTTPs request failed with: %(reason)s")
