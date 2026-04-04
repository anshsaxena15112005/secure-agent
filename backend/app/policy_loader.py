from pathlib import Path
import shutil
import yaml
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent.parent

POLICY_PATH = BASE_DIR / "policies" / "default_policy.yaml"
POLICY_BACKUP_PATH = BASE_DIR / "policies" / "default_policy.backup.yaml"
HISTORY_DIR = BASE_DIR / "policies" / "history"

HISTORY_DIR.mkdir(parents=True, exist_ok=True)

_POLICY_CACHE = None


def _generate_version_name():
    return datetime.utcnow().strftime("policy_%Y%m%d_%H%M%S.yaml")


def _save_current_to_history():
    if POLICY_PATH.exists():
        version_name = _generate_version_name()
        history_path = HISTORY_DIR / version_name
        shutil.copyfile(POLICY_PATH, history_path)
        return version_name
    return None


def load_policy():
    global _POLICY_CACHE
    with open(POLICY_PATH, "r", encoding="utf-8") as f:
        _POLICY_CACHE = yaml.safe_load(f) or {}
    return _POLICY_CACHE


def get_policy():
    global _POLICY_CACHE
    if _POLICY_CACHE is None:
        return load_policy()
    return _POLICY_CACHE


def reload_policy():
    return load_policy()


def read_policy_text():
    with open(POLICY_PATH, "r", encoding="utf-8") as f:
        return f.read()


def write_policy_text(content: str):
    # 🔥 save old version before overwrite
    _save_current_to_history()

    with open(POLICY_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    return reload_policy()


def reset_policy_text():
    if not POLICY_BACKUP_PATH.exists():
        raise FileNotFoundError("Backup policy file not found")

    # save current before reset
    _save_current_to_history()

    shutil.copyfile(POLICY_BACKUP_PATH, POLICY_PATH)
    return reload_policy()


# ---------- HISTORY ----------

def list_policy_versions():
    versions = []
    for file in sorted(HISTORY_DIR.glob("*.yaml"), reverse=True):
        versions.append({
            "name": file.name,
            "timestamp": file.stat().st_mtime
        })
    return versions


def restore_policy_version(version_name: str):
    target = HISTORY_DIR / version_name

    if not target.exists():
        raise FileNotFoundError("Version not found")

    # backup current before restore
    _save_current_to_history()

    shutil.copyfile(target, POLICY_PATH)
    return reload_policy()