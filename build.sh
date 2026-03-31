#!/bin/bash
# build.sh — Genera WhisperDictationVP.pkg desde el código fuente
set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="$(mktemp -d)"
PKG_ROOT="$BUILD_DIR/pkg_root"
VERSION="2.4"
OUTPUT="$HOME/Desktop/WhisperDictationVP.pkg"

echo "==> Preparando estructura..."

# ── Crear árbol de directorios ────────────────────────────────────────────────
APP_BUNDLE="$PKG_ROOT/Applications/Whisper Dictation VP.app/Contents"
mkdir -p "$APP_BUNDLE/MacOS"
mkdir -p "$APP_BUNDLE/Resources"
mkdir -p "$PKG_ROOT/usr/local/lib/whisper_dictation_vp"

# ── Copiar script Python ──────────────────────────────────────────────────────
cp "$REPO_DIR/src/whisper_dictation_vp.py" \
   "$PKG_ROOT/usr/local/lib/whisper_dictation_vp/"

# ── Copiar Info.plist ─────────────────────────────────────────────────────────
cp "$REPO_DIR/app/Info.plist" "$APP_BUNDLE/"

# ── Crear ejecutable del .app ─────────────────────────────────────────────────
# Lanza Python dentro de Terminal (minimizada) para heredar su permiso
# de Accesibilidad. Incluye detección de Python y protección anti-doble-instancia.
cat > "$APP_BUNDLE/MacOS/WhisperDictationVP" << 'LAUNCHER'
#!/bin/bash
if pgrep -f "whisper_dictation_vp.py" > /dev/null 2>&1; then
    exit 0
fi
PYTHON=""
for minor in $(seq 11 20); do
    candidate="/Library/Frameworks/Python.framework/Versions/3.${minor}/bin/python3"
    [ -f "$candidate" ] && PYTHON="$candidate" && break
done
if [ -z "$PYTHON" ]; then
    for candidate in \
        /opt/homebrew/opt/python@3.13/bin/python3 \
        /opt/homebrew/opt/python@3.12/bin/python3 \
        /opt/homebrew/opt/python@3.11/bin/python3 \
        /opt/homebrew/bin/python3 \
        /usr/local/opt/python@3.13/bin/python3 \
        /usr/local/opt/python@3.12/bin/python3 \
        /usr/local/opt/python@3.11/bin/python3 \
        /usr/local/bin/python3; do
        [ -f "$candidate" ] && PYTHON="$candidate" && break
    done
fi
if [ -z "$PYTHON" ]; then
    osascript -e 'tell app "System Events" to display dialog "Python no encontrado. Reinstala Whisper Dictation VP." buttons {"OK"} default button 1'
    exit 1
fi
osascript << APPLESCRIPT
tell application "Terminal"
    set w to do script "$PYTHON /usr/local/lib/whisper_dictation_vp/whisper_dictation_vp.py"
    delay 1.5
    set miniaturized of window 1 to true
end tell
APPLESCRIPT
LAUNCHER
chmod +x "$APP_BUNDLE/MacOS/WhisperDictationVP"

# ── Icono (opcional) ──────────────────────────────────────────────────────────
ICNS="$REPO_DIR/app/AppIcon.icns"
if [ -f "$ICNS" ]; then
  cp "$ICNS" "$APP_BUNDLE/Resources/AppIcon.icns"
  echo "    Icono incluido."
else
  echo "    [aviso] app/AppIcon.icns no encontrado — el .app no tendrá icono personalizado."
fi

# ── Imagen de fondo del instalador (opcional) ─────────────────────────────────
BG="$REPO_DIR/installer/resources/background.png"
if [ ! -f "$BG" ]; then
  echo "    [aviso] installer/resources/background.png no encontrado — se usará fondo por defecto."
fi

echo "==> Generando componente .pkg..."
pkgbuild \
  --root "$PKG_ROOT" \
  --scripts "$REPO_DIR/installer/scripts" \
  --identifier "com.vasyl.whisper-dictation-vp" \
  --version "$VERSION" \
  --install-location / \
  "$BUILD_DIR/WhisperDictationVP_component.pkg"

echo "==> Generando instalador final..."
productbuild \
  --distribution "$REPO_DIR/installer/distribution.xml" \
  --resources "$REPO_DIR/installer/resources" \
  --package-path "$BUILD_DIR" \
  "$OUTPUT"

rm -rf "$BUILD_DIR"

echo ""
echo "✓ Instalador generado: $OUTPUT"
