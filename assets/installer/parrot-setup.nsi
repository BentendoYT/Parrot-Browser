; Parrot Browser - Windows x64 installer (NSIS 3).
; Built on Linux by scripts/build-installer.sh from the packaged build (parrot-*-package.zip).
;
; Contract with Parrot-WinUpdater (silent update runs "<setup>.exe /S /D=<install dir>"):
;   - install dir      : $PROGRAMFILES64\Parrot Browser   (updater default path)
;   - executable       : parrot.exe
;   - registry         : HKLM\SOFTWARE\Clients\StartMenuInternet\Parrot Browser\shell\open\command
;                        (64-bit registry view; default value contains the path to parrot.exe)
; Required defines (makensis -D...): PKG_VERSION, PKG_DIR, OUT_FILE
; Optional defines: ICON_FILE, VC_REDIST, UPDATER_DIR (adds the optional WinUpdater component),
;                   VERSION_NUM (a.b.c.d for the file properties), EST_SIZE_KB

Unicode true
ManifestSupportedOS Win10

!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "x64.nsh"
!include "WinVer.nsh"

!ifndef PKG_VERSION
  !error "PKG_VERSION is required (makensis -DPKG_VERSION=...)"
!endif
!ifndef PKG_DIR
  !error "PKG_DIR is required (makensis -DPKG_DIR=<folder containing parrot.exe>)"
!endif
!ifndef OUT_FILE
  !error "OUT_FILE is required (makensis -DOUT_FILE=<setup.exe>)"
!endif
!ifndef EST_SIZE_KB
  !define EST_SIZE_KB 300000
!endif

!define APPNAME "Parrot Browser"
!define PROGNAME "parrot"
!define EXECUTABLE "${PROGNAME}.exe"
!define COMPANYNAME "Parrot"
!define UPDATER_EXE "Parrot-WinUpdater.exe"
!define UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"
!define CLIENT_KEY "Software\Clients\StartMenuInternet\${APPNAME}"
!define PROGID "ParrotHTM"

Name "${APPNAME}"
OutFile "${OUT_FILE}"
InstallDir "$PROGRAMFILES64\${APPNAME}"
RequestExecutionLevel admin
SetCompressor /SOLID lzma

!ifdef VERSION_NUM
  VIProductVersion "${VERSION_NUM}"
  VIFileVersion "${VERSION_NUM}"
  VIAddVersionKey "ProductName" "${APPNAME}"
  VIAddVersionKey "FileDescription" "${APPNAME} Setup"
  VIAddVersionKey "ProductVersion" "${PKG_VERSION}"
  VIAddVersionKey "FileVersion" "${PKG_VERSION}"
  VIAddVersionKey "CompanyName" "${COMPANYNAME}"
  VIAddVersionKey "LegalCopyright" "${APPNAME} contributors"
!endif

!ifdef ICON_FILE
  !define MUI_ICON "${ICON_FILE}"
  !define MUI_UNICON "${ICON_FILE}"
!endif
!define MUI_ABORTWARNING

!define MUI_WELCOMEPAGE_TITLE "Welcome to the ${APPNAME} Setup"
!define MUI_WELCOMEPAGE_TEXT "This setup will guide you through the installation of ${APPNAME} ${PKG_VERSION}.$\r$\n$\r$\nClick Next to continue."

!define MUI_FINISHPAGE_RUN
!define MUI_FINISHPAGE_RUN_TEXT "Create desktop shortcut"
!define MUI_FINISHPAGE_RUN_FUNCTION "CreateDesktopShortcut"
!define MUI_FINISHPAGE_RUN_NOTCHECKED
!define MUI_COMPONENTSPAGE_SMALLDESC

!insertmacro MUI_PAGE_WELCOME
!ifdef UPDATER_DIR
  !insertmacro MUI_PAGE_COMPONENTS
!endif
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

