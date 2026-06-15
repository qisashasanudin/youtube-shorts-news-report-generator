Get-ScheduledTask | Where-Object TaskName -like '*shorts-news*' | Select-Object TaskName, State, LastTaskResult | Format-Table -AutoSize
