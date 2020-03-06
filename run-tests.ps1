$HasTestsDir = Test-Path -Path tests -PathType Container
$HasProjectDir = Test-Path -Path yamlpath -PathType Container
if (-Not $HasTestsDir -Or -Not $HasProjectDir) {
    Write-Error "Please start this script only from within the top directory of the YAML Path project."
    exit 2
}

$EnvDirs = Get-ChildItem -Directory -Filter "env*"
ForEach ($EnvDir in $EnvDirs) {
    & "$($EnvDir.FullName)\Scripts\Activate.ps1"
    if (!$?) {
        Write-Error "`nERROR:  Unable to activate $EnvDir!"
        exit 20
    }

    $PythonVersion = $(python --version)
    Write-Output @"

        =========================================================================
        Using Python $PythonVersion...
        =========================================================================
"@

    Write-Output "...upgrading pip"
    python -m pip install --upgrade pip
    Write-Output "...reinstalling ruamel.yaml (because pip upgrades break it)"
    pip install --force-reinstall ruamel.yaml==0.15.96
    Write-Output "...upgrading testing tools"
    pip install --upgrade mypy pytest pytest-cov pytest-console-scripts pylint coveralls
    Write-Output "...installing self"
    pip install -e .

    Write-Output "`nMYPY..."
    mypy yamlpath | Out-String
    if (!$?) {
        Write-Error "MYPY Error: $?"
        exit 10
    }

    Write-Output "`nPYLINT..."
    pylint yamlpath | Out-String
    if (!$?) {
        Write-Error "PYLINT Error: $?"
        exit 11
    }

    Write-Output "`n PYTEST..."
    pytest -vv --cov=yamlpath --cov-report=term-missing --cov-fail-under=100 --script-launch-mode=subprocess tests
    if (!$?) {
        Write-Error "PYTEST Error: $?"
        exit 12
    }
}

Write-Output "Deactivating virtual Python environment..."
& deactivate
