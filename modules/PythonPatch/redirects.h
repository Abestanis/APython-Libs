#ifndef OUTPUT_REDIRECT_H
#define OUTPUT_REDIRECT_H

#ifdef __cplusplus
extern "C" {
#endif
#include <wchar.h>

typedef void (*_exitHandler)(int exitCode);

__attribute__((visibility("default"))) void setExitHandler(_exitHandler handler);
char* __wrap_setlocale(int category, const char *locale);
void __noreturn __wrap_exit(int code);
size_t __wrap_mbstowcs(wchar_t *dest, const char * src, size_t len);

#ifdef __cplusplus
}
#endif
#endif // OUTPUT_REDIRECT_H //
