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
#ifndef MS_WINI64
extern PyObject* PyInit_audioop(void);
#endif
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
#ifdef WIN32
extern PyObject* PyInit_msvcrt(void);
extern PyObject* PyInit__locale(void);
#endif
extern PyObject* PyInit__codecs(void);
extern PyObject* PyInit__weakref(void);
extern PyObject* PyInit_xxsubtype(void);
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
//extern PyObject* PyInit__winreg(void);
extern PyObject* PyInit__struct(void);
extern PyObject* PyInit__datetime(void);
extern PyObject* PyInit__functools(void);
extern PyObject* PyInit__json(void);
extern PyObject* PyInit_zlib(void);
extern PyObject* PyInit_pwd(void);
extern PyObject* PyInit_termios(void);
//extern PyObject* PyInit_rgbimg(void);
extern PyObject* PyInit_select(void);
extern PyObject* PyInit__socket(void);
//extern PyObject* PyInit_pcre(void);
extern PyObject* PyInit_fcntl(void);

extern PyObject* PyInit__multibytecodec(void);

extern PyObject* PyInit__codecs_cn(void);
extern PyObject* PyInit__codecs_hk(void);
extern PyObject* PyInit__codecs_iso2022(void);
extern PyObject* PyInit__codecs_jp(void);
extern PyObject* PyInit__codecs_kr(void);
extern PyObject* PyInit__codecs_tw(void);
//extern PyObject* PyInit__subprocess(void);
extern PyObject* PyInit__lsprof(void);
extern PyObject* PyInit__io(void);
extern PyObject* PyInit__ssl(void);
extern PyObject* PyInit_unicodedata(void);
extern PyObject* PyInit__ctypes(void);

struct _inittab _PyImport_Inittab[] = {

/* -- ADDMODULE MARKER 2 -- */

    /* This module lives in marshal.c */
    {"marshal", PyMarshal_Init},

    /* This lives in import.c */
    {"imp", PyInit_imp},

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

    //TODO: Edited:

    {"errno", PyInit_errno},

    {"array", PyInit_array},
    #ifdef MS_WINDOWS
    #ifndef MS_WINI64
    {"audioop", PyInit_audioop},
    #endif
    #endif
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
    {"_Pickle", PyInit__pickle},
    #ifdef WIN32
    {"msvcrt", PyInit_msvcrt},
    {"_locale", PyInit__locale},
    #endif
//    {"_subprocess", PyInit__subprocess},

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
//    {"_winreg", PyInit__winreg},
    {"_struct", PyInit__struct},
    {"_datetime", PyInit__datetime},
    {"_functools", PyInit__functools},
    {"_json", PyInit__json},

    {"xxsubtype", PyInit_xxsubtype},
    {"zipimport", PyInit_zipimport},
    {"zlib", PyInit_zlib},
    {"pwd", PyInit_pwd},
    {"termios", PyInit_termios},
    //{"rgbimg", PyInit_rgbimg},
    {"select", PyInit_select},
    {"_socket", PyInit__socket},
    //{"pcre", PyInit_pcre},
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
    {"_ssl", PyInit__ssl},
    {"unicodedata", PyInit_unicodedata},
    {"_ctypes", PyInit__ctypes},

    /* Sentinel */
    {0, 0}
};


#ifdef __cplusplus
}
#endif
