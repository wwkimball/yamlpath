#!/usr/bin/env bash
##########################################################################
# Run Python code quality tests against this project.
##########################################################################
if ! [ -d tests -a -d yamlpath ]; then
	echo "Please start this script only from within the top directory of the YAML Path project." >&2
	exit 2
fi

# Delete all cached data
find ./ -type d -name '__pycache__' -delete
rm -rf yamlpath.egg-info
rm -rf /tmp/yamlpath-python-coverage-data
rm -f .coverage

for envDir in env* venv*; do
	deactivate &>/dev/null
	if ! source "${envDir}/bin/activate"; then
		echo -e "\nWARNING:  Unable to activate ${envDir}!" >&2
		continue
	fi

	cat <<-EOF

		=============================================================================
		Using Python $(python --version)...
		=============================================================================
EOF

	echo "...spawning a new temporary Virtual Environment..."
	tmpVEnv=$(mktemp -d -t yamlpath-$(date +%Y%m%dT%H%M%S)-XXXXXXXXXX)
	if ! python -m venv "$tmpVEnv"; then
		rm -rf "$tmpVEnv"
		echo -e "\nERROR:  Unable to spawn a new temporary virtual environment at ${tmpVEnv}!" >&2
		exit 125
	fi
	deactivate
	if ! source "${tmpVEnv}/bin/activate"; then
		rm -rf "$tmpVEnv"
		echo -e "\nWARNING:  Unable to activate ${envDir}!" >&2
		continue
	fi

	echo "...upgrading pip"
	python -m pip install --upgrade pip >/dev/null

	echo "...upgrading setuptools"
	pip install --upgrade setuptools >/dev/null

	echo "...installing self"
	if ! pip install -e . >/dev/null; then
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
