#define MyAppName "Skrivi"
#define MyAppVersion GetEnv("SKRIVI_INSTALLER_VERSION")
#define MySourceDir GetEnv("SKRIVI_INSTALLER_SOURCE")
#define MyOutputDir GetEnv("SKRIVI_INSTALLER_OUTPUT")
#define MyProjectRoot GetEnv("SKRIVI_PROJECT_ROOT")

[Setup]
AppId={{B17E37FA-9342-4B72-96C4-76F57498A44E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=Skrivi
AppPublisherURL=https://skrivi.no/
AppSupportURL=https://github.com/workavoidance/Skrivi/issues
AppUpdatesURL=https://github.com/workavoidance/Skrivi/releases
DefaultDirName={localappdata}\Programs\Skrivi
DefaultGroupName=Skrivi
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
MinVersion=10.0.22000
OutputDir={#MyOutputDir}
OutputBaseFilename=Skrivi-{#MyAppVersion}-windows-x64-setup
SetupIconFile={#MyProjectRoot}\assets\skrivi.ico
UninstallDisplayIcon={app}\Skrivi.exe
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
SetupLogging=yes
LicenseFile={#MyProjectRoot}\LICENSE
ChangesAssociations=no
ChangesEnvironment=no
UsedUserAreasWarning=no

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[InstallDelete]
Type: filesandordirs; Name: "{app}\runtime"

[Files]
Source: "{#MySourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#MyProjectRoot}\README.md"; DestDir: "{app}\documentation"; Flags: ignoreversion
Source: "{#MyProjectRoot}\LICENSE"; DestDir: "{app}\documentation"; Flags: ignoreversion
Source: "{#MyProjectRoot}\CHANGELOG.md"; DestDir: "{app}\documentation"; Flags: ignoreversion
Source: "{#MyProjectRoot}\THIRD_PARTY_NOTICES.md"; DestDir: "{app}\documentation"; Flags: ignoreversion

[Icons]
Name: "{group}\Skrivi"; Filename: "{app}\Skrivi.exe"; WorkingDir: "{app}"
Name: "{group}\Uninstall Skrivi"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Skrivi"; Filename: "{app}\Skrivi.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\Skrivi.exe"; Description: "Launch Skrivi"; Flags: nowait postinstall skipifsilent

[Code]
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  RegisteredCommand: String;
  InstalledCommand: String;
begin
  if CurUninstallStep <> usUninstall then
    Exit;

  InstalledCommand := '"' + ExpandConstant('{app}\Skrivi.exe') + '"';
  if RegQueryStringValue(
    HKCU,
    'Software\Microsoft\Windows\CurrentVersion\Run',
    'Skrivi',
    RegisteredCommand
  ) and (CompareText(RegisteredCommand, InstalledCommand) = 0) then
    RegDeleteValue(
      HKCU,
      'Software\Microsoft\Windows\CurrentVersion\Run',
      'Skrivi'
    );
end;
