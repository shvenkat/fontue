"""Inspect and modify fonts with ease

Usage:
  fontue [options] <command> [<args>...]

Commands:
  info       View font metadata
  metrics    Summarize font or glyph dimensions
  add        Add glyphs from one font to another
  tweak      Perform minor modifications on glyphs
  remove     Remove glyphs from a font

Options:
  -h, --help           Show this message
  -V, --version        Program version
  -v, --verbose        Verbose messages to standard error
  -l FILE, --log=FILE  Log actions to FILE

Dependencies:
  fontforge with python bindings

Notes:
fontue handles all font formats supported by FontForge
"""


from docopt import docopt
import sys


COMMANDS = ['info', 'metrics', 'add', 'tweak', 'remove']
__version__ = 0.0


def main():
    args = docopt(__doc__,
                  version=__version__,
                  options_first=True)
    command = args['<command>']
    com_args = [command] + args['<args>']
    if command in COMMANDS:
        module = __import__(command)
        module.main(com_args)
    else:
        sys.exit("Invalid fontue command: %s" % (command,))


if __name__ == '__main__':
    main()
