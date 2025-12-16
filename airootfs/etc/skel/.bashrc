# add vim as default editor
export EDITOR=vim
export TERMINAL=foot
export BROWSER=firefox

# Add scripts path safely
if [[ ":$PATH:" != *":$HOME/AB_Scripts:"* ]]; then
    export PATH="$PATH:$HOME/AB_Scripts"
fi


alias ls='ls --color=auto'

# Package sizes
alias pkg_size="expac -H M '%m\t%n' | sort -h"

greenfile(){ curl -F "file=@$1" https://0x0.st; }


