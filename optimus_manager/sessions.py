import dbus
from subprocess import CalledProcessError, check_call
from .log_utils import get_logger


class SessionsError(Exception):
    pass


def logout_current_desktop_session():
    logger = get_logger()
    logger.info("Logging out")

    try:
        session_bus = dbus.SessionBus()

    except dbus.exceptions.DBusException:
        pass

    else:
        def logout_kde():
            kde = session_bus.get_object("org.kde.Shutdown", "/Shutdown")
            kde.logout()

        def logout_gnome():
            gnome = session_bus.get_object("org.gnome.SessionManager", "/org/gnome/SessionManager")
            gnome.Logout(1, dbus_interface="org.gnome.SessionManager")

        def logout_xfce():
            xfce = session_bus.get_object("org.xfce.SessionManager", "/org/xfce/SessionManager")
            xfce.Logout(False, True, dbus_interface="org.xfce.Session.Manager")

        def logout_deepin():
            deepin = session_bus.get_object('com.deepin.SessionManager', '/com/deepin/SessionManager')
            deepin.RequestLogout()

        for logout_func in [
            logout_kde,
            logout_gnome,
            logout_xfce,
            logout_deepin
        ]:
            try:
                logout_func()

            except dbus.exceptions.DBusException:
                pass

    for cmd in [
        "awesome-client \"awesome.quit()\"",  # AwesomeWM
        "bspc quit",  # bspwm
        "pkill -SIGTERM -f dwm",  # dwm
        "herbstclient quit",  # herbstluftwm
        "i3-msg exit",  # i3
        "pkill -SIGTERM -f lightdm" # lightdm
        "pkill -SIGTERM -f lxsession",  # LXDE
        "openbox --exit",  # Openbox
        "qtile cmd-obj -o cmd -f shutdown",  # qtile
        "pkill -SIGTERM -f xmonad",  # Xmonad
    ]:
        try:
            check_call(cmd, shell=True)
        except CalledProcessError:
            pass


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
