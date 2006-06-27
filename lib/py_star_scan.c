/* Call our flex scanner */
#include "Python.h"
#include <string.h>

#define STAR_SCANNER
#include "star_scanner.h"

static PyObject * get_input(PyObject * self, PyObject * args);
static PyObject * flex_scan(PyObject * self,PyObject * args);

static PyMethodDef StarScanMethods[] = {
    {"prepare",get_input, METH_VARARGS,"Prepare scanner input"},
    {"scan", flex_scan, METH_VARARGS, "Get next token"},
    {NULL,NULL,0,NULL}
    };


PyMODINIT_FUNC
initStarScan(void)
{
    (void) Py_InitModule("StarScan", StarScanMethods);
}

/* We need to read from the text string that the Python
scanner uses, so we get a handle on the string and use
that to feed flex */

static PyObject * 
get_input(PyObject * self, PyObject * args) 
{
PyObject * str_arg;  /* A python string object in theory */
if(!(PyArg_ParseTuple(args,"O",&str_arg))) return NULL;
input_string = PyString_AsString(str_arg);
string_pos = 0;
in_string_len = strlen(input_string);
star_clear();
return(Py_BuildValue(""));
}

static PyObject *
flex_scan(PyObject * self, PyObject * args)
{
char * token_str;    /* String token */
static char end_str[] = "END";
token_str = star_scanner();
if(token_str == 0) {
    printf("End seen\n");
    token_str = &end_str;
    }
return(Py_BuildValue("(iiss)",0,0,token_str,yytext));
}
