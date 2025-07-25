;--------------------- This requires Inno Setup 5 for compatibilities, an python 3.8.6 - 32 bits for autonomous modes.
#include "version.h"
#define MyAppName       Str(__appname__)
#define MyAppVersion    Str(__version__)
#define MyAppStatus     Str(__status__) + "-x86"    
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
DefaultDirName={pf}\{#MyAppDir}
DefaultGroupName={#MyAppName}
SetupIconFile=..\..\ddt4all_data\icons\obd.ico
OutputBaseFilename={#MyAppName}-Windows-Installer-v{#MyAppVersion}_{#MyAppStatus}
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
;WizardStyle=modern
DisableWelcomePage=no
UsedUserAreasWarning=no
AppId={{#APP_ID}

[Files]
Source: "win32_deps\VC_redist.x86.exe"; DestDir: "{app}\win32_deps"; Tasks: microsoft_runtimes
Source: "..\..\ecu.zip"; DestDir: "{app}";
Source: "\DDT4ALL-Dist-Versions\Python38-32\*"; DestDir: "{app}\Python386-32"; Flags: ignoreversion recursesubdirs; Excludes: "*.pyc"
;Source: "\DDT4ALL-Dist-Versions\Git-2.43.0\x64\*"; DestDir: "{app}\Git"; Flags: ignoreversion recursesubdirs
Source: "..\..\ddtplugins\*.py"; DestDir: "{app}\ddtplugins"; Flags: ignoreversion recursesubdirs; Excludes: "*.pyc"
Source: "..\..\json\*"; DestDir: "{app}\json"; Flags: ignoreversion recursesubdirs onlyifdoesntexist skipifsourcedoesntexist
Source: "..\..\ddt4all_data\icons\*"; DestDir: "{app}\ddt4all_data\icons"; Flags: ignoreversion recursesubdirs
Source: "..\..\ddt4all_data\tools\*"; DestDir: "{app}\ddt4all_data\tools"; Flags: ignoreversion recursesubdirs
Source: "..\..\ddt4all_data\locale\*"; DestDir: "{app}\ddt4all_data\locale"; Flags: ignoreversion recursesubdirs
Source: "..\..\*.py"; DestDir: "{app}"; Excludes: "*.pyc"
Source: "..\..\ddt4all_data\*.qss"; DestDir: "{app}\ddt4all_data"
Source: "..\..\ddt4all_data\projects.json"; DestDir: "{app}\ddt4all_data"; AfterInstall: AfterMyProgInstall

[InstallDelete]
Type: filesandordirs; Name: "{group}";
Type: filesandordirs; Name: "{app}"

[UninstallDelete]
Type: filesandordirs; Name: "{group}";
Type: filesandordirs; Name: "{app}"

[Run]
Filename: "{app}\win32_deps\VC_redist.x86.exe"; Tasks: microsoft_runtimes
Filename: "{app}\Python386-32\python.exe"; Parameters: """{app}\main.py"""; WorkingDir: "{app}"; Description: {cm:OpenAfterInstall}; Flags: postinstall nowait skipifsilent runasoriginaluser

[Code]
procedure AfterMyProgInstall;
begin
    // MsgBox(ExpandConstant('{cm:AfterMyProgInstall} {app}'), mbInformation, MB_OK);
    // remove developement config.json file
    DeleteFile(ExpandConstant('{app}\ddt4all_data\config.json'));
end;

[Dirs]
Name: "{app}"; Permissions: users-full
Name: "{app}\logs"; Permissions: users-full
Name: "{app}\json"; Permissions: users-full
Name: "{app}\ddt4all_data"; Permissions: users-full
Name: "{app}\vehicles"; Permissions: users-full

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "microsoft_runtimes"; Description: "{cm:MSruntimes}"; GroupDescription: "Microsoft Visual C++ Redistributable"

[Icons]
Name: "{app}\{#MyAppName}"; Filename: "{app}\Python386-32\python.exe"; WorkingDir: "{app}"; IconFilename: "{app}\ddt4all_data\icons\obd.ico"; Parameters: """{app}\main.py"""; Comment: "{#MyAppName} Diagnostic Tool"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"; Comment: "Uninstall {#MyAppName} Diagnostic Tool"
Name: "{group}\{#MyAppName}"; Filename: "{app}\Python386-32\python.exe"; WorkingDir: "{app}"; IconFilename: "{app}\ddt4all_data\icons\obd.ico"; Parameters: """{app}\main.py"""; Comment: "{#MyAppName} Diagnostic Tool"
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\Python386-32\python.exe"; WorkingDir: "{app}"; IconFilename: "{app}\ddt4all_data\icons\obd.ico"; Parameters: """{app}\main.py"""; Comment: "{#MyAppName} Diagnostic Tool"; Tasks: desktopicon

[CustomMessages]
en.MSruntimes=Install Microsoft Visual C++ Redistributable runtimes files
de.MSruntimes=Installieren Sie Microsoft Visual C++ Redistributable-Laufzeitdateien
fr.MSruntimes=Installer les fichiers d'exécution redistribuables Microsoft Visual C++
es.MSruntimes=Instalar archivos de tiempo de ejecución redistribuibles de Microsoft Visual C++
it.MSruntimes=Installare i file runtime ridistribuibili di Microsoft Visual C++
nl.MSruntimes=Installeer Microsoft Visual C++ Redistributable runtimes-bestanden
pl.MSruntimes=Zainstaluj pliki środowiska wykonawczego redystrybucyjnego Microsoft Visual C++
ptbr.MSruntimes=Instalar arquivos de tempo de execução redistribuíveis do Microsoft Visual C++
pt.MSruntimes=Instalar arquivos de tempo de execução redistribuíveis do Microsoft Visual C++
ru.MSruntimes=Установите распространяемые файлы среды выполнения Microsoft Visual C++.
tr.MSruntimes=Microsoft Visual C++ Yeniden Dağıtılabilir çalışma zamanı dosyalarını yükleyin
; -----------------------------------------------------------------------------
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
; -----------------------------------------------------------------------------
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
