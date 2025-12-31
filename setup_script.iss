; Скрипт для Inno Setup

#define MyAppName "Constructor Control Panel"
#define MyAppVersion "1.0"
#define MyAppPublisher "My Company"
#define MyAppExeName "ConstructorControlPanel.exe"

[Setup]
; Уникальный ID приложения
AppId={{A3B4C5D6-E7F8-9012-3456-7890ABCDEF12}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={commonpf}\KostruktorCP
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=Output
OutputBaseFilename=ConstructorSetup
Compression=lzma
SolidCompression=yes
SetupIconFile=icon.ico

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Dirs]
; Создаем папки, которые могут быть пустыми или нужны для работы
Name: "{app}\SynthSpeech"
Name: "{app}\AudioPanelSounds"

[Files]
; 1. Копируем сам EXE и все системные файлы из папки dist/ConstructorControlPanel
Source: "dist\ConstructorControlPanel\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; 2. Копируем папки с ресурсами из корня проекта
Source: "Items\*"; DestDir: "{app}\Items"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "BaseRoomSounds\*"; DestDir: "{app}\BaseRoomSounds"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "TimerSounds\*"; DestDir: "{app}\TimerSounds"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "PlayerButtons\*"; DestDir: "{app}\PlayerButtons"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "VisualTab\*"; DestDir: "{app}\VisualTab"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "OrangeLVL\*"; DestDir: "{app}\OrangeLVL"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "PurpleLVL\*"; DestDir: "{app}\PurpleLVL"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "Lore\*"; DestDir: "{app}\Lore"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "CharList\*"; DestDir: "{app}\CharList"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "BaseMusic\*"; DestDir: "{app}\BaseMusic"; Flags: ignoreversion recursesubdirs createallsubdirs
; AudioPanelSounds создается в [Dirs], но если там есть файлы по умолчанию, раскомментируйте строку ниже:
; Source: "AudioPanelSounds\*"; DestDir: "{app}\AudioPanelSounds"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "WhiteRoomMove\*"; DestDir: "{app}\WhiteRoomMove"; Flags: ignoreversion recursesubdirs createallsubdirs

; 3. Копируем шрифты и иконку
Source: "EpilepsySans.ttf"; DestDir: "{app}"; Flags: ignoreversion
Source: "EpilepsySansB.ttf"; DestDir: "{app}"; Flags: ignoreversion
Source: "Digiface.ttf"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
