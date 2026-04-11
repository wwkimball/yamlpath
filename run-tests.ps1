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

    $RequirementsFile = "requirements/test-tools/python-$PyVersion.txt"
    if (-Not (Test-Path -Path $RequirementsFile -PathType Leaf)) {
        $SupportedPythons = Get-SupportedLanguageVersions -LanguagePrefix "python"
        Write-Warning "`nWARNING:  Python $PyVersion is not supported because required test-tool constraints are missing: $RequirementsFile"
        Write-Warning "HINT:  Supported Python branches for this test runner are: $SupportedPythons."
        return $null
    }

    return $RequirementsFile
}

function Get-SupportedLanguageVersions {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$LanguagePrefix
    )

    $Supported = Get-ChildItem -Path "requirements/test-tools" -Filter "$LanguagePrefix-*.txt" -File |
        ForEach-Object {
            if ($_.BaseName -match "^$LanguagePrefix-([0-9]+\.[0-9]+)$") {
                $Matches[1]
            }
        } |
        Sort-Object -Unique

    if (-Not $Supported) {
        return "none"
    }

    return ($Supported -join ", ")
}

function Get-RubyEyamlConstraintsFile {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$RubyVersion
    )

    $ConstraintsFile = "requirements/test-tools/ruby-$RubyVersion.txt"
    if (-Not (Test-Path -Path $ConstraintsFile -PathType Leaf)) {
        $SupportedRubies = Get-SupportedLanguageVersions -LanguagePrefix "ruby"
        Write-Warning "`nWARNING:  Ruby $RubyVersion is not supported because EYAML constraints are missing: $ConstraintsFile"
        if ($RubyVersion -eq "2.6") {
            Write-Warning "HINT:  Ruby 2.6 is commonly the macOS system Ruby on Apple workstations."
            Write-Warning "HINT:  For tests, install and prioritize a supported Ruby ($SupportedRubies) using tools like Homebrew, rbenv, or asdf."
        } else {
            Write-Warning "HINT:  Supported Ruby branches for this test runner are: $SupportedRubies."
        }
        return $null
    }

    return $ConstraintsFile
}

function Get-RubyEyamlGemVersionConstraint {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$ConstraintsFile
    )

    $Constraint = Get-Content -Path $ConstraintsFile |
        Where-Object { -Not [string]::IsNullOrWhiteSpace($_) -And -Not $_.TrimStart().StartsWith("#") } |
        Select-Object -First 1
    if ([string]::IsNullOrWhiteSpace($Constraint)) {
        Write-Error "`nERROR:  No EYAML gem version constraint was found in $ConstraintsFile!"
        return $null
    }

    return $Constraint.Trim()
}

function Invoke-CleanupTestEnvironment {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$false)]
        [string]$TmpVEnvPath,

        [Parameter(Mandatory=$false)]
        [string]$TmpGemHomePath,

        [Parameter(Mandatory=$true)]
        [string]$OriginalPath
    )

    if (Get-Command deactivate -ErrorAction SilentlyContinue) {
        & deactivate
    }

    if (-Not [string]::IsNullOrEmpty($TmpVEnvPath) -And (Test-Path -Path $TmpVEnvPath -PathType Container)) {
        Remove-Item -Recurse -Force $TmpVEnvPath
    }

    if (-Not [string]::IsNullOrEmpty($TmpGemHomePath) -And (Test-Path -Path $TmpGemHomePath -PathType Container)) {
        Remove-Item -Recurse -Force $TmpGemHomePath
    }

    $env:PATH = $OriginalPath
    Remove-Item Env:GEM_HOME -ErrorAction SilentlyContinue
    Remove-Item Env:GEM_PATH -ErrorAction SilentlyContinue
}

