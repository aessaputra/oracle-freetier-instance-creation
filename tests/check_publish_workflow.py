"""Static check: GHCR publish workflow is manual-only and keeps multi-arch publishing."""
from pathlib import Path
import yaml

workflow = yaml.load(Path(".github/workflows/publish-image.yml").read_text(), Loader=yaml.BaseLoader)
assert list(workflow["on"]) == ["workflow_dispatch"], workflow["on"]

job = workflow["jobs"]["publish"]
assert job["if"] == "github.ref == 'refs/heads/main'", job["if"]
assert job["permissions"] == {"contents": "read", "packages": "write"}

build = job["steps"][-1]["with"]
assert build["platforms"] == "linux/amd64,linux/arm64"
assert build["push"] == "true"
assert "sha-${{ github.sha }}" in build["tags"]

readme = Path("README.md").read_text()
assert "pushes to `main`" not in readme
assert "Run workflow" in readme
print("PASS: workflow_dispatch only, main guard, multi-arch publish, README matches")
