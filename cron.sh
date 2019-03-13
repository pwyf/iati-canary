#!/bin/bash

echo 'Running refresh-iati task'
flask refresh-iati || exit $?

echo 'Running refresh-metadata task'
flask refresh-metadata || exit $?
