#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# (C) 2018 Dublin City University
# All rights reserved. This material may not be
# reproduced, displayed, modified or distributed without the express prior
# written permission of the copyright holder.

# Author: Joachim Wagner

# Example usage:
# ./combine.py en_ewt/dev_epoch_4[789].conllu > en_ewt/dev_combined.conllu

# Can also be imported as a python module

import bz2
import gzip
import importlib
import os
import random
import sys

def get_parse_iterator(filename):
    if filename.endswith('.gz'):
        f = gzip.GzipFile(filename, 'rb')
    elif filename.endswith('.bz2'):
        f = bz2.BZ2File(filename, 'r')  # always in binary mode
    else:
        f = open(filename, 'rb')
    for parse in get_parse_iterator_for_file(f):
        yield parse
    f.close()

def get_parse_iterator_for_file(f):
    word_fields = []
    comment_lines = []
    while True:
        line = f.readline()
        if not line or not line.strip():
            if word_fields:
                yield (word_fields, comment_lines)
            elif comment_lines:
                sys.stderr.write(
                    'Warning: Ignoring comments %r outside sentence block in %r\n' %(
                        comment_lines, filename
                ))
            if not line:
                break
            word_fields = []
            comment_lines = []
        elif line[0] == '#':
            comment_lines.append(line.rstrip())
        else:
            fields = line.split('\t')
            # strip line break from last field:
            fields[-1] = fields[-1].rstrip()
            word_fields.append(fields)

def usage(notSupported = None):
    sys.stderr.write('%s [options] input*.conllu > output.conllu\n' %sys.argv[0])
    options = (
        ('--method  STRING',
            'Method for combining parses; must be the name of a module in the'
            ' ud-combination/scripts folder that implements the combine() function'
            ' (default = linear)'),
        ('--weights  STRING',
            'Colon-separated list of weights; must match number'
            ' of supplied conllu input files'
            ' (default: equal weights)'),
        ('--outfile  FILE',
            'Write output to file instead of stdout'),
        ('--overwrite',
            'Delete existing output file before writing'
            ' (default: exit with error if file exists)'),
        ('--prune-labels',
            'Prune labels (keep label up to the first colon) before'
            ' voting'),
        ('--seed  SEED',
            'Set seed for breaking ties how to proceed in the greedy search'
            ' (default: 0 = use a unique random system seed)'),
        ('--random-tiebreaker',
            'Randomly break ties -- the 2018 shared task behaviour'
            ' (default: break ties with salted hashes of context information)'),
        ('--debug',
            'Print additional information to stderr'),
        ('--help',
            'show this message'),
    )
    # TODO: format options more nicely
    for option, description in options:
        if not notSupported or option.split()[0] not in notSupported:
            sys.stderr.write('\t%-28s %s\n' %(option, description))
    sys.exit(0)

def main():
    opt_help   = False
    opt_method = 'linear'
    opt_prune_labels = False
    opt_weights = None
    opt_outfile = None
    opt_overwrite = False
    opt_random_tiebreaker = False
    opt_debug   = False
    opt_seed    = 0
    while len(sys.argv) >= 2 and sys.argv[1][:1] == '-':
        option = sys.argv[1]
        del sys.argv[1]
        if option == '--method':
            opt_method = sys.argv[1]
            del sys.argv[1]
        elif option == '--weights':
            opt_weights = []
            for field in sys.argv[1].split(':'):
                opt_weights.append(float(field))
            del sys.argv[1]
        elif option == '--outfile':
            opt_outfile = sys.argv[1]
            del sys.argv[1]
        elif option == '--seed':
            opt_seed = int(sys.argv[1])
            del sys.argv[1]
        elif option in ('--prune-labels', '-p'):
            opt_prune_labels = True
        elif option in ('--overwrite', '--overwrite-existing'):
            opt_overwrite = True
        elif option in ('--random-tiebreaker', '--old-tiebreaker'):
            opt_random_tiebreaker = True
        elif option in ('--debug', '-d'):
            opt_debug = True
        elif option in ('--help', '-h'):
            opt_help = True
            break
        else:
            sys.stderr.write('Unsupported option %s\n' %option)
            opt_help = True
            break
    if len(sys.argv) == 1:
        opt_help = True
    if opt_help:
        usage()
        sys.exit(0)
    if opt_seed:
        # note that very large integers are ok and Python uses all
        # bits up to a very high limit
        # (floats, strings etc., however, are passed through hash()
        # and thus reduced to 64 bits)
        # Furthermore, note that we pass `opt_seed` to the combine
        # function as a hash salt. The `random` module is only used
        # with option --random-tiebreaker or to initialise the hash
        # salt when the seed is 0.
        random.seed(opt_seed)
    if opt_outfile:
        final_outfile = opt_outfile
        if os.path.exists(opt_outfile):
            if not opt_overwrite:
                sys.stderr.write('File %r exists. Use --overwrite to replace it.\n' %opt_outfile)
                sys.exit()
            else:
                opt_outfile = opt_outfile + '.part'
                if os.path.exists(opt_outfile):
                    # GzipFile cannot write to existing file
                    os.unlink(opt_outfile)
        if final_outfile.endswith('.gz'):
            out = gzip.GzipFile(opt_outfile, 'wb')
        elif final_outfile.endswith('.bz2'):
            out = bz2.BZ2File(opt_outfile, 'w')  # always in binary mode
        else:
            out = open(opt_outfile, 'wb')
    else:
        out = sys.stdout
    if opt_debug:
        sys.stderr.write('Weights: %r\n' %opt_weights)
    method = importlib.import_module(opt_method)
    inputs = []
    for filename in sys.argv[1:]:
        inputs.append(get_parse_iterator(filename))
    debug = opt_debug
    while True:
        parses = []
        for parse_interator in inputs:
            try:
                parses.append(parse_interator.next())
            except StopIteration:
                pass
        if parses:
            word_fields, comment_lines = method.combine(
                parses,
                prune_label = opt_prune_labels,
                weights = opt_weights,
                salt = opt_seed,
                old_tiebreaker = opt_random_tiebreaker,
                debug = debug
            )
            for comment in comment_lines:
                out.write(comment)
                out.write('\n')
            for fields in word_fields:
                out.write('\t'.join(fields))
                out.write('\n')
            out.write('\n')
        else:
            break
        debug = False  # only show debug info for first parse
    if opt_outfile:
        out.close()
        if final_outfile != opt_outfile:
            try:
                os.rename(opt_outfile, final_outfile)
            except:
                # atomic replace not supported or wrong permissions
                # --> try 2 step approach
                os.unlink(final_outfile)
                os.rename(opt_outfile, final_outfile)

if __name__ == '__main__':
    main()
