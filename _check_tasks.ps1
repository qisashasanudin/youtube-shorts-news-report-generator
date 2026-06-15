Get-ScheduledTask |
  Where-Object {
    $_.TaskName -like '*shorts-news*' -or
    $_.TaskName -like '*MashButton*'
  } |
  Sort-Object TaskName |
  Format-List TaskName, State, LastRunTime, NextRunTime
