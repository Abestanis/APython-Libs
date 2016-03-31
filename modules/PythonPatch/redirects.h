#ifndef OUTPUT_REDIRECT_H
#define OUTPUT_REDIRECT_H

// Because Android does not define it
typedef long fd_mask;

//extern int (*androidMoreCommandPointer)(const char* command);

int redirectedIsATty(int fd);
int redirectedIOCtl(int fd, int request, ...);
void __attribute__((noreturn)) redirectedExit(int code);
char* redirectedSetLocale(int category, const char *locale);
//int redirectedSystem(const char *command);

#endif // OUTPUT_REDIRECT_H //
