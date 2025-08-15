import os, base64, requests
from typing import List, Dict

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # create classic token with repo scope

def push_files_to_github(repo: str, branch: str, commit_message: str, files: List[Dict[str,str]]):
    """
    Creates/updates files via GitHub REST API. Minimal, no tree API for simplicity.
    """
    if not GITHUB_TOKEN:
        raise RuntimeError("Missing GITHUB_TOKEN env var.")
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}

    # Get default branch sha (head)
    r = requests.get(f"https://api.github.com/repos/{repo}/git/refs/heads/{branch}", headers=headers)
    if r.status_code == 404:
        raise RuntimeError(f"Branch '{branch}' not found in {repo}")
    r.raise_for_status()
    head_sha = r.json()["object"]["sha"]

    results = []
    for f in files:
        path, content = f["path"], f["content"]
        # Check if file exists to get its sha
        get_url = f"https://api.github.com/repos/{repo}/contents/{path}"
        gr = requests.get(get_url, headers=headers, params={"ref": branch})
        sha = gr.json().get("sha") if gr.status_code == 200 else None

        payload = {
            "message": commit_message,
            "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
            "branch": branch
        }
        if sha: payload["sha"] = sha

        ur = requests.put(get_url, headers=headers, json=payload)
        if ur.status_code >= 300:
            raise RuntimeError(f"GitHub push error for {path}: {ur.text}")
        results.append({"path": path, "status": "ok"})
    return {"pushed": results, "branch": branch, "repo": repo, "head_sha": head_sha}
