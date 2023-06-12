;--------------------- This requires Inno Setup 5 for compatibilities, an python 3.8.6 - 32 bits for autonomous modes.
#define MyAppName       "DDT4All"
#define MyAppVersion    GetDateTimeString('yy.mm.dd','','')
#define MyAppDir        "ddtall"
#define MyAppAuthor     "Cedric PAILLE"
#define MyAppCompany    "Cedric PAILLE"
#define MyAppContact    "cedricpaille@gmail.com"  
#define MyAppSupportURL "https://github.com/cedricp/ddt4all" 
#define MyAppReadmeMd   "https://github.com/cedricp/ddt4all/blob/master/README.md"
#define C_StartingYear  "2016"
#define C_EndingYear    GetDateTimeString('yyyy','','')
#define DateEUR         GetDateTimeString('dd.mm.yyyy','','')

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}

AppPublisherURL={#MyAppSupportURL}
AppSupportURL={#MyAppSupportURL}
AppUpdatesURL={#MyAppSupportURL}
AppReadmeFile={#MyAppReadmeMd}
AppContact={#MyAppContact}

;--------------------- Info for exe file properties
VersionInfoDescription={#MyAppName} installer
VersionInfoVersion={#MyAppVersion}
VersionInfoProductName={#MyAppName}
AppCopyright={#MyAppCompany} {#C_StartingYear}-{#C_EndingYear} 

;--------------------- Info Windows program list
UninstallDisplayIcon={app}\icons\obd.ico
UninstallDisplayName={#MyAppName}
AppPublisher={#MyAppCompany}

UsepreviousLanguage=No

DefaultDirName={pf}\{#MyAppDir}
DefaultGroupName={#MyAppDir}
SetupIconFile=icons\obd.ico
OutputBaseFilename={#MyAppDir}-win-installer-{#MyAppVersion}-python-3.8.6-32bits
VersionInfoCompany={#MyAppCompany}
VersionInfoTextVersion={#MyAppVersion}
VersionInfoCopyright={#MyAppCompany} {#C_StartingYear}-{#C_EndingYear} 
VersionInfoProductVersion={#MyAppVersion}
VersionInfoProductTextVersion={#MyAppVersion}
LicenseFile=license.txt
WizardStyle=modern

[Files]
//Source: "ecu.zip"; DestDir: "{app}"; Flags: onlyifdoesntexist skipifsourcedoesntexist
Source: "*.py"; DestDir: "{app}"; Excludes: "*.pyc"
Source: "*.qss"; DestDir: "{app}" ; AfterInstall: AfterMyProgInstall
Source: "\Python38-32\*"; DestDir: "{app}\Python38-32"; Flags: ignoreversion recursesubdirs; Excludes: "*.pyc"
Source: "ddtplugins\*"; DestDir: "{app}\ddtplugins"; Flags: ignoreversion recursesubdirs; Excludes: "*.pyc"
Source: "icons\*"; DestDir: "{app}\icons"; Flags: ignoreversion recursesubdirs
Source: "address\*"; DestDir: "{app}\address"; Flags: ignoreversion recursesubdirs
Source: "locale\*"; DestDir: "{app}\locale"; Flags: ignoreversion recursesubdirs
Source: "json\*"; DestDir: "{app}\json"; Flags: ignoreversion recursesubdirs onlyifdoesntexist skipifsourcedoesntexist

[InstallDelete]
Type: filesandordirs; Name: "{app}\__pycache__"
Type: filesandordirs; Name: "{app}\importlib"
Type: filesandordirs; Name: "{app}\python27"

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
procedure AfterMyProgInstall;
begin
    MsgBox(ExpandConstant('{cm:AfterMyProgInstall} {app}'), mbInformation, MB_OK);
end;

[Dirs]
Name: "{app}"; Permissions: users-full
Name: "{app}\logs"; Permissions: users-full
Name: "{app}\json"; Permissions: users-full
Name: "{app}\vehicles"; Permissions: users-full

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Icons]
Name: "{group}\ddt4all"; Filename: "{app}\Python38-32\python.exe"; Parameters: """{app}\main.py"""; WorkingDir: "{app}"; IconFilename: "{app}\icons\obd.ico"
Name: "{userdesktop}\ddt4all"; Filename: "{app}\Python38-32\python.exe"; Parameters: """{app}\main.py"""; WorkingDir: "{app}"; IconFilename: "{app}\icons\obd.ico"; Tasks: desktopicon

[CustomMessages]
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

[Languages]
Name: "en";   MessagesFile: "C:\Program Files (x86)\Inno Setup 5\Default.isl"
Name: "de";   MessagesFile: "C:\Program Files (x86)\Inno Setup 5\Languages\German.isl"
Name: "fr";   MessagesFile: "C:\Program Files (x86)\Inno Setup 5\Languages\French.isl"
Name: "es";   MessagesFile: "C:\Program Files (x86)\Inno Setup 5\Languages\Spanish.isl"
Name: "it";   MessagesFile: "C:\Program Files (x86)\Inno Setup 5\Languages\Italian.isl"
Name: "nl";   MessagesFile: "C:\Program Files (x86)\Inno Setup 5\Languages\Dutch.isl"
Name: "pl";   MessagesFile: "C:\Program Files (x86)\Inno Setup 5\Languages\Polish.isl"
Name: "ptbr"; MessagesFile: "C:\Program Files (x86)\Inno Setup 5\Languages\BrazilianPortuguese.isl"
Name: "pt";   MessagesFile: "C:\Program Files (x86)\Inno Setup 5\Languages\Portuguese.isl"
Name: "ru";   MessagesFile: "C:\Program Files (x86)\Inno Setup 5\Languages\Russian.isl"