; ---------------------------------------------------------------------------------------------
; parrot.exe is locked while the browser runs, so a failed rename of it means "still running".
; Result in $0: 1 = locked/running, 0 = free. (Defined twice: installer and uninstaller.)
!macro DEFINE_LOCK_CHECK un
Function ${un}IsBrowserLocked
  StrCpy $0 0
  ${If} ${FileExists} "$INSTDIR\${EXECUTABLE}"
    ClearErrors
    Rename "$INSTDIR\${EXECUTABLE}" "$INSTDIR\${EXECUTABLE}.lockcheck"
    ${If} ${Errors}
      StrCpy $0 1
    ${Else}
      Rename "$INSTDIR\${EXECUTABLE}.lockcheck" "$INSTDIR\${EXECUTABLE}"
    ${EndIf}
  ${EndIf}
FunctionEnd
!macroend
!insertmacro DEFINE_LOCK_CHECK ""
!insertmacro DEFINE_LOCK_CHECK "un."

Function EnsureNotRunning
  Call IsBrowserLocked
  ${If} $0 = 0
    Return
  ${EndIf}

  IfSilent 0 +4
    DetailPrint "${APPNAME} is still running, aborting because of silent install."
    SetErrorLevel 2
    Abort

  MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION "${APPNAME} is still running and has to be closed for the setup to continue.$\r$\n$\r$\nClick OK to close it now." IDOK +3
    SetErrorLevel 1
    Abort

  DetailPrint "Closing ${APPNAME}..."
  nsExec::ExecToLog 'taskkill /IM ${EXECUTABLE}'
  Sleep 3000
  Call IsBrowserLocked
  ${If} $0 = 1
    DetailPrint "${APPNAME} did not close, forcing it to quit..."
    nsExec::ExecToLog 'taskkill /F /IM ${EXECUTABLE}'
    Sleep 2000
    Call IsBrowserLocked
    ${If} $0 = 1
      MessageBox MB_ICONSTOP "${APPNAME} is still running and cannot be closed by the setup. Please close it manually and try again."
      SetErrorLevel 2
      Abort
    ${EndIf}
  ${EndIf}
FunctionEnd

; ---------------------------------------------------------------------------------------------
Section "${APPNAME}" main
  SectionIn RO
  SetRegView 64
  SetShellVarContext all

  Call EnsureNotRunning

!ifdef VC_REDIST
  ; Visual C++ runtime (no-op when a newer one is installed: exit code 1638; 3010 = reboot suggested)
  InitPluginsDir
  File "/oname=$PLUGINSDIR\vc_redist.x64.exe" "${VC_REDIST}"
  DetailPrint "Installing Visual C++ Redistributable..."
  ExecWait '"$PLUGINSDIR\vc_redist.x64.exe" /install /quiet /norestart' $0
  DetailPrint "Visual C++ Redistributable finished (exit code $0)"
