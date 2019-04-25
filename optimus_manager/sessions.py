from optimus_manager.bash import exec_bash, BashError


class SessionError(Exception):
    pass


def logout_all_x11_sessions():

    print("Logging out any open X11 session")

    x11_sessions = _get_x11_sessions()

    if len(x11_sessions) == 0:
        print("No X11 session to logout")
        return

    print("%d open sessions found" % len(x11_sessions))

    for session_id, user in x11_sessions:
        print("Terminating session %s (user %s)" % (session_id, user))
        exec_bash("loginctl terminate-session %s" % session_id)


def _get_x11_sessions():

    try:
        sessions_list_str = exec_bash("loginctl list-sessions --no-legend").stdout.decode('utf-8')[:-1]
    except BashError as e:
        raise SessionError("Cannot list sessions : %s" % str(e))

    x11_sessions = []

    for line in sessions_list_str.splitlines():

        line_items = line.split(" ")

        if len(line_items) != 5:
            print("Error listing X11 sessions : unexpected format at line : %s" % line)
            continue

        session_id, _, user, _, _ = line_items

        if _is_x11_session(session_id):
            x11_sessions.append((session_id, user))

    return x11_sessions


def _is_x11_session(session_id):

    try:

        session_info = exec_bash("loginctl show-session %s" % session_id).stdout.decode('utf-8')[:-1]
        return ("Type=x11" in session_info)

    except BashError as e:
        raise SessionError("Error checking type of session %s : %s" % (session_id, str(e)))
