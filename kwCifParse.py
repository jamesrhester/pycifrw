"""
1. This software copyright  Australian Synchrotron Research Program Inc.

2. Permission is hereby granted to use, copy and modify this software for
non-commercial purposes only.  Permission is also granted to use
reasonable portions of it in other software for non-commercial
purposes, provided that suitable acknowledgement is made.  Australian
Synchrotron Research Program Inc., as the owner of the copyright in
the software, does not grant any right to publish, sell or otherwise
redistribute the software, or modified versions of the software, to
third parties.  You are encouraged to communicate useful modifications
to Australian Synchrotron Research Program Inc. for inclusion in
future versions.
"""

CifGGramString = """
     Input :: ## this is the root nonterminal
        @R InputRule :: Input >> dblockseq 
        @R NullRule  :: Input >>

        @R DblockRule :: dblockseq >> data_heading dataseq
        @R MDblockRule :: dblockseq >> dblockseq data_heading dataseq
        @R EmptyBlockRule :: dblockseq >> data_heading

        @R DataSeqRule :: dataseq >> data
        @R MDataSeqRule :: dataseq >> dataseq data

        @R DataKvRule1a :: data >> data_name data_value_1
        @R DataKvRule2a :: data >> data_name data_value_2
        @R DataLpRule :: data >> data_loop

        @R LpRule     :: data_loop >> LBLOCK loopfield loopvalues
        @R LtRule     :: loopfield >> data_name
        @R LtmRule    :: loopfield >> loopfield data_name

        @R Lb2Rule    :: loopvalues >> data_value_2 
        @R LbRule     :: loopvalues >> data_value_1
        @R LbmRule     :: loopvalues >> loopvalues data_value_1
        @R Lb2mRule    :: loopvalues >> loopvalues data_value_2 

       """ 

def stripstring(value):
    if value:
        if value[0]== '\'' and value[-1]=='\'':
            return value[1:-1]
        if value[0]=='"' and value[-1]=='"':
            return value[1:-1]
    return value

def stripextras(value):
    # we get rid of semicolons and leading terminators etc.
     import re
     jj = re.compile("[\n\r\f \t\v]*")
     semis = re.compile("[\n\r\f \t\v]*[\n\r\f];")
     cut = semis.match(value)
     if cut:
          nv = value[cut.end():len(value)-2]
     else: nv = value
     cut = jj.match(nv)
     if cut:
          return stripstring(nv[cut.end():])
     return nv

def DeclareTerminals(Grammar):
     ordinary_char = "!%&\(\)*+,./:<=>?@0-9A-Za-z\\\\^`{}\|~"
     non_blank_char = ordinary_char+"\"#$';_"
     char = "([]"+non_blank_char+" \v\t-])"
     terminate = "\n|\r|\r\n|\f"
     dataheadingstr = "(D|d)(A|a)(T|t)(A|a)_"+"[]["+non_blank_char+"-]+"
     dv1str = "[]"+ordinary_char+";-][]["+non_blank_char+"-]*"
     dqstr = "\"((\"[]["+non_blank_char+"-])|([]["+ordinary_char+" \v\t#$';_-]))*\""
     sqstr = "'(('[]["+non_blank_char+"-])|([]["+ordinary_char+" \v\t#$\";_-]))*'"
     lotstr = "[]"+ordinary_char+"\" \v\t#$'_-]"+char+"*("+terminate+")*"
     scstr = "(\n|\r\n|\f)"+";"+char+"*("+terminate+")("+lotstr+")*;"
     dv1str = "("+dv1str + ")|"+sqstr+"|"+dqstr
     dv2str = "[]["+ordinary_char+"-][]["+non_blank_char+"-]*"
     dv2str = "("+dv2str + ")|"+dqstr+"|"+sqstr+"|("+scstr+")"
     Grammar.Addterm("LBLOCK","(L|l)(O|o)(O|o)(P|p)_",None)
     Grammar.Addterm("data_name","_"+"[]["+non_blank_char+"-]+",stripextras)
     Grammar.Addterm("data_heading",dataheadingstr,stripextras)
     Grammar.Addterm("data_value_1",dv1str,stripextras)
     Grammar.Addterm("data_value_2",dv2str,stripextras)

