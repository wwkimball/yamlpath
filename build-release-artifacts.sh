#!/usr/bin/env bash
###############################################################################
# Build release artifacts for the YAMLPath project.
###############################################################################
# Clean up old releases
[ -e dist ] && rm -rf dist

# Update pip and install release tools
python3 -m pip install --upgrade pip
pip3 install wheel || exit $?

# Require successful tests
if [ ! -x run-tests.sh ]; then
	echo "ERROR:  run-tests.sh script must exist and be executable in the present directory!" >&2
	exit 2
fi
./run-tests.sh || exit $?

# Build release artifacts
python3 setup.py sdist bdist_wheel || exit $?

# Generate a ZIP file for Windows users
cd dist || exit 2
relname=$(basename $(ls -1 ./*.tar.gz) .tar.gz)
mkdir win \
	&& cp "${relname}.tar.gz" win/ \
	&& cd win/ \
	&& tar xvzf ./*.tar.gz \
	&& rm -f ./*.gz \
	&& zip --recurse-paths --test --verbose "${relname}.zip" "${relname}"/ \
	&& mv ./*.zip .. \
	&& cd .. \
	&& rm -rf win

# Show the final release artifacts
ls -1 ./*
