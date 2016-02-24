"""
Usage:
  fontue info [options] <font>

Options:
  -h, --help    Show this message

Arguments:
  <font>    font file to inspect
"""


from docopt import docopt
try:
	import fontforge
except ImportError:
	if sys.version_info.major > 2:
		sys.stderr.write(('fortue depends on the FontForge python modules, ' +
                          'which only support Python 2. ' +
                          'Run "python2 {0}"\n').format(sys.argv[0]))
	else:
		sys.stderr.write(('fontue depends on the FontForge python modules. ' +
                          'Is FontForge with Python bindings installed?\n'))
	sys.exit(1)


def info(font):
    pass


def main(argv = []):
    args = docopt(__doc__,
                  argv = argv)
    info(args['<font>'])


if __name__ == '__main__':
    main()
