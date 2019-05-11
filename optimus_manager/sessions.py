import dbus
from optimus_manager.bash import exec_bash, BashError


class SessionsError(Exception):
    pass


def logout_current_desktop_session():

    print("Logging out the current desktop session")

    session_bus = dbus.SessionBus()

    # KDE Plasma
    kde = session_bus.get_object("org.kde.ksmserver", "/KSMServer")
    kde.logout(0, 3, 3, dbus_interface="org.kde.KSMServerInterface")

    # GNOME
    gnome = session_bus.get_object("org.gnome.SessionManager", "/org/gnome/SessionManager")
    gnome.Logout(1, dbus_interface="org.gnome.SessionManager")

    # XFCE
    xfce = session_bus.get_object("org.xfce.SessionManager", "/org/xfce/SessionManager")
    xfce.Logout(False, True, dbus_interface="org.xfce.Session.Manager")


def is_there_a_wayland_session():

    sessions_list = _get_sessions_list()

    for session_id, _ in sessions_list:
        session_type = _get_session_type(session_id)
        if session_type == "wayland":
            return True
    else:
        return False


def get_number_of_desktop_sessions(ignore_gdm=True):

    sessions_list = _get_sessions_list()

    count = 0
    for session_id, username in sessions_list:
        session_type = _get_session_type(session_id)
        if (session_type == "wayland" or session_type == "x11") and \
           (username != "gdm" or not ignore_gdm):
            count += 1

    return count


def _get_sessions_list():

    try:
        sessions_list_str = exec_bash("loginctl list-sessions --no-legend").stdout.decode('utf-8')[:-1]
    except BashError as e:
        raise SessionsError("Cannot list sessions : %s" % str(e))

    sessions_list = []

    for line in sessions_list_str.splitlines():

        line_items = line.split()

        if len(line_items) < 3:
            print("Warning : loginctl : cannot parse line : %s" % line)
            continue

        session_id = line_items[0]
        username = line_items[2]

        sessions_list.append((session_id, username))

    return sessions_list


def _get_session_type(session_id):

    try:

        session_info = exec_bash("loginctl show-session %s" % session_id).stdout.decode('utf-8')[:-1]

    except BashError as e:
        raise SessionsError("Error checking type of session %s : error running loginctl : %s" % (session_id, str(e)))

    for line in session_info.splitlines():
        if "Type=" in line:
            equal_sign_index = line.find("=")
            session_type = line[equal_sign_index+1:]
            return session_type
    else:
        raise SessionsError("Error checking type of session %s : no Type value" % session_id)
