#!/usr/bin/env bash
set -euo pipefail

echo "Purging credentials from git history..."

if ! command -v git >/dev/null 2>&1; then
  echo "Git no está disponible" ; exit 1
fi

if ! command -v git-filter-repo >/dev/null 2>&1; then
  echo "git-filter-repo no está instalado. Instálalo para purgar historial (https://github.com/newren/global-git-minimal/blob/master/doc/filter-repo.md)."; exit 1
fi

REPLACEMENTS=$(pwd)/scripts/strip_secrets.txt
if [ ! -f "$REPLACEMENTS" ]; then
  echo "No se encontró scripts/strip_secrets.txt"; exit 1
fi

BRANCH="clean-credentials-$(date +%Y%m%d%H%M%S)"
git checkout -b "$BRANCH"
git filter-repo --replace-text "$REPLACEMENTS" --force

echo "Pushed purged branch to origin (force-push recommended)."
git push -u origin "$BRANCH" --force

echo "Done. Create a PR to merge into master after verification." 
