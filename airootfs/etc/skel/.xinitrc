#!/usr/bin/env bash


systemctl --user import-environment DISPLAY

# Dbus fix
if [ -z "$DBUS_SESSION_BUS_ADDRESS" ]; then
    eval "$(dbus-launch --sh-syntax --exit-with-session)"
fi

# create user directories
/usr/bin/xdg-user-dirs-update

exec openbox-session 


