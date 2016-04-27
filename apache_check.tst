#salt web pkg.version apache2
#web:
# 2.4.7-1ubuntu4.9
correct-version-apache2-installed:
  module_and_function: pkg.version
  args: 'apache2'
  kwargs: ''
  pillar-data: ''
  assertion: assertEqual
  expected-return: 2.4.7-1ubuntu4.9
