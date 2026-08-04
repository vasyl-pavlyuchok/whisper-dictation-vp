; Instalador de Windows para Whisper Dictation VP (Inno Setup)
; Compilar: iscc /DAppVer=X.Y.Z installer\windows\installer.iss

#ifndef AppVer
  #define AppVer "0.0.0"
#endif

[Setup]
AppName=Whisper Dictation VP
AppVersion={#AppVer}
AppPublisher=Vasyl Pavlyuchok
AppPublisherURL=https://vasylpavlyuchok.com/ai/tools/whisper-dictation
AppSupportURL=https://github.com/vasyl-pavlyuchok/whisper-dictation-vp
DefaultDirName={localappdata}\Programs\WhisperDictationVP
DefaultGroupName=Whisper Dictation VP
PrivilegesRequired=lowest
OutputDir=output
OutputBaseFilename=WhisperDictationVP-Windows-Setup
SetupIconFile=..\..\app\AppIcon.ico
UninstallDisplayIcon={app}\WhisperDictationVP.exe
ShowLanguageDialog=yes
WizardStyle=modern
DisableProgramGroupPage=yes
Compression=lzma2
SolidCompression=yes

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"; InfoBeforeFile: "info_es.txt"
Name: "english"; MessagesFile: "compiler:Default.isl"; InfoBeforeFile: "info_en.txt"

[Tasks]
Name: "startup"; Description: "{cm:AutoStartProgram,Whisper Dictation VP}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\..\dist\WhisperDictationVP.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Whisper Dictation VP"; Filename: "{app}\WhisperDictationVP.exe"
Name: "{userstartup}\Whisper Dictation VP"; Filename: "{app}\WhisperDictationVP.exe"; Tasks: startup

[Run]
Filename: "{app}\WhisperDictationVP.exe"; Description: "{cm:LaunchProgram,Whisper Dictation VP}"; Flags: nowait postinstall skipifsilent
