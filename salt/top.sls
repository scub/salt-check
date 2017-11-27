base:
  '*':
    - apache
    - nothing
    - single_level_include

  'os:Ubuntu':
    - match: grain
    - single_level_include.uncommon
