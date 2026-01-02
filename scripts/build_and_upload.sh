#!/usr/bin/env bash
# ----------------------------------------------------------------------
#  build_and_upload.sh – tag a new version, push it, clean the build folder and rebuild
#
#  Usage:
#      ./build_and_upload.sh v1.8.1
# ----------------------------------------------------------------------

set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "Error: exactly one argument (the version) is required."
    exit 1
fi

while true; do
    read -rsp "Enter your PyPI token: " PYPI_TOKEN
    if [[ -n "$PYPI_TOKEN" ]]; then
        echo "Token saved"
        break
    else
        echo "Token cannot be empty – please try again."
    fi
done

VERSION="$1"

echo "Setting uv version to $VERSION ..."
uv version "$VERSION"

echo "Creating and pushing commit ..."
git add -A
git commit -m "version $VERSION"
git push

echo "Creating version tag $VERSION ..."
git tag "$VERSION"
git push origin --tags

if [[ -d "./dist" ]]; then
    echo "Removing existing ./dist folder ..."
    rm -rf "./dist"
fi

echo "Build package ..."
uv build
uv publish --token $PYPI_TOKEN

echo "Package built and uploaded successfully."
