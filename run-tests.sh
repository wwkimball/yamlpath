#!/usr/bin/env bash
##########################################################################
# Run Python code quality tests against this project.
##########################################################################
if ! [ -d tests -a -d yamlpath ]; then
	echo "Please start this script only from within the top directory of the YAML Path project." >&2
	exit 2
fi

if [ 1 -gt "$#" ]; then
	echo "You must specify at least one Python version.  Space-delimit multiples like: $0 3.6 3.7 3.8" >&2
	exit 2
fi

# Delete all cached data
find ./ -name '__pycache__' -type d -print0 | xargs -r0 -- rm -rf || exit $?
rm -rf yamlpath.egg-info
rm -rf /tmp/yamlpath-python-coverage-data
rm -f .coverage

for pythonVersion in "${@}"; do
	which deactivate &>/dev/null && deactivate &>/dev/null

	pyCommand=python${pythonVersion}
	if ! which "$pyCommand" &>/dev/null; then
		echo -e "\nWARNING:  Unable to find a Python binary named, ${pyCommand}!" >&2
		continue
	fi
	pyVersion=$("$pyCommand" --version)

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
	python -m pip install --upgrade pip >/dev/null

	echo "...upgrading setuptools"
	pip install --upgrade setuptools >/dev/null

	echo "...installing self (editable because without it, pytest-cov cannot trace code execution!)"
	if ! pip install --editable . >/dev/null; then
		deactivate
		rm -rf "$tmpVEnv"
		echo -e "\nERROR:  Unable to install self!" >&2
		exit 124
	fi

	echo "...upgrading testing tools"
	pip install --upgrade mypy pytest pytest-cov pytest-console-scripts \
		pylint coveralls pep257 >/dev/null

	echo -e "\nPEP257..."
	if ! pep257 yamlpath; then
		deactivate
		rm -rf "$tmpVEnv"
		echo "PEP257 Error: $?"
		exit 9
	fi

	echo -e "\nMYPY..."
	if ! mypy yamlpath; then
		deactivate
		rm -rf "$tmpVEnv"
		echo "MYPY Error: $?"
		exit 10
	fi

	echo -e "\nPYLINT..."
	if ! pylint yamlpath; then
		deactivate
		rm -rf "$tmpVEnv"
		echo "PYLINT Error: $?"
		exit 11
	fi

	echo -e "\nPYTEST..."
	if ! pytest \
		--verbose \
		--cov=yamlpath \
		--cov-report=term-missing \
		--cov-fail-under=100 \
		--script-launch-mode=subprocess \
		tests
	then
		deactivate
		rm -rf "$tmpVEnv"
		echo "PYTEST Error: $?"
		exit 12
	fi

	deactivate
	rm -rf "$tmpVEnv"
done
