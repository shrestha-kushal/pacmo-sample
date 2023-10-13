#!/bin/bash

# What follows is the bash script that will build
# a conda package for the project.

# save current directory for use later:
currentdir=$(pwd)

# make sure conda is installed:
condaprefix="/home/gitlab-runner/miniconda3"
echo "assuming conda installation directory: $condaprefix"
echo "checking for conda installation"
. "$condaprefix"/etc/profile.d/conda.sh
command -v conda &> /dev/null
found="$?"
if [[ $found -ne 0  ]]; then
  echo "command \"conda\" not found!"
  exit 1
fi
echo "conda command: $(command -v conda)"
echo "updating conda"

# update conda and conda-build packages:
conda update -q conda
conda update -q -y conda-build

# define the name, version, build string, and
# package id of the conda package:
appname="$CI_PROJECT_NAME"
appversion="$CI_COMMIT_TAG"
if [[ -z "$appversion" ]]; then
  appversion="0.cijob.num.${CI_JOB_ID}"
fi
appbuild="${CI_COMMIT_SHORT_SHA}"
packageid="${appname}=${appversion}=${appbuild}"

# export name, version, and build string for
# use by conda-build later:
export appname
export appversion
export appbuild

# NOTE: Script will build the conda package to a local
# conda channel with directory name "packages_channel".

# create "packages_channel":
outputdir="$currentdir/packages_channel"
rm -fr $outputdir
mkdir $outputdir

# TODO: remove pdi-dev channel upon beta release
# define command-line arguments for conda-build:
buildopts="\
  --channel http://conda.anaconda.org/conda-forge \
  --channel https://my-secret-host.com:8997/nexus/repository/pdi \
  --channel https://my-secret-host.com:8997/nexus/repository/pdi-dev \
  --output-folder $outputdir \
  --no-anaconda-upload \
  --no-test"

# build conda package:
echo "building conda package"
conda activate base
recipedir="$currentdir/conda-recipe"
conda build $buildopts $recipedir

# clean up unneeded build artifacts:
conda build purge

# save the path of the conda package tarball:
packagefile="$(conda build \
  --output \
  $buildopts \
  $recipedir)"

# deactivate base conda environment:
conda deactivate

# make sure the conda package tarball was created:
if [[ ! -e $packagefile ]]; then
  echo "file $packagefile not found"
  echo "package not created by conda build due to errors"
  exit 1
fi

# NOTE: all artifacts will be placed into an artifact
# directory named "packages"

# create "packages" directory:
packagedir=$currentdir/packages
rm -fr $packagedir
mkdir $packagedir

# save the name of the conda package tarball:
command -v basename &> /dev/null
found="$?"
if [[ $found -ne 0  ]]; then
  echo "command \"conda\" not found!"
  echo "unable to save conda package tarball name."
  exit 1
fi
packagename=$(basename $packagefile)
echo $packagename > $packagedir/packagename

# save conda package id:
echo $packageid > $packagedir/packageid

# save conda package tarball:
cp $packagefile $packagedir/

# splash results to screen:
echo "conda package archive $packagename created."
echo "conda package id: $packageid"
echo "Done."
exit 0
