# holds v1 runtime settings

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# anchors defaults to the repo, the app runs from Source/ so CWD cannot be trusted
REPO_ROOT = Path(__file__).resolve().parents[2]
VERSION = "1.1.0"


def build_label() -> str:
    # adds the deploy's short commit, so a run says which build produced it (decision T12-Q5)
    sha = os.environ.get("RAILWAY_GIT_COMMIT_SHA", "")
    return f"{VERSION}+{sha[:7]}" if sha else VERSION


class AnalysisSettings(BaseSettings):
    # reads DRIFTER_* variables, ignores everything else in the environment
    model_config = SettingsConfigDict(env_prefix="DRIFTER_", extra="ignore")

    # resolves owner/name to <base><owner>/<name>.git, tests point it at local bare repos
    remote_base_url: str = "https://github.com/"

    # stores run files, wiped on redeploy and restart until v3 makes it durable
    runs_dir: Path = REPO_ROOT / "runs"

    # holds temporary clones, None means the system temp folder
    clone_dir: Path | None = None

    # points at the pod's shared mapping, loaded at runtime (contract section 1)
    mapping_file: Path = REPO_ROOT / "docs" / "contract" / "mapping-v1.1.yaml"

    # caps each git call and the whole analysis, both end in 500 ANALYSIS_FAILED; 80 s stays under the pod's 90 s per call (spec 2.2)
    git_timeout: float = 60
    analysis_deadline: float = 80

    # runs at most this many analyses at once, extra requests wait for a slot
    max_concurrent: int = 2


@lru_cache
def get_settings() -> AnalysisSettings:
    # caches the settings, tests clear the cache after repointing the environment
    return AnalysisSettings()
