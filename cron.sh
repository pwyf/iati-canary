#!/bin/bash

echo 'Running refresh-iati task'
flask refresh-iati

echo 'Running refresh-metadata task'
flask refresh-metadata

echo 'Running validation task'
flask validate
