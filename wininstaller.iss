[Setup]
AppName=DDT4All
AppVersion=1.0
DefaultDirName={pf}\ddt4all
DefaultGroupName=ddt4all
SetupIconFile=icons\obd.ico
OutputBaseFilename=ddt4all-installer

[Files]
Source: "*.py"; DestDir: "{app}"
Source: "README.md"; DestDir: "{app}"
Source: "crcmod\*"; DestDir: "{app}\crcmod"; Flags: ignoreversion recursesubdirs; Excludes: "*.pyc"
Source: "Python38\*"; DestDir: "{app}\Python38"; Flags: ignoreversion recursesubdirs; Excludes: "*.pyc"
Source: "ddtplugins\*"; DestDir: "{app}\ddtplugins"; Flags: ignoreversion recursesubdirs; Excludes: "*.pyc"
Source: "icons\*"; DestDir: "{app}\icons"; Flags: ignoreversion recursesubdirs
Source: "json\*"; DestDir: "{app}\json"; Flags: ignoreversion recursesubdirs
Source: "locale\*"; DestDir: "{app}\locale"; Flags: ignoreversion recursesubdirs
Source: "serial\*"; DestDir: "{app}\serial"; Flags: ignoreversion recursesubdirs; Excludes: "*.pyc"
Source: "DDT4ALL.BAT"; DestDir: "{app}"; AfterInstall: AfterMyProgInstall
; Uncheck the line below to package ecu db
; Source: "ecu.zip"; DestDir: "{app}";

[InstallDelete]
Type: filesandordirs; Name: "{app}\importlib"
Type: filesandordirs; Name: "{app}\python27"

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
Name: "{group}\ddt4all"; Filename: "{app}\Python38\python.exe"; Parameters: """{app}\ddt4all.py"""; WorkingDir: "{app}"; IconFilename: "{app}\icons\obd.ico"
Name: "{userdesktop}\ddt4all"; Filename: "{app}\Python38\python.exe"; Parameters: """{app}\ddt4all.py"""; WorkingDir: "{app}"; IconFilename: "{app}\icons\obd.ico"; Tasks: desktopicon

[CustomMessages]
en.AfterMyProgInstall=Do not forget to install database to 
it.AfterMyProgInstall=Non dimenticare di installare il database in 
fr.AfterMyProgInstall=Pensez a installer une base de donnée dans 

[Languages]
Name: "en"; MessagesFile: "C:\Program Files (x86)\Inno Setup 5\Default.isl"; 
Name: "de"; MessagesFile: "C:\Program Files (x86)\Inno Setup 5\Languages\German.isl"; 
Name: "fr"; MessagesFile: "C:\Program Files (x86)\Inno Setup 5\Languages\French.isl"; 
Name: "es"; MessagesFile: "C:\Program Files (x86)\Inno Setup 5\Languages\Spanish.isl"; 
Name: "hu"; MessagesFile: "C:\Program Files (x86)\Inno Setup 5\Languages\Hungarian.isl"; 
Name: "it"; MessagesFile: "C:\Program Files (x86)\Inno Setup 5\Languages\Italian.isl"; 
Name: "nl"; MessagesFile: "C:\Program Files (x86)\Inno Setup 5\Languages\Dutch.isl"; 
Name: "pl"; MessagesFile: "C:\Program Files (x86)\Inno Setup 5\Languages\Polish.isl"; 
Name: "pt"; MessagesFile: "C:\Program Files (x86)\Inno Setup 5\Languages\Portuguese.isl"; 
Name: "ru"; MessagesFile: "C:\Program Files (x86)\Inno Setup 5\Languages\Russian.isl"; 
Name: "sr"; MessagesFile: "C:\Program Files (x86)\Inno Setup 5\Languages\SerbianLatin.isl"; 
