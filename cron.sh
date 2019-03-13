#!/bin/bash

echo 'Running refresh-iati task'
flask refresh-iati || exit $?

echo 'Running refresh-metadata task'
flask refresh-metadata || exit $?

echo 'Running validation task'
PUBLISHERS=$(ls -F __iatikitcache__/registry/metadata | grep /)
for p in $PUBLISHERS ; do
    DATASETS=$(ls -F __iatikitcache__/registry/metadata/$p | rev | cut -c 6- | rev)
    for d in $DATASETS ; do
        flask validate $d || exit $?
    done
done
