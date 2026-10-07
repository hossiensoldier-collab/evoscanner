#!/data/data/com.termux/files/usr/bin/bash
set -e
cd "$(dirname "$0")"
echo "=== Setup ==="
command -v python >/dev/null && echo "✓ python: $(python --version 2>&1)"
command -v ssh >/dev/null || { echo "installing openssh..."; pkg install openssh -y; }
command -v ssh >/dev/null && echo "✓ ssh: $(ssh -V 2>&1)"
command -v curl >/dev/null && echo "✓ curl: $(curl --version | head -1)"
mkdir -p ~/.ssh; chmod 700 ~/.ssh
chmod +x *.py *.sh 2>/dev/null || true
for f in server.py tunnel.py menu.py; do
    python -c "import py_compile; py_compile.compile('$f', doraise=True)" \
        && echo "✓ $f" || echo "✗ $f"
done
echo
echo "اجرا: python menu.py"
