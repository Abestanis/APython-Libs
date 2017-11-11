#include <locale.h>
#include <stdlib.h>
#include "redirects.h"

char* __real_setlocale(int category, const char *locale);
void __noreturn __real_exit(int code);
size_t __real_mbstowcs(wchar_t *dest, const char *src, size_t len);

static _exitHandler exitHandler = NULL;

// because: https://github.com/awong-dev/ndk/blob/master/sources/android/support/src/locale/setlocale.c
char* __wrap_setlocale(int category, const char *locale) {
    if (locale == NULL) {
        static const char C_LOCALE[] = "C";
        return (char*) C_LOCALE;
    }
    return __real_setlocale(category, locale);
}

__attribute__((visibility("default"))) void setExitHandler(_exitHandler handler) {
    exitHandler = handler;
}

void __noreturn __wrap_exit(int code) {
    if (exitHandler != NULL) {
        exitHandler(code);
    }
    __real_exit(code);
}

// Androids mbstowcs does not ignore the len parameter if dest is NULL
// and it includes the null terminating character in its return size
size_t __wrap_mbstowcs(wchar_t *dest, const char *src, size_t len) {
    return dest == NULL ? __real_mbstowcs(dest, src, 99999) - 1 : __real_mbstowcs(dest, src, len) - 1;
}
