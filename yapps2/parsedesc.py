######################################################################
# The remainder of this file is from parsedesc.{g,py}

def append(lst, x):
    "Imperative append"
    lst.append(x)
    return lst

def add_inline_token(tokens, str):
    tokens.insert( 0, (str, eval(str, {}, {})) )
    return Terminal(str)

def cleanup_choice(lst):
    if len(lst) == 0: return Sequence([])
    if len(lst) == 1: return lst[0]
    return apply(Choice, tuple(lst))

def cleanup_sequence(lst):
    if len(lst) == 1: return lst[0]
    return apply(Sequence, tuple(lst))

def cleanup_rep(node, rep):
    if rep == 'star':   return Star(node)
    elif rep == 'plus': return Plus(node)
    else:               return node

def resolve_name(tokens, id, args):
    if id in map(lambda x: x[0], tokens):
	# It's a token
	if args: 
	    print 'Warning: ignoring parameters on TOKEN %s<<%s>>' % (id, args)
        return Terminal(id)
    else:
        # It's a name, so assume it's a nonterminal
        return NonTerminal(id, args)


from string import *
import re
from yappsrt import *

class ParserDescriptionScanner(Scanner):
    patterns = [
        ('"rule"', re.compile('rule')),
        ('"ignore"', re.compile('ignore')),
        ('"token"', re.compile('token')),
        ('"option"', re.compile('option')),
        ('":"', re.compile(':')),
        ('"parser"', re.compile('parser')),
        ('[ \t\r\n]+', re.compile('[ \t\r\n]+')),
        ('#.*?\r?\n', re.compile('#.*?\r?\n')),
        ('END', re.compile('$')),
        ('ATTR', re.compile('<<.+?>>')),
        ('STMT', re.compile('{{.+?}}')),
        ('ID', re.compile('[a-zA-Z_][a-zA-Z_0-9]*')),
        ('STR', re.compile('[rR]?\'([^\\n\'\\\\]|\\\\.)*\'|[rR]?"([^\\n"\\\\]|\\\\.)*"')),
        ('LP', re.compile('\\(')),
        ('RP', re.compile('\\)')),
        ('LB', re.compile('\\[')),
        ('RB', re.compile('\\]')),
        ('OR', re.compile('[|]')),
        ('STAR', re.compile('[*]')),
        ('PLUS', re.compile('[+]')),
        ('QUEST', re.compile('[?]')),
        ('COLON', re.compile(':')),
    ]
    def __init__(self, str):
        Scanner.__init__(self,None,['[ \t\r\n]+', '#.*?\r?\n'],str)

class ParserDescription(Parser):
    def Parser(self):
        self._scan('"parser"')
        ID = self._scan('ID')
        self._scan('":"')
        Options = self.Options()
        Tokens = self.Tokens()
        Rules = self.Rules(Tokens)
        END = self._scan('END')
        return Generator(ID,Options,Tokens,Rules)

    def Options(self):
        opt = {}
        while self._peek() == '"option"':
            self._scan('"option"')
            self._scan('":"')
            Str = self.Str()
            opt[Str] = 1
        return opt

    def Tokens(self):
        tok = []
        while self._peek() in ['"token"', '"ignore"']:
            _token_ = self._peek()
            if _token_ == '"token"':
                self._scan('"token"')
                ID = self._scan('ID')
                self._scan('":"')
                Str = self.Str()
                tok.append( (ID,Str) )
            elif _token_ == '"ignore"':
                self._scan('"ignore"')
                self._scan('":"')
                Str = self.Str()
                tok.append( ('#ignore',Str) )
            else:
                raise SyntaxError(self._pos, 'Could not match Tokens')
        return tok

    def Rules(self, tokens):
        rul = []
        while self._peek() == '"rule"':
            self._scan('"rule"')
            ID = self._scan('ID')
            OptParam = self.OptParam()
            self._scan('":"')
            ClauseA = self.ClauseA(tokens)
            rul.append( (ID,OptParam,ClauseA) )
        return rul

    def ClauseA(self, tokens):
        ClauseB = self.ClauseB(tokens)
        v = [ClauseB]
        while self._peek() == 'OR':
            OR = self._scan('OR')
            ClauseB = self.ClauseB(tokens)
            v.append(ClauseB)
        return cleanup_choice(v)

    def ClauseB(self, tokens):
        v = []
        while self._peek() in ['STR', 'ID', 'LP', 'LB', 'STMT']:
            ClauseC = self.ClauseC(tokens)
            v.append(ClauseC)
        return cleanup_sequence(v)

    def ClauseC(self, tokens):
        ClauseD = self.ClauseD(tokens)
        _token_ = self._peek()
        if _token_ == 'PLUS':
            PLUS = self._scan('PLUS')
            return Plus(ClauseD)
        elif _token_ == 'STAR':
            STAR = self._scan('STAR')
            return Star(ClauseD)
        elif _token_ not in ['"ignore"', '"token"', '"option"', '":"', '"parser"', 'ATTR', 'QUEST', 'COLON']:
            return ClauseD
        else:
            raise SyntaxError(self._pos, 'Could not match ClauseC')

    def ClauseD(self, tokens):
        _token_ = self._peek()
        if _token_ == 'STR':
            STR = self._scan('STR')
            t = (STR, eval(STR,{},{}))
            if t not in tokens: tokens.insert( 0, t )
            return Terminal(STR)
        elif _token_ == 'ID':
            ID = self._scan('ID')
            OptParam = self.OptParam()
            return resolve_name(tokens, ID, OptParam)
        elif _token_ == 'LP':
            LP = self._scan('LP')
            ClauseA = self.ClauseA(tokens)
            RP = self._scan('RP')
            return ClauseA
        elif _token_ == 'LB':
            LB = self._scan('LB')
            ClauseA = self.ClauseA(tokens)
            RB = self._scan('RB')
            return Option(ClauseA)
        elif _token_ == 'STMT':
            STMT = self._scan('STMT')
            return Eval(STMT[2:-2])
        else:
            raise SyntaxError(self._pos, 'Could not match ClauseD')

    def OptParam(self):
        if self._peek() == 'ATTR':
            ATTR = self._scan('ATTR')
            return ATTR[2:-2]
        return ''

    def Str(self):
        STR = self._scan('STR')
        return eval(STR,{},{})


