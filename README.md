## ⚙️ Function

Enhances the performance and power management on Nvidia Optimus Laptops, by properly selecting when to use each GPU.

The Nvidia GPU runs the whole desktop, while the Intel/AMD GPU acts as relay between the Nvidia GPU and the screen.

More info at the [wiki](https://github.com/Askannz/optimus-manager/wiki).


## 🔧 Contributing

1. Thorougly test code. See the scripts at [`package`](https://github.com/Askannz/optimus-manager/tree/master/package).
2. Open a [pull request](https://github.com/Askannz/optimus-manager/pulls).
3. Accepted in two days.


## 🔥 Issues

Try the guides on:
- [Installation](https://wiki.archlinux.org/title/NVIDIA).
- [Troubleshooting](https://wiki.archlinux.org/title/NVIDIA/Troubleshooting).
- [FAQ](https://github.com/Askannz/optimus-manager/wiki/FAQ,-common-issues,-troubleshooting).

If those don't work, or the ease of use can be improved:
1. Isolate which specific config is causing your issue.
2. Open an [issue report](https://github.com/Askannz/optimus-manager/issues).
3. When requesting further info your report may be closed. Just reopen it when done so.


## 🖥️ Supported platforms

- Graphic protocols: Xorg, Wayland without configurable options.
- Display managers : SDDM, LightDM, GDM, [custom](https://github.com/Askannz/optimus-manager/wiki/FAQ,-common-issues,-troubleshooting#my-display-manager-is-not-sddm-lightdm-nor-sddm), [none](https://github.com/Askannz/optimus-manager/wiki/FAQ,-common-issues,-troubleshooting#i-do-not-use-a-display-manager-i-use-startx-or-xinit).


## 💽 Installation

1. If you are not using the standard `linux` kernel, install the `linux-headers` package variant that matches your kernel name.

2. [Install the appropiate `nvidia` package](https://wiki.archlinux.org/title/NVIDIA#Installation).

3. Install the `optimus-manager` package. In the AUR: [`optimus-manager-git`](https://aur.archlinux.org/packages/optimus-manager-git).


## 📝 Configuration

On X11 the Nvidia GPU is used for everything by default. This provides maximum performance and ease of use at the expense of power consumption. If you want to try to optimize this, see `/etc/optimus-manager/`.

On Wayland the Nvidia GPU is used for high performance apps which use GLX or Vulkan. While the integrated GPU for no so demanding apps which use EGL, like the desktop itself and the web browser. This behavior is not configurable.


## 🔀 Modes

* `nvidia` switches to the Nvidia GPU.
* `integrated` switches to the integrated GPU, and powers the Nvidia GPU off.
* `hybrid` switches to the integrated GPU, but leaves the Nvidia GPU available for on-demand offloading. Similar to how Optimus works on Windows. More info at [the Wiki](https://github.com/Askannz/optimus-manager/wiki/Nvidia-GPU-offloading-for-%22hybrid%22-mode).

⚠️ Warning:
- In the configuration file, if `auto_logout=yes`, switching will log out and close all applications.
- Switching to and from "integrated" mode can be unstable.


## 📎 System Tray

All desktops:
* [`optimus-manager-qt`](https://github.com/Shatur95/optimus-manager-qt).

Gnome:
* [`optimus-manager-indicator`](https://extensions.gnome.org/extension/2908/optimus-manager-indicator/).
* [`optimus-manager-argos`](https://github.com/inzar98/optimus-manager-argos).


## 🎰 Boot entries

Useful if you want to have different entries for different GPU startup modes.

This only affects which GPU your desktop session starts with, nothing prior to that.

Edit your boot loader config to have the kernel parameter `optimus-manager.startup=[nvidia\integrated\hybrid]`.

Or if you are using the GRUB bootloader, you can use [`optimus-manager-grub`](https://github.com/hakasapl/optimus-manager-grub).


## 📜 Terminal

- `optimus-manager --switch [nvidia\integrated\hybrid]`
