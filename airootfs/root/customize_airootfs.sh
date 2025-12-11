#!/usr/bin/env bash
# Configure live iso
# 
set -e -u -x
shopt -s extglob

# Set locales
sed -i 's/#\(en_US\.UTF-8\)/\1/' /etc/locale.gen
locale-gen

# Allow Parallel Downloads in pacman
sed -i "s/^#Parallel/Parallel/g" /etc/pacman.conf 

# Un-comment mirrorlist to allow pacman to work live....
sed -i "s/#Server/Server/g" /etc/pacman.d/mirrorlist

# Sudo to allow no password
sed -i 's/# %wheel ALL=(ALL:ALL) NOPASSWD: ALL/%wheel ALL=(ALL:ALL) NOPASSWD: ALL/g' /etc/sudoers
chown -c root:root /etc/sudoers
chmod -c 0440 /etc/sudoers

# Configure gparted to run with sudo for elevated permissions
#sed -i 's|^Exec=/usr/bin/gparted|Exec=sudo /usr/bin/gparted|' /usr/share/applications/gparted.desktop

# Hide gparted from Openbox menu and rofi
sed -i '/^Categories=/a Hidden=true' /usr/share/applications/gparted.desktop

# Hostname
echo "waybang" > /etc/hostname

# Vconsole
echo "KEYMAP=us" > /etc/vconsole.conf
echo "FONT=Lat2-Terminus16" >> /etc/vconsole.conf

# Locale
echo "LANG=en_US.UTF-8" > /etc/locale.conf
echo "LC_COLLATE=C" >> /etc/locale.conf

# Set clock to UTC
hwclock --systohc --utc

# Timezone
ln -sf /usr/share/zoneinfo/Canada/Montreal /etc/localtime

# Target directory where systemd user service symlinks will be created
TARGET_DIR="/etc/skel/.config/systemd/user/default.target.wants"

# Source directory for official systemd user service files
UNIT_SRC="/usr/lib/systemd/user"

# List of user services to be auto-enabled at login
SERVICES=(
  "wireplumber.service"
  "pipewire.service"
  "pipewire-pulse.service"
)

# Create target directory if it doesn't exist
mkdir -p "$TARGET_DIR"

# Loop through the list and create symlinks for each service
for service in "${SERVICES[@]}"; do
  ln -sf "$UNIT_SRC/$service" "$TARGET_DIR/$service"
done

# Add live user
useradd -m -p "" -G "wheel" -s /bin/bash -g users wblive 
chown wblive /home/wblive

# Start required systemd services
systemctl enable {pacman-init,NetworkManager}.service -f

# Set graphical target
systemctl set-default graphical.target
