#!/bin/bash

# What follows is the bash script that will build
# the project documentation.

# save current directory for use later:
currentdir=$(pwd)

# define nexus repo urls:
nexusurl="https://my-secret-host.com:8997/nexus/repository"
prodchannel="${nexusurl}/pdi"

# make sure artifacts directory is present:
packagedir="${currentdir}/packages"
if [[ ! -d $packagedir ]]; then
  echo "packages directory does not exit"
  exit 1
fi

# make sure conda is installed:
condaprefix="/home/gitlab-runner/miniconda3"
echo "assuming conda installation directory: $condaprefix"
echo "checking for conda installation"
. "$condaprefix"/etc/profile.d/conda.sh
command -v conda &> /dev/null
found="$?"
if [[ $found -ne 0 ]]; then
  echo "command \"conda\" not found!"
  exit 1
fi
echo "conda command: $(command -v conda)"

# update conda packages in base environment:
echo "updating conda packages."
conda activate base
conda update -q -y conda
conda update -q -y multimarkdown
conda deactivate

# check that multimarkdown is installed in base env:
conda activate base
command -v multimarkdown &> /dev/null
found="$?"
if [[ $found -ne 0 ]]; then
  echo "command \"multimarkdown\" not found!"
  exit 1
fi
conda deactivate

# read package id:
packageidfile="$packagedir/packageid"
if [[ ! -f $packageidfile ]]; then
  echo "package id file $packageidfile does not exit"
  exit 1
fi
packageid="$(cat $packageidfile)"

# determine conda channel option for conda env creation:
gittag="$CI_COMMIT_TAG"
if [[ -z $gittag ]]; then
  channel="pdi-dev"
  channelurl="${nexusurl}/${channel}"
  channelopt="-c $channelurl"
else
  channelopt=""
fi

# create the project docs environment:
pdocenv="${CI_PROJECT_NAME}_docs"
conda create \
  -q \
  -y \
  -n $pdocenv \
  -c conda-forge \
  -c $prodchannel \
  $channelopt \
  $packageid

# check that pdoc3 is installed in package env:
conda activate $pdocenv
command -v pdoc3 &> /dev/null
found="$?"
if [[ $found -ne 0 ]]; then
  echo "command \"pdoc3\" not found!"
  echo "Please make pdoc3 a dependency of you project."
  exit 1
fi
conda deactivate

# make .public directory:
dotpubdir="${currentdir}/.public"
rm -fr $dotpubdir
mkdir $dotpubdir

# render all markdown files:
conda activate base
pushd .
cd docs
rm -f *.html
multimarkdown -b *.md
cp -r images styles *.html $dotpubdir/
popd
conda deactivate

# render api docs:
conda activate $pdocenv
apidir="$dotpubdir/api"
moddir="$currentdir/src/pacmo"
pdoc3 --config show_source_code=False --html -o $apidir $moddir
if [[ $? -ne 0 ]]; then
  echo "command \"pdoc3\" returned non zero status."
  exit 1
fi
conda deactivate

# make public directory:
pubdir="${currentdir}/public"
rm -fr $pubdir
mv $dotpubdir $pubdir

# summary splash:
echo "Done"
