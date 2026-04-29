#!/usr/bin/env bash
################################################################################
# Run Python code quality tests against this project.
################################################################################
if ! [ -d tests -a -d yamlpath ]; then
	echo "Please start this script only from within the top directory of the YAML Path project." >&2
	exit 2
fi

if [ 1 -gt "$#" ]; then
	echo "You must specify at least one Python version.  Space-delimit multiples like: $0 3.10 3.11 3.12 3.13 3.14" >&2
	exit 2
fi

function resolveRequirementsFile {
	local python_version="$1"
	local requirements_file="requirements/test-tools/python-${python_version}.txt"
	local supported_pythons=""
	if ! [ -f "$requirements_file" ]; then
		supported_pythons=$(getSupportedVersions "python")
		echo -e "\nWARNING:  Python ${python_version} is not supported because required test-tool constraints are missing: ${requirements_file}" >&2
		echo "HINT:  Supported Python branches for this test runner are: ${supported_pythons}." >&2
		return 1
	fi

	echo "$requirements_file"
}

function getSupportedVersions {
	local language_prefix="$1"
	local requirement_file=""
	local joined=""
	local version=""
	local supported=()
	local sorted_supported=()

	for requirement_file in requirements/test-tools/${language_prefix}-*.txt; do
		if ! [ -f "$requirement_file" ]; then
			continue
		fi

		if [[ "${requirement_file##*/}" =~ ^${language_prefix}-([0-9]+\.[0-9]+)\.txt$ ]]; then
			supported+=("${BASH_REMATCH[1]}")
		fi
	done

	if [ 0 -eq "${#supported[@]}" ]; then
		echo "none"
		return 0
	fi

	while IFS= read -r version; do
		sorted_supported+=("$version")
	done < <(printf '%s\n' "${supported[@]}" | sort -uV)

	for version in "${sorted_supported[@]}"; do
		if [ -n "$joined" ]; then
			joined="${joined}, "
		fi
		joined="${joined}${version}"
	done

	echo "$joined"
}

function resolveRubyConstraintsFile {
	local ruby_version="$1"
	local constraints_file="requirements/test-tools/ruby-${ruby_version}.txt"
	local supported_rubies=""
	if ! [ -f "$constraints_file" ]; then
		supported_rubies=$(getSupportedVersions "ruby")
		echo -e "\nWARNING:  Ruby ${ruby_version} is not supported because its dependency file is missing: ${constraints_file}" >&2
		if [ "$ruby_version" = "2.6" ]; then
			echo "HINT:  Ruby 2.6 is commonly the macOS system Ruby on Apple workstations." >&2
			echo "HINT:  For tests, install and prioritize a supported Ruby (${supported_rubies}) using tools like Homebrew, rbenv, or asdf." >&2
		else
			echo "HINT:  Supported Ruby branches for this test runner are: ${supported_rubies}." >&2
		fi
		return 1
	fi

	echo "$constraints_file"
}

function cleanupTestEnvironment {
	local venv_dir="$1"
	local gem_home="$2"
	local original_path="$3"

	if which deactivate &>/dev/null; then
		deactivate
	fi

	if [ -n "$venv_dir" ]; then
		rm -rf "$venv_dir"
	fi

	if [ -n "$gem_home" ]; then
		rm -rf "$gem_home"
	fi

	unset GEM_HOME GEM_PATH
	PATH="$original_path"
}

# Delete all cached data
find ./ -name '__pycache__' -type d -print0 | xargs -0 rm -rf || exit $?
rm -rf yamlpath.egg-info
rm -rf /tmp/yamlpath-python-coverage-data
rm -f .coverage

for pythonVersion in "${@}"; do
	originalPath="$PATH"
	tmpGemHome=""

	if which deactivate &>/dev/null; then
		echo "Deactivating Python $(python --version).  If this dumps you right back to the shell prompt, you were running Microsoft's VSCode-embedded Python and were just put into a sub-shell; just exit to resume tests."
		deactivate
	fi

	pyCommand=python${pythonVersion}
	if ! which "$pyCommand" &>/dev/null; then
		echo -e "\nWARNING:  Unable to find a Python binary named, ${pyCommand}!" >&2
		continue
	fi
	pyVersion=$("$pyCommand" --version)
	if ! requirementsFile=$(resolveRequirementsFile "$pythonVersion"); then
		continue
	fi
	if ! which ruby &>/dev/null; then
		echo -e "\nWARNING:  Unable to find a Ruby binary named, ruby!" >&2
		continue
	fi
	rubyVersion=$(ruby --version | sed -E 's/.* ([0-9]+\.[0-9]+)\..*/\1/')
	if [ -z "$rubyVersion" ]; then
		echo -e "\nWARNING:  Unable to determine the Ruby major.minor version from: $(ruby --version)!" >&2
		continue
	fi
	if ! rubyConstraintsFile=$(resolveRubyConstraintsFile "$rubyVersion"); then
		continue
	fi

	cat <<-EOF

		=============================================================================
		Using Python ${pyVersion}...
		=============================================================================
