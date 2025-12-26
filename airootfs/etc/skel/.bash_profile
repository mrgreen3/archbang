# ArchBANG login shell configuration
# Starts labwc (Wayland compositor)

. $HOME/.bashrc

# Start labwc on TTY1
if [[ -z $WAYLAND_DISPLAY && -z $DISPLAY && $XDG_VTNR -eq 1 ]]; then
    export XDG_CURRENT_DESKTOP=labwc
    export XDG_SESSION_TYPE=wayland
    exec labwc
fi



