#!/bin/bash

echo 'Running refresh-iati task'
flask refresh-iati

echo 'Running refresh-metadata task'
flask refresh-metadata

echo 'Running download-errors task'
flask download-errors

echo 'Running schema-errors task'
flask schema-errors
