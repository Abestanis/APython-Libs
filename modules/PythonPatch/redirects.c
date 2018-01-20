#include <locale.h>
#include <stdlib.h>
#include <unistd.h>
#include "redirects.h"

char* __real_setlocale(int category, const char *locale);
void __noreturn __real_exit(int code);
size_t __real_mbstowcs(wchar_t *dest, const char *src, size_t len);
char* __real_ttyname(int __fd);

static _exitHandler exitHandler = NULL;
static char ttyPathBuffer[128];

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

char* __wrap_ttyname(int __fd) {
    char* filePath = __real_ttyname(__fd);
    if (filePath != NULL || !isatty(__fd)) {
        return filePath;
    }
    char pathBuffer[64];
    snprintf(pathBuffer, 64, "/proc/self/fd/%d", __fd);
    ssize_t pathSize = readlink(
            pathBuffer, ttyPathBuffer, sizeof(ttyPathBuffer) / sizeof(ttyPathBuffer[0]) - 1);
    if (pathSize == -1) { return NULL; }
    ttyPathBuffer[pathSize] = '\0';
    return ttyPathBuffer;
    
}
