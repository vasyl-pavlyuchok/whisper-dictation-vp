[🇪🇸 Español](README.md) | 🇬🇧 **English**

# 🎙 Whisper Dictation VP

[![Release](https://img.shields.io/github/v/release/vasyl-pavlyuchok/whisper-dictation-vp?label=version&color=84cc16)](../../releases/latest)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![macOS](https://img.shields.io/badge/macOS-Intel%20%7C%20Apple%20Silicon-black?logo=apple)](../../releases/latest)
[![Windows](https://img.shields.io/badge/Windows-10%20%7C%2011%20(beta)-0078d4?logo=windows)](../../releases/latest)

**Dictate instead of typing, into any app.** Double-tap a key, speak, single tap — and the text appears right where you were writing. Free and open source: it runs on **Groq's free API** (whisper-large-v3) — months of daily use without ever hitting a limit. No subscription: what a Wispr Flow costs, you save every month.

🌐 **Automatic language detection** — just speak and Whisper recognizes the language on its own:

🇪🇸 🇬🇧 🇺🇦 🇫🇷 🇩🇪 🇮🇹 🇵🇹 🇨🇳 🇷🇺 🇸🇦 🇮🇳 🇯🇵 🇰🇷 🇹🇷 🇵🇱 🇳🇱

Designed by **Vasyl Pavlyuchok** & **Claude** — v3.2.0

---

## Why it exists

Dictating instead of typing completely changes how fast you work. Apps like Wispr Flow proved how powerful this way of interacting is; this app was born from that idea, but **free and under your control**: your API key, no monthly fee. It auto-detects the language, has a **personal dictionary** for your vocabulary (those names and terms that always come out wrong) and an **AI Format** mode that cleans up filler words and punctuation as you speak. The first version was built with Claude in one afternoon; today it's a fully native app for macOS and Windows, validated with daily use, and shared so more people can access tools like this without paying a subscription.

---

## Downloads

Go to the [**Releases**](../../releases/latest) page and download the version for your system:

| System | File |
|--------|------|
| **macOS Apple Silicon** (M1/M2/M3/M4) | `WhisperDictationVP-AppleSilicon.pkg` |
| **macOS Intel** | `WhisperDictationVP-Intel.pkg` |
| **Windows 10/11** (beta) | `WhisperDictationVP-Windows.zip` |

> **v3.0+** — The macOS app is **100% native**: Python is embedded, so you **don't need Python installed and no Terminal window ever opens**. Just install and dictate.

---

## How it works

1. **Double-tap** the hotkey (right Option by default) to start recording
2. Speak freely — no need to hold any key
3. **Single tap** to stop
4. The text appears pasted right where you were writing

The menu bar icon shows the state: 🎙 ready · ⭕ recording · ⏳ transcribing

---

## Transcription providers

You only need **one** API key to get started. **Recommended: Groq** — free, blazing fast, and it runs whisper-large-v3, by far the best-performing model.

| Provider | Model | Price | Get your key at |
|----------|-------|-------|-----------------|
| **Groq** ⭐ recommended | whisper-large-v3 | **Free** | [console.groq.com](https://console.groq.com) |
| OpenAI | whisper-1 | Paid | [platform.openai.com](https://platform.openai.com) |
| Deepgram | nova-2 | Free tier | [console.deepgram.com](https://console.deepgram.com) |
| AssemblyAI | universal | Free tier | [app.assemblyai.com](https://app.assemblyai.com) |

**Getting your Groq key (1 minute):**
1. Go to [console.groq.com](https://console.groq.com) and create a free account
2. Open **API Keys** → **Create API Key**
3. Copy the key (starts with `gsk_...`)
4. On first launch of Whisper Dictation VP, pick **Groq** and paste the key

---

## macOS installation

1. Download the `.pkg` for your architecture from [Releases](../../releases/latest)
2. Double-click to run the installer *(if macOS warns about an unidentified developer: right-click → Open)*
3. When it finishes, the app opens by itself and macOS asks for permissions
4. On first launch, the app asks for your provider and API key

### Required permissions

**Accessibility (required)** — to detect the dictation key and paste the text:

1. macOS shows the prompt automatically when the app opens. If it doesn't:
2. **System Settings → Privacy & Security → Accessibility**
3. Enable **Whisper Dictation VP**
4. Quit the app (🎙 icon → Salir) and open it again

> Accessibility must be re-granted after each update because the app's signature changes; it's one click per version.

**Microphone** — macOS asks automatically the first time you record.

---

## Windows installation (beta)

1. Download `WhisperDictationVP-Windows.zip` from [Releases](../../releases/latest)
2. Unzip and run `WhisperDictationVP.exe` *(if SmartScreen warns: More info → Run anyway)*
3. The icon appears in the system tray; on first launch it asks for your API key
4. Double-tap **right Alt** to record, single tap to stop

---

## Features

- **Double-tap to record** — start without holding any key; single tap to stop
- **Native app** — embedded Python, no external dependencies, no Terminal windows
- **✨ AI Format** — a free LLM (via Groq) removes filler words and fixes punctuation and casing before pasting
- **📖 Personal dictionary** — add proper nouns and technical terms Whisper tends to get wrong; applied both to transcription and AI formatting
- **Automatic language detection** — speak any language and Whisper detects it; or pin one of 16 languages
- **Interactive history** — click any of the last 10 transcriptions to view, copy or edit it
- **4 AI providers** — add, switch or remove APIs from the menu
- **Configurable hotkey** — right/left Option, Command or Control
- **🔔 Update notifications** — the app checks GitHub once a day and offers new versions from the menu (can be turned off with one click)
- **Silence detection** — nothing is sent to the API if there's no voice
- Starts automatically at login

---

## Building from source

**macOS** (Python 3.11+ needed only to build):

```bash
./build.sh
```

Generates `WhisperDictationVP-<Arch>.pkg` on the Desktop with the app and its embedded Python via PyInstaller.

**Automated releases** — pushing a `v*` tag makes GitHub Actions build all three versions (macOS arm64, macOS x86_64 and Windows) and publish them to Releases.

---

## Uninstalling

**macOS:**

```bash
launchctl unload ~/Library/LaunchAgents/com.vasyl.whisper-dictation-vp.plist
rm -f ~/Library/LaunchAgents/com.vasyl.whisper-dictation-vp.plist
sudo rm -rf "/Applications/Whisper Dictation VP.app"
rm -f ~/.whisper_dictation_vp.json
```

**Windows:** delete the unzipped folder and `%USERPROFILE%\.whisper_dictation_vp.json`.

---

## Changelog

See the full changelog (in Spanish) in [README.md](README.md#changelog). Highlights:

- **v3.2.0** — update notifications with opt-out toggle; dual hotkey listening channel (native NSEvent monitor + pynput)
- **v3.1.x** — AI Format (LLM cleanup), personal dictionary, automatic language detection with 17 language options, native clipboard, critical hotkey fixes
- **v3.0.0** — fully native macOS app (embedded Python), Windows beta, CI/CD releases
- **v2.x** — multi-provider support, interactive history, configurable hotkey and language

---

## License

MIT — see [LICENSE](LICENSE)
