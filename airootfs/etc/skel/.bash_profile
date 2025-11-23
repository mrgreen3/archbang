# ArchBANG login shell configuration
# Determines whether to start Sway (Wayland) or Openbox (X11)

. $HOME/.bashrc

# Check kernel cmdline for sway=1 parameter
if grep -q "sway=1" /proc/cmdline 2>/dev/null; then
    # Start Sway (Wayland)
    if [[ -z $WAYLAND_DISPLAY && -z $DISPLAY ]]; then
        export XDG_CURRENT_DESKTOP=sway
        export XDG_SESSION_TYPE=wayland
        exec sway
    fi
else
    # Start Openbox (X11) - default
    if [[ -z $DISPLAY && $XDG_VTNR -eq 1 ]]; then
        export XDG_CURRENT_DESKTOP=openbox
        export XDG_SESSION_TYPE=x11
        exec startx
    fi
fi



