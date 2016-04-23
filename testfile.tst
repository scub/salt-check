example-test-1:
  module_and_function: cmd.run
  args: 'echo "hello"'
  kwargs: ''
  pillar-data: ''
  assertion: assertEqual
  expected-return:  'hello'

example-test-2:
  module_and_function: cmd.run
  args: 'echo "hellos"'
  kwargs: ''
  pillar-data: ''
  assertion: assertEqual
  expected-return:  'hello'
