#!/usr/bin/env bash
###############################################################################
# Build release artifacts for the YAMLPath project.
###############################################################################
# Clean up old releases
[ -e dist ] && rm -rf dist

# Require successful tests
if [ ! -x run-tests.sh ]; then
	echo "ERROR:  run-tests.sh script must exist and be executable in the present directory!" >&2
	exit 2
fi
./run-tests.sh || exit $?

# Create a dedicated virtual Python enviroment for this
envName=venv-build-release-artifacts-$(date +%Y%m%dT%H%M%S)
if [ 0 -ne $? ]; then
	echo "ERROR:  Unable to identify the build virtual environment!  Is date a command?" >&2
	exit 3
fi
echo "Building virtual environment for $(python3 --version):  ${envName}"
rm -rf "$envName"
python3 -m pip install --upgrade pip
python3 -m venv "$envName" || exit 86
source "$envName"/bin/activate || exit 87

# Update pip and install release tools
echo "Installing release tools..."
pip3 install ruamel.yaml wheel || exit $?

# Build release artifacts
echo "Building release artifacts..."
python3 setup.py sdist bdist_wheel || exit $?

# Generate a ZIP file for Windows users
echo "Building Windows ZIP file..."
pushd dist || exit 2
relname=$(basename $(ls -1 ./*.tar.gz) .tar.gz)
mkdir win \
	&& cp "${relname}.tar.gz" win/ \
	&& pushd win/ \
	&& tar xvzf ./*.tar.gz \
	&& rm -f ./*.gz \
	&& zip --recurse-paths --test --verbose "${relname}.zip" "${relname}"/ \
	&& mv ./*.zip .. \
	&& popd \
	&& rm -rf win
popd

# Clean up
echo "Cleaning up..."
deactivate
if ! rm -rf "$envName"; then
	echo "WARNING:  Unable to remove temporary build environment:  ${envName}!"
fi
if ! rm -rf build; then
	echo "WARNING:  Unable to remove build directory!"
fi
if ! rm -rf yamlpath.egg-info; then
	echo "WARNING:  Unable to remove EGG information directory!"
fi

# Show the final release artifacts
echo -e "\nRelease artifacts:"
ls -1 ./dist/*
