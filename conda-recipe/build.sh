#!/bin/bash

if [[ ! -d "$SP_DIR" ]] ; then
  echo "python site-packages directory not available"
  echo "creating $SP_DIR"
fi
mkdir -p $SP_DIR
cp -r $SRC_DIR/pacmo $SP_DIR/pacmo
