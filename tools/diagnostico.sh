#!/bin/bash
# Diagnóstico de Whisper Dictation VP (macOS).
#
# Responde a la pregunta «¿por qué no responde la tecla?» sin adivinar.
# No instala nada, no modifica nada, no necesita sudo.
#
#   bash tools/diagnostico.sh
#
# Pégale la salida entera a Claude si algo no cuadra.

APP="/Applications/Whisper Dictation VP.app"
BUNDLE_ID="com.vasyl.whisper-dictation-vp"
LOG="$HOME/Library/Logs/WhisperDictationVP.log"
CONFIG="$HOME/.whisper_dictation_vp.json"

ok()   { printf '  \033[32m✓\033[0m %s\n' "$1"; }
bad()  { printf '  \033[31m✗\033[0m %s\n' "$1"; }
warn() { printf '  \033[33m!\033[0m %s\n' "$1"; }
head_() { printf '\n\033[1m── %s\033[0m\n' "$1"; }

printf '\033[1mWhisper Dictation VP — diagnóstico\033[0m\n'
printf 'macOS %s · %s · %s\n' "$(sw_vers -productVersion)" "$(uname -m)" "$(date '+%Y-%m-%d %H:%M')"

# ── 1. ¿Está instalada y qué build es? ───────────────────────────────────────
head_ "1. Instalación"
if [ -d "$APP" ]; then
  VER=$(defaults read "$APP/Contents/Info.plist" CFBundleShortVersionString 2>/dev/null)
  ok "Instalada — versión $VER"

  # La clave que hace que macOS enseñe el diálogo de Monitorización de entrada.
  # Si falta, el build es anterior al arreglo y NUNCA pedirá ese permiso.
  if defaults read "$APP/Contents/Info.plist" NSInputMonitoringUsageDescription >/dev/null 2>&1; then
    ok "Info.plist declara NSInputMonitoringUsageDescription"
  else
    bad "Info.plist NO declara NSInputMonitoringUsageDescription"
    echo "      → build anterior al arreglo: la app no puede pedir"
    echo "        «Monitorización de entrada» y no aparecerá en esa lista."
    echo "        ESTA ES LA CAUSA MÁS PROBABLE. Instala v3.5.2 o superior."
  fi

  if codesign -dv "$APP" 2>&1 | grep -q adhoc; then
    warn "Firma ad-hoc — los permisos se pierden en cada actualización (esperado)"
  else
    ok "Firma estable — los permisos sobreviven a las actualizaciones"
  fi
else
  bad "No está instalada en /Applications"
fi

# ── 2. ¿Está corriendo? ──────────────────────────────────────────────────────
head_ "2. Proceso"
if pgrep -f "Whisper Dictation VP.app/Contents/MacOS" >/dev/null 2>&1; then
  ok "En ejecución (PID $(pgrep -f 'Whisper Dictation VP.app/Contents/MacOS' | tr '\n' ' '))"
else
  bad "No está en ejecución — ábrela antes de seguir:  open -a 'Whisper Dictation VP'"
fi

# ── 3. Permisos TCC ──────────────────────────────────────────────────────────
# Se consulta la base de datos de TCC. Si el terminal no tiene Acceso Total al
# Disco fallará: en ese caso manda la sección 4 (el log de la app), que es la
# fuente fiable porque la escribe el propio proceso.
head_ "3. Permisos (TCC)"
tcc_query() { # $1=servicio  $2=etiqueta
  local out
  out=$(sqlite3 "/Library/Application Support/com.apple.TCC/TCC.db" \
        "select auth_value from access where service='$1' and client='$BUNDLE_ID';" 2>/dev/null)
  case "$out" in
    2)  ok   "$2: CONCEDIDO" ;;
    0)  bad  "$2: DENEGADO" ;;
    "") bad  "$2: NO APARECE EN LA LISTA" ;;
    *)  warn "$2: valor $out" ;;
  esac
}
if sqlite3 "/Library/Application Support/com.apple.TCC/TCC.db" "select 1;" >/dev/null 2>&1; then
  tcc_query kTCCServiceListenEvent   "Monitorización de entrada (LEER la tecla)"
  tcc_query kTCCServiceAccessibility "Accesibilidad (PEGAR el texto)"
else
  warn "Sin acceso a TCC.db (el terminal necesita Acceso Total al Disco)"
  echo "      → usa la sección 4, o míralo a mano en:"
  echo "        Ajustes del Sistema → Privacidad y seguridad →"
  echo "        Monitorización de entrada  /  Accesibilidad"
fi

# ── 4. Lo que dice la propia app ─────────────────────────────────────────────
head_ "4. Log de la app"
if [ -f "$LOG" ]; then
  echo "  $LOG"
  PERM=$(grep -a "permisos —" "$LOG" | tail -1)
  [ -n "$PERM" ] && printf '  \033[1m%s\033[0m\n' "$PERM"
  echo "  ── últimas 20 líneas ──"
  tail -20 "$LOG" | sed 's/^/  /'
  echo "  ── eventos de hotkey registrados: $(grep -ac 'hotkey ev' "$LOG" 2>/dev/null || echo 0) ──"
  if [ "$(grep -ac 'hotkey ev' "$LOG" 2>/dev/null || echo 0)" = "0" ]; then
    bad "CERO eventos de teclado recibidos"
    echo "      → la app no está viendo el teclado. Es el síntoma exacto de"
    echo "        «Monitorización de entrada» sin conceder."
  fi
else
  bad "No hay log en $LOG (¿la app llegó a arrancar?)"
fi

# ── 5. Configuración ─────────────────────────────────────────────────────────
head_ "5. Configuración"
if [ -f "$CONFIG" ]; then
  /usr/bin/python3 - "$CONFIG" <<'PY'
import json, sys
c = json.load(open(sys.argv[1]))
print(f"  tecla={c.get('hotkey')}  idioma={c.get('language')}  "
      f"proveedor={c.get('active_provider') or '(ninguno)'}  "
      f"apis={list(c.get('providers', {}))}  "
      f"historial={len(c.get('history', []))}")
PY
else
  warn "Sin config todavía ($CONFIG)"
fi

head_ "Siguiente paso"
cat <<'EOF'
  Si arriba ves «NO APARECE EN LA LISTA» o «CERO eventos de teclado»,
  el problema es el permiso de Monitorización de entrada.

  Para ver la app funcionando en vivo desde el código (sin instalar):
      pip3 install -r requirements-dev.txt   # o usa .buildenv
      python3 src/whisper_dictation_vp.py
  Al ejecutarse desde el terminal, el permiso lo aporta el TERMINAL:
  concédeselo a él y podrás probar el dictado al momento.
EOF
