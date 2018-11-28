import subprocess


class BashError(Exception):
    pass


def exec_bash(command):
    ret = subprocess.run(["bash", "-c", command], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if ret.returncode != 0:
        raise BashError("Failed to execute '%s' : %s" % (command, ret.stderr.decode('utf-8')[:-1]))

    return ret
