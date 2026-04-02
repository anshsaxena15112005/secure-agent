from pathlib import Path
import yaml

POLICY_PATH = Path(__file__).resolve().parent.parent.parent / "policies" / "default_policy.yaml"

_POLICY_CACHE = None


def load_policy():
    global _POLICY_CACHE
    with open(POLICY_PATH, "r", encoding="utf-8") as f:
        _POLICY_CACHE = yaml.safe_load(f)
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
    with open(POLICY_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    return reload_policy()