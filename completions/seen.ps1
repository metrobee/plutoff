# PowerShell completion for seen (Windows)
Register-ArgumentCompleter -Native -CommandName seen, plutoff -ScriptBlock {
    param($wordToComplete, $commandAst, $cursorPosition)

    $subOptions = @('kuusk', 'mänd', 'kask', 'sookask', 'haab', 'lepp', 'sanglepp', 'tamm', 'saar', 'vaher', 'sarapuu', 'pärn')
    $tyypOptions = @('lamatüvi', 'känd', 'tüügas', 'lamaoks', 'elavpuu', 'kõdupuit', 'kõdu', 'okkad', 'lehed', 'muld')
    $ohtrusOptions = @('üksikud', 'vähe', 'mõõdukalt', 'sage', 'palju', 'massiliselt')

    if ($wordToComplete -like "sub:*") {
        $prefix = "sub:"
        $term = $wordToComplete.Substring(4)
        $subOptions | Where-Object { $_ -like "$term*" } | ForEach-Object {
            [System.Management.Automation.CompletionResult]::new("$prefix$_", "$prefix$_", 'ParameterValue', "Substraat: $_")
        }
        return
    }

    if ($wordToComplete -like "tyyp:*" -or $wordToComplete -like "tüüp:*") {
        $pfx = if ($wordToComplete -like "tyyp:*") { "tyyp:" } else { "tüüp:" }
        $term = $wordToComplete.Substring($pfx.Length)
        $tyypOptions | Where-Object { $_ -like "$term*" } | ForEach-Object {
            [System.Management.Automation.CompletionResult]::new("$pfx$_", "$pfx$_", 'ParameterValue', "Tüüp: $_")
        }
        return
    }

    if ($wordToComplete -like "ohtrus:*") {
        $prefix = "ohtrus:"
        $term = $wordToComplete.Substring(7)
        $ohtrusOptions | Where-Object { $_ -like "$term*" } | ForEach-Object {
            [System.Management.Automation.CompletionResult]::new("$prefix$_", "$prefix$_", 'ParameterValue', "Ohtrus: $_")
        }
        return
    }

    $allFlags = @('sub:', 'tyyp:', 'tüüp:', 'ohtrus:', 'märkus:', '--help', '--list', '--sync', '--force', '--keep')
    $allFlags | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
        [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterName', $_)
    }
}
