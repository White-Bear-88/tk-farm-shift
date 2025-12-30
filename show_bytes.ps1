$b = [System.IO.File]::ReadAllBytes('C:\Users\hoops\tk-farm-shift\deploy.ps1')
for ($i=0; $i -lt [Math]::Min($b.Length,120); $i++) { Write-Host ("{0:X2}" -f $b[$i]) }
