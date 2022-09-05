get-childitem C:\Users\Jason\Downloads\jd-gui-windows-1.6.6\classes.jar.src -file -Recurse | ForEach-Object {
    if ($hi = get-content $_.FullName | select-string 'https' -List) {
        $hi
    }
}