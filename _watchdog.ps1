Get-ScheduledTask |
  Where-Object { $_.TaskName -like '*shorts*' -or $_.TaskName -like '*MashButton*' -or $_.TaskName -like '*youtube*' -or $_.TaskName -like '*upload*' -or $_.TaskName -like '*scheduler*' } |
  Format-List TaskName, State, LastRunTime, NextRunTime
