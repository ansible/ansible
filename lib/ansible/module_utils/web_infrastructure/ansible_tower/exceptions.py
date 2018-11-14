# Copyright 2018, Ansible, Inc.
# Luke Sneeringer <lsneeringer@ansible.com>
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

import click
from click._compat import get_text_stderr


class TowerCLIError(click.ClickException):
    """Base exception class for problems raised within Tower CLI.
    This class adds coloring to exceptions.
    """
    fg = 'red'
    bg = None
    bold = True

    def show(self, file=None):
        if file is None:
            file = get_text_stderr()
        click.secho('Error: %s' % self.format_message(), file=file,
                    fg=self.fg, bg=self.bg, bold=self.bold)


class UsageError(TowerCLIError):
    """An exception class for reporting usage errors.

    This uses an exit code of 2 in order to match click (which matters more
    than following the erstwhile "standard" of using 64).
    """
    exit_code = 2


class BadRequest(TowerCLIError):
    """An exception class for reporting unexpected error codes from Ansible
    Tower such that 400 <= code < 500.

    In theory, we should never, ever get these.
    """
    exit_code = 40


class AuthError(TowerCLIError):
    """An exception class for reporting when a request failed due to an
    authorization failure.
    """
    exit_code = 41


class Forbidden(TowerCLIError):
    """An exception class for reporting when a user doesn't have permission
    to do something.
    """
    exit_code = 43


class NotFound(TowerCLIError):
    """An exception class for reporting when a request went through without
    incident, but the requested content could not be found.
    """
    exit_code = 44


class MethodNotAllowed(BadRequest):
    """An exception class for sending a request to a URL where the URL doesn't
    accept that method at all.
    """
    exit_code = 45


class MultipleResults(TowerCLIError):
    """An exception class for reporting when a request that expected one
    and exactly one result got more than that.
    """
    exit_code = 49


class ServerError(TowerCLIError):
    """An exception class for reporting server-side errors which are expected
    to be ephemeral.
    """
    exit_code = 50


class Found(TowerCLIError):
    """An exception class for when a record already exists, and we were
    explicitly told that it shouldn't.
    """
    exit_code = 60


class RelatedError(TowerCLIError):
    """An exception class for errors where we can't find related objects
    that we expect to find.
    """
    exit_code = 61


class MultipleRelatedError(RelatedError):
    """An exception class for errors where we try to find a single related
    object, and get more than one.
    """
    exit_code = 62


class ValidationError(TowerCLIError):
    """An exception class for invalid values being sent as option
    switches to Tower CLI.
    """
    exit_code = 64


class CannotStartJob(TowerCLIError):
    """An exception class for jobs that cannot be started within Tower
    for whatever reason.
    """
    exit_code = 97


class Timeout(TowerCLIError):
    """An exception class for timeouts encountered within Tower CLI,
    usually for monitoring.
    """
    exit_code = 98


class JobFailure(TowerCLIError):
    """An exception class for job failures that require error codes within
    the Tower CLI.
    """
    exit_code = 99


class ConnectionError(TowerCLIError):
    """An exception class to bubble requests errors more nicely,
    and communicate connection issues to the user.
    """
    exit_code = 120
