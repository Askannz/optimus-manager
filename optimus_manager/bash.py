import subprocess


class BashError(Exception):
    pass


def exec_bash(command):

    try:
        out = subprocess.check_output(
            ["bash", "-c", command],
            stderr=subprocess.STDOUT
        ).decode("utf8").strip()

    except subprocess.CalledProcessError as e:
        out = e.stdout.decode("utf8")
        raise BashError(
            "Failed to execute '%s' :\n%s" % (
                command, out))

    return out
