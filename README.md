optimus-manager
==================

This Linux program provides a solution for GPU switching on Optimus laptops (a.k.a laptops with dual Nvidia/Intel GPUs).

Obviously this is unofficial, I am not affiliated with Nvidia in any way.

**Only Archlinux (plus derivatives like Manjaro) is supported for now.**
Only Xorg sessions are supported (no Wayland).

Supported display managers are : SDDM, LightDM, GDM.

optimus-manager *might* still work with other display managers but you have to configure them manually (see [this section](#my-display-manager-is-not-sddm-lightdm-nor-sddm)).

The "why"
----------

On Windows, the Optimus technology works by dynamically offloading rendering to the Nvidia GPU when running 3D-intensive applications, while the desktop session itself runs on the Intel GPU.

However, on Linux, the Nvidia driver does not provide such offloading capabilities ([yet](https://devtalk.nvidia.com/default/topic/957981/linux/prime-render-offloading-on-nvidia-optimus/post/5276481/#5276481)), which difficult for us to use the full potential of our machines without destroying their battery life.

Currently, if you have Linux installed on an Optimus laptop, there are three methods to use your Nvidia GPU :

- **Run your whole X session on the Intel GPU and use [Bumblebee](https://github.com/Bumblebee-Project/Bumblebee) to offload rendering to the Nvidia GPU.** While this mimic the behavior of Optimus on Windows, this is an unofficial, hacky solution with three major drawbacks : 1. a noticeable performance hit (because Bumblebee has to use your CPU to copy frames over to the display) 2. no support for Vulkan (therefore, it is incompatible with DXVK and any native game using Vulkan, like Shadow of the Tomb Raider for instance) 3. you will be unable to use any video output (like HDMI ports) connected to the Nvidia GPU, unless you have the open-source `nouveau` driver loaded to this GPU at the same time (or use some solution like intel-virtual-output).

- **Use [nvidia-xrun](https://github.com/Witko/nvidia-xrun) to have the Nvidia GPU run on its own X server in another virtual terminal**. You still have to run two X servers at the same time, and you do not have acess to your normal desktop environment while in the virtual terminal of the Nvidia GPU. Also, in my own experience, desktop environments are prone prone to crashing when switching between virtual terminals while the nvidia driver is running.

- **Run your whole X session on the Nvidia GPU and disable rendering on the Intel GPU.** This allows you to run your applications at full performance, with Vulkan support, and with access to all video outputs. However, since your power-hungry Nvidia GPU is turned on at all times, it has a massive impact on your battery life.
This method is often called Nvidia PRIME, although technically PRIME is just the technology that allows your Nvidia GPU to send its frames to the built-in display of your laptop *via* the Intel GPU.

An acceptable middle ground could be to use the third method *on demand* : switching the X session to the Nvidia GPU when you need extra rendering power, and then switching it back to Intel when you are done, to save battery life.

Unfortunately the X server configuration is set-up in a permanent manner with configuration files, which makes switching a hassle because you have to rewrite those files every time you want to switch GPUs. You also have to restart the X server for those changes to be taken into account.

This is what this tool does for you : it dynamically writes the X configuration at boot time, rewrites it every time you need to switch GPUs, and also loads the appropriate kernel modules to make sure your GPUs are properly turned on/off.

Note that this is nothing new : Ubuntu has been using that method for years with their `prime-select` script.

In practice, here is what happens when switching to the Intel GPU (for example) :
1. Your login manager is automatically stopped, which also stops the X server (warning : this closes all opened applications)
2. The Nvidia modules are unloaded and either `bbswitch` or `nouveau` are loaded instead. `bbswitch` is used to turn off the card on machines which do not support power management from the kernel, while `nouveau` is the open-source driver for Nvidia cards, which allows you to use external outputs even in Intel mode.
3. The configuration for X and your login manager is updated (note that the configuration is saved to dedicated files, this will *not* overwrite any of your own configuration files)
4. The login manager is restarted.


Before using optimus-manager, be aware that this is still a *hacky* solution and may have stability issues with some desktop environments/display managers.

I will happily deprecate this tool the day Nvidia implements proper GPU offloading in their Linux driver.


Installation
----------

You can use this AUR package : [optimus-manager](https://aur.archlinux.org/packages/optimus-manager/)

Then, enable the daemon :

```
$ sudo systemctl enable optimus-manager.service
```
Then, reboot (it is necessary for the new Systemd configuration to take effect).

**IMPORTANT :** make sure you do not have any configuration file conflicting with the ones autogenerated by optimus-manager. In particular, remove everything related to displays or GPUs in `/etc/X11/xorg.conf` and `/etc/X11/xorg.conf.d/`. Also, avoid running `nvidia-xconfig` or using the `Save to X Configuration file` in the Nvidia control panel. If you need to apply specific options to your Xorg config, see the [Configuration](#configuration) section.

**For Manjaro users** : In addition to the above, do *not* install your GPU drivers through MHWD. It will autogenerate Xorg configuration files which conflicts with optimus-manager. If you have already done it, be sure to remove anything GPU-related in `/etc/X11/xorg.conf.d/`. Also, Manjaro comes with bumblebee enabled by default so remember to disable it (see the next paragraph).

Also, if you have bumblebee installed on your system, uninstall it or at least make sure the `bumblebeed` service is disabled. Finally, make sure the `bbswitch` module is not loaded at boot time (check `/etc/modules-load.d/`).

Finally, make sure the nvidia driver is installed. On Archlinux, you can use the packages `nvidia` ir `nvidia-dkms`. On Manjaro, the packages have names like `linuxXXX-nvidia` (where `XXX` is the kernel version). For games, it is also recommended to install `nvidia-utils` and `lib32-nvidia-utils`.


Uninstallation
----------

If you do not want to use `optimus-manager` anymore, you need to run `optimus-manager --cleanup` to clear any leftover autogenerated configuration file, then uninstall the program. Just disabling the daemon is not enough because the Sytemd scripts will still be executed.

Usage
----------

Make sure the systemd service `optimus-manager.service` is running, then run
```
optimus-manager --switch nvidia
```
to switch to the Nvidia GPU, and
```
optimus-manager --switch intel
```
to switch to the Intel GPU.

(you can also use `optimus-manager --switch auto` to automatically switch to the other mode)

*WARNING :* Switching GPUs automatically restarts your display manager, so make sure you save your work and close all your applications before doing so.

You can setup autologin in your display manager so that you do not have to re-enter your password every time.


You can also specify which GPU you want to be used by default when the system boots :

```
optimus-manager --set-startup MODE
```

Where `MODE` can be `intel`, `nvidia`, or `nvidia_once`. The last one is a special mode which makes your system use the Nvidia GPU at boot, but for one boot only. After that it reverts to `intel` mode. This can be useful to test your Nvidia configuration and make sure you do not end up with an unusable X server.

**For GNOME users** : for now, optimus-manager has some random issues with restarting the GNOME desktop environment, so you may experience issues after a GPU switch. If you want to go the safe way, use the `--set-startup` option to set the GPU you want and reboot your computer.

#### System Tray Icon

optimus-manager includes a system tray icon that makes it easy to switch GPUs. It should work on most desktop environments.

To make the tray icon automatically launch with your DE, it is usually enough to do:
```
ln -s /usr/share/applications/optimus-manager-systray.desktop ~/.config/autostart/optimus-manager-systray.desktop
```

A Gnome Shell extension was also made, you can find it here : [optimus-manager-argos](https://github.com/inzar98/optimus-manager-argos).

Configuration
----------

The default configuration file can be found at `/usr/share/optimus-manager.conf`. Please do not edit this file ; instead, edit the config file at `/etc/optimus-manager/optimus-manager.conf` (create it if it does not exist).

(Note : the user configuration file used to be at `/etc/optimus-manager.conf`. This path is now deprecated. It still works for now but will be ignored in the future.)

Any parameter not specified in your config file will take value from the default file. Remember to include the section headers of the options you override.

Please refer to the comments in the [default config file](https://github.com/Askannz/optimus-manager/blob/master/optimus-manager.conf) for descriptions of the available parameters. In particular, it is possible to set common Xorg options like DRI version or triple buffering, as well as some kernel module loading options.

You can also add your own Xorg options in `/etc/optimus-manager/xorg-intel.conf` and `/etc/optimus-manager/xorg-nvidia.conf`. Anything you put in those files will be written to the "Device" section of the auto-generated Xorg configuration file corresponding to their respective GPU mode.

FAQ / Troubleshooting
----------

General troubleshooting advice : you can view the logs of the optimus-manager daemon by running `journalctl -u optimus-manager.service`, but the most important log is the one from your display manager : `journalctl -u display-manager.service`. Please include both if you have to open a GitHub issue. Add `-b0` if you want to see the logs for the current boot (`-b-1` for the previous boot, etc) and add `--no-pager` if you need to copy-paste the whole log.

The Arch wiki can be a great resource for troubleshooting. Check the following pages : [NVIDIA](https://wiki.archlinux.org/index.php/NVIDIA), [NVDIA Optimus](https://wiki.archlinux.org/index.php/NVIDIA_Optimus), [Bumblebee](https://wiki.archlinux.org/index.php/Bumblebee) (even if optimus-manager does not use Bumblebee, some advices related to power switching can still be applicable)



#### How can I check which GPU my X session is running on ?

Run `optimus-manager --print-mode`. Alternatively, you can run `glxinfo | grep "server glx vendor string"`. You will see `Nvidia corporation` if you are running on Nvidia, and `SGI` otherwise.

#### When I switch GPUs, my system completely locks up (I cannot even switch to a TTY with Ctrl+Alt+F*x*)

It is very likely your laptop is plagued by one of the numerous ACPI issues associated with Optimus laptops on Linux, and caused by manufacturers having their own implementations. The symptoms are often similar : a complete system lockup if you try to run any program that uses the Nvidia GPU while it is powered off. Unfortunately there is no universal fix, but the solution often involves adding a kernel parameter to your boot options. You can find more information on [this GitHub issue](https://github.com/Bumblebee-Project/Bumblebee/issues/764), where people have been reporting solutions for specific laptop models. Check [this Arch Wiki page](https://wiki.archlinux.org/index.php/Kernel_parameters) to learn how to set a kernel parameter at boot.

You can also try changing the power switching backend in the configuration file (section `[optimus]`, parameter `switching`). If that fails, also try disabling `pci_reset` or `pci_power_control`.

#### GPU switching works but my system locks up if I am in Intel mode and start any of the following programs : VLC, lspci, anything that polls the PCI devices

This is due to ACPI problems, see the previous question.

#### I think my Nvidia GPU stays powered on even in Intel mode (my battery drains too fast)

The default PCI power management does not work for some laptop models. Try switching the power switching backend to `bbswitch` (option `switching`, Section `[optimus]`). You can also check `dmesg` for errors related to `nouveau` or PCI power management.  

#### My display manager is not SDDM, LightDM nor SDDM

You must configure it manually so that it executes the script `/usr/bin/optimus-manager_Xsetup` on startup. The X server may still work without that step but your login manager will show a black screen on the built-in monitor instead of the login window. You can also set up autologin to avoid that.

#### The display manager stops but does not restart (a.k.a I am stuck in TTY mode)

This is generally a problem with the X server not restarting. Refer to the next question.


#### When I try to switch GPUs, I end up with a black screen (or a black screen with only a blinking cursor)

First, make sure your system is not completely locked up and you can still switch between TTYs with Ctrl+Alt+F1,F2,etc. If you cannot, [refer to this question](#when-i-switch-gpus-my-system-completely-locks-up-i-cannot-even-switch-to-a-tty-with-ctrlaltfx).

If you can still switch between TTYs, it generally means that the X server failed to restart. In addition to the optimus-manager logs, you can check the Xorg logs at for more information. Those logs are usually at `/var/log/Xorg.0.log` or `~/.local/share/xorg/Xorg.0.log` (they may have a different number than `0`). If you managed to return to a graphical session, be sure to include the log from the server that failed and not the running one (the logs from the previous attempt end with the `.old` extension).

Some fixes you can try :
- Setting the power switching backend to `bbswitch` in the configuration file (section `[optimus]`, parameter `switching`)
- Setting `modeset` to `no` in the `[intel]` and `[nvidia]` sections
- Changing the DRI versions from 3 to 2

If that does not fix your problem and you have to open a GitHub issue, please attach the Xorg log in addition to the optimus-manager daemon log and the display manager log.

#### GPU switching works but I cannot run any 3D application in Intel mode (they fail to launch with some error message)

Check if the `nvidia` module is still loaded in Intel mode. That should not happen, but if it is the case, then logout, stop the display manager manually, unload all Nvidia modules (`nvidia_drm`, `nvidia_modeset`, `nvidia-uvm`, and `nvidia`, in that order) and restart the display manager.

Consider opening a GitHub issue about this, with logs attached.

#### After switching GPUs, I experience poor CPU performance or heavy stuttering, or my external video outputs do not work

If the problem occurs after switching to Nvidia, try setting `modeset` to `no` in the `[nvidia]` section of the configuration file.

If the problem occurs after switching to Intel, try setting `modeset` to `no` in the `[intel]` section of the configuration file, or you can also try disabling nouveau by setting the `switching` option in the `[optimus]` section to `bbswitch`. Note that those two fixes may prevent you from using your video outputs (such as HDMI) in Intel mode.

#### I do not want optimus-manager to stop/restart my display manager

You can disable control of the login manager by setting the option `login_manager_control` to `no` in the section `[optimus]` of the config file. With that configuration, the GPU switch will happen the next time you restart the display manager service after calling `optimus-manager --switch`.

#### I do not use a display manager (I use startx or xinit)

First, you have to add the line `/usr/bin/optimus-manager_Xsetup` to your `.xinitrc` so that this script is executed when X starts. This *may* be necessary to set up PRIME.

Switching GPUs is also a little different in that case. First, the X server **must not be running while switching** (because the rendering kernel modules need to be unloaded), so you have do it from a TTY for example. Call `optimus-manager --switch`, then `/usr/bin/optimus-manager-setup --setup-start`, then start the X server. After you close the X server, it is recommended you also do `/usr/bin/optimus-manager-setup --setup-stop` to remove leftover configuration files.

#### When I switch to Nvidia, the built-in screen of the laptop stays black but I can still input my password or use monitors plugged to a video output

It seems that PRIME is not properly configured. Please open a GitHub issue with logs attached, and include as much details about your login manager as you can.

#### Could this tool work on distributions other than Arch or its derivatives ?

Maybe. It will not work on Ubuntu because Canonical has its own tool to deal with Optimus (`prime-select`). If you are on Ubuntu you should be using that.

It will not work on the default install of Fedora because it uses Wayland (it *might* work in Xorg mode though).

I do not know enough about the specificities of other distributions to port this tool to them. Feel free to help though :)

Credit
----------
The Intel and Nvidia logos are from the [FlatWoken project](https://github.com/alecive/FlatWoken) created by Alessandro Roncone.
