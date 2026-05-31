import json
import os
from datetime import datetime, timedelta
from config import FACTORY_DIR

DB_PATH = os.path.join(FACTORY_DIR, "jmthon_factory.json")


def _load():
    if not os.path.exists(DB_PATH):
        return {"users": {}, "stats": {"total_users": 0, "total_installs": 0}}
    with open(DB_PATH, "r") as f:
        return json.load(f)


def _save(data):
    with open(DB_PATH, "w") as f:
        json.dump(data, f, indent=2)


def add_user(user_id, username, first_name):
    data = _load()
    uid = str(user_id)
    if uid not in data["users"]:
        data["users"][uid] = {
            "user_id": user_id,
            "username": username or None,
            "first_name": first_name,
            "is_installed": False,
            "install_date": None,
            "expiry_date": None,
            "phone": None,
            "status": "none",
            "created_at": datetime.now().isoformat(),
        }
        data["stats"]["total_users"] = len(data["users"])
    _save(data)


def get_user(user_id):
    data = _load()
    return data["users"].get(str(user_id))


def update_user(user_id, **kwargs):
    data = _load()
    uid = str(user_id)
    if uid not in data["users"]:
        return False
    for key, value in kwargs.items():
        if value is not None:
            data["users"][uid][key] = value
    _save(data)
    return True


def delete_user(user_id):
    data = _load()
    uid = str(user_id)
    if uid in data["users"]:
        del data["users"][uid]
        data["stats"]["total_users"] = len(data["users"])
    _save(data)


def get_all_users():
    data = _load()
    return list(data["users"].values())


def get_installed_users():
    return [u for u in get_all_users() if u.get("is_installed")]


def get_expired_users():
    now = datetime.now()
    result = []
    for u in get_installed_users():
        exp = u.get("expiry_date")
        if exp and datetime.fromisoformat(exp) <= now:
            result.append(u)
    return result


def get_stats():
    all_users = get_all_users()
    installed = get_installed_users()
    expired = get_expired_users()
    running = [u for u in installed if u.get("status") == "running" and
               u.get("expiry_date") and datetime.fromisoformat(u["expiry_date"]) > datetime.now()]
    return {
        "total_users": len(all_users),
        "installed": len(installed),
        "running": len(running),
        "expired": len(expired),
        "stopped": len([u for u in installed if u.get("status") == "stopped"]),
    }
