import collections
from io import BytesIO

from ansible.modules.web_infrastructure.jenkins_plugin import JenkinsPlugin


def pass_function(*args, **kwargs):
    pass


GITHUB_DATA = {"url": u'https://api.github.com/repos/ansible/ansible',
               "response": b"""
{
  "id": 3638964,
  "name": "ansible",
  "full_name": "ansible/ansible",
  "owner": {
    "login": "ansible",
    "id": 1507452,
    "avatar_url": "https://avatars2.githubusercontent.com/u/1507452?v=4",
    "gravatar_id": "",
    "url": "https://api.github.com/users/ansible",
    "html_url": "https://github.com/ansible",
    "followers_url": "https://api.github.com/users/ansible/followers",
    "following_url": "https://api.github.com/users/ansible/following{/other_user}",
    "gists_url": "https://api.github.com/users/ansible/gists{/gist_id}",
    "starred_url": "https://api.github.com/users/ansible/starred{/owner}{/repo}",
    "subscriptions_url": "https://api.github.com/users/ansible/subscriptions",
    "organizations_url": "https://api.github.com/users/ansible/orgs",
    "repos_url": "https://api.github.com/users/ansible/repos",
    "events_url": "https://api.github.com/users/ansible/events{/privacy}",
    "received_events_url": "https://api.github.com/users/ansible/received_events",
    "type": "Organization",
    "site_admin": false
  },
  "private": false,
  "html_url": "https://github.com/ansible/ansible",
  "description": "Ansible is a radically simple IT automation platform that makes your applications and systems easier to deploy.",
  "fork": false,
  "url": "https://api.github.com/repos/ansible/ansible",
  "forks_url": "https://api.github.com/repos/ansible/ansible/forks",
  "keys_url": "https://api.github.com/repos/ansible/ansible/keys{/key_id}",
  "collaborators_url": "https://api.github.com/repos/ansible/ansible/collaborators{/collaborator}",
  "teams_url": "https://api.github.com/repos/ansible/ansible/teams",
  "hooks_url": "https://api.github.com/repos/ansible/ansible/hooks",
  "issue_events_url": "https://api.github.com/repos/ansible/ansible/issues/events{/number}",
  "events_url": "https://api.github.com/repos/ansible/ansible/events",
  "assignees_url": "https://api.github.com/repos/ansible/ansible/assignees{/user}",
  "branches_url": "https://api.github.com/repos/ansible/ansible/branches{/branch}",
  "tags_url": "https://api.github.com/repos/ansible/ansible/tags",
  "blobs_url": "https://api.github.com/repos/ansible/ansible/git/blobs{/sha}",
  "git_tags_url": "https://api.github.com/repos/ansible/ansible/git/tags{/sha}",
  "git_refs_url": "https://api.github.com/repos/ansible/ansible/git/refs{/sha}",
  "trees_url": "https://api.github.com/repos/ansible/ansible/git/trees{/sha}",
  "statuses_url": "https://api.github.com/repos/ansible/ansible/statuses/{sha}",
  "languages_url": "https://api.github.com/repos/ansible/ansible/languages",
  "stargazers_url": "https://api.github.com/repos/ansible/ansible/stargazers",
  "contributors_url": "https://api.github.com/repos/ansible/ansible/contributors",
  "subscribers_url": "https://api.github.com/repos/ansible/ansible/subscribers",
  "subscription_url": "https://api.github.com/repos/ansible/ansible/subscription",
  "commits_url": "https://api.github.com/repos/ansible/ansible/commits{/sha}",
  "git_commits_url": "https://api.github.com/repos/ansible/ansible/git/commits{/sha}",
  "comments_url": "https://api.github.com/repos/ansible/ansible/comments{/number}",
  "issue_comment_url": "https://api.github.com/repos/ansible/ansible/issues/comments{/number}",
  "contents_url": "https://api.github.com/repos/ansible/ansible/contents/{+path}",
  "compare_url": "https://api.github.com/repos/ansible/ansible/compare/{base}...{head}",
  "merges_url": "https://api.github.com/repos/ansible/ansible/merges",
  "archive_url": "https://api.github.com/repos/ansible/ansible/{archive_format}{/ref}",
  "downloads_url": "https://api.github.com/repos/ansible/ansible/downloads",
  "issues_url": "https://api.github.com/repos/ansible/ansible/issues{/number}",
  "pulls_url": "https://api.github.com/repos/ansible/ansible/pulls{/number}",
  "milestones_url": "https://api.github.com/repos/ansible/ansible/milestones{/number}",
  "notifications_url": "https://api.github.com/repos/ansible/ansible/notifications{?since,all,participating}",
  "labels_url": "https://api.github.com/repos/ansible/ansible/labels{/name}",
  "releases_url": "https://api.github.com/repos/ansible/ansible/releases{/id}",
  "deployments_url": "https://api.github.com/repos/ansible/ansible/deployments",
  "created_at": "2012-03-06T14:58:02Z",
  "updated_at": "2017-09-19T18:10:54Z",
  "pushed_at": "2017-09-19T18:04:51Z",
  "git_url": "git://github.com/ansible/ansible.git",
  "ssh_url": "git@github.com:ansible/ansible.git",
  "clone_url": "https://github.com/ansible/ansible.git",
  "svn_url": "https://github.com/ansible/ansible",
  "homepage": "https://www.ansible.com/",
  "size": 91174,
  "stargazers_count": 25552,
  "watchers_count": 25552,
  "language": "Python",
  "has_issues": true,
  "has_projects": true,
  "has_downloads": true,
  "has_wiki": false,
  "has_pages": false,
  "forks_count": 8893,
  "mirror_url": null,
  "open_issues_count": 4283,
  "forks": 8893,
  "open_issues": 4283,
  "watchers": 25552,
  "default_branch": "devel",
  "organization": {
    "login": "ansible",
    "id": 1507452,
    "avatar_url": "https://avatars2.githubusercontent.com/u/1507452?v=4",
    "gravatar_id": "",
    "url": "https://api.github.com/users/ansible",
    "html_url": "https://github.com/ansible",
    "followers_url": "https://api.github.com/users/ansible/followers",
    "following_url": "https://api.github.com/users/ansible/following{/other_user}",
    "gists_url": "https://api.github.com/users/ansible/gists{/gist_id}",
    "starred_url": "https://api.github.com/users/ansible/starred{/owner}{/repo}",
    "subscriptions_url": "https://api.github.com/users/ansible/subscriptions",
    "organizations_url": "https://api.github.com/users/ansible/orgs",
    "repos_url": "https://api.github.com/users/ansible/repos",
    "events_url": "https://api.github.com/users/ansible/events{/privacy}",
    "received_events_url": "https://api.github.com/users/ansible/received_events",
    "type": "Organization",
    "site_admin": false
  },
  "network_count": 8893,
  "subscribers_count": 1733
}
"""
               }


def test__get_json_data(mocker):
    "test the json conversion of _get_url_data"

    timeout = 30
    params = {
        'url': GITHUB_DATA['url'],
        'timeout': timeout
    }
    module = mocker.Mock()
    module.params = params

    JenkinsPlugin._csrf_enabled = pass_function
    JenkinsPlugin._get_installed_plugins = pass_function
    JenkinsPlugin._get_url_data = mocker.Mock()
    JenkinsPlugin._get_url_data.return_value = BytesIO(GITHUB_DATA['response'])
    jenkins_plugin = JenkinsPlugin(module)

    json_data = jenkins_plugin._get_json_data(
        "{url}".format(url=GITHUB_DATA['url']),
        'CSRF')

    assert isinstance(json_data, collections.Mapping)
