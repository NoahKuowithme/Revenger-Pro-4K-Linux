pkgname=revenger-pro-4k
pkgver=2.0.0
pkgrel=1
pkgdesc='Linux companion app for the COUGAR Revenger Pro 4K mouse'
arch=('any')
url='https://github.com/NoahKuowithme/Revenger-Pro-4K-Linux'
license=('GPL-3.0-or-later')
depends=('python' 'python-gobject' 'gtk4' 'libadwaita' 'systemd')
install='revenger-pro-4k.install'
source=()
sha256sums=()

package() {
  cd "$startdir"
  install -d "$pkgdir/usr/lib/revenger-pro-4k/revengerctl" \
    "$pkgdir/usr/bin" \
    "$pkgdir/usr/share/applications" \
    "$pkgdir/usr/share/icons/hicolor/scalable/apps" \
    "$pkgdir/usr/share/doc/revenger-pro-4k" \
    "$pkgdir/usr/share/licenses/revenger-pro-4k" \
    "$pkgdir/usr/lib/udev/rules.d" \
    "$pkgdir/usr/lib/revenger-pro-4k/udev"
  cp -a revengerctl/. "$pkgdir/usr/lib/revenger-pro-4k/revengerctl/"
  find "$pkgdir/usr/lib/revenger-pro-4k" -type d -name __pycache__ -prune -exec rm -rf {} +
  find "$pkgdir/usr/lib/revenger-pro-4k" -type f -name '*.py[co]' -delete
  install -m 755 revenger-pro-4k revengerctl-cli \
    "$pkgdir/usr/lib/revenger-pro-4k/"
  install -m 755 packaging/bin/revenger-pro-4k packaging/bin/revengerctl-cli \
    "$pkgdir/usr/bin/"
  install -m 644 revenger-pro-4k.desktop \
    "$pkgdir/usr/share/applications/io.github.noahkuowithme.Revenger-Pro-4K-Linux.desktop"
  install -m 644 icons/io.github.noahkuowithme.Revenger-Pro-4K-Linux.svg \
    "$pkgdir/usr/share/icons/hicolor/scalable/apps/io.github.noahkuowithme.Revenger-Pro-4K-Linux.svg"
  install -m 644 udev/72-revenger-pro-4k.rules \
    "$pkgdir/usr/lib/udev/rules.d/72-revenger-pro-4k.rules"
  install -m 644 udev/72-revenger-pro-4k.rules \
    "$pkgdir/usr/lib/revenger-pro-4k/udev/72-revenger-pro-4k.rules"
  install -m 644 README.md INSTRUCTIONS.md \
    "$pkgdir/usr/share/doc/revenger-pro-4k/"
  install -m 644 LICENSE "$pkgdir/usr/share/licenses/revenger-pro-4k/"
}
