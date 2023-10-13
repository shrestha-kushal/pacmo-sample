#!/bin/bash

# make sure artifacts directory is present:
packagedir="$(pwd)/packages"
if [[ ! -d $packagedir ]]; then
  echo "packages directory does not exit"
  exit 1
fi

# acquire conda package tarball path:
packagenamefile="$packagedir/packagename"
if [[ ! -f $packagenamefile ]]; then
  echo "package name file $packagenamefile does not exit"
  exit 1
fi
packagename="$(cat $packagenamefile)"
packagefile="$packagedir/$packagename"
if [[ ! -e $packagefile ]]; then
  echo "conda package file $packagefile does not exist."
  exit 1
fi
echo "conda package file: $packagefile"

# determine conda channel for conda package:
gittag="$CI_COMMIT_TAG"
if [[ -z $gittag ]]; then
  channel="pdi-dev"
else
  channel="pdi"
fi
channeldir="/home/pdiConda/$channel"

# add package to conda channel directory:
echo "adding package file to $channeldir/linux-64"
mkdir -p $channeldir/linux-64
cp "$packagefile" $channeldir/linux-64/

# check that conda is installed:
echo "checking for conda installation"
condaprefix="/home/gitlab-runner/miniconda3"
. "$condaprefix"/etc/profile.d/conda.sh
command -v conda &> /dev/null
found="$?"
if [[ $found -ne 0  ]]; then
  echo "command \"conda\" not found!"
  exit 1
fi

# update conda channel index:
echo "indexing conda channel $channel"
conda index --no-progress -n $channel $channeldir

# read package id:
packageidfile="$packagedir/packageid"
if [[ ! -f $packageidfile ]]; then
  echo "package id file $packageidfile does not exit"
  exit 1
fi
packageid="$(cat $packageidfile)"

# summary splash:
echo "conda package $packageid now available in conda channel $channel"
echo "Done."
