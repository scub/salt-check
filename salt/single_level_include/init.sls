#
# This state tree is an example of a single level
# include; additional states from the same tree are
# applied on top of the base state provided to
# the larger class of minions.
#
# The states themselves are uneventful, the behavior
# that this state will highlight is created by the
# include structure in this state.
#
# Common formats for this state's inclusion in top.sls:
#
# base:
#   '*':
#     - single_level_include
#
#   'distinct_minion_id.fqdn':
#     - single_level_include.uncommon
#
include:
  - .common
