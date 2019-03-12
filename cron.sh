#!/bin/bash

echo 'Running refresh-iati task'
flask refresh-iati || exit $?

echo 'Running refresh-metadata task'
flask refresh-metadata || exit $?

echo 'Deleting iatikit registry data'
rm -rf __iatikitcache__/registry/data

echo 'Running validation task'
flask validate || exit $?
