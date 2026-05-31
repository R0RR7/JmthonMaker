import os
import signal
import subprocess
import sys
import time
import shutil
from config import MASTER_DIR, DEPLOY_DIR


def _deploy_path(user_id):
    return os.path.join(DEPLOY_DIR, str(user_id))


def deploy(user_id, env_vars):
    dpath = _deploy_path(user_id)
    os.makedirs(dpath, exist_ok=True)

    with open(os.path.join(dpath, ".env"), "w") as f:
        for k, v in env_vars.items():
            f.write(f"{k}={v}\n")

    db_file = os.path.join(dpath, "database.json")
    if not os.path.exists(db_file):
        with open(db_file, "w") as f:
            f.write("{}")

    for _dir in ("resources", "plugins"):
        _link = os.path.join(dpath, _dir)
        if not os.path.exists(_link):
            os.symlink(os.path.join(MASTER_DIR, _dir), _link)

    proc_env = os.environ.copy()
    for k in ("API_ID", "API_HASH", "SESSION", "BOT_TOKEN"):
        proc_env.pop(k, None)
    proc_env["PYTHONPATH"] = f"{MASTER_DIR}:{proc_env.get('PYTHONPATH', '')}"

    log_path = os.path.join(dpath, "deploy.log")
    if os.path.exists(log_path):
        import shutil
        ts = time.strftime("%Y%m%d-%H%M%S")
        shutil.move(log_path, f"{log_path}.{ts}")
    log = open(log_path, "a")
    proc = subprocess.Popen(
        [sys.executable, "-m", "jmthon"],
        cwd=dpath,
        env=proc_env,
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )

    with open(os.path.join(dpath, "pid"), "w") as f:
        f.write(str(proc.pid))
    with open(os.path.join(dpath, "start_time"), "w") as f:
        f.write(str(time.time()))

    time.sleep(5)
    if proc.poll() is not None:
        raise RuntimeError("⟐ فشلت عملية التنصيب حاول مجددا وتأكد من البيانات")

    return proc.pid


def stop(user_id):
    dpath = _deploy_path(user_id)
    pid_file = os.path.join(dpath, "pid")
    if not os.path.exists(pid_file):
        return True
    with open(pid_file) as f:
        pid = int(f.read().strip())
    try:
        pgid = os.getpgid(pid)
        os.killpg(pgid, signal.SIGTERM)
        time.sleep(2)
        try:
            os.killpg(pgid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    except ProcessLookupError:
        pass
    for fname in ("pid",):
        fpath = os.path.join(dpath, fname)
        if os.path.exists(fpath):
            os.remove(fpath)
    return True


def is_running(user_id):
    dpath = _deploy_path(user_id)
    pid_file = os.path.join(dpath, "pid")
    if not os.path.exists(pid_file):
        return False
    with open(pid_file) as f:
        pid = int(f.read().strip())
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, OSError):
        return False


def restart(user_id):
    stop(user_id)
    time.sleep(3)
    env_file = os.path.join(_deploy_path(user_id), ".env")
    env_vars = {}
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    env_vars[k] = v
    return deploy(user_id, env_vars)


def cleanup(user_id):
    stop(user_id)
    dpath = _deploy_path(user_id)
    if os.path.exists(dpath):
        shutil.rmtree(dpath)
    return True


def get_uptime(user_id):
    dpath = _deploy_path(user_id)
    start_file = os.path.join(dpath, "start_time")
    if os.path.exists(start_file):
        with open(start_file) as f:
            return max(0, int(time.time() - float(f.read().strip())))
    return 0
