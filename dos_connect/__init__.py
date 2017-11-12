"""
dos_connect
==========
Provides
  1. Observe buckets into registry
  2. Inventory buckets into registry
  3. Web app to query into registry
"""
import argparse
import logging
import sys


def common_args(argparser):
    """ options common to all cli """
    argparser.add_argument('--dry_run', '-d',
                           help='dry run',
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
