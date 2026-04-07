$HasTestsDir = Test-Path -Path tests -PathType Container
$HasProjectDir = Test-Path -Path yamlpath -PathType Container
if (-Not $HasTestsDir -Or -Not $HasProjectDir) {
    Write-Error "Please start this script only from within the top directory of the YAML Path project."
    exit 2
}

# Credit: https://stackoverflow.com/a/54935264
function New-TemporaryDirectory {
    [CmdletBinding(SupportsShouldProcess = $true)]
    param()
    $parent = [System.IO.Path]::GetTempPath()
    do {
        $name = [System.IO.Path]::GetRandomFileName()
        $item = New-Item -Path $parent -Name $name -ItemType "directory" -ErrorAction SilentlyContinue
    } while (-not $item)
    return $Item
}

function Get-TestToolsRequirementsFile {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$PyVersion
    )

    $VersionDigits = $PyVersion -replace "\."
    $RequirementsFile = "requirements/test-tools/py$VersionDigits.txt"
    if (-Not (Test-Path -Path $RequirementsFile -PathType Leaf)) {
        Write-Warning "`nWARNING:  Python $PyVersion is not supported because required test-tool constraints are missing: $RequirementsFile"
        return $null
    }

    return $RequirementsFile
}

$EnvDirs = Get-ChildItem -Directory -Filter "venv*"
ForEach ($EnvDir in $EnvDirs) {
    & "$($EnvDir.FullName)\Scripts\Activate.ps1"
    if (!$?) {
        Write-Error "`nERROR:  Unable to activate $EnvDir!"
        continue
    }

    $PythonVersion = $(python --version)
    $PyVersionMatch = [regex]::Match($PythonVersion, "([0-9]+\.[0-9]+)\.[0-9]+")
    if (-Not $PyVersionMatch.Success) {
        & deactivate
        Write-Error "`nERROR:  Unable to parse Python version from: $PythonVersion"
        continue
    }

    $PyMajorMinor = $PyVersionMatch.Groups[1].Value
    $RequirementsFile = Get-TestToolsRequirementsFile -PyVersion $PyMajorMinor
    if ([string]::IsNullOrEmpty($RequirementsFile)) {
        & deactivate
        continue
    }
    Write-Output @"

        =========================================================================
        Using Python $PythonVersion...
        =========================================================================
"@

    Write-Output "...spawning a new temporary Virtual Environment..."
    $TmpVEnv = New-TemporaryDirectory
    python -m venv $TmpVEnv
    if (!$?) {
        Write-Error "`nERROR:  Unable to spawn a new temporary virtual environment at $TmpVEnv!"
        exit 125
    }
    & deactivate
    & "$($TmpVEnv.FullName)\Scripts\Activate.ps1"
    if (!$?) {
        Write-Error "`nERROR:  Unable to activate $TmpVEnv!"
        continue
    }

    Write-Output "...upgrading pip"
    python -m pip install --upgrade pip

    Write-Output "...upgrading setuptools"
    pip install --upgrade setuptools

    Write-Output "...upgrading wheel"
    pip install --upgrade wheel

    Write-Output "...installing self"
    pip install --editable .
    if (!$?) {
        & deactivate
        Remove-Item -Recurse -Force $TmpVEnv
        Write-Error "`nERROR:  Unable to install self!"
        exit 124
    }

    Write-Output "...installing pinned testing tools from $RequirementsFile"
    pip install -r $RequirementsFile
    if (!$?) {
        & deactivate
        Remove-Item -Recurse -Force $TmpVEnv
        Write-Error "`nERROR:  Unable to install pinned testing tools from $RequirementsFile!"
        exit 122
    }

    Write-Output "`nPYDOCSTYLE..."
    pydocstyle yamlpath | Out-String
    if (!$?) {
        & deactivate
        Remove-Item -Recurse -Force $TmpVEnv
        Write-Error "PYDOCSTYLE Error: $?"
        exit 9
    }

    Write-Output "`nMYPY..."
    mypy yamlpath | Out-String
    if (!$?) {
        & deactivate
        Remove-Item -Recurse -Force $TmpVEnv
        Write-Error "MYPY Error: $?"
        exit 10
    }

    Write-Output "`nPYLINT..."
    pylint yamlpath | Out-String
    if (!$?) {
        & deactivate
        Remove-Item -Recurse -Force $TmpVEnv
        Write-Error "PYLINT Error: $?"
        exit 11
    }

    Write-Output "`n PYTEST..."
    pytest -vv --cov=yamlpath --cov-report=term-missing --cov-fail-under=100 --script-launch-mode=subprocess tests
    if (!$?) {
        & deactivate
        Remove-Item -Recurse -Force $TmpVEnv
        Write-Error "PYTEST Error: $?"
        exit 12
    }

    Write-Output "Deactivating virtual Python environment..."
    & deactivate
    Remove-Item -Recurse -Force $TmpVEnv
}
