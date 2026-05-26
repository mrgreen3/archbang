# add vim as default editor
export EDITOR=vim
export TERMINAL=foot
export BROWSER=firefox

# Add scripts path safely
if [[ ":$PATH:" != *":$HOME/Scripts:"* ]]; then
    export PATH="$PATH:$HOME/Scripts"
fi

alias ls='ls --color=auto'

# Package sizes
alias pkg_size="expac -H M '%m\t%n' | sort -h"

# fzf shell integration
eval "$(fzf --bash)"

# fzf defaults
export FZF_DEFAULT_OPTS="--height 40% --reverse --border"
export FZF_CTRL_R_OPTS="--border"

# Enhanced history function
fh() {
  local cmd
  cmd=$(history | awk '{$1=""; print substr($0,2)}' | tac | sort -u | fzf \
    --height 40% \
    --reverse \
    --border \
    --prompt="History ❯ " \
    --preview 'echo {}' \
    --preview-window=up:1:wrap \
  )
  if [ -n "$cmd" ]; then
    echo -e "\n> $cmd"
    read -p "Run? [y/N/c(opy)] " ans
    if [[ "$ans" =~ ^[Yy]$ ]]; then
      history -s "$cmd"
      eval "$cmd"
    elif [[ "$ans" =~ ^[Cc]$ ]]; then
      echo "$cmd" | wl-copy && echo "Copied to clipboard."
    fi
  fi
}

# Bindings for fh
bind -x '"\C-h": fh'

