#!/usr/bin/env python

''' This script is used to lint changeset before code checkin
    It get the changeset from the repo and base specified by
    command line arguments. And run cpplint over the changeset.
'''
# TODO(wang16): Use pylint for .py files
# TODO(wang16): Only show error for the lines do changed in the changeset

import os
import optparse
import re
import subprocess
import sys

def IsWindows():
  return sys.platform == 'cygwin' or sys.platform.startswith('win')

def IsLinux():
  return sys.platform.startswith('linux')

def IsMac():
  return sys.platform.startswith('darwin')

def GitExe():
  if IsWindows():
    return 'git.bat'
  else:
    return 'git'

def GetCommandOutput(command):
  proc = subprocess.Popen(command, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, bufsize=1)
  output = proc.communicate()[0]
  result = proc.returncode
  if result:
    raise Exception('%s: %s' % (subprocess.list2cmdline(diff), output))
  return output

def find_depot_tools_in_path():
  paths = os.getenv('PATH').split(os.path.pathsep)
  for path in paths:
    if os.path.basename(path) == 'depot_tools':
      return path
  return None

def repo_is_dirty():
  return GetCommandOutput([GitExe(), 'diff', 'HEAD']).strip() != ''

def get_tracking_remote():
  branch = [GitExe(), 'branch', '-vv', '-a']
  # The output of git branch -vv will be in format
  # * <branch>     <hash> [<remote>: ahead <n>, behind <m>] <subject>
  #   <branch>     <hash> <subject>
  output = GetCommandOutput(branch)
  branches = output.split('\n')
  for branch in branches:
    # we only need active branch first.
    if not branch.startswith('*'):
      continue
    detail = branch[1:].strip().split(' ', 1)[1].strip().split(' ', 1)[1].strip()
    if detail.startswith('['):
      remote = detail[1:].split(']', 1)[0]
      remote = remote.split(':',1)[0].strip()
      # verify that remotes/branch or branch is a real branch
      # There is still chance that developer named his commit
      # as [origin/branch], in this case
      exists = [\
          r_branch for r_branch in branches \
              if r_branch.strip().startswith('remotes/'+remote) or \
                 r_branch.strip().startswith(remote)]
      if len(exists) == 0:
        remote = ''
    else:
      remote = ''
    break
  if remote == '':
    if repo_is_dirty():
      remote = 'HEAD'
    else:
      remote = 'HEAD~'
  print 'Base is not specified, '\
        'will use %s as comparasion base for linting' % remote
  return remote

def get_change_file_list(base):
  diff = [GitExe(), 'diff', '--name-only', base]
  output = GetCommandOutput(diff)
  return [line.strip() for line in output.strip().split('\n')]
 
def do_lint(repo, base, args):
  # Try to import cpplint from depot_tools first
  try:
    import cpplint
  except ImportError:
    depot_tools_path = find_depot_tools_in_path()
    if depot_tools_path != None:
      sys.path.append(depot_tools_path)

  try:
    import cpplint
    import cpplint_chromium
    import gcl
  except ImportError:
    sys.stderr.write("Can't find cpplint, please add your depot_tools \
                      to PATH or PYTHONPATH")
    return 1

  '''Following code is referencing depot_tools/gcl.py: CMDlint
  '''
  # dir structure should be src/cameo for cameo
  #                         src/third_party/WebKit for blink
  #                         src/ for chromium
  # lint.py should be located in src/cameo/tools/lint.py
  _lint_py = os.path.abspath(__file__)
  _dirs = _lint_py.split(os.path.sep)
  src_root = os.path.sep.join(_dirs[:len(_dirs)-3])
  if repo == 'cameo':
    base_repo = os.path.join(src_root, 'cameo')
  elif repo == 'chromium':
    base_repo = src_root
  elif repo == 'blink':
    base_repo = os.path.join(src_root, 'third_party', 'WebKit')
  else:
    raise NotImplementedError('repo must in cameo, blink and chromium')
  previous_cwd = os.getcwd()
  os.chdir(base_repo)
  if base == None:
    base = get_tracking_remote()
  changeset = get_change_file_list(base)
  # pass the build/header_guard check
  if repo == 'cameo':
    os.rename('.git', '.git.rename')
  try:
    # Process cpplints arguments if any.
    filenames = cpplint.ParseArguments(args + changeset)

    white_list = gcl.GetCodeReviewSetting("LINT_REGEX")
    if not white_list:
      white_list = gcl.DEFAULT_LINT_REGEX
    white_regex = re.compile(white_list)
    black_list = gcl.GetCodeReviewSetting("LINT_IGNORE_REGEX")
    if not black_list:
      black_list = gcl.DEFAULT_LINT_IGNORE_REGEX
    black_regex = re.compile(black_list)
    extra_check_functions = [cpplint_chromium.CheckPointerDeclarationWhitespace]
    for filename in filenames:
      if white_regex.match(filename):
        if black_regex.match(filename):
          print "Ignoring file %s" % filename
        else:
          cpplint.ProcessFile(filename, cpplint._cpplint_state.verbose_level,
                              extra_check_functions)
      else:
        print "Skipping file %s" % filename
  finally:
    if repo == 'cameo':
      os.rename('.git.rename', '.git')
    os.chdir(previous_cwd)

  print "Total errors found: %d\n" % cpplint._cpplint_state.error_count
  return 1

from optparse import OptionParser, BadOptionError
class PassThroughOptionParser(OptionParser):
  def _process_long_opt(self, rargs, values):
    try:
      OptionParser._process_long_opt(self, rargs, values)
    except BadOptionError, err:
      self.largs.append(err.opt_str)

  def _process_short_opts(self, rargs, values):
    try:
      OptionParser._process_short_opts(self, rargs, values)
    except BadOptionError, err:
      self.largs.append(err.opt_str)

def main():
  option_parser = PassThroughOptionParser()

  option_parser.add_option('--repo', default='cameo',
      help='The repo to do lint, should be in [cameo, blink, chromium]\
            cameo by default')
  option_parser.add_option('--base', default=None,
      help='The base point to get change set. If not specified, it will choose:\r\n' +
           '  1. Active branch\'s tracking branch if exist\n' +
           '  2. HEAD if current repo is dirty\n' +
           '  3. HEAD~ elsewise')

  options, args = option_parser.parse_args()
  
  sys.exit(do_lint(options.repo, options.base, args))

if __name__ == '__main__':
  main()
