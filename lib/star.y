/* @(#)star.y	1.7	2/10/93 */
/*******************************************************************************

This code was written and designed by 
Andrew Gene HALL of I.N. Services Pty. Ltd., Scarborough WA, Australia,
for the 
University of Western Australia, Crawley WA, Australia.

*******************************************************************************/

%{
#include "diagmesg.h"
#include "sf_space.h"

/* local variables */
Data_Seq *		temp_DS = NULL;
char *			current_GH = NULL;
char *			next_GH = NULL;
char *			current_DH = NULL;
char *			next_DH = NULL;
char *			current_SH = NULL;
char *			current_DN = NULL;
Data_Item *		current_di = NULL;
char		*root_Block_Names;
char		*root_Data_Names;
char		*root_Data_Names_save;
Block_Seq	*last_BS;
/* null terminated arrary of ptrs to the global blocks */
Global_Seq	*globals; 
Data_Seq	*last_DS;
Data_Seq	*last_DS_save;
int		star_line_count = 1;
char		*last_star_token = NULL;
char *tsearch();

#include "star_scanner.c"
/* star_scanner defines malloc so 
 * its important that it comes in before utilitys
 */
#include "utilitys.h"
#include "star.h"

/* redefine yylex */
#ifdef yylex
#undef yylex
#endif
#define yylex star_scanner

/* BOTCHES to help in compiling */
/* redefine yyparse */
#ifdef yyparse
#undef yyparse
#endif
#define yyparse	parse_star

#define yyerror	star_error

#ifdef YYDEBUG
#define xmalloc malloc
#endif 

/* end BOTCHES */

/* global variables */
extern Block_Seq	*beginning_of_BS;

%}

/* Yacc Declarations */
%start star_file

%union {
   char *		string;
   Block_Seq *		star_file_val;
   Data_Seq *		data_block_body_val;
   Data_Name_Seq *	data_loop_definition_val;
   Data_Item *		data_item_val;
   }

%token FRAME_CODE DATA_HEADING DATA_NAME DOUBLE_QUOTED_TEXT_STRING GLOBAL_HEADING LOOP_ NON_QUOTED_TEXT_STRING SAVE_HEADING SAVE_END SEMI_COLON_BOUNDED_TEXT_STRING SINGLE_QUOTED_TEXT_STRING STOP_ 

%type <star_file_val>			star_file block global_block data_block
%type <data_block_body_val>		data_block_body data save_frame
					save_frame_body save_item data_loop 
%type <data_loop_definition_val>	data_loop_definition data_loop_field
					nested_data_loop
%type <data_item_val>			data_item
/* Yacc Rules */
%%
star_file :
	  /* empty */
		{  
		   INFORM_MSG("Starting Parser for STAR File.");
		   DEBUG_MSG("star_file : empty"); 
                   /* initialise the global function */
                   globals = NULL;
		   $$ = NULL; 
		}
        | star_file block
		{  
                   register Block_Seq	*t = $2;
		   char			**found;
		   Boolean		force = FALSE;

		   DEBUG_MSG("star_file : star_file block"); 

	           if( t->tag == GLOBAL_BLOCK )
                      /* for global blocks don't check the name, 
	                 but force the insertion */
	              force = TRUE;
		   else
		      /* check that the name is not already present */
		      found = (char **)tsearch(t->name, &root_Block_Names, strcmp);

		   if( $1 == NULL ) {
		      /* forget the empty and return the block as the head of
		       * the sequence */
		      beginning_of_BS = $$ = last_BS = t;
		   }
		   else {
		      /* Place the Block at the end of the sequence */
                      if( force || *found == t->name ) {
		         last_BS->next = t;
		         last_BS = t;
		      }
                      else {
		         ERROR_MSG("Block Name is already present:");
		         ERROR_MSG(t->name);
		         free_Block_Seq(t);
		      }
		      $$ = $1;
		   }
		}
        ;

block :
	  global_block
		{  
		   DEBUG_MSG("block : global_block");
		   $$ = $1; 
		}
        | data_block
		{  
		   DEBUG_MSG("block : data_block");
		   $$ = $1; 
		}
	;

