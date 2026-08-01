' run_agent_hidden.vbs
'
' Launches the Client Agent with pythonw.exe so that NO console window
' ever appears, and no window flashes on screen even for a moment.
'
' EDIT the two paths below before deploying:
'   1. Path to pythonw.exe (use pythonw, NOT python, to suppress the console)
'   2. Path to main_agent.py (module form is used so relative imports work)
'
' This file is intended to be triggered by Windows Task Scheduler at
' user logon (see README.md for the exact steps). It can also be placed
' directly in the Startup folder if you prefer that over Task Scheduler.

Set objShell = CreateObject("WScript.Shell")

' Dynamically resolves to the current user's AppData folder, regardless of their username or spaces in the name
localAppData = objShell.ExpandEnvironmentStrings("%LOCALAPPDATA%")

' Wraps the path in quotes to safely handle spaces in usernames
pythonwPath = """" & localAppData & "\Programs\Python\Python313\pythonw.exe"""

' The global deployment directory (must be created on all target machines)
scriptDir   = "C:\WallpaperFleetManager\wallpaper-fleet-manager"

command     = pythonwPath & " -m client.main_agent"

objShell.CurrentDirectory = scriptDir

' 0 = Hidden Window, False = Do not wait for script to finish
objShell.Run command, 0, False