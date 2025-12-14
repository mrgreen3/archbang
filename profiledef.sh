#!/usr/bin/env bash
#
# Profile modified for WayBang
# by Mr Green [mrgreen@archbang.org]

iso_name="waybang-beta"
iso_label="WAYBANG_$(date +%d%m)"
iso_publisher="WayBANG <https://www.archbang.org>"
iso_application="WayBang Live/Rescue Iso (Beta)"
iso_version="$(date +%d%m)"
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
  ["/etc/skel/AB_Scripts/"]="0:0:755"
  ["/etc/skel/.config/waybar/scripts/"]="0:0:755"
  ["/root/mvuser"]="0:0:755"
)
#bootstrap_tarball_compression=(gzip -cn9)