global_block :
	  GLOBAL_HEADING 
          data_block_body
		{  
                   register Block_Seq	*t;
                   register Global_Seq	*tmp_globals;

		   DEBUG_MSG("global_block : GLOBAL_HEADING data_block_body");
		   Malloc( Block_Seq, t);
		   t->tag = GLOBAL_BLOCK;
                   if( current_GH ) {
		      t->name = current_GH;
                      current_GH = NULL;
                   }
                   else {
		      t->name = next_GH;
		      next_GH = NULL;
		   }
		   t->block.global_block = $2;
		   root_Data_Names = NULL;
		   t->next = NULL;
                   /* add this to the head of the list of globals */
                   Malloc( Global_Seq, tmp_globals );
                   tmp_globals->global_entry = t;
                   tmp_globals->next = globals;
                   globals = tmp_globals;
		   $$ = t;
		}
        ;

data_block :
	  DATA_HEADING 
          data_block_body
		{  
                   register Block_Seq	*t;

		   DEBUG_MSG("data_block : DATA_HEADING data_block_body");
		   Malloc( Block_Seq, t);
		   t->tag = DATA_BLOCK;
                   if( current_DH ) {
		      t->name = current_DH;
                      current_DH = NULL;
                   }
                   else {
		      t->name = next_DH;
                      next_DH = NULL;
	           }
		   t->block.data_block.actual_data = $2;
		   root_Data_Names = NULL;
		   t->block.data_block.global_data = globals;
		   t->next = NULL;
		   $$ = t;
		}
        ;

data_block_body : 
	  /* empty */
		{
		   DEBUG_MSG("data_block_body : empty");
		   $$ = NULL
		}
        | data_block_body data
		{  
                   register Data_Seq	*t = $2;
		   register Data_Seq	*body = $1;
		   char			**found;

		   DEBUG_MSG("data_block_body : data_block_body data");

		   for(; t; t = t->next ) {
		      /* check that the name is not already present */
		      found = (char **)tsearch(t->name, &root_Data_Names, strcmp);

		      if( body == NULL ) {
		         /* forget the empty and return the data as the head of
		          * the sequence */
		         body = last_DS = t;
		      }
		      else
		         /* Place the Data at the end of the sequence */
                         if( *found == t->name ) {
		            last_DS->next = t;
		            last_DS = t;
		         }
                         else {
		            ERROR_MSG("Data Name is already present:");
		            ERROR_MSG(t->name);
/* must solve the problem of doing a t = t->next later
		            free_Data_Seq(t);
*/
		         }
		   }
		   $$ = body;
		}
        ;

data : 
	  DATA_NAME data_item 
		{
		   register Data_Seq	*d;
		
		   DEBUG_MSG("data : DATA_NAME data_item");
		   Malloc( Data_Seq, d);
		   d->name = current_DN;
		   d->tag = DATA_ITEM;
		   d->data.data_item = $2;
		   d->next = NULL;
 		   $$ = d; 
		}
	| data_loop
		{
		   DEBUG_MSG("data : data_loop");
 		   $$ = $1; 
		}
	| save_frame
		{
		   DEBUG_MSG("data : save_frame");
		   $$ = $1;
		}
        ;

save_frame :
	  SAVE_HEADING 
	  save_frame_body
	  SAVE_END 
		{
		   register Data_Seq	*d;
		
		   DEBUG_MSG("save_frame : SAVE_HEADING save_frame_body SAVE_END");
		   Malloc( Data_Seq, d);
		   d->tag = SAVE_BLOCK;
		   d->name = current_SH;
		   d->data.save_block = $2; 
		   root_Data_Names_save = NULL;
		   d->next = NULL;
 		   $$ = d; 
		}
	;

