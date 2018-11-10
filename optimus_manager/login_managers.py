import os
import optimus_manager.envs as envs
from optimus_manager.detection import get_login_managers


class LoginManagerError(Exception):
    pass


def configure_login_managers(mode):

    login_managers = get_login_managers()

    if len(login_managers) == 0:
        msg = "No supported login manager detected. Please manually configure" \
              "your login manager to use the display setup script at %s. If you" \
              "use xinit, add this script to your .xinitrc" % envs.XSETUP_PATH
        print(msg)
        return

    for manager_name in login_managers:

        if manager_name == "sddm":
            _configure_sddm(mode)


def _configure_sddm(mode):

    CONF_FOLDER_PATH = "/etc/sddm.conf.d/"

    conf_filepath = os.path.join(CONF_FOLDER_PATH. envs.SDDM_CONF_NAME)

    if mode == "intel":

        if os.path.isfile(conf_filepath):
            os.remove(conf_filepath)

    elif mode == "nvidia":

        if not os.path.isdir(CONF_FOLDER_PATH):
            os.mkdir(CONF_FOLDER_PATH)

        text = "[X11]\n" \
               "DisplayCommand=%s\n" % envs.XSETUP_PATH

        try:
            with open(conf_filepath, 'w') as f:
                f.write(text)

        except IOError:
            raise LoginManagerError("Cannot write to %s" % conf_filepath)
