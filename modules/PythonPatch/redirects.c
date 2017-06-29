#include "redirects.h"
#include <locale.h>
#include <pthread.h>
#include <stdlib.h>

// because: https://github.com/awong-dev/ndk/blob/master/sources/android/support/src/locale/setlocale.c
char* redirectedSetLocale(int category, const char *locale) {
    if (locale == NULL) {
        static const char C_LOCALE[] = "C";
        return (char*) C_LOCALE;
    }
    return setlocale(category, locale);
}

void __noreturn redirectedExit(int code) {
    pthread_exit((void*) code);
}

// Androids mbstowcs does not ignore the len parameter if dest is NULL
// and it includes the null terminating character in its return size
extern size_t redirectedMbstowcs(wchar_t *dest, const char *src, size_t len) {
    return dest == NULL ? mbstowcs(dest, src, 99999) - 1 : mbstowcs(dest, src, len) - 1;
}