!endif

  SetOutPath "$INSTDIR"
  SetOverwrite on
  File /r "${PKG_DIR}/*.*"

  ; Start menu
  CreateDirectory "$SMPROGRAMS\${APPNAME}"
  CreateShortCut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\${EXECUTABLE}" "" "$INSTDIR\${EXECUTABLE}" 0
  CreateShortCut "$SMPROGRAMS\${APPNAME}\Uninstall.lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\uninstall.exe" 0

  WriteUninstaller "$INSTDIR\uninstall.exe"

  ; Add/Remove Programs
  WriteRegStr HKLM "${UNINST_KEY}" "DisplayName" "${APPNAME}"
  WriteRegStr HKLM "${UNINST_KEY}" "DisplayVersion" "${PKG_VERSION}"
  WriteRegStr HKLM "${UNINST_KEY}" "Publisher" "${COMPANYNAME}"
  WriteRegStr HKLM "${UNINST_KEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKLM "${UNINST_KEY}" "DisplayIcon" "$INSTDIR\${EXECUTABLE},0"
  WriteRegStr HKLM "${UNINST_KEY}" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegStr HKLM "${UNINST_KEY}" "QuietUninstallString" '"$INSTDIR\uninstall.exe" /S'
  WriteRegDWORD HKLM "${UNINST_KEY}" "NoModify" 1
  WriteRegDWORD HKLM "${UNINST_KEY}" "NoRepair" 1
  WriteRegDWORD HKLM "${UNINST_KEY}" "EstimatedSize" ${EST_SIZE_KB}

  ; Windows default-browser integration
  WriteRegStr HKLM "${CLIENT_KEY}" "" "${APPNAME}"
  WriteRegStr HKLM "${CLIENT_KEY}\Capabilities" "ApplicationName" "${APPNAME}"
  WriteRegStr HKLM "${CLIENT_KEY}\Capabilities" "ApplicationDescription" "${APPNAME}"
  WriteRegStr HKLM "${CLIENT_KEY}\Capabilities" "ApplicationIcon" "$INSTDIR\${EXECUTABLE},0"
  WriteRegStr HKLM "${CLIENT_KEY}\Capabilities\FileAssociations" ".htm" "${PROGID}"
  WriteRegStr HKLM "${CLIENT_KEY}\Capabilities\FileAssociations" ".html" "${PROGID}"
  WriteRegStr HKLM "${CLIENT_KEY}\Capabilities\FileAssociations" ".pdf" "${PROGID}"
  WriteRegStr HKLM "${CLIENT_KEY}\Capabilities\Startmenu" "StartMenuInternet" "${APPNAME}"
  WriteRegStr HKLM "${CLIENT_KEY}\Capabilities\URLAssociations" "http" "${PROGID}"
  WriteRegStr HKLM "${CLIENT_KEY}\Capabilities\URLAssociations" "https" "${PROGID}"
  WriteRegStr HKLM "${CLIENT_KEY}\DefaultIcon" "" "$INSTDIR\${EXECUTABLE},0"
  ; Parrot-WinUpdater reads this value (it must contain parrot.exe)
  WriteRegStr HKLM "${CLIENT_KEY}\shell\open\command" "" "$INSTDIR\${EXECUTABLE}"
  WriteRegStr HKLM "Software\RegisteredApplications" "${APPNAME}" "${CLIENT_KEY}\Capabilities"

  WriteRegStr HKLM "Software\Classes\${PROGID}" "" "${APPNAME} Handler"
  WriteRegStr HKLM "Software\Classes\${PROGID}" "AppUserModelId" "${COMPANYNAME}"
  WriteRegStr HKLM "Software\Classes\${PROGID}\Application" "AppUserModelId" "${COMPANYNAME}"
  WriteRegStr HKLM "Software\Classes\${PROGID}\Application" "ApplicationIcon" "$INSTDIR\${EXECUTABLE},0"
  WriteRegStr HKLM "Software\Classes\${PROGID}\Application" "ApplicationName" "${APPNAME}"
  WriteRegStr HKLM "Software\Classes\${PROGID}\Application" "ApplicationDescription" "Start ${APPNAME}"
  WriteRegStr HKLM "Software\Classes\${PROGID}\Application" "ApplicationCompany" "${COMPANYNAME}"
  WriteRegStr HKLM "Software\Classes\${PROGID}\DefaultIcon" "" "$INSTDIR\${EXECUTABLE},0"
  WriteRegStr HKLM "Software\Classes\${PROGID}\shell\open\command" "" '"$INSTDIR\${EXECUTABLE}" -osint -url "%1"'
SectionEnd

!ifdef UPDATER_DIR
Section /o "Parrot WinUpdater" winupdater
  SetRegView 64
  SetShellVarContext all
  SetOutPath "$INSTDIR"
  File "${UPDATER_DIR}/${UPDATER_EXE}"
  File "${UPDATER_DIR}/ScheduledTask-Create.ps1"
  File "${UPDATER_DIR}/ScheduledTask-Remove.ps1"
  CreateShortCut "$SMPROGRAMS\${APPNAME}\Parrot WinUpdater.lnk" "$INSTDIR\${UPDATER_EXE}" "" "$INSTDIR\${UPDATER_EXE}" 0
