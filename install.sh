#!/usr/bin/env bash
set -e

echo "🍄 Paigaldan PlutoF 'seen' CLI tööriista (macOS / Linux)..."

# 1. Paigalda vajalikud Python paketid
python3 -m pip install -r requirements.txt

# 2. Seadista käsk ~/.local/bin kausta
mkdir -p ~/.local/bin
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
chmod +x "$CURRENT_DIR/seen.py"
ln -sf "$CURRENT_DIR/seen.py" ~/.local/bin/seen

# 3. Kontrolli keskkonnamuutujat
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo "💡 Lisa järgmine rida oma ~/.zshrc või ~/.bashrc faili:"
    echo 'export PATH="$HOME/.local/bin:$PATH"'
fi

# 4. Kontrolli .plutof_env olemasolu
if [ ! -f "$HOME/.plutof_env" ]; then
    echo "⚠️  Faili ~/.plutof_env ei leitud. Kopeerin näidise..."
    cp .env.example "$HOME/.plutof_env"
    echo "👉 Palun ava fail ~/.plutof_env ja sisesta sinna oma PlutoF kasutajatunnused!"
fi

echo "✅ Paigaldus edukalt lõpetatud! Käivita abi saamiseks: seen --help"
