$base = 'c:\Users\mulug\OneDrive\Desktop\end\pro'
$names = @('dashboard.py', 'addis_ababa_dashboard.py', 'kifle_ketema_dashboard.py', 'wereda_dashboard.py')
foreach ($name in $names) {
    $p = Join-Path $base $name
    if (Test-Path $p) {
        $c = (Get-Content $p -Raw) -replace 'LEARNIX', 'LIQ' -replace 'Learnix', 'liq'
        Set-Content $p $c -NoNewline
        Write-Output "Done: $name"
    } else {
        Write-Output "Not found: $name"
    }
}
