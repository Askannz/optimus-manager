from optimus_manager.bash import exec_bash, BashError


def logout_all_desktop_sessions():

    print("Logging out any open desktop session")

    # KDE Plasma
    try:
        exec_bash("qdbus org.kde.ksmserver /KSMServer logout 0 3 3")
    except BashError:
        pass

    # GNOME
    try:
        exec_bash("gnome-session-quit --logout --force")
    except BashError:
        pass
