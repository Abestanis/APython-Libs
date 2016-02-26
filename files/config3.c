/* -*- C -*- ***********************************************
Copyright (c) 2000, BeOpen.com.
Copyright (c) 1995-2000, Corporation for National Research Initiatives.
Copyright (c) 1990-1995, Stichting Mathematisch Centrum.
All rights reserved.

See the file "Misc/COPYRIGHT" for information on usage and
redistribution of this file, and for a DISCLAIMER OF ALL WARRANTIES.
******************************************************************/

/* Module configuration */

/* !!! !!! !!! This file is edited by the makesetup script !!! !!! !!! */

/* This file contains the table of built-in modules.
   See init_builtin() in import.c. */

#include "Python.h"

#ifdef __cplusplus
extern "C" {
#endif


/* -- ADDMODULE MARKER 1 -- */

extern PyObject* PyMarshal_Init(void);
extern PyObject* PyInit_imp(void);
extern PyObject* PyInit_gc(void);
extern PyObject* PyInit__ast(void);
extern PyObject* _PyWarnings_Init(void);
extern PyObject* PyInit__string(void);

extern PyObject* PyInit_errno(void);

extern PyObject* PyInit_array(void);
extern PyObject* PyInit_audioop(void);
extern PyObject* PyInit_binascii(void);
extern PyObject* PyInit_cmath(void);
extern PyObject* PyInit_math(void);
extern PyObject* PyInit__md5(void);
extern PyObject* PyInit_posix(void);
extern PyObject* PyInit__operator(void);
extern PyObject* PyInit_signal(void);
extern PyObject* PyInit__sha1(void);
extern PyObject* PyInit__sha256(void);
extern PyObject* PyInit__sha512(void);
extern PyObject* PyInit_time(void);
extern PyObject* PyInit__thread(void);
extern PyObject* PyInit__pickle(void);
extern PyObject* PyInit__locale(void);
extern PyObject* PyInit__codecs(void);
extern PyObject* PyInit__weakref(void);
extern PyObject* PyInit_zipimport(void);
extern PyObject* PyInit__random(void);
extern PyObject* PyInit_itertools(void);
extern PyObject* PyInit__collections(void);
extern PyObject* PyInit__heapq(void);
extern PyObject* PyInit__bisect(void);
extern PyObject* PyInit__symtable(void);
extern PyObject* PyInit_mmap(void);
extern PyObject* PyInit__csv(void);
extern PyObject* PyInit__sre(void);
extern PyObject* PyInit_parser(void);
extern PyObject* PyInit__struct(void);
extern PyObject* PyInit__datetime(void);
extern PyObject* PyInit__functools(void);
extern PyObject* PyInit__json(void);
extern PyObject* PyInit_zlib(void);
extern PyObject* PyInit_pwd(void);
extern PyObject* PyInit_termios(void);
extern PyObject* PyInit_select(void);
extern PyObject* PyInit__socket(void);
extern PyObject* PyInit_fcntl(void);

extern PyObject* PyInit__multibytecodec(void);

extern PyObject* PyInit__codecs_cn(void);
extern PyObject* PyInit__codecs_hk(void);
extern PyObject* PyInit__codecs_iso2022(void);
extern PyObject* PyInit__codecs_jp(void);
extern PyObject* PyInit__codecs_kr(void);
extern PyObject* PyInit__codecs_tw(void);
extern PyObject* PyInit__lsprof(void);
extern PyObject* PyInit__io(void);
extern PyObject* PyInit_unicodedata(void);
extern PyObject* PyInit_atexit(void);
extern PyObject* PyInit__posixsubprocess(void);
extern PyObject* PyInit_pyexpat(void);
extern PyObject* PyInit__elementtree(void);
extern PyObject* PyInit__multiprocessing(void);
extern PyObject* PyInit_ossaudiodev(void);
extern PyObject* PyInit__opcode(void);
extern PyObject* PyInit__stat(void);
extern PyObject* PyInit__tracemalloc(void);
extern PyObject* PyInit_faulthandler(void);
extern PyObject* PyInit_resource(void);
extern PyObject* PyInit_syslog(void);

struct _inittab _PyImport_Inittab[] = {

/* -- ADDMODULE MARKER 2 -- */

    /* This module lives in marshal.c */
    {"marshal", PyMarshal_Init},

    /* This lives in import.c */
    {"_imp", PyInit_imp},

    /* This lives in Python/Python-ast.c */
    {"_ast", PyInit__ast},
    
    /* This lives in Objects/unicodeobject.c */
    {"_string", PyInit__string},

    /* These entries are here for sys.builtin_module_names */
    {"__main__", NULL},
    {"__builtin__", NULL},
    {"sys", NULL},
    {"exceptions", NULL},

    /* This lives in gcmodule.c */
    {"gc", PyInit_gc},

    /* This lives in _warnings.c */
    {"_warnings", _PyWarnings_Init},

    {"errno", PyInit_errno},

    {"array", PyInit_array},
    {"audioop", PyInit_audioop},
    {"binascii", PyInit_binascii},
    {"cmath", PyInit_cmath},
    {"errno", PyInit_errno},
    {"math", PyInit_math},
    {"_md5", PyInit__md5},
    {"posix", PyInit_posix},
    {"_operator", PyInit__operator},
    {"signal", PyInit_signal},
    {"_sha1", PyInit__sha1},
    {"_sha256", PyInit__sha256},
    {"_sha512", PyInit__sha512},
    {"time", PyInit_time},
    #ifdef WITH_THREAD
    {"_thread", PyInit__thread},
    #endif
    {"_pickle", PyInit__pickle},
    {"_locale", PyInit__locale},

    {"_codecs", PyInit__codecs},
    {"_weakref", PyInit__weakref},
    {"_random", PyInit__random},
    {"_bisect", PyInit__bisect},
    {"_heapq", PyInit__heapq},
    {"_lsprof", PyInit__lsprof},
    {"itertools", PyInit_itertools},
    {"_collections", PyInit__collections},
    {"_symtable", PyInit__symtable},
    {"mmap", PyInit_mmap},
    {"_csv", PyInit__csv},
    {"_sre", PyInit__sre},
    {"parser", PyInit_parser},
    {"_struct", PyInit__struct},
    {"_datetime", PyInit__datetime},
    {"_functools", PyInit__functools},
    {"_json", PyInit__json},

    {"zipimport", PyInit_zipimport},
    {"zlib", PyInit_zlib},
    {"pwd", PyInit_pwd},
    {"termios", PyInit_termios},
    {"select", PyInit_select},
    {"_socket", PyInit__socket},
    {"fcntl", PyInit_fcntl},

    /* CJK codecs */
    {"_multibytecodec", PyInit__multibytecodec},
    {"_codecs_cn", PyInit__codecs_cn},
    {"_codecs_hk", PyInit__codecs_hk},
    {"_codecs_iso2022", PyInit__codecs_iso2022},
    {"_codecs_jp", PyInit__codecs_jp},
    {"_codecs_kr", PyInit__codecs_kr},
    {"_codecs_tw", PyInit__codecs_tw},

    {"_io", PyInit__io},
    {"unicodedata", PyInit_unicodedata},
    {"atexit", PyInit_atexit},
    {"_posixsubprocess", PyInit__posixsubprocess},
    {"pyexpat", PyInit_pyexpat},
    {"_elementtree", PyInit__elementtree},
    {"_multiprocessing", PyInit__multiprocessing},
    {"ossaudiodev", PyInit_ossaudiodev},
    {"_opcode", PyInit__opcode},
    {"_stat", PyInit__stat},
    {"_tracemalloc", PyInit__tracemalloc},
    {"faulthandler", PyInit_faulthandler},
    {"resource", PyInit_resource},
    {"syslog", PyInit_syslog},

    /* Sentinel */
    {0, 0}
};


#ifdef __cplusplus
}
#endif
