"""Temporary live check of release write permissions with the workflow token."""

import os
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from publish_release import REPOSITORY, github_request


tag = f"test-ci-permissions-{os.environ['GITHUB_RUN_ID']}-{os.environ['GITHUB_RUN_ATTEMPT']}"
sha = os.environ["GITHUB_SHA"]
tag_path = f"git/ref/tags/{tag}"
release_path = f"releases/tags/{tag}"
summary = Path(os.environ["GITHUB_STEP_SUMMARY"])


def report(message):
    print(message, flush=True)
    with summary.open("a") as output:
        output.write(f"- {message}\n")


def get_optional(path):
    try:
        return github_request("GET", path)
    except HTTPError as error:
        if error.code == 404:
            return None
        raise


def delete(path):
    request = Request(
        f"https://api.github.com/repos/{REPOSITORY}/{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {os.environ['GH_TOKEN']}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "aip-release-permission-check",
        },
        method="DELETE",
    )
    with urlopen(request, timeout=30) as response:
        if response.status != 204:
            raise RuntimeError(f"Unexpected DELETE status: {response.status}")


if get_optional(tag_path) is not None or get_optional(release_path) is not None:
    raise RuntimeError(f"Refusing to reuse an existing test artifact: {tag}")

report(f"Runner: {os.environ['RUNNER_NAME']}; commit: {sha}; test tag: {tag}")
errors = []
try:
    created_tag = github_request("POST", "git/refs", {"ref": f"refs/tags/{tag}", "sha": sha})
    if created_tag["object"]["sha"] != sha:
        raise RuntimeError("Created tag points to an unexpected commit")
    report(f"PASS: created tag {tag} using GITHUB_TOKEN")

    release = github_request("POST", "releases", {
        "tag_name": tag,
        "target_commitish": sha,
        "name": f"Temporary CI permission test: {tag}",
        "body": "Temporary GITHUB_TOKEN write-permission check. Automatically removed by the test workflow.",
        "draft": False,
        "prerelease": True,
        "make_latest": "false",
        "generate_release_notes": False,
    })
    report(f"PASS: created published prerelease {release['html_url']} (release ID {release['id']})")

    actual_tag = github_request("GET", tag_path)
    actual_release = github_request("GET", release_path)
    if actual_tag["object"]["sha"] != sha:
        raise RuntimeError("Tag verification failed")
    if (actual_release["id"], actual_release["draft"], actual_release["prerelease"]) != (release["id"], False, True):
        raise RuntimeError("Release verification failed")
    report("PASS: independently read back and verified the test tag and published prerelease")
except Exception as error:
    errors.append(f"Write verification failed: {error}")
finally:
    for kind, path in (("release", release_path), ("tag", tag_path)):
        try:
            artifact = get_optional(path)
            if artifact is not None:
                if kind == "release":
                    if artifact["target_commitish"] != sha or artifact["tag_name"] != tag:
                        raise RuntimeError("Refusing to delete a release with unexpected ownership")
                    delete(f"releases/{artifact['id']}")
                else:
                    if artifact["object"]["sha"] != sha:
                        raise RuntimeError("Refusing to delete a tag with an unexpected commit")
                    delete(f"git/refs/tags/{tag}")
                report(f"PASS: deleted test {kind} using GITHUB_TOKEN")
            if get_optional(path) is not None:
                raise RuntimeError(f"Test {kind} still exists after cleanup")
            report(f"PASS: verified test {kind} is absent")
        except Exception as error:
            errors.append(f"Cleanup of test {kind} failed: {error}")

for error in errors:
    report(f"FAIL: {error}")
if errors:
    raise SystemExit(1)
report("PASS: tag and release write permissions work, and all test artifacts were removed")
