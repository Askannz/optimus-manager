import dbus


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

    for session in sessions_list:
        session_type = _get_session_type(session)
        if session_type == "wayland":
            return True
    else:
        return False


def get_number_of_desktop_sessions(ignore_gdm=True):

    sessions_list = _get_sessions_list()

    count = 0
    for session in sessions_list:

        username = session[2]

        session_type = _get_session_type(session)
        if (session_type == "wayland" or session_type == "x11") and \
           (username != "gdm" or not ignore_gdm):
            count += 1

    return count


def _get_sessions_list():

    system_bus = dbus.SystemBus()
    logind = system_bus.get_object("org.freedesktop.login1", "/org/freedesktop/login1")
    sessions_list = logind.ListSessions(dbus_interface="org.freedesktop.login1.Manager")

    return sessions_list


def _get_session_type(session):

    system_bus = dbus.SystemBus()
    session_interface = system_bus.get_object("org.freedesktop.login1", session[4])
    properties_manager = dbus.Interface(session_interface, 'org.freedesktop.DBus.Properties')

    return properties_manager.Get("org.freedesktop.login1.Session", "Type")
