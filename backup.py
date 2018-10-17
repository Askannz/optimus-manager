import os
import shutil
import envs


# TODO : Should copy files instead of moving them ? (Preserving the existing backup)
def restore_backup():

    backup_path = os.path.join(envs.SYSTEM_CONFIGS_PATH, "backup/")

    if not os.path.isdir(backup_path) or not os.listdir(backup_path):
        print("WARNING : No backup to restore !")
    else:

        # Cleanup
        print("Cleaning up before restoring backup")
        if os.path.isdir("/etc/X11/xorg.conf.d/"):
            shutil.rmtree("/etc/X11/xorg.conf.d/")

        # Restoring Xorg config
        backup_main_xorg_conf_path = os.path.join(backup_path, "xorg", "xorg.conf")
        if os.path.isfile(backup_main_xorg_conf_path):
            shutil.move(backup_main_xorg_conf_path, "/etc/X11/xorg.conf")

        backup_xorg_conf_folder_path = os.path.join(backup_path, "xorg", "xorg.conf.d")
        if os.path.isdir(backup_xorg_conf_folder_path):

            os.mkdir("/etc/X11/xorg.conf.d/")

            for f in os.listdir(backup_xorg_conf_folder_path):
                backup_xorg_subconf_path = os.path.join(backup_xorg_conf_folder_path, f)
                dest_xorg_subconf_path = os.path.join("/etc/X11/xorg.conf.d/", f)
                shutil.move(backup_xorg_subconf_path, dest_xorg_subconf_path)

        # Removing leftover backup folder (should be empty at this point)
        shutil.rmtree(backup_path)


def make_backup():

    backup_path = os.path.join(envs.SYSTEM_CONFIGS_PATH, "backup/")

    # Cleanup
    if os.path.isdir(backup_path) and os.listdir(backup_path):
        print("WARNING : There is an existing backup ! Overwriting...")  # TODO : Add a "force" option instead
        shutil.rmtree(backup_path)
    else:
        os.mkdir(backup_path)

    # Backing up Xorg config
    backup_main_xorg_conf_path = os.path.join(backup_path, "xorg", "xorg.conf")
    if os.path.isfile("/etc/X11/xorg.conf"):
        shutil.copy("/etc/X11/xorg.conf", backup_main_xorg_conf_path)

    backup_xorg_conf_folder_path = os.path.join(backup_path, "xorg", "xorg.conf.d")
    if os.path.isdir("/etc/X11/xorg.conf.d/"):

        os.mkdir(backup_xorg_conf_folder_path)

        for f in os.listdir(backup_xorg_conf_folder_path):
            backup_xorg_subconf_path = os.path.join(backup_xorg_conf_folder_path, f)
            dest_xorg_subconf_path = os.path.join("/etc/X11/xorg.conf.d/", f)
            shutil.copy(backup_xorg_subconf_path, dest_xorg_subconf_path)
