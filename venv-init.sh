#!/bin/bash

cd ..
virtualenv tumbletime 
cd tumbletime
bin/pip install flask
bin/pip install flask_oauthlib
bin/pip install pytumblr 
