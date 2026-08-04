# -*- mode: python ; coding: utf-8 -*-
# Spec de PyInstaller — genera "Whisper Dictation VP.app" con Python embebido.
# Uso: pyinstaller --noconfirm app/whisper_dictation_vp.spec (desde la raíz del repo)

import os

APP_VERSION = "3.2.0"
repo_dir = os.path.dirname(os.path.abspath(SPECPATH))

a = Analysis(
    [os.path.join(repo_dir, "src", "whisper_dictation_vp.py")],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        "groq", "openai", "deepgram", "assemblyai",
        "dotenv", "rumps", "pynput", "sounddevice",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "PIL", "PyQt5", "PySide2"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="WhisperDictationVP",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="WhisperDictationVP",
)

app = BUNDLE(
    coll,
    name="Whisper Dictation VP.app",
    icon=os.path.join(repo_dir, "app", "AppIcon.icns"),
    bundle_identifier="com.vasyl.whisper-dictation-vp",
    version=APP_VERSION,
    info_plist={
        "CFBundleDisplayName": "Whisper Dictation VP",
        "CFBundleName": "Whisper Dictation VP",
        "CFBundleShortVersionString": APP_VERSION,
        "CFBundleVersion": APP_VERSION,
        "LSUIElement": True,
        "NSMicrophoneUsageDescription":
            "Whisper Dictation VP necesita el micrófono para grabar tu voz.",
        "NSAccessibilityUsageDescription":
            "Whisper Dictation VP necesita Accesibilidad para detectar la "
            "tecla de dictado y pegar el texto.",
        "NSAppleEventsUsageDescription":
            "Whisper Dictation VP necesita enviar eventos a System Events "
            "para pegar el texto transcrito.",
        "NSHumanReadableCopyright":
            "© Vasyl Pavlyuchok & Claude — Licencia MIT",
    },
)
