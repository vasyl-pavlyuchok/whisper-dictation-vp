tell application "Terminal"
    set w to do script "python3 /usr/local/lib/whisper_dictation_vp/whisper_dictation_vp.py"
    delay 1
    set miniaturized of window 1 to true
end tell