save_frame_body :
	  /* empty */
		{
		   DEBUG_MSG("save_frame_body : empty");
		   $$ = NULL;
		}
	| save_frame_body save_item
		{  
                   register Data_Seq	*t = $2;
		   register Data_Seq	*body = $1;
		   char			**found;

		   DEBUG_MSG("save_frame_body : save_frame_body save_item");

		   for(; t; t = t->next ) {
		      /* check that the name is not already present */
		      found = (char **)tsearch(t->name, &root_Data_Names_save, strcmp);

		      if( body == NULL ) {
		         /* forget the empty and return the data as the head of
		          * the sequence */
		         body = last_DS_save = t;
		      }
		      else
		         /* Place the Data at the end of the sequence */
                         if( *found == t->name ) {
		            last_DS_save->next = t;
		            last_DS_save = t;
		         }
                         else {
		            ERROR_MSG("Data Name is already present:");
		            ERROR_MSG(t->name);
/* must solve the problem of doing a t = t->next later
		            free_Data_Seq(t);
*/
		         }
		   }
		   $$ = body;
		}
	;

save_item :
	  DATA_NAME data_item 
		{
		   register Data_Seq	*d;
		
		   DEBUG_MSG("save_item : DATA_NAME data_item");
		   Malloc( Data_Seq, d);
		   d->name = current_DN;
		   d->tag = DATA_ITEM;
		   d->data.data_item = $2;
		   d->next = NULL;
 		   $$ = d; 
		}
	| data_loop
		{
		   DEBUG_MSG("save_item : data_loop");
 		   $$ = $1; 
		}
	;

data_loop :
	  loop_ 
	  data_loop_definition
		{
                   Data_Seq	*t;
                   register int	i, n;

		   /* take a definition and decompose it into a sequence of data
                   */
		   temp_DS = Data_Seq_froma_Data_Name_Seq( $2, $2 );

                   /* Set up stacks for processing in data_loop_values parsing.
                   */
                   if( ! RPIV )
                      if( RPIV = (int *)malloc( ++N_blocks_RPIV * BLOCK_SIZE * sizeof( int )) )
                         Sizeof_RPIV += BLOCK_SIZE;
                      else
                         ERROR_MSG("Out of memory, for RPIV.");
                   if( ! NPIV )
                      if( NPIV = (int *)malloc( ++N_blocks_NPIV * BLOCK_SIZE * sizeof( int )) )
                         Sizeof_NPIV += BLOCK_SIZE;
                      else
                         ERROR_MSG("Out of memory, for NPIV.");
                   if( ! tail_positions )
                      if( tail_positions = (ptrptrLVS *)malloc( ++N_blocks_tp * BLOCK_SIZE * sizeof( ptrptrLVS )) )
                         Sizeof_tp += BLOCK_SIZE;
                      else
                         ERROR_MSG("Out of memory, for tail_positions.");
                   if( ! restart_positions )
                      if( restart_positions = (ptrDNS *)malloc( ++N_blocks_rp * BLOCK_SIZE * sizeof( ptrDNS )) )
                         Sizeof_rp += BLOCK_SIZE;
                      else
                         ERROR_MSG("Out of memory, for restart_positions.");
                   if( ! next_positions )
                      if( next_positions = (ptrDNS *)malloc( ++N_blocks_np * BLOCK_SIZE * sizeof( ptrDNS )) )
                         Sizeof_np += BLOCK_SIZE;
                      else
                         ERROR_MSG("Out of memory, for next_positions.");

                   /* Set the beginning of the loop to be the first
                   ** restart position.
                   */
                   Push_Restart_Name_Posn( temp_DS->data.loop.packet_members );

                   /* Set the next node to be processed to be the beginning 
                   ** of the loop.
                   */
                   Push_Next_Name_Posn( temp_DS->data.loop.packet_members );
/* fprintf(stderr,"packet_members = %p\n",temp_DS->data.loop.packet_members); */

                   /* Initialise the stack. */
                   t = temp_DS;
                   n = Number_of_Names( t->data.loop.packet_members );
/* fprintf(stderr,"number of names in the loop = %d\n",n); */
                   for( i = 0; i < n; i++ ) {
                      /* Add where each node's data is to be placed 
                      ** onto the stack.
                      */
                      Push_Tail_Posn( &(t->data.loop.values) );
                      t = t->next;
                   }
                   /* Set the data positions at the bottom of the stack */
                   Push_Restart_Data_Posn( 0 );
                   Push_Next_Data_Posn( 0 );
		}
	  data_loop_values
		{
		   DEBUG_MSG("data_loop : LOOP_ data_loop_definition data_loop_values");
                   Stop_Loop( BOTTOM );
		   $$ = temp_DS;
		   temp_DS = NULL;
		}
	;