def parse(rule, text):
    P = ParserDescription(ParserDescriptionScanner(text))
    return wrap_error_reporter(P, rule)




# This replaces the default main routine

yapps_options = [
    ('context-insensitive-scanner', 'context-insensitive-scanner',
     'Scan all tokens (see docs)')
    ]

def generate(inputfilename, outputfilename='', dump=0, **flags):
    """Generate a grammar, given an input filename (X.g)
    and an output filename (defaulting to X.py)."""

    if not outputfilename:
	if inputfilename[-2:]=='.g': outputfilename = inputfilename[:-2]+'.py'
	else: raise "Invalid Filename", outputfilename
        
    print 'Input Grammar:', inputfilename
    print 'Output File:', outputfilename
    
    DIVIDER = '\n%%\n' # This pattern separates the pre/post parsers
    preparser, postparser = None, None # Code before and after the parser desc

    # Read the entire file
    s = open(inputfilename,'r').read()

    # See if there's a separation between the pre-parser and parser
    f = find(s, DIVIDER)
    if f >= 0: preparser, s = s[:f]+'\n\n', s[f+len(DIVIDER):]

    # See if there's a separation between the parser and post-parser
    f = find(s, DIVIDER)
    if f >= 0: s, postparser = s[:f], '\n\n'+s[f+len(DIVIDER):]

    # Create the parser and scanner
    p = ParserDescription(ParserDescriptionScanner(s))
    if not p: return
    
    # Now parse the file
    t = wrap_error_reporter(p, 'Parser')
    if not t: return # Error
    if preparser is not None: t.preparser = preparser
    if postparser is not None: t.postparser = postparser

    # Check the options
    for f in t.options.keys():
        for opt,_,_ in yapps_options:
            if f == opt: break
        else:
            print 'Warning: unrecognized option', f
    # Add command line options to the set
    for f in flags.keys(): t.options[f] = flags[f]
            
    # Generate the output
    if dump:
        t.dump_information()
    else:
        t.output = open(outputfilename, 'w')
        t.generate_output()

if __name__=='__main__':
    import sys, getopt
    optlist, args = getopt.getopt(sys.argv[1:], 'f:', ['dump'])
    if not args or len(args) > 2:
        print 'Usage:'
        print '  python', sys.argv[0], '[flags] input.g [output.py]'
        print 'Flags:'
        print ('  --dump' + ' '*40)[:35] + 'Dump out grammar information'
        for flag, _, doc in yapps_options:
            print ('  -f' + flag + ' '*40)[:35] + doc
    else:
        # Read in the options and create a list of flags
	flags = {}
	for opt in optlist:
	    for flag, name, _ in yapps_options:
		if opt == ('-f', flag):
		    flags[name] = 1
		    break
	    else:
                if opt == ('--dump', ''):
                    flags['dump'] = 1
		else:
                    print 'Warning - unrecognized option:  ', opt[0], opt[1]

        apply(generate, tuple(args), flags)
