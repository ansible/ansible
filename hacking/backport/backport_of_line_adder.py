#!/usr/bin/env python
# (c) 2020, Red Hat, Inc. <relrod@redhat.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import annotations

from github.PullRequest import PullRequest
from github import Github
import os
import re
import sys

PULL_URL_RE = re.compile(r'(?P<user>\S+)/(?P<repo>\S+)#(?P<ticket>\d+)')
PULL_HTTP_URL_RE = re.compile(r'https?://(?:www\.|)github.com/(?P<user>\S+)/(?P<repo>\S+)/pull/(?P<ticket>\d+)')
PULL_BACKPORT_IN_TITLE = re.compile(r'.*\(#?(?P<ticket1>\d+)\)|\(backport of #?(?P<ticket2>\d+)\).*', re.I)
PULL_CHERRY_PICKED_FROM = re.compile(r'\(?cherry(?:\-| )picked from(?: ?commit|) (?P<hash>\w+)(?:\)|\.|$)')
TICKET_NUMBER = re.compile(r'(?:^|\s)#(\d+)')


def normalize_pr_url(pr, allow_non_ansible_ansible=False, only_number=False):
    '''
    Given a PullRequest, or a string containing a PR number, PR URL,
    or internal PR URL (e.g. ansible-collections/community.general#1234),
    return either a full github URL to the PR (if only_number is False),
    or an int containing the PR number (if only_number is True).

    Throws if it can't parse the input.
    '''
    if isinstance(pr, PullRequest):
        return pr.html_url

    if pr.isnumeric():
        if only_number:
            return int(pr)
        return 'https://github.com/ansible/ansible/pull/{0}'.format(pr)

    # Allow for forcing ansible/ansible
    if not allow_non_ansible_ansible and 'ansible/ansible' not in pr:
        raise Exception('Non ansible/ansible repo given where not expected')

    re_match = PULL_HTTP_URL_RE.match(pr)
    if re_match:
        if only_number:
            return int(re_match.group('ticket'))
        return pr

    re_match = PULL_URL_RE.match(pr)
    if re_match:
        if only_number:
            return int(re_match.group('ticket'))
        return 'https://github.com/{0}/{1}/pull/{2}'.format(
            re_match.group('user'),
            re_match.group('repo'),
            re_match.group('ticket'))

    raise Exception('Did not understand given PR')


def url_to_org_repo(url):
    '''
    Given a full Github PR URL, extract the user/org and repo name.
    Return them in the form: "user/repo"
    '''
    match = PULL_HTTP_URL_RE.match(url)
    if not match:
        return ''
    return '{0}/{1}'.format(match.group('user'), match.group('repo'))


def generate_new_body(pr, source_pr):
    '''
    Given the new PR (the backport) and the originating (source) PR,
    construct the new body for the backport PR.

    If the backport follows the usual ansible/ansible template, we look for the
    '##### SUMMARY'-type line and add our "Backport of" line right below that.

    If we can't find the SUMMARY line, we add our line at the very bottom.

    This function does not side-effect, it simply returns the new body as a
    string.
    '''
    backport_text = '\nBackport of {0}\n'.format(source_pr)
    body_lines = pr.body.split('\n')
    new_body_lines = []

    added = False
    for line in body_lines:
        if 'Backport of http' in line:
            raise Exception('Already has a backport line, aborting.')
        new_body_lines.append(line)
        if line.startswith('#') and line.strip().endswith('SUMMARY'):
            # This would be a fine place to add it
            new_body_lines.append(backport_text)
            added = True
    if not added:
        # Otherwise, no '#### SUMMARY' line, so just add it at the bottom
        new_body_lines.append(backport_text)

    return '\n'.join(new_body_lines)


def get_prs_for_commit(g, commit):
    '''
    Given a commit hash, attempt to find the hash in any repo in the
    ansible orgs, and then use it to determine what, if any, PR it appeared in.
    '''

    commits = g.search_commits(
        'hash:{0} org:ansible org:ansible-collections is:public'.format(commit)
    ).get_page(0)
    if not commits or len(commits) == 0:
        return []
    pulls = commits[0].get_pulls().get_page(0)
    if not pulls or len(pulls) == 0:
        return []
    return pulls


