!define APPNAME "Wind Data Insight Pro"
!define COMPANYNAME "Tata Consultancy Engineering Pvt Ltd"
!define DESCRIPTION "Professional wind turbine data analysis platform"
!define DEVELOPER "Mr. Nigam"
!define HELPURL "https://www.tce.co.in"
!define VERSIONMAJOR 1
!define VERSIONMINOR 0
!define VERSIONBUILD 0
!define APPNAMENOSP "Wind-Data-Insight-Pro"

InstallDir "$PROGRAMFILES64\${COMPANYNAME}\${APPNAME}"

Name "${APPNAME}"
OutFile "${APPNAMENOSP}-Setup.exe"

!include LogicLib.nsh
!include MUI2.nsh

!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"
!define MUI_WELCOMEPAGE_TITLE "Welcome to ${APPNAME} Setup"
!define MUI_WELCOMEPAGE_TEXT "This wizard will install ${APPNAME}.$\r$\n$\r$\nDeveloped by ${COMPANYNAME}$\r$\n$\r$\nClick Next to continue."
!define MUI_FINISHPAGE_RUN "$INSTDIR\${APPNAMENOSP}.exe"
!define MUI_FINISHPAGE_RUN_TEXT "Launch ${APPNAME}"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

VIProductVersion "${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}.0"
VIAddVersionKey "ProductName" "${APPNAME}"
VIAddVersionKey "CompanyName" "${COMPANYNAME}"
VIAddVersionKey "FileDescription" "${DESCRIPTION}"
VIAddVersionKey "FileVersion" "${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}.0"
VIAddVersionKey "LegalCopyright" "© ${COMPANYNAME}"

Section "Install"
    SetOutPath $INSTDIR
    
    ; Copy main executable
    File "dist\${APPNAMENOSP}.exe"
    
    ; Copy icon files for file associations
    SetOutPath "$INSTDIR\resources\app_icon"
    File "resources\app_icon\wwip_file.ico"
    File "resources\app_icon\wwip_file.ico"
    
    ; Create uninstaller
    SetOutPath $INSTDIR
    WriteUninstaller "$INSTDIR\uninstall.exe"
    
    ; Create Start Menu shortcuts
    CreateDirectory "$SMPROGRAMS\${COMPANYNAME}"
    CreateShortcut "$SMPROGRAMS\${COMPANYNAME}\${APPNAME}.lnk" "$INSTDIR\${APPNAMENOSP}.exe" "" "$INSTDIR\resources\app_icon\wwip_file.ico" 0
    CreateShortcut "$SMPROGRAMS\${COMPANYNAME}\Uninstall ${APPNAME}.lnk" "$INSTDIR\uninstall.exe"
    
    ; Register file association for .wdip files
    WriteRegStr HKCR ".wdip" "" "WindDataInsightPro.Project"
    WriteRegStr HKCR "WindDataInsightPro.Project" "" "Wind Data Insight Pro Project"
    WriteRegStr HKCR "WindDataInsightPro.Project\DefaultIcon" "" "$INSTDIR\resources\app_icon\wwip_file.ico,0"
    WriteRegStr HKCR "WindDataInsightPro.Project\shell\open\command" "" '"$INSTDIR\${APPNAMENOSP}.exe" --project "%1"'
    
    ; Add to Windows registry for uninstall
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "DisplayName" "${APPNAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "Publisher" "${COMPANYNAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "UninstallString" "$\"$INSTDIR\uninstall.exe$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "DisplayIcon" "$\"$INSTDIR\resources\app_icon\wwip_file.ico$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "DisplayVersion" "${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "InstallLocation" "$INSTDIR"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "NoRepair" 1
    
    ; Notify Windows of file association changes
    System::Call 'shell32.dll::SHChangeNotify(i, i, i, i) v (0x08000000, 0, 0, 0)'
    
    DetailPrint "Installation completed successfully!"
SectionEnd

Function CreateDesktopShortcut
    CreateShortcut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\${APPNAMENOSP}.exe" "" "$INSTDIR\resources\app_icon\wwip_file.ico" 0
FunctionEnd

Section "Uninstall"
    ; Remove files
    Delete "$INSTDIR\${APPNAMENOSP}.exe"
    Delete "$INSTDIR\uninstall.exe"
    Delete "$INSTDIR\resources\app_icon\wwip_file.ico"
    Delete "$INSTDIR\resources\app_icon\wwip_file.ico"
    RMDir "$INSTDIR\resources\app_icon"
    RMDir "$INSTDIR\resources"
    RMDir "$INSTDIR"
    
    ; Remove shortcuts
    Delete "$SMPROGRAMS\${COMPANYNAME}\${APPNAME}.lnk"
    Delete "$SMPROGRAMS\${COMPANYNAME}\Uninstall ${APPNAME}.lnk"
    Delete "$DESKTOP\${APPNAME}.lnk"
    RMDir "$SMPROGRAMS\${COMPANYNAME}"
    
    ; Remove file associations
    DeleteRegKey HKCR ".wdip"
    DeleteRegKey HKCR "WindDataInsightPro.Project"
    
    ; Remove registry entries
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}"
    
    ; Notify Windows of changes
    System::Call 'shell32.dll::SHChangeNotify(i, i, i, i) v (0x08000000, 0, 0, 0)'
    
    MessageBox MB_OK "Uninstallation completed successfully!"
SectionEnd
