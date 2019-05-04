# Maintainer: Robin Lange <robin dot langenc at gmail dot com>
# Contributor: Robin Lange <robin dot langenc at gmail dot com>
pkgname=optimus-manager-git
pkgver=1.0
pkgrel=1
pkgdesc="Management utility to handle GPU switching for Optimus laptops (Git version)"
arch=('any')
url="https://github.com/Askannz/optimus-manager"
license=('MIT')
conflicts=("optimus-manager")
provides=("optimus-manager")
depends=('python' 'python-setuptools' 'mesa-demos' 'xorg-xrandr')
optdepends=('bbswitch: alternative power switching method'
            'xf86-video-intel: provides the Xorg intel driver')
makedepends=('python-setuptools' 'git')
backup=('etc/optimus-manager/xorg-intel.conf'
        'etc/optimus-manager/xorg-nvidia.conf'
        'etc/optimus-manager/xsetup-intel.sh'
        'etc/optimus-manager/xsetup-nvidia.sh'
        'var/lib/optimus-manager/startup_mode'
        'var/lib/optimus-manager/requested_mode')
source=("git+https://github.com/Askannz/optimus-manager.git#branch=master")
sha256sums=('SKIP')

pkgver() {
  cd "${srcdir}/optimus-manager/"
  printf "r%s.%s" "$(git rev-list --count HEAD)" "$(git rev-parse --short HEAD)"
}
 
build() {
 
  cd "${srcdir}/optimus-manager/"
  python setup.py build
 
}
 
 
package() {

  install="optimus-manager.install"
 
  cd "${srcdir}/optimus-manager/"
 
  install -Dm644 LICENSE "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
  install -Dm644 modules/optimus-manager.conf "$pkgdir/usr/lib/modprobe.d/optimus-manager.conf"
  install -Dm644 systemd/optimus-manager.service "$pkgdir/usr/lib/systemd/system/optimus-manager.service"
  install -Dm644 optimus-manager.conf "$pkgdir/usr/share/optimus-manager.conf"
  
  install -Dm644 var/startup_mode "$pkgdir/var/lib/optimus-manager/startup_mode"
  install -Dm644 var/requested_mode "$pkgdir/var/lib/optimus-manager/requested_mode"
  
  install -Dm755 scripts/prime-switch-boot "$pkgdir/usr/bin/prime-switch-boot"
  install -Dm755 scripts/prime-switch "$pkgdir/usr/bin/prime-switch"
  install -Dm755 scripts/prime-offload "$pkgdir/usr/bin/prime-offload"
  
  install -Dm644 login_managers/sddm/20-optimus-manager.conf "$pkgdir/etc/sddm.conf.d/20-optimus-manager.conf"
  install -Dm644 login_managers/lightdm/20-optimus-manager.conf  "$pkgdir/etc/lightdm/lightdm.conf.d/20-optimus-manager.conf"
  
  install -Dm644 config/xorg-intel.conf "$pkgdir/etc/optimus-manager/xorg-intel.conf"
  install -Dm644 config/xorg-nvidia.conf "$pkgdir/etc/optimus-manager/xorg-nvidia.conf"
  
  install -Dm755 config/xsetup-intel.sh "$pkgdir/etc/optimus-manager/xsetup-intel.sh"
  install -Dm755 config/xsetup-nvidia.sh "$pkgdir/etc/optimus-manager/xsetup-nvidia.sh"
 
  python setup.py install --root="$pkgdir/" --optimize=1 --skip-build
 
} 
