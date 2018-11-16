import subprocess


def exec_bash(command):
    return subprocess.run(["bash", "-c", command], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
