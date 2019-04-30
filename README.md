# IATI Canary

![Credit: Dick Daniels (http://carolinabirds.org/); License: https://creativecommons.org/licenses/by-sa/3.0/deed.en](canary/static/img/canary.jpg)

## How does it work?

IATI Canary leans heavily on some of the somewhat hidden outputs of [IATI Data Dump](https://andylolz.github.io/iati-data-dump/) – specifically, the various error logs that are [stored as GitHub gists here.](https://gist.github.com/andylolz/8a4e0657ec14c999de6f70f339656852)

## A note about design

It might be nicer to store an error history for each dataset. But it’s not feasible to do that whilst staying within the 10,000 database row limit that’s imposed on the free tier of postgres on Heroku.

## Installation

```shell
cp .env.example .env
```

…and modify as appropriate.

Install dependencies using pipenv:

```shell
pipenv install
```

## Getting started

Run a local development server:

```shell
pipenv run flask run
```

Various commands need to be run as cron tasks. Specifically:

```shell
pipenv run flask cleanup
pipenv run flask fetch-errors
pipenv run flask send-emails
```
