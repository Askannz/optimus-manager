from optimus_manager.bash import exec_bash, BashError


class SessionError(Exception):
    pass


def get_x11_sessions():

    try:
        sessions_list_str = exec_bash("loginctl list-sessions --no-legend | awk '{print $1}'").stdout.decode('utf-8')[:-1]
    except BashError as e:
        raise SessionError("Cannot list sessions : %s" % str(e))

    sessions = list(sessions_list_str.splitlines())
    return list(filter(_is_x11_session, sessions))


def terminate_session(session):

    try:
        exec_bash("loginctl terminate-session %s" % session)
    except BashError as e:
        raise SessionError("Cannot kill session %s : %s" % (session, str(e)))


def _is_x11_session(session):

    try:

        session_info = exec_bash("loginctl show-session %s").stdout.decode('utf-8')[:-1]
        return ("Type=x11" in session_info)

    except BashError as e:
        raise SessionError("Error checking type of session %s : %s" % (session, str(e)))
