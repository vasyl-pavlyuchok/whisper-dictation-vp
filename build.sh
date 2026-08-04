#!/bin/bash
# build.sh — Genera WhisperDictationVP.pkg desde el código fuente.
# v3.0: la app se empaqueta con PyInstaller (Python embebido) — el usuario
# final NO necesita tener Python instalado ni se abre ninguna Terminal.
set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="$(mktemp -d)"
PKG_ROOT="$BUILD_DIR/pkg_root"
VERSION="3.6.1"
ARCH="$(uname -m)"
case "$ARCH" in
  arm64)  ARCH_LABEL="AppleSilicon" ;;
  x86_64) ARCH_LABEL="Intel" ;;
  *)      ARCH_LABEL="$ARCH" ;;
esac
OUTPUT_DIR="${OUTPUT_DIR:-$HOME/Desktop}"
OUTPUT="$OUTPUT_DIR/WhisperDictationVP-${ARCH_LABEL}.pkg"
VENV="$REPO_DIR/.buildenv"

# ── 1. Localizar Python 3.11+ para el build ───────────────────────────────────
PYTHON=""
for candidate in \
    /Library/Frameworks/Python.framework/Versions/3.13/bin/python3 \
    /Library/Frameworks/Python.framework/Versions/3.12/bin/python3 \
    /Library/Frameworks/Python.framework/Versions/3.11/bin/python3 \
    /opt/homebrew/bin/python3 \
    /usr/local/bin/python3 \
    "$(command -v python3)"; do
  if [ -f "$candidate" ]; then
    if "$candidate" -c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)" 2>/dev/null; then
      PYTHON="$candidate" && break
    fi
  fi
done
[ -z "$PYTHON" ] && { echo "✗ Se necesita Python 3.11+ para compilar."; exit 1; }
echo "==> Python de build: $PYTHON"

# ── 2. Entorno virtual de build con dependencias + PyInstaller ────────────────
if [ ! -d "$VENV" ]; then
  echo "==> Creando entorno de build en .buildenv..."
  "$PYTHON" -m venv "$VENV"
fi
echo "==> Instalando dependencias..."
"$VENV/bin/pip" install --quiet --upgrade pip
"$VENV/bin/pip" install --quiet pyinstaller rumps pynput sounddevice numpy \
  python-dotenv groq openai deepgram-sdk assemblyai \
  pyobjc-framework-Cocoa pyobjc-framework-ApplicationServices

# ── 3. Compilar el .app con PyInstaller ───────────────────────────────────────
echo "==> Compilando Whisper Dictation VP.app (PyInstaller)..."
"$VENV/bin/pyinstaller" --noconfirm \
  --distpath "$BUILD_DIR/dist" \
  --workpath "$BUILD_DIR/work" \
  "$REPO_DIR/app/whisper_dictation_vp.spec"

APP_SRC="$BUILD_DIR/dist/Whisper Dictation VP.app"
[ -d "$APP_SRC" ] || { echo "✗ PyInstaller no generó el .app"; exit 1; }

# ── 3b. Firma estable (si existe el certificado local) ────────────────────────
# Con una identidad de firma constante, macOS conserva el permiso de
# Accesibilidad entre versiones y no hay que reconcederlo en cada update.
SIGN_ID="Whisper Dictation VP Signing"
if security find-identity -p codesigning 2>/dev/null | grep -q "$SIGN_ID"; then
  echo "==> Firmando con identidad estable: $SIGN_ID"
  codesign --force --deep --sign "$SIGN_ID" "$APP_SRC" 2>/dev/null || \
    echo "    [aviso] fallo al firmar — se mantiene la firma ad-hoc"
else
  echo "    [aviso] sin certificado local — firma ad-hoc (el permiso de"
  echo "    Accesibilidad habrá que reconcederlo tras cada actualización)"
fi

# ── 4. Montar la raíz del paquete ─────────────────────────────────────────────
mkdir -p "$PKG_ROOT/Applications"
cp -R "$APP_SRC" "$PKG_ROOT/Applications/"

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