import CifFile
def dblockinterp(): pass
def nameinterp(): pass
def textinterp(): pass
def dkvrulea(list,context): 
    return {list[0]:list[1]}
    
def lbrule(list,context):
    #print 'lbrule ' + `list`
    return list

def lb2rule(list,context):
    #print 'lb2rule ' + `list`
    return list

def lbmrule(list,context):
    #print 'lbmrule ' + `list[1]`
    list[0].append(list[1])
    return list[0]

def lb2mrule(list,context):
    #print 'lb2mrule ' + `list[1]`
    list[0].append(list[1])
    return list[0]

def ltrule(list,context):
    return list

def ltmrule(list,context):
    list[0].append(list[1])
    return list[0]

def lprule(list,context):
    noitems = len(list[1])
    nopoints = divmod(len(list[2]),noitems)
    if nopoints[1]!=0:    #mismatch
        raise "CifError:loop item mismatch"
    nopoints = nopoints[0]
    newdict = {}
    for i in range(0,noitems):
        templist = []
        for j in range(0,nopoints):
            templist.append(list[2][j*noitems + i])
        newdict.update({list[1][i]:templist})
    context["loops"].append(newdict)
    return {"dummy":''}    # to keep things easy

def datalprule(list,context):
    return list[0]

def dataseqrule(list,context):
    return list[0]

def mdataseqrule(list,context):
    list[0].update(list[1])
    return list[0]

def dblockrule(list,context):
    list[1].update({"loops":context["loops"]})
    context["loops"] = []
    if list[1].has_key("dummy"):
        del list[1]["dummy"]
    return {list[0][5:]:list[1]}

def mtblockrule(list,context):
    return {list[0][5:]:{"loops":context["loops"]}}

def mdblockrule(list,context):
    list[2].update({"loops":context["loops"]})
    context["loops"] = []
    if list[2].has_key("dummy"):
        del list[2]["dummy"]
    list[0].update({list[1][5:]:list[2]})
    return list[0]

def inputrule(list,context):
    return list[0]

def nullrule(list,context):
    return {}


def BindRules(Grammar):
    Grammar.Bind("DataKvRule1a", dkvrulea)
    Grammar.Bind("DataKvRule2a", dkvrulea)

    Grammar.Bind("LtRule", ltrule)
    Grammar.Bind("LtmRule", ltmrule)

    Grammar.Bind("LbRule", lbrule)
    Grammar.Bind("LbmRule", lbmrule)
    Grammar.Bind("Lb2Rule", lb2rule)
    Grammar.Bind("Lb2mRule", lb2mrule)

    Grammar.Bind("LpRule", lprule)
    Grammar.Bind("DataLpRule",datalprule)

    Grammar.Bind("DataSeqRule",dataseqrule)
    Grammar.Bind("MDataSeqRule",mdataseqrule)

    Grammar.Bind("InputRule", inputrule)
    Grammar.Bind("DblockRule", dblockrule)
    Grammar.Bind("MDblockRule", mdblockrule)
    Grammar.Bind("NullRule", nullrule)
    Grammar.Bind("EmptyBlockRule",mtblockrule)

def CifGramBuild():
    import kjCParseBuild
    CifG = kjCParseBuild.NullCGrammar()
    CifG.SetCaseSensitivity(1)
    DeclareTerminals(CifG)
    gramterms = "Input dblockseq dataseq data data_loop loopfield loopvalues"
    CifG.Nonterms(gramterms)
    CifG.Declarerules(CifGGramString)
    CifG.whitespace("(( |\t|\v|\n|\r|\f)(?!;))|( |\t|\v)")  #our own addition
    CifG.comments(["#.*\n(?!;)","#.*"])
    CifG.Compile()
    BindRules(CifG)
    return CifG 


