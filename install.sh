#!/usr/bin/env bash
set -e

echo "Paigaldan PlutoFF ('seen') CLI tööriista..."

# 1. Python sõltuvused
python3 -m pip install -q -r requirements.txt

# 2. Seadista käsk ~/.local/bin kausta
mkdir -p ~/.local/bin
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
chmod +x "$CURRENT_DIR/seen.py"
ln -sf "$CURRENT_DIR/seen.py" ~/.local/bin/seen
ln -sf "$CURRENT_DIR/seen.py" ~/.local/bin/plutoff

# 3. Seadista Tab autocompletion (Zsh ja Bash)
if [ -n "$ZSH_VERSION" ] || [ "$SHELL" = "/bin/zsh" ] || [ "$SHELL" = "/usr/bin/zsh" ]; then
    mkdir -p ~/.zfunc
    cp "$CURRENT_DIR/completions/seen.zsh" ~/.zfunc/_seen
    cp "$CURRENT_DIR/completions/seen.zsh" ~/.zfunc/_plutoff
    
    if ! grep -q "fpath=(~/.zfunc" ~/.zshrc 2>/dev/null; then
        echo 'fpath=(~/.zfunc $fpath)' >> ~/.zshrc
        echo 'autoload -Uz compinit && compinit' >> ~/.zshrc
    fi
elif [ -n "$BASH_VERSION" ] || [ "$SHELL" = "/bin/bash" ]; then
    mkdir -p ~/.bash_completion.d
    cp "$CURRENT_DIR/completions/seen.bash" ~/.bash_completion.d/seen
    if ! grep -q "seen.bash" ~/.bashrc 2>/dev/null; then
        echo 'source ~/.bash_completion.d/seen' >> ~/.bashrc
    fi
fi

# 4. Kontrolli .plutof_env
if [ ! -f "$HOME/.plutof_env" ]; then
    cp .env.example "$HOME/.plutof_env"
    echo "Fail ~/.plutof_env loodud. Sisesta sinna oma PlutoF volitused."
fi

echo "Paigaldus edukalt lõpetatud! Käsk 'seen' ja Tab-täiendus on valmis."
