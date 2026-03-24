import pygit2
import json
import os
from Variable import MY_GITHUB_TOKEN, Repo_URL
from sql_glot import analyze_sql

# =============================
# 1. REPO SETUP
# =============================
CLONE_PATH = "./temp_pr_analysis"
callbacks = pygit2.RemoteCallbacks(credentials=pygit2.UserPass(MY_GITHUB_TOKEN, "x-oauth-basic"))

if os.path.exists(CLONE_PATH):
    repo = pygit2.Repository(CLONE_PATH)
else:
    repo = pygit2.clone_repository(Repo_URL, CLONE_PATH, callbacks=callbacks)

# Fetching latest metadata for both PRs and Main
repo.remotes["origin"].fetch([
    "+refs/pull/*/head:refs/remotes/origin/pull/*",
    "+refs/heads/main:refs/remotes/origin/main"
], callbacks=callbacks)

# =============================
# 2. CONTENT HELPER
# =============================
def get_raw_content(tree, path):
    if not path:
        return ""
    # Define which files we actually want to read as text
    TEXT_EXTENSIONS = ('.py', '.sql', '.txt', '.md', '.json', '.html', '.css','.csv')
    
    # Check if the file is a text-based format
    if not path.lower().endswith(TEXT_EXTENSIONS):
        return "[Binary/Non-Text Content Hidden]"

    try:
        entry = tree[path]
        return repo[entry.id].data.decode("utf-8", errors="ignore").strip()
    except KeyError:
        return ""


# =============================
# 3. DATA TRANSFORMATION
# =============================
pr_refs = [ref for ref in repo.references if "refs/remotes/origin/pull/" in ref]
latest_pr_ref = sorted(pr_refs, key=lambda x: int(x.split('/')[-1]))[-1]
pr_id = latest_pr_ref.split('/')[-1]

# Compare PR Head against the Main branch
new_commit = repo.revparse_single(latest_pr_ref)
old_commit = repo.revparse_single("refs/remotes/origin/main")

diff = repo.diff(old_commit.tree, new_commit.tree)

# Even if you change code inside, 20% similarity will keep it as 'renamed'
diff.find_similar(flags=pygit2.GIT_DIFF_FIND_RENAMES, rename_threshold=20)

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
    # Logic: Pick the correct name for the JSON key
    if patch.delta.status == pygit2.GIT_DELTA_DELETED:
        filename = patch.delta.old_file.path
    else:
        filename = patch.delta.new_file.path
    
    old_raw = get_raw_content(old_commit.tree, patch.delta.old_file.path)
    new_raw = get_raw_content(new_commit.tree, patch.delta.new_file.path)

    if filename.lower().endswith(".sql"):
        old_content = analyze_sql(old_raw)
        new_content = analyze_sql(new_raw)
    else:
        old_content = old_raw
        new_content = new_raw

    output["changes"][filename] = {
        "status": status_map.get(patch.delta.status, "unknown"),
        "old_content": old_content,
        "new_content": new_content
    }

output["summary"]["total_files_changed"] = len(output["changes"])

# =============================
# 4. OUTPUT
# =============================
print(json.dumps(output, indent=2, ensure_ascii=False))

# parsed = json.loads(json.dumps(output)) 
# OLD_CONTENT=parsed["changes"]["Hello_new.py"]["old_content"]
# CONTENT=parsed["changes"]["Hello_new.py"]["new_content"] 

# # print(parsed)

# print("Normal Print:")

# print("Old Content:\n", json.dumps(OLD_CONTENT, indent=2) if isinstance(OLD_CONTENT, dict) else OLD_CONTENT)
# print("New Content:\n", json.dumps(CONTENT, indent=2) if isinstance(CONTENT, dict) else CONTENT)
# print("Type of New Content:", type(CONTENT))
