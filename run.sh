#!/bin/bash

source venv/bin/activate

export FLASK_APP=app:app
export FLASK_ENV=development

flask run

