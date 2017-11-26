#!/bin/bash

salt-call saltutil.sync_modules
salt-call saltcheck.run_highstate_tests
