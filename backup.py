import os
import shutil
import envs


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

            if not os.path.isdir("/etc/X11/xorg.conf.d/"):
                os.mkdir("/etc/X11/xorg.conf.d/")

            for f in os.listdir(backup_xorg_conf_folder_path):
                backup_xorg_subconf_path = os.path.join(backup_xorg_conf_folder_path, f)
                dest_xorg_subconf_path = os.path.join("/etc/X11/xorg.conf.d/", f)
                shutil.move(backup_xorg_subconf_path, dest_xorg_subconf_path)

        # Removing leftover backup folder (should be empty at this point)
        shutil.rmtree(backup_path)
