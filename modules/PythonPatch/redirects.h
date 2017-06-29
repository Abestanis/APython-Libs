#ifndef OUTPUT_REDIRECT_H
#define OUTPUT_REDIRECT_H

#include <wchar.h>

char* redirectedSetLocale(int category, const char *locale);
void redirectedExit(int code);
size_t redirectedMbstowcs(wchar_t *dest, const char * src, size_t len);

#endif // OUTPUT_REDIRECT_H //
