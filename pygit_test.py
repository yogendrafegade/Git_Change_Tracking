import pygit2
import json
import os
import shutil
from Variable import MY_GITHUB_TOKEN, Repo_URL
# =============================
# CONFIG & AUTH
# =============================
CLONE_PATH = "./temp_pr_analysis"

# Cleanup previous runs
if os.path.exists(CLONE_PATH):
    shutil.rmtree(CLONE_PATH)

callbacks = pygit2.RemoteCallbacks(
    credentials=pygit2.UserPass(MY_GITHUB_TOKEN, "x-oauth-basic")
)

# =============================
# 1. CLONE REPOSITORY
# =============================
repo = pygit2.clone_repository(Repo_URL, CLONE_PATH, callbacks=callbacks)

# =============================
# 2. FIND DYNAMIC PR REF
# =============================
# We fetch all remote branches and PR refs
repo.remotes["origin"].fetch(["+refs/pull/*/head:refs/remotes/origin/pull/*"], callbacks=callbacks)

def get_latest_pr_ref(repo):
    pr_refs = [ref for ref in repo.references if "refs/remotes/origin/pull/" in ref]
    if not pr_refs:
        raise Exception("No Pull Requests found in this repository!")
    # Return the most recent one based on the reference name (number)
    return sorted(pr_refs, key=lambda x: int(x.split('/')[-1]))[-1]

TARGET_PR_REF = get_latest_pr_ref(repo)
PR_NUMBER = TARGET_PR_REF.split('/')[-1]

# =============================
# 3. IDENTIFY BASE (MAIN)
# =============================
def find_base_ref(repo):
    for name in ["main", "master"]:
        ref_path = f"refs/remotes/origin/{name}"
        if ref_path in repo.references:
            return ref_path
    return "refs/remotes/origin/main"

FROM_REF = find_base_ref(repo)
TO_REF = TARGET_PR_REF

# =============================
# 4. COMPARE TREES (BLOBS)
# =============================
old_commit = repo.revparse_single(FROM_REF)
new_commit = repo.revparse_single(TO_REF)
diff = repo.diff(old_commit.tree, new_commit.tree)

def get_file_content(tree, path):
    try:
        entry = tree[path]
        blob = repo[entry.id]
        return blob.data.decode("utf-8", errors="ignore").splitlines()
    except KeyError:
        return []

# =============================
# 5. GENERATE JSON
# =============================
status_map = {
    pygit2.GIT_DELTA_ADDED: "added",
    pygit2.GIT_DELTA_DELETED: "deleted",
    pygit2.GIT_DELTA_MODIFIED: "modified"
}

output = {
    "changes": [],
    "summary": {
        "comparison_type": "automated_pr_analysis",
        "pr_id": PR_NUMBER,
        "base_branch": FROM_REF,
        "total_files_changed": 0
    }
}

for patch in diff:
    file_data = {
        "filename": patch.delta.new_file.path,
        "status": status_map.get(patch.delta.status, "unknown"),
        "old_content": get_file_content(old_commit.tree, patch.delta.old_file.path),
        "new_content": get_file_content(new_commit.tree, patch.delta.new_file.path)
    }
    output["changes"].append(file_data)

output["summary"]["total_files_changed"] = len(output["changes"])

print(json.dumps(output, indent=2))