from __future__ import absolute_import

import logging
import os.path
import re

from pip._vendor.packaging.version import parse as parse_version
from pip._vendor.six.moves.urllib import parse as urllib_parse
from pip._vendor.six.moves.urllib import request as urllib_request

from pip._internal.compat import samefile
from pip._internal.exceptions import BadCommand
from pip._internal.utils.misc import display_path
from pip._internal.utils.temp_dir import TempDirectory
from pip._internal.vcs import VersionControl, vcs

urlsplit = urllib_parse.urlsplit
urlunsplit = urllib_parse.urlunsplit


logger = logging.getLogger(__name__)


HASH_REGEX = re.compile('[a-fA-F0-9]{40}')


def looks_like_hash(sha):
    return bool(HASH_REGEX.match(sha))


class Git(VersionControl):
    name = 'git'
    dirname = '.git'
    repo_name = 'clone'
    schemes = (
        'git', 'git+http', 'git+https', 'git+ssh', 'git+git', 'git+file',
    )
    # Prevent the user's environment variables from interfering with pip:
    # https://github.com/pypa/pip/issues/1130
    unset_environ = ('GIT_DIR', 'GIT_WORK_TREE')
    default_arg_rev = 'HEAD'

    def __init__(self, url=None, *args, **kwargs):

        # Works around an apparent Git bug
        # (see http://article.gmane.org/gmane.comp.version-control.git/146500)
        if url:
            scheme, netloc, path, query, fragment = urlsplit(url)
            if scheme.endswith('file'):
                initial_slashes = path[:-len(path.lstrip('/'))]
                newpath = (
                    initial_slashes +
                    urllib_request.url2pathname(path)
                    .replace('\\', '/').lstrip('/')
                )
                url = urlunsplit((scheme, netloc, newpath, query, fragment))
                after_plus = scheme.find('+') + 1
                url = scheme[:after_plus] + urlunsplit(
                    (scheme[after_plus:], netloc, newpath, query, fragment),
                )

        super(Git, self).__init__(url, *args, **kwargs)

    def get_base_rev_args(self, rev):
        return [rev]

    def get_git_version(self):
        VERSION_PFX = 'git version '
        version = self.run_command(['version'], show_stdout=False)
        if version.startswith(VERSION_PFX):
            version = version[len(VERSION_PFX):].split()[0]
        else:
            version = ''
        # get first 3 positions of the git version becasue
        # on windows it is x.y.z.windows.t, and this parses as
        # LegacyVersion which always smaller than a Version.
        version = '.'.join(version.split('.')[:3])
        return parse_version(version)

    def export(self, location):
        """Export the Git repository at the url to the destination location"""
        if not location.endswith('/'):
            location = location + '/'

        with TempDirectory(kind="export") as temp_dir:
            self.unpack(temp_dir.path)
            self.run_command(
                ['checkout-index', '-a', '-f', '--prefix', location],
                show_stdout=False, cwd=temp_dir.path
            )

    def get_revision_sha(self, dest, rev):
        """
        Return a commit hash for the given revision if it names a remote
        branch or tag.  Otherwise, return None.

        Args:
          dest: the repository directory.
          rev: the revision name.
        """
        # Pass rev to pre-filter the list.
        output = self.run_command(['show-ref', rev], cwd=dest,
                                  show_stdout=False, on_returncode='ignore')
        refs = {}
        for line in output.strip().splitlines():
            try:
                sha, ref = line.split()
            except ValueError:
                # Include the offending line to simplify troubleshooting if
                # this error ever occurs.
                raise ValueError('unexpected show-ref line: {!r}'.format(line))

            refs[ref] = sha

        branch_ref = 'refs/remotes/origin/{}'.format(rev)
        tag_ref = 'refs/tags/{}'.format(rev)

        return refs.get(branch_ref) or refs.get(tag_ref)

    def check_rev_options(self, dest, rev_options):
        """Check the revision options before checkout.

        Returns a new RevOptions object for the SHA1 of the branch or tag
        if found.

        Args:
          rev_options: a RevOptions object.
        """
        rev = rev_options.arg_rev
        sha = self.get_revision_sha(dest, rev)

        if sha is not None:
            return rev_options.make_new(sha)

        # Do not show a warning for the common case of something that has
        # the form of a Git commit hash.
        if not looks_like_hash(rev):
            logger.warning(
                "Did not find branch or tag '%s', assuming revision or ref.",
                rev,
            )
        return rev_options

    def is_commit_id_equal(self, dest, name):
        """
        Return whether the current commit hash equals the given name.

        Args:
          dest: the repository directory.
          name: a string name.
        """
        if not name:
            # Then avoid an unnecessary subprocess call.
            return False

        return self.get_revision(dest) == name

    def switch(self, dest, url, rev_options):
        self.run_command(['config', 'remote.origin.url', url], cwd=dest)
        cmd_args = ['checkout', '-q'] + rev_options.to_args()
        self.run_command(cmd_args, cwd=dest)

        self.update_submodules(dest)

    def update(self, dest, rev_options):
        # First fetch changes from the default remote
        if self.get_git_version() >= parse_version('1.9.0'):
            # fetch tags in addition to everything else
            self.run_command(['fetch', '-q', '--tags'], cwd=dest)
        else:
            self.run_command(['fetch', '-q'], cwd=dest)
        # Then reset to wanted revision (maybe even origin/master)
        rev_options = self.check_rev_options(dest, rev_options)
        cmd_args = ['reset', '--hard', '-q'] + rev_options.to_args()
        self.run_command(cmd_args, cwd=dest)
        #: update submodules
        self.update_submodules(dest)

    def obtain(self, dest):
        url, rev = self.get_url_rev()
        rev_options = self.make_rev_options(rev)
        if self.check_destination(dest, url, rev_options):
            rev_display = rev_options.to_display()
            logger.info(
                'Cloning %s%s to %s', url, rev_display, display_path(dest),
            )
            self.run_command(['clone', '-q', url, dest])

            if rev:
                rev_options = self.check_rev_options(dest, rev_options)
                # Only do a checkout if the current commit id doesn't match
                # the requested revision.
                if not self.is_commit_id_equal(dest, rev_options.rev):
                    rev = rev_options.rev
                    # Only fetch the revision if it's a ref
                    if rev.startswith('refs/'):
                        self.run_command(
                            ['fetch', '-q', url] + rev_options.to_args(),
                            cwd=dest,
                        )
                        # Change the revision to the SHA of the ref we fetched
                        rev = 'FETCH_HEAD'
                    self.run_command(['checkout', '-q', rev], cwd=dest)

            #: repo may contain submodules
            self.update_submodules(dest)

    def get_url(self, location):
        """Return URL of the first remote encountered."""
        remotes = self.run_command(
            ['config', '--get-regexp', r'remote\..*\.url'],
            show_stdout=False, cwd=location,
        )
        remotes = remotes.splitlines()
        found_remote = remotes[0]
        for remote in remotes:
            if remote.startswith('remote.origin.url '):
                found_remote = remote
                break
        url = found_remote.split(' ')[1]
        return url.strip()

    def get_revision(self, location):
        current_rev = self.run_command(
            ['rev-parse', 'HEAD'], show_stdout=False, cwd=location,
        )
        return current_rev.strip()

    def _get_subdirectory(self, location):
        """Return the relative path of setup.py to the git repo root."""
        # find the repo root
        git_dir = self.run_command(['rev-parse', '--git-dir'],
                                   show_stdout=False, cwd=location).strip()
        if not os.path.isabs(git_dir):
            git_dir = os.path.join(location, git_dir)
        root_dir = os.path.join(git_dir, '..')
        # find setup.py
        orig_location = location
        while not os.path.exists(os.path.join(location, 'setup.py')):
            last_location = location
            location = os.path.dirname(location)
            if location == last_location:
                # We've traversed up to the root of the filesystem without
                # finding setup.py
                logger.warning(
                    "Could not find setup.py for directory %s (tried all "
                    "parent directories)",
                    orig_location,
                )
                return None
        # relative path of setup.py to repo root
        if samefile(root_dir, location):
            return None
        return os.path.relpath(location, root_dir)

    def get_src_requirement(self, dist, location):
        repo = self.get_url(location)
        if not repo.lower().startswith('git:'):
            repo = 'git+' + repo
        egg_project_name = dist.egg_name().split('-', 1)[0]
        if not repo:
            return None
        current_rev = self.get_revision(location)
        req = '%s@%s#egg=%s' % (repo, current_rev, egg_project_name)
        subdirectory = self._get_subdirectory(location)
        if subdirectory:
            req += '&subdirectory=' + subdirectory
        return req

    def get_url_rev(self):
        """
        Prefixes stub URLs like 'user@hostname:user/repo.git' with 'ssh://'.
        That's required because although they use SSH they sometimes doesn't
        work with a ssh:// scheme (e.g. Github). But we need a scheme for
        parsing. Hence we remove it again afterwards and return it as a stub.
        """
        if '://' not in self.url:
            assert 'file:' not in self.url
            self.url = self.url.replace('git+', 'git+ssh://')
            url, rev = super(Git, self).get_url_rev()
            url = url.replace('ssh://', '')
        else:
            url, rev = super(Git, self).get_url_rev()

        return url, rev

    def update_submodules(self, location):
        if not os.path.exists(os.path.join(location, '.gitmodules')):
            return
        self.run_command(
            ['submodule', 'update', '--init', '--recursive', '-q'],
            cwd=location,
        )

    @classmethod
    def controls_location(cls, location):
        if super(Git, cls).controls_location(location):
            return True
        try:
            r = cls().run_command(['rev-parse'],
                                  cwd=location,
                                  show_stdout=False,
                                  on_returncode='ignore')
            return not r
        except BadCommand:
            logger.debug("could not determine if %s is under git control "
                         "because git is not available", location)
            return False


vcs.register(Git)
