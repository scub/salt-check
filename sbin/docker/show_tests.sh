#!/bin/bash

salt-call saltutil.sync_modules
salt-call saltcheck.show_tests
