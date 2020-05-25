import dbus
from .bash import exec_bash, BashError
from .log_utils import get_logger


class SessionsError(Exception):
    pass


def logout_current_desktop_session():

    logger = get_logger()

    logger.info("Logging out the current desktop session")

    try:
        session_bus = dbus.SessionBus()
    except dbus.exceptions.DBusException:
        pass
    else:
        # KDE Plasma
        try:
            kde = session_bus.get_object("org.kde.ksmserver", "/KSMServer")
            kde.logout(0, 3, 3, dbus_interface="org.kde.KSMServerInterface")
        except dbus.exceptions.DBusException:
            pass

        # GNOME
        try:
            gnome = session_bus.get_object("org.gnome.SessionManager", "/org/gnome/SessionManager")
            gnome.Logout(1, dbus_interface="org.gnome.SessionManager")
        except dbus.exceptions.DBusException:
            pass

        # XFCE
        try:
            xfce = session_bus.get_object("org.xfce.SessionManager", "/org/xfce/SessionManager")
            xfce.Logout(False, True, dbus_interface="org.xfce.Session.Manager")
        except dbus.exceptions.DBusException:
            pass

        # Deepin
        try:
            deepin = session_bus.get_object('com.deepin.SessionManager', '/com/deepin/SessionManager')
            deepin.RequestLogout()
        except dbus.exceptions.DBusException:
            pass

    # i3
    try:
        exec_bash("i3-msg exit")
    except BashError:
        pass

    # openbox
    try:
        exec_bash("openbox --exit")
    except BashError:
        pass

    # AwesomeWM
    try:
        exec_bash("awesome-client \"awesome.quit()\"")
    except BashError:
        pass

    # bspwm
    try:
        exec_bash("bspc quit")
    except BashError:
        pass

    # lxde
    try:
        exec_bash("pkill -SIGTERM -f lxsession")
    except BashError:
        pass


def is_there_a_wayland_session():

    sessions_list = _get_sessions_list()

    for session in sessions_list:
        session_type = _get_session_type(session)
        if session_type == "wayland":
            return True

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
