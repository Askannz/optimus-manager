from optimus_manager.bash import exec_bash, BashError
from optimus_manager.polling import poll_block


class SessionError(Exception):
    pass


def terminate_current_x11_sessions():

    def any_session_left(): return (len(get_x11_sessions()) != 0)

    x11_sessions = get_x11_sessions()

    if len(x11_sessions) == 0:
        return

    for mode in ["terminate", "sigterm", "sigkill"]:

        print("%d open sessions found, terminating them manually with \"%s\"" % (len(x11_sessions), mode))

        for session in x11_sessions:
            terminate_session(session, mode)

        success = poll_block(any_session_left)

        if success:
            return
        else:
            x11_sessions = get_x11_sessions()

    else:
        raise SessionError("Failed to terminate loginctl x11 sessions")


def get_x11_sessions():

    try:
        sessions_list_str = exec_bash("loginctl list-sessions --no-legend | awk '{print $1}'").stdout.decode('utf-8')[:-1]
    except BashError as e:
        raise SessionError("Cannot list sessions : %s" % str(e))

    sessions = list(sessions_list_str.splitlines())
    return list(filter(_is_x11_session, sessions))


def terminate_session(session, mode="terminate"):

    assert mode in ["terminate", "sigterm", "sigkill"]

    try:
        if mode == "terminate":
            exec_bash("loginctl terminate-session %s" % session)
        elif mode == "sigterm":
            exec_bash("loginctl kill-session %s -s SIGTERM" % session)
        elif mode == "sigkill":
            exec_bash("loginctl kill-session %s -s SIGKILL" % session)
    except BashError as e:
        raise SessionError("Cannot kill session %s : %s" % (session, str(e)))


def _is_x11_session(session):

    try:

        session_info = exec_bash("loginctl show-session %s" % session).stdout.decode('utf-8')[:-1]
        return ("Type=x11" in session_info)

    except BashError as e:
        raise SessionError("Error checking type of session %s : %s" % (session, str(e)))