SectionEnd

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${main} "Install the browser for all users"
  !insertmacro MUI_DESCRIPTION_TEXT ${winupdater} "A companion tool to update ${APPNAME} with a single click"
!insertmacro MUI_FUNCTION_DESCRIPTION_END
!endif

; ---------------------------------------------------------------------------------------------
Function .onInit
  ${IfNot} ${RunningX64}
    MessageBox MB_ICONSTOP "${APPNAME} requires a 64-bit version of Windows."
    Abort
  ${EndIf}
  ${IfNot} ${AtLeastWin10}
    MessageBox MB_ICONSTOP "${APPNAME} requires Windows 10 or newer."
    Abort
  ${EndIf}

  SetRegView 64
  ; Keep the existing install location on updates, but never override an explicit /D=
  ReadRegStr $0 HKLM "${UNINST_KEY}" "InstallLocation"
  ${If} $0 != ""
  ${AndIf} $INSTDIR == "$PROGRAMFILES64\${APPNAME}"
    StrCpy $INSTDIR $0
  ${EndIf}

!ifdef UPDATER_DIR
  ; Pre-select WinUpdater when it is already installed
  ${If} ${FileExists} "$INSTDIR\${UPDATER_EXE}"
    SectionSetFlags ${winupdater} ${SF_SELECTED}
  ${EndIf}
!endif
FunctionEnd

Function CreateDesktopShortcut
  SetShellVarContext all
  CreateShortCut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\${EXECUTABLE}" "" "$INSTDIR\${EXECUTABLE}" 0
FunctionEnd

; ---------------------------------------------------------------------------------------------
Function un.onInit
  SetRegView 64
FunctionEnd

Section "Uninstall"
  SetRegView 64
  SetShellVarContext all

  Call un.IsBrowserLocked
  ${If} $0 = 1
    DetailPrint "${APPNAME} is still running, closing it..."
    nsExec::ExecToLog 'taskkill /F /IM ${EXECUTABLE}'
    Sleep 2000
  ${EndIf}

  RMDir /r "$SMPROGRAMS\${APPNAME}"
  Delete "$DESKTOP\${APPNAME}.lnk"

  ; Only delete the folder recursively when it really is a Parrot install and not a system folder
  StrCpy $R0 0
  ${If} ${FileExists} "$INSTDIR\${EXECUTABLE}"
    StrCpy $R0 1
  ${ElseIf} ${FileExists} "$INSTDIR\application.ini"
    StrCpy $R0 1
  ${EndIf}
  ${If} $INSTDIR == "$PROGRAMFILES64"
  ${OrIf} $INSTDIR == "$PROGRAMFILES"
  ${OrIf} $INSTDIR == "$WINDIR"
  ${OrIf} $INSTDIR == "$SYSDIR"
    StrCpy $R0 0
  ${EndIf}
  ${If} $R0 = 1
    RMDir /r "$INSTDIR"
  ${Else}
    DetailPrint "$INSTDIR does not look like a ${APPNAME} folder, only removing the uninstaller."
    Delete "$INSTDIR\uninstall.exe"
  ${EndIf}

  DeleteRegKey HKLM "${UNINST_KEY}"
  DeleteRegKey HKLM "${CLIENT_KEY}"
  DeleteRegValue HKLM "Software\RegisteredApplications" "${APPNAME}"
  DeleteRegKey HKLM "Software\Classes\${PROGID}"

  ; WinUpdater leftovers: per-user data and scheduled tasks
  DetailPrint "Removing WinUpdater data and scheduled tasks"
  SetShellVarContext current
  FindFirst $0 $1 "$PROFILE\..\*"
  loop:
    StrCmp $1 "" done
    RMDir /r "$PROFILE\..\$1\AppData\Roaming\${APPNAME}\WinUpdater"
    FindNext $0 $1
    Goto loop
  done:
  FindClose $0
  SetShellVarContext all
  nsExec::ExecToLog `powershell -NoProfile -Command "Get-ScheduledTask '${COMPANYNAME}*WinUpdater*' | Unregister-ScheduledTask -Confirm:$$false"`
SectionEnd
