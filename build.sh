#!/bin/bash
# build.sh — Genera WhisperDictationVP.pkg desde el código fuente
set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="$(mktemp -d)"
PKG_ROOT="$BUILD_DIR/pkg_root"
VERSION="1.3"
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

# ── Copiar Info.plist y launch_whisper.scpt ───────────────────────────────────
cp "$REPO_DIR/app/Info.plist"           "$APP_BUNDLE/"
cp "$REPO_DIR/app/launch_whisper.scpt"  "$APP_BUNDLE/Resources/"

# ── Crear ejecutable del .app (launcher shell → osascript) ───────────────────
cat > "$APP_BUNDLE/MacOS/WhisperDictationVP" << 'EOF'
#!/bin/bash
osascript "$(dirname "$0")/../Resources/launch_whisper.scpt"
EOF
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