data_loop_definition :
	  data_loop_field
		{
		/* first piece of data */
		   DEBUG_MSG("data_loop_definition : data_loop_field");
/* ??? recursive use of data_loop_definition is the problem */
		   $$ = $1;
		}
	| data_loop_definition data_loop_field
		{
                   register Data_Name_Seq	*i;

		   DEBUG_MSG("data_loop_definition : data_loop_definition data_loop_field");
		   /* add the last one to the end of the list */
                   for( i = $$; i->next; i = i->next ); /* scan to the end of the list */
		   i->next = $2;
		   $$ = $1;
		}
	;

data_loop_field :
	  DATA_NAME 
		{
		   register Data_Name_Seq	*n;

		   DEBUG_MSG("data_loop_field : DATA_NAME");
		   Malloc( Data_Name_Seq, n);
		   n->tag = NAME;
		   n->node.name = current_DN;
		   n->next = NULL;
		   $$ = n;
		}
	| nested_data_loop
		{
		   register Data_Name_Seq	*n;

		   DEBUG_MSG("data_loop_field : nested_data_loop");
		   Malloc( Data_Name_Seq, n);
		   n->tag = SUB_LOOP;
		   n->node.sub_loop = $1;
		   n->next = NULL;
		   $$ = n;
		}
	;

nested_data_loop :
	  loop_ 
	  data_loop_definition
	  stop_
		{
		   DEBUG_MSG("nested_data_loop : LOOP_ data_loop_definition stop_");
		   $$ = $2;
		}
	;

loop_ :
	  LOOP_ 
		{
		   DEBUG_MSG("loop_ : LOOP_");
		}
	;

stop_ :
	  /* empty */
		{
		   DEBUG_MSG("stop_ : empty");
		}
	| STOP_ 
		{
		   DEBUG_MSG("stop_ : STOP_");
		}
	;

data_loop_values :
	  data_loop_item
		{
                   DEBUG_MSG("data_loop_values : data_loop_item ");
		}
	| data_loop_values data_loop_item 
		{
                   DEBUG_MSG("data_loop_values : data_loop_values data_loop_item");
		}
	;

data_loop_item :
	  data_item
		{
                   DEBUG_MSG("data_loop_item : data_item ");
                   Add_Data_Item( $1 );
		}
	| stop_
		{
                   DEBUG_MSG("data_loop_item : stop_ ");
                   Stop_Loop(STOP_);
		}
	;

data_item :
	  NON_QUOTED_TEXT_STRING
		{
                   DEBUG_MSG("data_item : NON_QUOTED_TEXT_STRING ");
		   $$ = current_di;
		}
	| DOUBLE_QUOTED_TEXT_STRING
		{
                   DEBUG_MSG("data_item : DOUBLE_QUOTED_TEXT_STRING ");
		   $$ = current_di;
		}
	| SINGLE_QUOTED_TEXT_STRING
		{
                   DEBUG_MSG("data_item : SINGLE_QUOTED_TEXT_STRING ");
		   $$ = current_di;
		}
	| SEMI_COLON_BOUNDED_TEXT_STRING 
		{
                   DEBUG_MSG("data_item : SEMI_COLON_BOUNDED_TEXT_STRING ");
		   $$ = current_di;
		}
	| FRAME_CODE
		{
                   DEBUG_MSG("data_item : FRAME_CODE ");
		   $$ = current_di;
		}
	;

