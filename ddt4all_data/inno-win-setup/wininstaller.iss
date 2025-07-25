#include "version.h"
#define MyAppName       Str(__appname__)
#define MyAppVersion    Str(__version__)
#define MyAppStatus     Str(__status__) + "-x64"    
#define MyAppDir        MyAppName
#define MyAppAuthor     Str(__author__)
#define MyAppCompany    Str(__author__)
#define MyAppContact    Str(__email__)  
#define MyAppSupportURL "https://github.com/cedricp/ddt4all" 
#define MyAppReadmeMd   "https://github.com/cedricp/ddt4all/blob/master/README.md"
#define MyCopyright     Str(__copyright__) + " - " + MyAppAuthor
#define APP_ID          "{3E70988F-0D77-4639-800D-2CD9DB2617B1}"

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion} {#MyAppStatus}
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
ArchitecturesInstallIn64BitMode=x64 ia64
ArchitecturesAllowed=x64 arm64 ia64
Compression=lzma2/ultra64
AllowUNCPath=true
MinVersion=6.1sp1
InternalCompressLevel=ultra
DefaultDirName={commonpf}\{#MyAppDir}
DefaultGroupName={#MyAppName}
SetupIconFile=..\..\ddt4all_data\icons\obd.ico
OutputBaseFilename={#MyAppName}-Windows-Installer-v{#MyAppVersion}_{#MyAppStatus}
UsePreviousPrivileges=True
VersionInfoCompany={#MyAppCompany}
VersionInfoTextVersion={#MyAppVersion}
VersionInfoCopyright={#MyCopyright} 
VersionInfoProductVersion={#MyAppVersion}
VersionInfoProductTextVersion={#MyAppVersion}
VersionInfoOriginalFileName={#MyAppName}
LicenseFile=..\..\license.txt
WizardSmallImageFile=installer_wizard_image.bmp
WizardImageFile=WizardImage0.bmp
DisableDirPage=yes
DisableProgramGroupPage=yes
;WizardStyle=modern
DisableWelcomePage=no
UsedUserAreasWarning=no
AppId={{#APP_ID}

[Files]
Source: "..\..\ecu.zip"; DestDir: "{app}";
Source: "\DDT4ALL-Dist-Versions\Python313\*"; DestDir: "{app}\Python313-x64"; Flags: ignoreversion recursesubdirs; Excludes: "*.pyc"
;Source: "\DDT4ALL-Dist-Versions\Git-2.43.0\x64\*"; DestDir: "{app}\Git"; Flags: ignoreversion recursesubdirs
Source: "..\..\ddtplugins\*.py"; DestDir: "{app}\ddtplugins"; Flags: ignoreversion recursesubdirs; Excludes: "*.pyc"
Source: "..\..\json\*"; DestDir: "{app}\json"; Flags: ignoreversion recursesubdirs onlyifdoesntexist skipifsourcedoesntexist
Source: "..\..\ddt4all_data\icons\*"; DestDir: "{app}\ddt4all_data\icons"; Flags: ignoreversion recursesubdirs
Source: "..\..\ddt4all_data\tools\*"; DestDir: "{app}\ddt4all_data\tools"; Flags: ignoreversion recursesubdirs
Source: "..\..\ddt4all_data\locale\*"; DestDir: "{app}\ddt4all_data\locale"; Flags: ignoreversion recursesubdirs
Source: "..\..\*.py"; DestDir: "{app}"; Excludes: "*.pyc"
Source: "..\..\ddt4all_data\*.qss"; DestDir: "{app}\ddt4all_data";
Source: "..\..\ddt4all_data\projects.json"; DestDir: "{app}\ddt4all_data"; AfterInstall: AfterMyProgInstall

[InstallDelete]
Type: filesandordirs; Name: "{group}";
Type: filesandordirs; Name: "{app}"

[UninstallDelete]
Type: filesandordirs; Name: "{group}";
Type: filesandordirs; Name: "{app}"

[Run]
Filename: "{app}\Python313-x64\python.exe"; Parameters: """{app}\main.py"""; WorkingDir: {app}; Description: {cm:OpenAfterInstall}; Flags: postinstall nowait skipifsilent runasoriginaluser

[Code]
procedure AfterMyProgInstall;
begin
    // MsgBox(ExpandConstant('{cm:AfterMyProgInstall} {app}'), mbInformation, MB_OK);
    // remove developement config.json file
    DeleteFile(ExpandConstant('{app}\ddt4all_data\config.json'));
end;

[Dirs]
Name: "{app}\logs"; Permissions: users-full
Name: "{app}\json"; Permissions: users-full
Name: "{app}\vehicles"; Permissions: users-full
Name: "{app}\ddt4all_data"; Permissions: users-full

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Icons]
Name: "{app}\{#MyAppName}"; Filename: "{app}\Python313-x64\python.exe"; WorkingDir: "{app}"; IconFilename: "{app}\ddt4all_data\icons\obd.ico"; Parameters: """{app}\main.py"""; Comment: "{#MyAppName} Diagnostic Tool"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"; Comment: "Uninstall {#MyAppName} Diagnostic Tool"
Name: "{group}\{#MyAppName}"; Filename: "{app}\Python313-x64\python.exe"; WorkingDir: "{app}"; IconFilename: "{app}\ddt4all_data\icons\obd.ico"; Parameters: """{app}\main.py"""; Comment: "{#MyAppName} Diagnostic Tool"
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\Python313-x64\python.exe"; WorkingDir: "{app}"; IconFilename: "{app}\ddt4all_data\icons\obd.ico"; Parameters: """{app}\main.py"""; Comment: "{#MyAppName} Diagnostic Tool"; Tasks: desktopicon

[CustomMessages]
en.OpenAfterInstall=Open {#MyAppName} after installation
de.OpenAfterInstall={#MyAppName} nach Abschluss der Installation öffnen
fr.OpenAfterInstall=Ouvrir {#MyAppName} après l'installation
es.OpenAfterInstall=Abrir {#MyAppName} tras la instalación
it.OpenAfterInstall=Apri {#MyAppName} dopo l'installazione
nl.OpenAfterInstall={#MyAppName} starten na installatie
pl.OpenAfterInstall=Otwórz program {#MyAppName} po zakończeniu instalacji
ptbr.OpenAfterInstall=Abrir o {#MyAppName} após a instalação
pt.OpenAfterInstall=Abrir o {#MyAppName} após a instalação
ru.OpenAfterInstall=Открыть {#MyAppName} после окончания установки
tr.OpenAfterInstall=Kurulumdan sonra {#MyAppName}'i aç
en.AfterMyProgInstall=Do not forget to install database to %n%n
de.AfterMyProgInstall=Erwägen Sie die Installation einer Datenbank in%n%n
fr.AfterMyProgInstall=Pensez a installer une base de données dans%n%n
es.AfterMyProgInstall=Considere instalar una base de datos en%n%n
it.AfterMyProgInstall=Non dimenticare di installare il database in%n%n
nl.AfterMyProgInstall=Overweeg een database te installeren in%n%n
pl.AfterMyProgInstall=Rozważ zainstalowanie bazy danych w%n%n
ptbr.AfterMyProgInstall=Considere instalar um banco de dados em%n%n
pt.AfterMyProgInstall=Considere instalar um banco de dados em%n%n
ru.AfterMyProgInstall=Рассмотрите возможность установки базы данных в%n%n
tr.AfterMyProgInstall=Veritabanını şuraya yüklemeyi unutmayın %n%n

[Languages]
Name: "en";   MessagesFile: "compiler:\Default.isl"
Name: "de";   MessagesFile: "compiler:\Languages\German.isl"
Name: "fr";   MessagesFile: "compiler:\Languages\French.isl"
Name: "es";   MessagesFile: "compiler:\Languages\Spanish.isl"
Name: "it";   MessagesFile: "compiler:\Languages\Italian.isl"
Name: "nl";   MessagesFile: "compiler:\Languages\Dutch.isl"
Name: "pl";   MessagesFile: "compiler:\Languages\Polish.isl"
Name: "ptbr"; MessagesFile: "compiler:\Languages\BrazilianPortuguese.isl"
Name: "pt";   MessagesFile: "compiler:\Languages\Portuguese.isl"
Name: "ru";   MessagesFile: "compiler:\Languages\Russian.isl"
Name: "tr";   MessagesFile: "compiler:\Languages\Turkish.isl"
