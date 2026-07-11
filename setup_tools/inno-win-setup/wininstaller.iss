;--------------------- This requires Inno Setup 5.6.1(u) for compatibilities, an python 2.7 - Windows XP 32/64 bits for autonomous modes.
#include "version.h"
#define MyAppName       Str(__appname__) 
#define MyAppVersion    Str(__version__)
#define MyAppCodeName   StringChange(Str(__codename__), " ", "-")
#define MyAppDir        MyAppName
#define MyAppAuthor     Str(__author__)
#define MyAppCompany    Str(__author__)
#define MyAppContact    Str(__email__)  
#define MyAppSupportURL "https://github.com/cedricp/ddt4all" 
#define MyAppReadmeMd   "https://github.com/cedricp/ddt4all/blob/master/README.md"
#define MyCopyright     Str(__copyright__) + " - " + MyAppAuthor
#define APP_ID          "{3E70988F-0D77-4639-800D-2CD9DB2617B1}"
#define PYTHON_FOLDER   "Python27"

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion} {#MyAppCodeName}
AppPublisherURL={#MyAppSupportURL}
AppSupportURL={#MyAppSupportURL}
AppUpdatesURL={#MyAppSupportURL}
AppReadmeFile={#MyAppReadmeMd}
AppContact={#MyAppContact}
VersionInfoDescription={#MyAppName} Windows-Installer
VersionInfoVersion={#MyAppVersion}
VersionInfoProductName={#MyAppName}
AppCopyright={#MyCopyright} 
UninstallDisplayIcon={uninstallexe}
UninstallDisplayName={#MyAppName}
AppPublisher={#MyAppCompany}
DefaultDirName={pf}\{#MyAppDir}
DefaultGroupName={#MyAppName}
SetupIconFile=..\..\icons\obd.ico
OutputBaseFilename={#MyAppName}-Windows-Installer-v{#MyAppVersion}_{#MyAppCodeName}
VersionInfoCompany={#MyAppCompany}
ArchitecturesAllowed=x86 x64
Compression=lzma2/ultra
AllowUNCPath=true
VersionInfoTextVersion={#MyAppVersion}
VersionInfoCopyright={#MyCopyright}
VersionInfoProductVersion={#MyAppVersion}
VersionInfoProductTextVersion={#MyAppVersion}
LicenseFile=..\..\license.txt
WizardSmallImageFile=installer_wizard_image.bmp
WizardImageFile=WizardImage0.bmp
DisableDirPage=yes
DisableProgramGroupPage=yes
DisableWelcomePage=no
UsedUserAreasWarning=no
AppId={{#APP_ID}

[Files]
Source: "..\..\*.py"; DestDir: "{app}"
Source: "..\..\crcmod\*"; DestDir: "{app}\crcmod"; Flags: ignoreversion recursesubdirs; Excludes: "*.pyc"
Source: "\DDT4ALL-Dist-Versions\Python27\*"; DestDir: "{app}\{#PYTHON_FOLDER}"; Flags: ignoreversion recursesubdirs; Excludes: "*.pyc"
Source: "..\..\ddtplugins\*"; DestDir: "{app}\ddtplugins"; Flags: ignoreversion recursesubdirs; Excludes: "*.pyc"
Source: "..\..\icons\*"; DestDir: "{app}\icons"; Flags: ignoreversion recursesubdirs
Source: "..\..\importlib\*"; DestDir: "{app}\importlib"; Flags: ignoreversion recursesubdirs; Excludes: "*.pyc"
Source: "..\..\locale\*"; DestDir: "{app}\locale"; Flags: ignoreversion recursesubdirs
Source: "..\..\serial\*"; DestDir: "{app}\serial"; Flags: ignoreversion recursesubdirs; Excludes: "*.pyc"
Source: "..\..\README.md"; DestDir: "{app}"; AfterInstall: AfterMyProgInstall('Do not forget to install database to ', ExpandConstant('{app}'))
; Uncheck the line below to package ecu db
; Source: "ecu.zip"; DestDir: "{app}";

[Code]
procedure AfterMyProgInstall(S: String; P: String);
begin
    MsgBox(S + P, mbInformation, MB_OK);
end;

[Dirs]
Name: "{app}\logs"; Permissions: users-full
Name: "{app}\json"; Permissions: users-full
Name: "{app}\vehicles"; Permissions: users-full

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}";GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Icons]
Name: "{group}\ddt4all"; Filename: "{app}\{#PYTHON_FOLDER}\python.exe"; Parameters: """{app}\main.py"""; WorkingDir: "{app}"; IconFilename: "{app}\icons\obd.ico"
Name: "{userdesktop}\ddt4all"; Filename: "{app}\{#PYTHON_FOLDER}\python.exe"; Parameters: """{app}\main.py"""; WorkingDir: "{app}"; IconFilename: "{app}\icons\obd.ico"; Tasks: desktopicon