#ifdef STAR_SCANNER
char * input_string;     /* where flex gets input */
size_t string_pos;          /* current position */
size_t in_string_len;       /* total length */
extern char * star_scanner(void);
extern void star_clear(void);
extern char * yytext;
#else
extern char * input_string;
extern size_t string_pos;
extern size_t in_string_len;
#endif

