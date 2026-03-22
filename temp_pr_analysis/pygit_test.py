import pygit2
import json
import os
from Variable import MY_GITHUB_TOKEN, Repo_URL

# =============================
# 1. REPO SETUP
# =============================
CLONE_PATH = "./temp_pr_analysis"
callbacks = pygit2.RemoteCallbacks(credentials=pygit2.UserPass(MY_GITHUB_TOKEN, "x-oauth-basic"))

if os.path.exists(CLONE_PATH):
    repo = pygit2.Repository(CLONE_PATH)
else:
    repo = pygit2.clone_repository(Repo_URL, CLONE_PATH, callbacks=callbacks)

# Fetch PR refs
repo.remotes["origin"].fetch(["+refs/pull/*/head:refs/remotes/origin/pull/*"], callbacks=callbacks)

# =============================
# 2. CONTENT HELPER
# =============================
def get_raw_content(tree, path):
    try:
        entry = tree[path]
        # Returns raw string; json.dumps converts newlines to \n automatically
        return repo[entry.id].data.decode("utf-8", errors="ignore").strip()
    except KeyError:
        return ""

# =============================
# 3. DATA TRANSFORMATION
# =============================
pr_refs = [ref for ref in repo.references if "refs/remotes/origin/pull/" in ref]
latest_pr_ref = sorted(pr_refs, key=lambda x: int(x.split('/')[-1]))[-1]
pr_id = latest_pr_ref.split('/')[-1]

old_commit = repo.revparse_single("refs/remotes/origin/main")
new_commit = repo.revparse_single(latest_pr_ref)
diff = repo.diff(old_commit.tree, new_commit.tree)

# The Structure: "changes" is an object {}, not a list []
output = {
    "changes": {}, 
    "summary": {
        "comparison_type": "Mainbranch vs Feature",
        "pr_id": pr_id,
        "base_branch": "main",
        "head_branch": f"Pull Request #{pr_id}",
        "total_files_changed": 0
    }
}

status_map = {
    pygit2.GIT_DELTA_ADDED: "added",
    pygit2.GIT_DELTA_DELETED: "deleted",
    pygit2.GIT_DELTA_MODIFIED: "modified",
    pygit2.GIT_DELTA_RENAMED: "renamed"
}

for patch in diff:
    filename = patch.delta.new_file.path
    
    # Map filename as the KEY in the dictionary
    output["changes"][filename] = {
        "status": status_map.get(patch.delta.status, "unknown"),
        "old_content": get_raw_content(old_commit.tree, patch.delta.old_file.path),
        "new_content": get_raw_content(new_commit.tree, patch.delta.new_file.path)
    }

output["summary"]["total_files_changed"] = len(output["changes"])

# =============================
# 4. OUTPUT (STRICT VALID JSON)
# =============================
# Using indent=2 for a clean, scannable look
print(json.dumps(output, indent=2))


parsed = json.loads(json.dumps(output)) 
CONTENT=parsed["changes"]["Hello.py"]["new_content"] 

print(parsed)

print("Normal Print:")

print(CONTENT)
print(type(CONTENT))