%%
/* ancillary functions for parsing and building the internal representation */
Data_Seq *
Data_Seq_froma_Data_Name_Seq(
Data_Name_Seq	*packet,
Data_Name_Seq	*list )
{
   Data_Seq	*i;
   Data_Seq	*t = NULL;

   if( list ) {
      switch( list->tag ) {

      case NAME:
         /* build a data node */
         Malloc( Data_Seq, t);
         DEBUG_MSG("Data_Seq_froma_Data_Name_Seq, DATA_NAME:");
         DEBUG_MSG(list->node.name);
         t->name = list->node.name;
         t->tag = LOOP;
         t->data.loop.values = NULL;
         t->data.loop.packet_members = packet;
         /* recursively proceed along the list */
         t->next = Data_Seq_froma_Data_Name_Seq( packet, list->next );
         break;

      case SUB_LOOP:
         /* recursively descend into the Nested Loop */
         DEBUG_MSG("Data_Seq_froma_Data_Name_Seq, Recursive call for Sub Loop.");
         t = Data_Seq_froma_Data_Name_Seq( packet, list->node.sub_loop );
         /* recursively proceed along the list,
            placing the rest of the list after the Sub Loop */
         for( i = t; i->next; i = i->next ); /* scan to the end of the list */
         i->next = Data_Seq_froma_Data_Name_Seq( packet, list->next );
         break;

      default:
         ERROR_MSG("Data_Seq_froma_Data_Name_Seq: Unknown node type in sequence.");
      }
   }
   return( t );
} /* Data_Seq_froma_Data_Name_Seq */

/*
********************************************************************************
*/

/* Various Stacks for retaining state information between calls
*/

/* Operations on a stack of 
** Restart Positions In List_Value_Sequence
*/
int *RPIV = NULL;	/* stack of restart positions within the L_V_Ss */
int current_RPIV = -1;	/* the current top of the stack */
int Sizeof_RPIV = 0;	/* the current size of the stack */
int N_blocks_RPIV = 0;	/* the number of blocks in the stack */

/*
********************************************************************************
*/

/* Operations on a stack of 
** The Next Tail Position In List_Value_Sequence
*/
int *NPIV = NULL;	/* stack of offsets into the stack of tail positions
                	** within the L_V_Ss */
int current_NPIV = -1;	/* the current top of the stack */
int Sizeof_NPIV = 0;	/* the current size of the stack */
int N_blocks_NPIV = 0;	/* the number of blocks in the stack */

/*
********************************************************************************
*/

/* Operations on a stack of
** Pointers into List_Value_Sequence
*/
ptrptrLVS	*tail_positions = NULL;	/* stack of pointers to pointers */
int current_tp = -1;	/* the current top of the stack */
int Sizeof_tp = 0;	/* the current size of the stack */
int N_blocks_tp = 0;	/* the number of blocks in the stack */

/*
********************************************************************************
*/

/* Operations on a stack of
** Pointers into a Data_Name_Sequence,
** indicating the restart position for a packet
*/
ptrDNS	*restart_positions = NULL;	/* stack of pointers */
int current_rp = -1;	/* the current top of the stack */
int Sizeof_rp = 0;	/* the current size of the stack */
int N_blocks_rp = 0;	/* the number of blocks in the stack */

/*
********************************************************************************
*/

/* Operations on a stack of
** Pointers into a Data_Name_Sequence,
** indicating the next position in the packet
*/
ptrDNS	*next_positions = NULL;	/* stack of pointers */
int current_np = -1;	/* the current top of the stack */
int Sizeof_np = 0;	/* the current size of the stack */
int N_blocks_np = 0;	/* the number of blocks in the stack */

/*
********************************************************************************
*/

