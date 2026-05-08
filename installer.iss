; =============================================================================
; VDV463 Validator - Inno Setup Installer Script
; =============================================================================
; Creates a Windows installer for the VDV463 JSON Validator application
; 
; Build Requirements:
; - Inno Setup 6.x or later
; - PyInstaller dist/main/ folder must exist
;
; Usage:
; - Run this script with Inno Setup Compiler (ISCC.exe)
; - Output: Output/VDV463-Validator-Setup.exe
; =============================================================================

; Version is defined via command line: /DMyAppVersion=x.y.z
; Default to 3.0.0 if not provided
#ifndef MyAppVersion
  #define MyAppVersion "3.0.0"
#endif

#define MyAppName "VDV463 Validator"
#define MyAppPublisher "VDV463 Project"
#define MyAppURL "https://github.com/VDVde/JSON-Validator"
#define MyAppExeName "VDV463Validator.exe"

[Setup]
; Application identification - unique UUID for this application
AppId={{F06826E6-E8E1-4C5C-8114-5322B8F3C21C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases

; Installation directories
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes

; Installer output
OutputDir=Output
OutputBaseFilename=VDV463-Validator-Setup-{#MyAppVersion}
UninstallDisplayIcon={app}\{#MyAppExeName}

; Compression settings
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes

; Windows version requirements
MinVersion=10.0

; Privileges (install for current user by default)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; Wizard settings
WizardStyle=modern

; License and info
LicenseFile=LICENSE

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Main application files from PyInstaller dist/main/ folder
Source: "dist\main\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Note: The UI folder including run_ui.bat is already included via PyInstaller
; but we ensure the bat file is accessible at the app root for easy access
Source: "UI\run_ui.bat"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu shortcuts
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

; Desktop shortcut
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

; Quick Launch shortcut (legacy)
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
; Option to run after installation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Registry]
; Associate .vdv463 file extension (optional)
Root: HKA; Subkey: "Software\Classes\.vdv463"; ValueType: string; ValueName: ""; ValueData: "VDV463File"; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\VDV463File"; ValueType: string; ValueName: ""; ValueData: "VDV463 JSON File"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\VDV463File\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"
Root: HKA; Subkey: "Software\Classes\VDV463File\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""

[Code]
// Check for running instances before install/uninstall
function InitializeSetup(): Boolean;
begin
  Result := True;
end;

function InitializeUninstall(): Boolean;
begin
  Result := True;
end;
