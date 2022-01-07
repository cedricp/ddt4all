[Setup]
AppName=DDT4All
AppVersion=1.0
DefaultDirName={pf}\ddt4all
DefaultGroupName=ddt4all
SetupIconFile=icons\obd.ico
OutputBaseFilename=ddt4all-win-installer
UsePreviousPrivileges=True

[Files]
Source: "DDT4ALL.BAT"; DestDir: "{app}"; AfterInstall: AfterMyProgInstall
Source: "README.md"; DestDir: "{app}"
Source: "requirements.txt"; DestDir: "{app}"
Source: "license.txt"; DestDir: "{app}"
Source: "ecu.zip"; DestDir: "{app}"; Flags: onlyifdoesntexist skipifsourcedoesntexist
Source: "*.py"; DestDir: "{app}"
Source: "venv\*"; DestDir: "{app}\venv"; Flags: ignoreversion recursesubdirs; Excludes: "*.pyc"
Source: "ddtplugins\*"; DestDir: "{app}\ddtplugins"; Flags: ignoreversion recursesubdirs; Excludes: "*.pyc"
Source: "icons\*"; DestDir: "{app}\icons"; Flags: ignoreversion recursesubdirs
Source: "address\*"; DestDir: "{app}\address"; Flags: ignoreversion recursesubdirs
Source: "locale\*"; DestDir: "{app}\locale"; Flags: ignoreversion recursesubdirs
Source: "json\*"; DestDir: "{app}\json"; Flags: ignoreversion recursesubdirs onlyifdoesntexist skipifsourcedoesntexist

[InstallDelete]
Type: filesandordirs; Name: "{app}\importlib"
Type: filesandordirs; Name: "{app}\python27"
Type: filesandordirs; Name: "{app}\Python38"

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
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}";GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Icons]
Name: "{group}\ddt4all"; Filename: "{app}\venv\Scripts\python.exe"; Parameters: """{app}\ddt4all.py"""; WorkingDir: "{app}"; IconFilename: "{app}\icons\obd.ico"
Name: "{userdesktop}\ddt4all"; Filename: "{app}\venv\Scripts\python.exe"; Parameters: """{app}\ddt4all.py"""; WorkingDir: "{app}"; IconFilename: "{app}\icons\obd.ico"; Tasks: desktopicon

[CustomMessages]
en.AfterMyProgInstall=Do not forget to install database to 
de.AfterMyProgInstall=Erwägen Sie die Installation einer Datenbank in
fr.AfterMyProgInstall=Pensez a installer une base de donnée dans
es.AfterMyProgInstall=Considere instalar una base de datos en
it.AfterMyProgInstall=Non dimenticare di installare il database in
nl.AfterMyProgInstall=Overweeg een database te installeren in
pl.AfterMyProgInstall=Rozważ zainstalowanie bazy danych w
ptbr.AfterMyProgInstall=Considere instalar um banco de dados em
pt.AfterMyProgInstall=Considere instalar um banco de dados em
ru.AfterMyProgInstall=Рассмотрите возможность установки базы данных в

[Languages]
Name: "en"; MessagesFile: "C:\Program Files (x86)\Inno Setup 6\Default.isl"
Name: "de"; MessagesFile: "C:\Program Files (x86)\Inno Setup 6\Languages\German.isl"
Name: "fr"; MessagesFile: "C:\Program Files (x86)\Inno Setup 6\Languages\French.isl"
Name: "es"; MessagesFile: "C:\Program Files (x86)\Inno Setup 6\Languages\Spanish.isl"
Name: "it"; MessagesFile: "C:\Program Files (x86)\Inno Setup 6\Languages\Italian.isl"
Name: "nl"; MessagesFile: "C:\Program Files (x86)\Inno Setup 6\Languages\Dutch.isl"
Name: "pl"; MessagesFile: "C:\Program Files (x86)\Inno Setup 6\Languages\Polish.isl"
Name: "ptbr"; MessagesFile: "C:\Program Files (x86)\Inno Setup 6\Languages\BrazilianPortuguese.isl"
Name: "pt"; MessagesFile: "C:\Program Files (x86)\Inno Setup 6\Languages\Portuguese.isl"
Name: "ru"; MessagesFile: "C:\Program Files (x86)\Inno Setup 6\Languages\Russian.isl"