void
Add_Data_Item(
Data_Item *	data)
{
   ptrDNS		t = NULL;
   List_Value_Seq	*u = NULL;
   int			n,j,i = -1;
   
   if( !( t = Pop_Next_Name_Posn) ){
      /* at the end of a packet, go back to the beginning */
      DEBUG_MSG("Add_Data_Item: At the end of a packet, going back to the beginning.");
      t = Top_Restart_Name_Posn;
      (void) Pop_Next_Data_Posn;
      i = Top_Restart_Data_Posn;
      Push_Next_Data_Posn( i );
   }
   
/* debug
fprintf(stderr,"t = %p\n",t);
*/
   switch( t->tag ) {
   case NAME:
      DEBUG_MSG("Add_Data_Item: data for,");
      DEBUG_MSG(t->node.name);
      /* build a data node */
      Malloc( List_Value_Seq, u);
      u->tag = DATA_ITEM;
      u->element.data_item = data;
      u->next = NULL;
      /* add the node to the values already held */
      *(tail_positions[ Top_Next_Data_Posn ]) = u;
      /* replace the next position for the next time around */
      tail_positions[ Top_Next_Data_Posn ] = &(u->next);
      /* shift to the next data position */
      i = Pop_Next_Data_Posn;
      Push_Next_Data_Posn( i + 1 );
      /* shift to the next node in Data_Name_Sequence */
      Push_Next_Name_Posn( t->next );
      break;

   case SUB_LOOP:
      DEBUG_MSG("Add_Data_Item: Set up a sub-loop.");
      /* set up the name stacks for step down into the next level */
      /* shift to the next node in Data_Name_Sequence, at this higher level */
      Push_Next_Name_Posn( t->next );
      /* push the beginning of the sub_loop onto the restart stack */
      Push_Restart_Name_Posn( t->node.sub_loop );
      /* set the next name to the beginning of the sub_loop */
      Push_Next_Name_Posn( t->node.sub_loop );

      n = Number_of_Names( t->node.sub_loop );
      for( j = 0; j < n; j++ ) {
         /* build a sub_loop node */
         Malloc( List_Value_Seq, u);
         u->tag = SUB_LOOP;
         u->element.sub_loop = NULL;
         u->next = NULL;
         /* get the next data to be updated */
         i = Pop_Next_Data_Posn;
         /* add the node to the values already held */
         *(tail_positions[ i ]) = u;
         /* overwrite the next position for the next time around */
         tail_positions[ i ] = &(u->next);
         /* push the sub_loop position onto the top, for the lower level */
         Push_Tail_Posn( &(u->element.sub_loop) ); 
         if( ! j )
            /* the first time */
            /* so place the restart position */
            Push_Restart_Data_Posn( current_tp );
         /* shift to the next data position */
         Push_Next_Data_Posn( i + 1 );
      }
      /* set the next data position for the sub_loop */
      i = Top_Restart_Data_Posn;
      Push_Next_Data_Posn( i );
      /* recall yourself with the same input */
      Add_Data_Item( data );
      break;

   default:
      ERROR_MSG("Add_Data_Item: Unknown node in a Data_Name_Sequence.");
   }
} /* Add_Data_Item */

void
Stop_Loop(
Domain	token)
{
   ptrDNS	last;

   if( last = Pop_Next_Name_Posn ) {
      /* there is still some data left to be processed */
      /* Assume the incoming data has its data "stop_" in the right position.
      ** For now, ignore the rest of the loop structure, even though this will
      ** put loop data out of allignment for future processing.
      */
      ERROR_MSG("Misaligned loop data, expecting data for:");
      switch( last->tag ) {
      case NAME:
         ERROR_MSG(last->node.name);
         break;
      case SUB_LOOP:
         /* what we really need to do is to set up a sub_loop on the stacks,
         ** proceed down into that next level, get the names, and then come
         ** back up to the next level.
         */
         ERROR_MSG("a whole Sub-Loop");
         break;
      default:
         ERROR_MSG("Stop_Loop: Unexpected node in a Data Name Sequence");
      }
   }
   /* Now proceed back up to the previous level */
   (void) Pop_Restart_Name_Posn;
   /* shrink down the Data Stack */
   while( current_tp >= Top_Restart_Data_Posn ) Decrement_Tail_Posn;
   (void) Pop_Restart_Data_Posn;
   (void) Pop_Next_Data_Posn;
   /* if there is no more data and we still arn't at the top of the loop,
   ** then keep going
   */
   if( token == BOTTOM && current_rp >= 0 ) Stop_Loop( token );
} /* Stop_Loop */

yyerror(char *s)
{
  char	*t;
  int	i = YYTRANSLATE(yychar);

  /* assume 12 chars will be enough to print an int */
  t = (char *)malloc( (22 + 12 + 1) * sizeof(char));
  ERROR_MSG(sprintf( t, "Syntax Error in line: %-12d", star_line_count));
  free( t );
  t = (char *)malloc( (12 + strlen(yytname[i]) + 1) * sizeof(char));
  ERROR_MSG(sprintf( t, "Unexpected %s,", yytname[i]));
  ERROR_MSG(last_star_token);
  free( t );
}
