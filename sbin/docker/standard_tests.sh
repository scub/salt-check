#!/bin/bash

salt-call saltutil.sync_modules
salt-call saltcheck.run_state_tests standard_tests
