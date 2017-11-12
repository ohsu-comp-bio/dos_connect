"""
util
==========
common utility functions
"""
import argparse
import logging


def common_args(argparser):
    """ options common to all cli """
    argparser.add_argument('--dry_run', '-d',
                           help='''dry run''',
                           default=False,
                           action='store_true')
    argparser.add_argument("-v", "--verbose", help="increase output verbosity",
                           default=False,
                           action="store_true")
    return argparser


def common_logging(args):
    if args.verbose:
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    else:
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)
