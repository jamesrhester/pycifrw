#!/usr/bin/python2

#
# Yapps 2 - yet another python parser system
# Copyright 1999-2003 by Amit J. Patel <amitp@cs.stanford.edu>
#
# This version of Yapps 2 can be distributed under the
# terms of the MIT open source license, either found in the LICENSE file
# included with the Yapps distribution
# <http://theory.stanford.edu/~amitp/yapps/> or at
# <http://www.opensource.org/licenses/mit-license.php>
#

from __future__ import print_function

import sys, re

import yappsrt, parsetree

def generate(inputfilename, outputfilename='', dump=0, **flags):
    """Generate a grammar, given an input filename (X.g)
    and an output filename (defaulting to X.py)."""

    if not outputfilename:
        if inputfilename.endswith('.g'):
            outputfilename = inputfilename[:-2] + '.py'
        else:
            raise Exception('Must specify output filename if input filename is not *.g')

    DIVIDER = '\n%%\n' # This pattern separates the pre/post parsers
    preparser, postparser = None, None # Code before and after the parser desc

    # Read the entire file
    s = open(inputfilename,'r').read()

    # See if there's a separation between the pre-parser and parser
    f = s.find(DIVIDER)
    if f >= 0: preparser, s = s[:f]+'\n\n', s[f+len(DIVIDER):]

    # See if there's a separation between the parser and post-parser
    f = s.find(DIVIDER)
    if f >= 0: s, postparser = s[:f], '\n\n'+s[f+len(DIVIDER):]

    # Create the parser and scanner and parse the text
    scanner = grammar.ParserDescriptionScanner(s)
    if preparser: scanner.first_line_number = 1 + preparser.count('\n')
    parser = grammar.ParserDescription(scanner)
    t = yappsrt.wrap_error_reporter(parser, 'Parser')
    if t is None: return # Failure
    if preparser is not None: t.preparser = preparser
    if postparser is not None: t.postparser = postparser

    # Check the options
    for f in t.options.keys():
        for opt,_,_ in yapps_options:
            if f == opt: break
        else:
            print('Warning: unrecognized option', f, file=sys.stderr)
    # Add command line options to the set
    for f in flags.keys(): t.options[f] = flags[f]

    # Generate the output
    if dump:
        t.dump_information()
    else:
        t.output = open(outputfilename, 'w')
        t.generate_output()

if __name__ == '__main__':
    import doctest
    doctest.testmod(sys.modules['__main__'])
    doctest.testmod(parsetree)

    # Someday I will use optparse, but Python 2.3 is too new at the moment.
    yapps_options = [
        ('context-insensitive-scanner',
         'context-insensitive-scanner',
         'Scan all tokens (see docs)'),
        ]

    import getopt
    optlist, args = getopt.getopt(sys.argv[1:], 'f:', ['help', 'dump', 'use-devel-grammar'])
    if not args or len(args) > 2:
        print('Usage:', file=sys.stderr)
        print('  python', sys.argv[0], '[flags] input.g [output.py]', file=sys.stderr)
        print('Flags:', file=sys.stderr)
        print(('  --dump' + ' '*40)[:35] + 'Dump out grammar information', file=sys.stderr)
        print(('  --use-devel-grammar' + ' '*40)[:35] + 'Use the devel grammar parser from yapps_grammar.py instead of the stable grammar from grammar.py', file=sys.stderr)
        for flag, _, doc in yapps_options:
            print(('  -f' + flag + ' '*40)[:35] + doc, file=sys.stderr)
    else:
        # Read in the options and create a list of flags
        flags = {}
        use_devel_grammar = 0
        for opt in optlist:
            for flag, name, _ in yapps_options:
                if opt == ('-f', flag):
                    flags[name] = 1
                    break
            else:
                if opt == ('--dump', ''):
                    flags['dump'] = 1
                elif opt == ('--use-devel-grammar', ''):
                    use_devel_grammar = 1
                else:
                    print('Warning: unrecognized option', opt[0], opt[1], file=sys.stderr)

        if use_devel_grammar:
            import yapps_grammar as grammar
        else:
            import grammar

        generate(*tuple(args), **flags)