def search_backport(pr, g, ansible_ansible):
    '''
    Do magic. This is basically the "brain" of 'auto'.
    It will search the PR (the newest PR - the backport) and try to find where
    it originated.

    First it will search in the title. Some titles include things like
    "foo bar change (#12345)" or "foo bar change (backport of #54321)"
    so we search for those and pull them out.

    Next it will scan the body of the PR and look for:
      - cherry-pick reference lines (e.g. "cherry-picked from commit XXXXX")
      - other PRs (#nnnnnn) and (foo/bar#nnnnnnn)
      - full URLs to other PRs

    It will take all of the above, and return a list of "possibilities",
    which is a list of PullRequest objects.
    '''

    possibilities = []

    # 1. Try searching for it in the title.
    title_search = PULL_BACKPORT_IN_TITLE.match(pr.title)
    if title_search:
        ticket = title_search.group('ticket1')
        if not ticket:
            ticket = title_search.group('ticket2')
        try:
            possibilities.append(ansible_ansible.get_pull(int(ticket)))
        except Exception:
            pass

    # 2. Search for clues in the body of the PR
    body_lines = pr.body.split('\n')
    for line in body_lines:
        # a. Try searching for a `git cherry-pick` line
        cherrypick = PULL_CHERRY_PICKED_FROM.match(line)
        if cherrypick:
            prs = get_prs_for_commit(g, cherrypick.group('hash'))
            possibilities.extend(prs)
            continue

        # b. Try searching for other referenced PRs (by #nnnnn or full URL)
        tickets = [('ansible', 'ansible', ticket) for ticket in TICKET_NUMBER.findall(line)]
        tickets.extend(PULL_HTTP_URL_RE.findall(line))
        tickets.extend(PULL_URL_RE.findall(line))
        if tickets:
            for ticket in tickets:
                # Is it a PR (even if not in ansible/ansible)?
                # TODO: As a small optimization/to avoid extra calls to GitHub,
                # we could limit this check to non-URL matches. If it's a URL,
                # we know it's definitely a pull request.
                try:
                    repo_path = '{0}/{1}'.format(ticket[0], ticket[1])
                    repo = ansible_ansible
                    if repo_path != 'ansible/ansible':
                        repo = g.get_repo(repo_path)
                    ticket_pr = repo.get_pull(int(ticket))
                    possibilities.append(ticket_pr)
                except Exception:
                    pass
            continue  # Future-proofing

    return possibilities


def prompt_add():
    '''
    Prompt the user and return whether or not they agree.
    '''
    res = input('Shall I add the reference? [Y/n]: ')
    return res.lower() in ('', 'y', 'yes')


def commit_edit(new_pr, pr):
    '''
    Given the new PR (the backport), and the "possibility" that we have decided
    on, prompt the user and then add the reference to the body of the new PR.

    This method does the actual "destructive" work of editing the PR body.
    '''
    print('I think this PR might have come from:')
    print(pr.title)
    print('-' * 50)
    print(pr.html_url)
    if prompt_add():
        new_body = generate_new_body(new_pr, pr.html_url)
        new_pr.edit(body=new_body)
        print('I probably added the reference successfully.')


if __name__ == '__main__':
    if (
        len(sys.argv) != 3 or
        not sys.argv[1].isnumeric()
    ):
        print('Usage: <new backport PR> <already merged PR, or "auto">')
        sys.exit(1)

    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        print('Go to https://github.com/settings/tokens/new and generate a '
              'token with "repo" access, then set GITHUB_TOKEN to that token.')
        sys.exit(1)

    # https://github.com/settings/tokens/new
    g = Github(token)
    ansible_ansible = g.get_repo('ansible/ansible')

    try:
        pr_num = normalize_pr_url(sys.argv[1], only_number=True)
        new_pr = ansible_ansible.get_pull(pr_num)
    except Exception:
        print('Could not load PR {0}'.format(sys.argv[1]))
        sys.exit(1)

    if sys.argv[2] == 'auto':
        print('Trying to find originating PR...')
        possibilities = search_backport(new_pr, g, ansible_ansible)
        if not possibilities:
            print('No match found, manual review required.')
            sys.exit(1)
        # TODO: Logic above can return multiple possibilities/guesses, but we
        # only handle one here. We can cycle/prompt through them or something.
        # For now, use the first match, which is also the most likely
        # candidate.
        pr = possibilities[0]
        commit_edit(new_pr, pr)
    else:
        try:
            # TODO: Fix having to call this twice to save some regex evals
            pr_num = normalize_pr_url(sys.argv[2], only_number=True, allow_non_ansible_ansible=True)
            pr_url = normalize_pr_url(sys.argv[2], allow_non_ansible_ansible=True)
            pr_repo = g.get_repo(url_to_org_repo(pr_url))
            pr = pr_repo.get_pull(pr_num)
        except Exception as e:
            print(e)
            print('Could not load PR {0}'.format(sys.argv[2]))
            sys.exit(1)
        commit_edit(new_pr, pr)