EOF

	echo "...spawning a new temporary Virtual Environment..."
	tmpVEnv=$(mktemp -d -t yamlpath-$(date +%Y%m%dT%H%M%S)-XXXXXXXXXX)
	if ! "$pyCommand" -m venv "$tmpVEnv"; then
		rm -rf "$tmpVEnv"
		echo -e "\nERROR:  Unable to spawn a new temporary virtual environment at ${tmpVEnv}!" >&2
		exit 125
	fi
	if ! source "${tmpVEnv}/bin/activate"; then
		rm -rf "$tmpVEnv"
		echo -e "\nWARNING:  Unable to activate ${tmpVEnv}!" >&2
		continue
	fi

	echo "...upgrading pip"
	python -m pip install --no-cache-dir --upgrade pip >/dev/null

	echo "...upgrading setuptools"
	pip install --no-cache-dir --upgrade setuptools >/dev/null

	echo "...upgrading wheel"
	pip install --no-cache-dir --upgrade wheel >/dev/null

	echo "...installing self (editable because without it, pytest-cov cannot trace code execution!)"
	if ! pip install --no-cache-dir --editable . >/dev/null; then
		deactivate
		rm -rf "$tmpVEnv"
		echo -e "\nERROR:  Unable to install self!" >&2
		exit 124
	fi

	echo "...installing pinned testing tools from ${requirementsFile}"
	if ! pip install --no-cache-dir -r "${requirementsFile}" >/dev/null; then
		cleanupTestEnvironment "$tmpVEnv" "$tmpGemHome" "$originalPath"
		echo -e "\nERROR:  Unable to install pinned testing tools from ${requirementsFile}!" >&2
		exit 123
	fi

	echo "...installing isolated EYAML Ruby Gem constrained by ${rubyConstraintsFile}"
	if ! which gem &>/dev/null; then
		cleanupTestEnvironment "$tmpVEnv" "$tmpGemHome" "$originalPath"
		echo -e "\nERROR:  Unable to find the Ruby Gem tool, 'gem'!" >&2
		exit 121
	fi
	tmpGemHome=$(mktemp -d -t yamlpath-eyaml-gems-$(date +%Y%m%dT%H%M%S)-XXXXXXXXXX)
	export GEM_HOME="$tmpGemHome"
	export GEM_PATH="$GEM_HOME"
	export PATH="${GEM_HOME}/bin:${PATH}"
	if ! gem install \
		--no-document \
		--install-dir "$GEM_HOME" \
		--bindir "${GEM_HOME}/bin" \
		-g "$rubyConstraintsFile" \
		--no-lock \
	>/dev/null; then
		cleanupTestEnvironment "$tmpVEnv" "$tmpGemHome" "$originalPath"
		echo -e "\nERROR:  Unable to install EYAML via Ruby dependency file ${rubyConstraintsFile} into ${tmpGemHome}!" >&2
		exit 122
	fi
	if ! [ -x "${GEM_HOME}/bin/eyaml" ]; then
		cleanupTestEnvironment "$tmpVEnv" "$tmpGemHome" "$originalPath"
		echo -e "\nERROR:  Isolated EYAML executable was not installed to ${GEM_HOME}/bin/eyaml!" >&2
		exit 120
	fi
	if ! which eyaml &>/dev/null; then
		cleanupTestEnvironment "$tmpVEnv" "$tmpGemHome" "$originalPath"
		echo -e "\nERROR:  The isolated EYAML binary was not found on PATH after installation!" >&2
		exit 120
	fi

	echo -e "\nPYDOCSTYLE..."
	if ! pydocstyle yamlpath; then
		cleanupTestEnvironment "$tmpVEnv" "$tmpGemHome" "$originalPath"
		echo "PYDOCSTYLE Error: $?"
		exit 9
	fi

	echo -e "\nMYPY..."
	if ! mypy yamlpath; then
		cleanupTestEnvironment "$tmpVEnv" "$tmpGemHome" "$originalPath"
		echo "MYPY Error: $?"
		exit 10
	fi

	echo -e "\nPYRIGHT..."
	if ! pyright; then
		cleanupTestEnvironment "$tmpVEnv" "$tmpGemHome" "$originalPath"
		echo "PYRIGHT Error: $?"
		exit 13
	fi

	echo -e "\nPYLINT..."
	pylintRCFile="requirements/test-tools/pylintrc-python-${pythonVersion}.ini"
	if ! [ -f "$pylintRCFile" ]; then
		cleanupTestEnvironment "$tmpVEnv" "$tmpGemHome" "$originalPath"
		echo -e "\nERROR:  Pylint RC file not found:  ${pylintRCFile}" >&2
		exit 119
	fi
	if ! pylint \
			--rcfile="$pylintRCFile" \
			yamlpath
	then
		cleanupTestEnvironment "$tmpVEnv" "$tmpGemHome" "$originalPath"
		echo "PYLINT Error: $?"
		exit 11
	fi

	echo -e "\nPYTEST..."
	pytest \
		--verbose \
		--cov=yamlpath \
		--cov-report=term-missing \
		--cov-fail-under=100 \
		--script-launch-mode=subprocess \
		tests
	pytestErrorCode=$?
	if [ 0 -ne "$pytestErrorCode" ]; then
		cleanupTestEnvironment "$tmpVEnv" "$tmpGemHome" "$originalPath"
		echo "PYTEST Error: ${pytestErrorCode}"
		exit 12
	fi

	cleanupTestEnvironment "$tmpVEnv" "$tmpGemHome" "$originalPath"
done
