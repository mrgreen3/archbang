#!/usr/bin/env bash
# ArchBang profile

iso_name="archbang"
iso_label="ARCHBANG_RC_$(date +%d%m%y)"
iso_publisher="ArchBang <https://www.archbang.org>"
iso_application="ArchBang Live Iso (RC)"
# DDMMYY dev build date with an rc suffix for release-candidate builds; swap
# for semantic versioning (e.g. "1.0.0") on final release
iso_version="$(date +%d%m%y)-rc"
install_dir="arch"
buildmodes=("iso")
bootmodes=('bios.syslinux'
           'uefi.systemd-boot')
arch="x86_64"
pacman_conf="pacman.conf"
airootfs_image_type="squashfs"
airootfs_image_tool_options=('-comp' 'xz' '-Xbcj' 'x86' '-b' '1M' '-Xdict-size' '1M')
bootstrap_tarball_compression=('zstd' '-c' '-T0' '--auto-threads=logical' '--long' '-19')
file_permissions=(
  ["/etc/shadow"]="0:0:400"
  ["/root"]="0:0:750"
  ["/root/.gnupg"]="0:0:700"
  ["/etc/skel/Scripts/"]="0:0:755"
  ["/etc/sudoers.d/archbang-gtkgreet-theme"]="0:0:440"
)
#bootstrap_tarball_compression=(gzip -cn9)
