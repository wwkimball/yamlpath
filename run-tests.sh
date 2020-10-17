#!/usr/bin/env bash
##########################################################################
# Run Python code quality tests against this project.
##########################################################################
if ! [ -d tests -a -d yamlpath ]; then
	echo "Please start this script only from within the top directory of the YAML Path project." >&2
	exit 2
fi

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

	echo "...upgrading pip"
	python -m pip install --upgrade pip >/dev/null
	echo "...reinstalling ruamel.yaml (because pip upgrades break it)"
	#pip install --force-reinstall ruamel.yaml==0.15.96 >/dev/null
	pip install --force-reinstall ruamel.yaml >/dev/null
	echo "...upgrading ruamel.yaml"
	pip install --upgrade ruamel.yaml
	echo "...upgrading testing tools"
	pip install --upgrade mypy pytest pytest-cov pytest-console-scripts \
		pylint coveralls pep257 >/dev/null
	echo "...installing self"
	pip install -e . >/dev/null

	echo -e "\nPEP257..."
	if ! pep257 yamlpath; then
		echo "PEP257 Error: $?"
		exit 9
	fi

	echo -e "\nMYPY..."
	if ! mypy yamlpath; then
		echo "MYPY Error: $?"
		exit 10
	fi

	echo -e "\nPYLINT..."
	if ! pylint yamlpath; then
		echo "PYLINT Error: $?"
		exit 11
	fi

	echo -e "\nPYTEST..."
	if ! pytest \
		-vv \
		--cov=yamlpath \
		--cov-report=term-missing \
		--cov-fail-under=100 \
		--script-launch-mode=subprocess \
		tests
	then
		echo "PYTEST Error: $?"
		exit 12
	fi
done

