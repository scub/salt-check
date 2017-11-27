#!/bin/bash
#
# Aliases for use internal to docker container; 
#
# To use: 'source /opt/sbin/aliases.sh' inside the container.
#
# Currently targets salt-call specific behavior by utilizing
# the call name from the execution module... every keystroke counts! ;o 
#
#

alias run_highstate_tests='salt-call saltcheck.run_highstate_tests'
alias rht='salt-call saltcheck.run_highstate_tests'
alias run_standard_tests='salt-call saltcheck.run_state_tests standard_tests'
alias rst='salt-call saltcheck.run_state_tests standard_tests'
alias run_tests='salt-call saltcheck.run_tests'
alias rt='salt-call saltcheck.run_tests'
alias show_tests='salt-call saltcheck.show_tests'
alias stt='salt-call saltcheck.show_tests'
alias show_top='salt-call state.show_top'
alias sts='salt-call state.show_top'
alias sync_modules='salt-call saltutil.sync_modules'
alias sm='salt-call saltutil.sync_modules'
alias clear='clear; tput cup $LINES 0;'
