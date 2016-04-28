example-test-1-hello:
  module_and_function: cmd.run
  #args: 'echo "hello"'
  args: ['echo "hello"']
  kwargs: ''
  pillar-data: ''
  assertion: assertEqual
  expected-return:  'hello'

example-test-2-hellos:
  module_and_function: cmd.run
  args: ['echo "hellos"']
  kwargs: ''
  pillar-data: ''
  assertion: assertEqual
  expected-return:  'hello'

example-test-3-/tmp/hello:
  module_and_function: file.file_exists
  args: /tmp/hello
  kwargs: ''
  pillar-data: ''
  assertion: assertEqual
  expected-return:  True

example-test-4-md5sum:
  module_and_function: file.check_hash
  args: /etc/passwd md5:7051b07b9c41d2996accb575c0877861
  kwargs: ''
  pillar-data: 'sample_file_pillar_key: bad data'
  assertion: assertEqual
  expected-return: True
  