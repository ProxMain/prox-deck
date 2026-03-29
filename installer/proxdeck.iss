#define MyAppName "Prox Deck"
#ifndef MyAppVersion
  #define MyAppVersion "1.0.0-alpha"
#endif
#define MyAppPublisher "Prox Deck"
#define MyAppExeName "ProxDeck.exe"

[Setup]
AppId={{5A6FC1A7-9DA8-47B8-AE96-E0CB9DC39C34}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Prox Deck
DefaultGroupName=Prox Deck
DisableProgramGroupPage=yes
OutputBaseFilename=ProxDeck-{#MyAppVersion}-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\{#MyAppExeName}

[Files]
Source: "..\dist\ProxDeck\ProxDeck.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\ProxDeck\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\Prox Deck"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Prox Deck"; Filename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch Prox Deck"; Flags: nowait postinstall skipifsilent
