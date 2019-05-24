optimus-manager
==================

**IMPORTANT :** this README is for version v1.0. If you are still using the previous version (v0.8), the corresponding README is available here : https://github.com/Askannz/optimus-manager/wiki/v0.8-README

This Linux program provides a solution for GPU switching on Optimus laptops (i.e laptops with a dual Nvidia/Intel GPU configuration).

Obviously this is unofficial, I am not affiliated with Nvidia in any way.

**Only Archlinux and Archlinux-based distributions (such as Manjaro) are supported for now.**
Only Xorg sessions are supported (no Wayland).

Supported display managers are : SDDM, LightDM, GDM.

optimus-manager *might* still work with other display managers but you have to configure them manually (see [this FAQ section](https://github.com/Askannz/optimus-manager/wiki/FAQ,-common-issues,-troubleshooting#my-display-manager-is-not-sddm-lightdm-nor-sddm)).

Introduction
----------
GPU offloading with Nvidia cards is not supported on Linux, which can make it hard to use your Optimus laptop at full performance. optimus-manager provides a workaround to this problem by allowing you to run your whole desktop session on the Nvidia GPU, while the Intel GPU only acts as a "relay" between the Nvidia GPU and your screen.

This is essentially a port to Archlinux of the **nvidia-prime** solution created by Canonical for Ubuntu.

To learn more about the current Optimus situation on Linux and how this solution works, read the [Home Wiki page](https://github.com/Askannz/optimus-manager/wiki).


IMPORTANT : Gnome and GDM users
----------

If you use Gnome or the Gnome Display Manager (GDM), there are a couple extra requirements to be able to use optimus-manager :

* The default `gdm` package from the Archlinux and Manjaro repositories is not compatible with optimus-manager, so you must replace it with this patched version : [gdm-prime](https://aur.archlinux.org/packages/gdm-prime/) (also replaces `libgdm`). The patch was written by Canonical for Ubuntu and simply adds two script entry points specifically for Prime switching. The package is otherwise identical to the official one.

* Gnome launches Wayland sessions by default, which are incompatible with optimus-manager. To force Xorg sessions, You need to edit the file `/etc/gdm/custom.conf` and remove the `#` before the line `#WaylandEnable=false`.

Another quirk of GDM is that the X server may not automatically restart after a GPU switch. If you see an empty black screen or a black screen with a blinking cursor, try switching back to an empty TTY (with Ctrl+Alt+F5 for instance), then back to TTY1 with Ctrl+Alt+F1. See [this FAQ question](https://github.com/Askannz/optimus-manager/wiki/FAQ,-common-issues,-troubleshooting#after-trying-to-switch-gpus-i-am-stuck-with-a-black-screen-or-a-black-screen-with-a-blinking-cursor-or-a-tty-login-screen).


Installation
----------

Naturally, you must have the proprietary nvidia driver installed on your system. On Archlinux, you can use the packages `nvidia` or `nvidia-dkms`. On Manjaro, it is fine to use the built-in driver utility.

You can install optimus-manager from this AUR package : [optimus-manager](https://aur.archlinux.org/packages/optimus-manager/)

Reboot your computer after installation (this is necessary for the new display manager configuration to take effect).

After reboot, the optimus-manager daemon should have been started automatically, but you can check its status with `systemctl status optimus-manager.service`.

**Important notes :**

* **Custom Xorg config :** optimus-manager works by auto-generating a Xorg configuration file and putting it into `/etc/X11/xorg.conf.d/`. If you already have custom Xorg configuration files at that location or at `/etc/X11/xorg.conf `, it is strongly advised that you remove anything GPU-related from them to make sure that they do not interfere with the GPU switching process.

* **Nvidia-generated Xorg config :** Similarly, if you have ever used the `nvidia-xonfig` utility or the `Save to X Configuration File` button in the Nvidia control panel, a Xorg config file may have been generated at `/etc/X11/xorg.conf `. It is highly recommended to delete it before trying to switch GPUs.

* **Manjaro-generated Xorg config :** Manjaro has its own driver utility called MHWD that also auto-generates a Xorg config file at `/etc/X11/xorg.conf.d/90-mhwd.conf`. optimus-manager will automatically delete that file to avoid issues.

* **Manjaro Gnome** : see the previous section **Gnome and GDM users**

* **Manjaro KDE** : Manjaro ships with a default configuration for SDDM (the default login manager for KDE) which overrides some keys needed by optimus-manager. To fix this, you need to edit the file `/etc/sddm.conf` and simply put a `#` before the line starting with `DisplayCommand`and the one starting with `DisplayStopCommand`.

* **Bumblebee :** optimus-manager is incompatible with Bumblebee since both tools would be trying to control GPU power switching at the same time. If Bumblebee is installed, you must disable its daemon (`sudo systemctl disable bumblebeed.service`, then reboot). This is particularly important for Manjaro users since Bumblebee is installed by default.

Uninstallation
----------

To uninstall the program, simply remove the `optimus-manager` package. The auto-generated Xorg config file will be automatically cleaned up.

You can also force cleanup by running `optimus-manager --cleanup`.

Not that simply disabling the daemon will not prevent `optimus-manager` from running, as most of the GPU setup process happens in scripts directly run by the login manager.

Usage
----------

Run
* `optimus-manager --switch nvidia` to switch to the Nvidia GPU
* `optimus-manager --switch intel` to switch to the Intel GPU.
* `optimus-manager --switch auto` to automatically detect which mode you are currently running in and switch to the other.

*WARNING :* Switching GPUs automatically logs you out, so make sure you save your work and close all your applications before doing so.

You can disable auto-logout in the configuration file. In that case, the GPU switch will not be effective until the next login.

You can also specify which GPU you want to be used by default when the system boots :

```
optimus-manager --set-startup MODE
```

Where `MODE` can be `intel`, `nvidia`, or `nvidia_once`. The last one is a special mode which makes your system use the Nvidia GPU at boot, but for one boot only. After that it reverts to `intel` mode. This can be useful to test your Nvidia configuration and make sure you do not end up with an unusable X server.

#### System Tray App

![optimus-manager systray screenshot](systray.png "optimus-manager systray")

The program [optimus-manager-qt](https://github.com/Shatur95/optimus-manager-qt) provides a system tray icon for easy switching. It also includes a GUI for setting options without editing the configuration file manually.    
AUR package : [optimus-manager-qt](https://aur.archlinux.org/packages/optimus-manager-qt/)

A Gnome Shell extension is also available here : [optimus-manager-argos](https://github.com/inzar98/optimus-manager-argos).

Configuration
----------

The default configuration file can be found at `/usr/share/optimus-manager.conf`. Please do not edit this file ; instead, edit the config file at `/etc/optimus-manager/optimus-manager.conf` (or create it if it does not exist).

Any parameter not specified in your config file will take value from the default file. Remember to include the section headers of the options you override.

Please refer to the comments in the [default config file](https://github.com/Askannz/optimus-manager/blob/master/optimus-manager.conf) for descriptions of the available parameters. In particular, it is possible to set common Xorg options like DRI version or triple buffering, as well as some kernel module loading options.

Some config changes will not be effective until you computer is rebooted or the optimus-manager service is restarted.

You can also add your own Xorg options in `/etc/optimus-manager/xorg-intel.conf` and `/etc/optimus-manager/xorg-nvidia.conf`. Anything you put in those files will be written to the "Device" section of the auto-generated Xorg configuration file corresponding to their respective GPU mode.

Finally, if you need the display manager to run some specific commands to set up the display (to force a particular resolution, for instance), you can write them to `/etc/optimus-manager/xsetup-intel.sh` (for Intel mode) and `/etc/optimus-manager/xsetup-nvidia.sh` (for Nvidia mode).

FAQ / Troubleshooting
----------

See the [FAQ section](https://github.com/Askannz/optimus-manager/wiki/FAQ,-common-issues,-troubleshooting) in the Wiki.

Credit
----------
The Qt tray app was created by [Shatur95](https://github.com/Shatur95).