$EnvDirs = Get-ChildItem -Directory -Filter "venv*"
ForEach ($EnvDir in $EnvDirs) {
    $OriginalPath = $env:PATH
    $TmpGemHome = $null

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
    if (-Not (Get-Command ruby -ErrorAction SilentlyContinue)) {
        & deactivate
        Write-Warning "`nWARNING:  Unable to find a Ruby binary named, ruby!"
        continue
    }
    $RubyVersionOutput = ruby --version
    $RubyVersionMatch = [regex]::Match($RubyVersionOutput, "([0-9]+\.[0-9]+)\.[0-9]+")
    if (-Not $RubyVersionMatch.Success) {
        & deactivate
        Write-Warning "`nWARNING:  Unable to determine the Ruby major.minor version from: $RubyVersionOutput"
        continue
    }
    $RubyMajorMinor = $RubyVersionMatch.Groups[1].Value
    $RubyConstraintsFile = Get-RubyEyamlConstraintsFile -RubyVersion $RubyMajorMinor
    if ([string]::IsNullOrWhiteSpace($RubyConstraintsFile)) {
        & deactivate
        continue
    }
    $EyamlGemConstraint = Get-RubyEyamlGemVersionConstraint -ConstraintsFile $RubyConstraintsFile
    if ([string]::IsNullOrWhiteSpace($EyamlGemConstraint)) {
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
        Invoke-CleanupTestEnvironment -TmpVEnvPath $TmpVEnv.FullName -TmpGemHomePath $null -OriginalPath $OriginalPath
        Write-Error "`nERROR:  Unable to install pinned testing tools from $RequirementsFile!"
        exit 122
    }

    Write-Output "...installing isolated EYAML Ruby Gem constrained by $RubyConstraintsFile"
    if (-Not (Get-Command gem -ErrorAction SilentlyContinue)) {
        Invoke-CleanupTestEnvironment -TmpVEnvPath $TmpVEnv.FullName -TmpGemHomePath $null -OriginalPath $OriginalPath
        Write-Error "`nERROR:  Unable to find the Ruby Gem tool, 'gem'!"
        exit 121
    }
    $TmpGemHome = New-TemporaryDirectory
    $env:GEM_HOME = $TmpGemHome.FullName
    $env:GEM_PATH = $TmpGemHome.FullName
    $env:PATH = "$($TmpGemHome.FullName)$([System.IO.Path]::PathSeparator)$($env:PATH)"
    gem install --no-document hiera-eyaml -v $EyamlGemConstraint | Out-String
    if (!$?) {
        Invoke-CleanupTestEnvironment -TmpVEnvPath $TmpVEnv.FullName -TmpGemHomePath $TmpGemHome.FullName -OriginalPath $OriginalPath
        Write-Error "`nERROR:  Unable to install hiera-eyaml $EyamlGemConstraint into $($TmpGemHome.FullName)!"
        exit 123
    }
    if (-Not (Get-Command eyaml -ErrorAction SilentlyContinue)) {
        Invoke-CleanupTestEnvironment -TmpVEnvPath $TmpVEnv.FullName -TmpGemHomePath $TmpGemHome.FullName -OriginalPath $OriginalPath
        Write-Error "`nERROR:  The isolated EYAML binary was not found on PATH after installation!"
        exit 120
    }

    Write-Output "`nPYDOCSTYLE..."
    pydocstyle yamlpath | Out-String
    if (!$?) {
        Invoke-CleanupTestEnvironment -TmpVEnvPath $TmpVEnv.FullName -TmpGemHomePath $TmpGemHome.FullName -OriginalPath $OriginalPath
        Write-Error "PYDOCSTYLE Error: $?"
        exit 9
    }

    Write-Output "`nMYPY..."
    mypy yamlpath | Out-String
    if (!$?) {
        Invoke-CleanupTestEnvironment -TmpVEnvPath $TmpVEnv.FullName -TmpGemHomePath $TmpGemHome.FullName -OriginalPath $OriginalPath
        Write-Error "MYPY Error: $?"
        exit 10
    }

    Write-Output "`nPYRIGHT..."
    pyright | Out-String
    if (!$?) {
        Invoke-CleanupTestEnvironment -TmpVEnvPath $TmpVEnv.FullName -TmpGemHomePath $TmpGemHome.FullName -OriginalPath $OriginalPath
        Write-Error "PYRIGHT Error: $?"
        exit 13
    }

    Write-Output "`nPYLINT..."
    pylint yamlpath | Out-String
    if (!$?) {
        Invoke-CleanupTestEnvironment -TmpVEnvPath $TmpVEnv.FullName -TmpGemHomePath $TmpGemHome.FullName -OriginalPath $OriginalPath
        Write-Error "PYLINT Error: $?"
        exit 11
    }

    Write-Output "`n PYTEST..."
    pytest -vv --cov=yamlpath --cov-report=term-missing --cov-fail-under=100 --script-launch-mode=subprocess tests
    if (!$?) {
        Invoke-CleanupTestEnvironment -TmpVEnvPath $TmpVEnv.FullName -TmpGemHomePath $TmpGemHome.FullName -OriginalPath $OriginalPath
        Write-Error "PYTEST Error: $?"
        exit 12
    }

    Write-Output "Deactivating virtual Python environment..."
    Invoke-CleanupTestEnvironment -TmpVEnvPath $TmpVEnv.FullName -TmpGemHomePath $TmpGemHome.FullName -OriginalPath $OriginalPath
}
