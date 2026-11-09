Option Explicit

Dim shell, fso, scriptDir, entry, cmd, rc
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
entry = fso.BuildPath(scriptDir, "scheduled_entry.ps1")
cmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File """ & entry & """"

' 0 = hidden window; True = wait for completion so Scheduled Task gets the real exit code.
rc = shell.Run(cmd, 0, True)
WScript.Quit rc
