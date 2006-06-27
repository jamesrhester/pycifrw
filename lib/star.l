/*******************************************************************************
This code borrows some patterns from star.l,    
which was written and designed by 
Andrew Gene HALL of I.N. Services Pty. Ltd., Scarborough WA, Australia,
for the University of Western Australia, Crawley WA, Australia.

Present code by JRH to work with PyCIFRW v 3.1
*******************************************************************************/
/* Lex Definitions for a STAR File */

%{

/* Global Definitions */
#include <ctype.h>
#include <stdio.h>

#include "star_scanner.h"

#define YY_DECL char * star_scanner() 

/* redefine YY_INPUT to come from our global string */
#define YY_INPUT(buf,result,max_size)\
{\
if(string_pos == in_string_len) result = YY_NULL;\
if(string_pos + max_size <= in_string_len) {\
    strncpy(buf,input_string+string_pos,max_size);\
    string_pos +=max_size;\
    result =max_size;\
    } else {\
    strncpy(buf,input_string+string_pos,in_string_len - string_pos);\
    result = in_string_len - string_pos;\
    string_pos = in_string_len;\
    }\
}

%}

a		[aA]
b		[bB]
d		[dD]
e		[eE]
g		[gG]
l		[lL]
o		[oO]
p		[pP]
s		[sS]
t		[tT]
v		[vV]
Dollar		\$
Data_		{d}{a}{t}{a}_
Loop_		{l}{o}{o}{p}_
Global_		{g}{l}{o}{b}{a}{l}_
Stop_		{s}{t}{o}{p}_
Save_		{s}{a}{v}{e}_
Char		[^\n\r\0]
Blank		[\n \t\r\0]
NonBlank	[^\n \t\r]
NonDQuote	[^\n\r"\0]
NonSQuote	[^\n\r'\0]
NotUnderscore	[^\n \r\t_\0]
Space	        [\t ]
Spaces          [\t ]*
Comment		#[^\n\r]*
EndOfLine	{Spaces}({Comment})?(\n|\r|\r\n)

%a 4000
%o 6000
%x Alltext
%option noyywrap

/* Lex Rules fo a STAR File */
%%
{Loop_}                 {return("LBLOCK");}
{Global_}               {return("GLOBAL");}
{Stop_}                 {return("STOP");}
{Save_}{NonBlank}+      {return("save_heading");}
{Save_}                 {return("save_end");}
{Data_}{NonBlank}+      {return("data_heading");}
_{NonBlank}+            {return("data_name");}
{Spaces}                {/* do nothing */}
{Comment}               {/* do nothing */}
{EndOfLine}/[^;]        {/* do nothing */}

(\n|\r\n);([^\n\r])*(\r\n|\r|\n)+ {BEGIN(Alltext);return("start_sc_line");}
<Alltext>[^;\r\n]([^\r\n])*(\r\n|\r|\n)+   {return("sc_line_of_text");}
<Alltext>;                                 {BEGIN(INITIAL);
					    return("end_sc_line");}

([^\n\r\t \"#$\'_\[\]\0]{NonBlank}*) {return("data_value_1");}

\'[^\n\r\f]*\'  {/* this code borrowed from star.l in
                 starbase.  We can't write a rule in 
                 flex to accept a quote if the following
                 character is not blank, and accepting
                 the following non-blank may swallow the
                 closing quote! */ 

                 char *p;
                 p = yytext;
                 /* step over first quote */
                 p++;
                 /* scan to "?
                  * (? == null) or (? == space) => end of string, stop
                  */
                 while ( p = strchr( p, '\''))
                    if (isspace( *(++p))) {
                       /* (? == space) => push back rest of the input,
                        *                 S_Q_T_S */
                       /* this is to avoid side effects in the macro */
                       int       i = yyleng - strlen(p);
                       yyless( i );
                       }
                 return("data_value_1");
                 }

\"[^\n\r\f]*\"  {/* this code borrowed from star.l in
                 starbase.  We can't write a rule in 
                 flex to accept a quote only if the following
                 character is not blank, and writing a
                 quote-nonblank rule may swallow the
                 closing quote. */ 

                 char *p;
                 p = yytext;
                 /* step over first quote */
                 p++;
                 /* scan to '?
                  * (? == null) or (? == space) => end of string, stop
                  */
                 while ( p = strchr( p, '\"'))
                    if (isspace( *(++p))) {
                       /* (? == space) => push back rest of the input,
                        *                 S_Q_T_S */
                       /* this is to avoid side effects in the macro */
                       int       i = yyleng - strlen(p);
                       yyless( i );
                       }
                 return("data_value_1");
                 }

\0                      {YY_FLUSH_BUFFER; return("END");}

.			{
			printf("Unexpected Character\n");
			printf("<%d>\n",yytext[0]);
                        YY_FLUSH_BUFFER;
                        return("(error)");
			}
%%
/* This routine is called during initialisation to avoid any problems
   which might arise due to a syntax error not re-initialising the 
   scanner.  Each time the scanner is initialised, the buffer is
   flushed */
void star_clear(void) {
    yy_flush_buffer(YY_CURRENT_BUFFER);
    BEGIN(INITIAL);
    }
