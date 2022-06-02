cmake_minimum_required(VERSION 3.5.0)

# TODO: Recheck excluded files

set(PYTHON_SHORT_VERSION 3.10)
project(Python${PYTHON_SHORT_VERSION} C)

if(NOT DEFINED CMAKE_ANDROID_ARCH_ABI)
    message(FATAL_ERROR "Build must be a crosscompile for Android!")
endif()

if(${CMAKE_ANDROID_ARCH_ABI} STREQUAL "arm64-v8a" OR
        ${CMAKE_ANDROID_ARCH_ABI} STREQUAL "mips64" OR
        ${CMAKE_ANDROID_ARCH_ABI} STREQUAL "x86_64")
    add_definitions(-DABI_64_BIT -DCONFIG_64)
else()
    add_definitions(-UABI_64_BIT -DCONFIG_32)
endif()
if(${CMAKE_ANDROID_ARCH_ABI} STREQUAL "arm64-v8a" OR
        ${CMAKE_ANDROID_ARCH_ABI} STREQUAL "armeabi-v7a" OR
        ${CMAKE_ANDROID_ARCH_ABI} STREQUAL "armeabi-v6" OR
        ${CMAKE_ANDROID_ARCH_ABI} STREQUAL "armeabi" OR
        ${CMAKE_ANDROID_ARCH_ABI} STREQUAL "mips" OR
        ${CMAKE_ANDROID_ARCH_ABI} STREQUAL "mips64")
    add_definitions(-DANSI) # TODO: Check if this is necessary
endif()
if(${CMAKE_ANDROID_ARCH_ABI} STREQUAL "x86" OR
        ${CMAKE_ANDROID_ARCH_ABI} STREQUAL "x86_64")
    add_definitions(-DASM) # TODO: Check if this is necessary
endif()
if(${CMAKE_ANDROID_ARCH_ABI} STREQUAL "x86")
    add_definitions(-UCONFIG_64 -DPPRO)
endif()
if(${CMAKE_ANDROID_ARCH_ABI} STREQUAL "x86_64")
    add_definitions(-DBLAKE2_USE_SSE=1)
endif()

add_library(python${PYTHON_SHORT_VERSION} SHARED)
find_library(z-lib z)
set(pythonPatch-lib -Wl,--whole-archive pythonPatch -Wl,--no-whole-archive)

add_definitions(-DPLATFORM="android" -DVERSION="${PYTHON_SHORT_VERSION}" -DHAVE_EXPAT_CONFIG_H
        -DSOABI="apython-${CMAKE_ANDROID_ARCH_ABI}" -DEXTRA_FUNCTIONALITY -DNDEBUG -DABIFLAGS=""
        -DPy_BUILD_CORE -DPy_BUILD_CORE_BUILTIN -DPLATLIBDIR="lib" -DXML_DEV_URANDOM)


include(CheckTypeSize)
include(TestBigEndian)
set(ALIGNOF_LONG 4)
set(ALIGNOF_SIZE_T 4)
set(ANDROID_API_LEVEL ${CMAKE_SYSTEM_VERSION})
if(ANDROID_API_LEVEL EQUAL 1)
    STRING(REGEX REPLACE "^android-" "" ANDROID_API_LEVEL "${ANDROID_PLATFORM}")
endif()
set(haveFloatEndianessSource "${CMAKE_BINARY_DIR}${CMAKE_FILES_DIRECTORY}/CMakeTmp/src.c")
file(WRITE "${haveFloatEndianessSource}" "
double d = 90904234967036810337470478905505011476211692735615632014797120844053488865816695273723469097858056257517020191247487429516932130503560650002327564517570778480236724525140520121371739201496540132640109977779420565776568942592.0;
int main() {
    volatile double a = d; 
    return 0;
}
")
set(haveFloatEndianessBinary ${CMAKE_BINARY_DIR}${CMAKE_FILES_DIRECTORY}/CheckTypeSize/${var}.bin)
try_compile(haveFloatEndianess ${CMAKE_BINARY_DIR} ${haveFloatEndianessSource}
        COMPILE_DEFINITIONS ${CMAKE_REQUIRED_DEFINITIONS}
        LINK_OPTIONS ${CMAKE_REQUIRED_LINK_OPTIONS}
        LINK_LIBRARIES ${CMAKE_REQUIRED_LIBRARIES}
        CMAKE_FLAGS
        "-DCOMPILE_DEFINITIONS:STRING=${CMAKE_REQUIRED_FLAGS}"
        "-DINCLUDE_DIRECTORIES:STRING=${CMAKE_REQUIRED_INCLUDES}"
        COPY_FILE ${haveFloatEndianessBinary})
file(REMOVE ${haveFloatEndianessSource})
if(haveFloatEndianess)
    file(STRINGS ${haveFloatEndianessBinary} strings REGEX "^seesnoon$|^noonsees$")
    file(REMOVE ${haveFloatEndianessBinary})
    if("${strings}" STREQUAL noonsees)
        set(FLOAT_WORDS_BIGENDIAN True)
        set(DOUBLE_IS_BIG_ENDIAN_IEEE754 True)
    elseif("${strings}" STREQUAL seesnoon)
        set(DOUBLE_IS_LITTLE_ENDIAN_IEEE754 True)
    else()
        set(DOUBLE_IS_ARM_MIXED_ENDIAN_IEEE754 True)
    endif()
endif()
set(ENABLE_IPV6 TRUE)
check_c_source_compiles("
#include <unistd.h>

int main() {
    (void) getpgrp(0);
    return 0;
}
" GETPGRP_HAVE_ARG)
check_function_exists(accept4 HAVE_ACCEPT4)
check_function_exists(acosh HAVE_ACOSH)
check_include_file(netdb.h HAVE_NETDB_H)
if(HAVE_NETDB_H)
    list(APPEND CMAKE_EXTRA_INCLUDE_FILES netdb.h)
    check_type_size("struct addrinfo" SIZEOF_ADDRINFO LANGUAGE C)
    set(HAVE_ADDRINFO ${HAVE_SIZEOF_ADDRINFO})
    list(REMOVE_AT CMAKE_EXTRA_INCLUDE_FILES -1)
endif()
check_function_exists(alarm HAVE_ALARM)
check_include_file(alloca.h HAVE_ALLOCA_H)
check_symbol_exists(altzone time.h HAVE_ALTZONE)
check_function_exists(asinh HAVE_ASINH)
check_include_file(asm/types.h HAVE_ASM_TYPES_H)
check_function_exists(atanh HAVE_ATANH)
check_function_exists(bind_textdomain_codeset HAVE_BIND_TEXTDOMAIN_CODESET)
check_include_file(bluetooth/bluetooth.h HAVE_BLUETOOTH_BLUETOOTH_H)
check_include_file(bluetooth.h HAVE_BLUETOOTH_H)

check_c_source_compiles("
int val;
int main() {
    __atomic_store_n(&val, 1, __ATOMIC_SEQ_CST);
    (void)__atomic_load_n(&val, __ATOMIC_SEQ_CST);
    return 0;
}
" HAVE_BUILTIN_ATOMIC)
check_function_exists(chflags HAVE_CHFLAGS)
check_function_exists(chown HAVE_CHOWN)
check_function_exists(chroot HAVE_CHROOT)
check_function_exists(clock HAVE_CLOCK)
check_function_exists(clock_getres HAVE_CLOCK_GETRES)
check_function_exists(clock_gettime HAVE_CLOCK_GETTIME)
check_function_exists(clock_settime HAVE_CLOCK_SETTIME)
check_function_exists(close_range HAVE_CLOSE_RANGE)
set(HAVE_COMPUTED_GOTOS TRUE)
check_function_exists(confstr HAVE_CONFSTR)
check_include_file(conio.h HAVE_CONIO_H)
check_function_exists(copysign HAVE_COPYSIGN)
check_function_exists(copy_file_range HAVE_COPY_FILE_RANGE)
check_include_file(crypt.h HAVE_CRYPT_H)
check_function_exists(crypt_r HAVE_CRYPT_R)
check_function_exists(ctermid HAVE_CTERMID)
check_function_exists(ctermid_r HAVE_CTERMID_R)
set(HAVE_CURSES_FILTER TRUE)
set(HAVE_CURSES_H TRUE)
set(HAVE_CURSES_HAS_KEY TRUE)
set(HAVE_CURSES_IMMEDOK TRUE)
set(HAVE_CURSES_IS_PAD TRUE)
set(HAVE_CURSES_IS_TERM_RESIZED TRUE)
set(HAVE_CURSES_RESIZETERM TRUE)
set(HAVE_CURSES_RESIZE_TERM TRUE)
set(HAVE_CURSES_SYNCOK TRUE)
set(HAVE_CURSES_TYPEAHEAD TRUE)
set(HAVE_CURSES_USE_ENV TRUE)
set(HAVE_CURSES_WCHGAT TRUE)
set(HAVE_CURSES_WCHGAT TRUE)
check_symbol_exists(isfinite math.h HAVE_DECL_ISFINITE)
check_symbol_exists(isinf math.h HAVE_DECL_ISINF)
check_symbol_exists(isnan math.h HAVE_DECL_ISNAN)
check_symbol_exists(RTLD_DEEPBIND dlfcn.h HAVE_DECL_RTLD_DEEPBIND)
check_symbol_exists(RTLD_GLOBAL dlfcn.h HAVE_DECL_RTLD_GLOBAL)
check_symbol_exists(RTLD_LAZY dlfcn.h HAVE_DECL_RTLD_LAZY)
check_symbol_exists(RTLD_LOCAL dlfcn.h HAVE_DECL_RTLD_LOCAL)
check_symbol_exists(RTLD_MEMBER dlfcn.h HAVE_DECL_RTLD_MEMBER)
check_symbol_exists(RTLD_NODELETE dlfcn.h HAVE_DECL_RTLD_NODELETE)
check_symbol_exists(RTLD_NOLOAD dlfcn.h HAVE_DECL_RTLD_NOLOAD)
check_symbol_exists(RTLD_NOW dlfcn.h HAVE_DECL_RTLD_NOW)
check_symbol_exists(tzname time.h HAVE_DECL_TZNAME)
set(HAVE_DEVICE_MACROS TRUE)
set(HAVE_DEV_PTMX TRUE)
check_include_file(direct.h HAVE_DIRECT_H)
check_struct_has_member("struct dirent" d_type dirent.h HAVE_DIRENT_D_TYPE)
check_include_file(dirent.h HAVE_DIRENT_HEADER)
if(HAVE_DIRENT_HEADER)
    check_c_source_compiles("
#include <dirent.h>
int main() {
    DIR* dir;
    return 0;
}
" HAVE_DIRENT_H)
endif()
check_symbol_exists(dirfd dirent.h HAVE_DIRFD)
check_include_file(dlfcn.h HAVE_DLFCN_H)
check_function_exists(dlopen HAVE_DLOPEN)
check_function_exists(dup2 HAVE_DUP2)
check_function_exists(dup3 HAVE_DUP3)
check_function_exists(_dyld_shared_cache_contains_path HAVE_DYLD_SHARED_CACHE_CONTAINS_PATH)
check_function_exists(_dyld_shared_cache_contains_path HAVE_DYLD_SHARED_CACHE_CONTAINS_PATH)
set(HAVE_DYNAMIC_LOADING TRUE)
check_include_file(endian.h HAVE_ENDIAN_H)
check_function_exists(epoll_create HAVE_EPOLL)
check_function_exists(epoll_create1 HAVE_EPOLL_CREATE1)
check_function_exists(erf HAVE_ERF)
check_function_exists(erfc HAVE_ERFC)
check_include_file(errno.h HAVE_ERRNO_H)
check_function_exists(eventfd HAVE_EVENTFD)
check_function_exists(execv HAVE_EXECV)
check_function_exists(explicit_bzero HAVE_EXPLICIT_BZERO)
check_function_exists(explicit_memset HAVE_EXPLICIT_MEMSET)
check_function_exists(expm1 HAVE_EXPM1)
check_function_exists(faccessat HAVE_FACCESSAT)
check_function_exists(fchdir HAVE_FCHDIR)
check_function_exists(fchmod HAVE_FCHMOD)
check_function_exists(fchmodat HAVE_FCHMODAT)
check_function_exists(fchown HAVE_FCHOWN)
check_function_exists(fchownat HAVE_FCHOWNAT)
check_include_file(fcntl.h HAVE_FCNTL_H)
check_function_exists(fdatasync HAVE_FDATASYNC)
check_function_exists(fdopendir HAVE_FDOPENDIR)
check_function_exists(fdwalk HAVE_FDWALK)
check_function_exists(fexecve HAVE_FEXECVE)
check_function_exists(finite HAVE_FINITE)
check_function_exists(flock HAVE_FLOCK)
check_function_exists(fork HAVE_FORK)
check_function_exists(forkpty HAVE_FORKPTY)
check_function_exists(fpathconf HAVE_FPATHCONF)
check_function_exists(fseek64 HAVE_FSEEK64)
check_function_exists(fseeko HAVE_FSEEKO)
check_function_exists(fstatat HAVE_FSTATAT)
check_function_exists(fstatvfs HAVE_FSTATVFS)
check_function_exists(fsync HAVE_FSYNC)
check_function_exists(ftell64 HAVE_FTELL64)
check_function_exists(ftello HAVE_FTELLO)
check_function_exists(ftime HAVE_FTIME)
check_function_exists(ftruncate HAVE_FTRUNCATE)
check_function_exists(futimens HAVE_FUTIMENS)
check_function_exists(futimes HAVE_FUTIMES)
check_function_exists(futimesat HAVE_FUTIMESAT)
check_function_exists(gai_strerror HAVE_GAI_STRERROR)
check_function_exists(gamma HAVE_GAMMA)
check_c_source_compiles("
int main() {
    unsigned int fpcr;
    __asm__ __volatile__ (\"fmove.l %%fpcr,%0\" : \"=g\" (fpcr));
    __asm__ __volatile__ (\"fmove.l %0,%%fpcr\" : : \"g\" (fpcr));
    return 0;
}
" HAVE_GCC_ASM_FOR_MC68881)
check_c_source_compiles("
int main() {
    __asm__ __volatile__ (\"movq %rcx, %rax\");
    return 0;
}
" HAVE_GCC_ASM_FOR_X64)
check_c_source_compiles("
int main() {
    unsigned short cw;
    __asm__ __volatile__ (\"fnstcw %0\" : \"=m\" (cw));
    __asm__ __volatile__ (\"fldcw %0\" : : \"m\" (cw));
    return 0;
}
" HAVE_GCC_ASM_FOR_X87)
check_type_size(__uint128_t SIZEOF___UINT128_T LANGUAGE C)
set(HAVE_GCC_UINT128_T ${HAVE_SIZEOF___UINT128_T})
if(HAVE_SIZEOF___UINT128_T)
    add_definitions(-DHAVE_UINT128_T)
endif()
check_function_exists(getaddrinfo HAVE_GETADDRINFO)
check_function_exists(flockfile HAVE_FLOCKFILE)
check_function_exists(getc_unlocked HAVE_GETC_UNLOCKED)
check_function_exists(funlockfile HAVE_FUNLOCKFILE)
if(HAVE_FLOCKFILE AND HAVE_GETC_UNLOCKED AND HAVE_FUNLOCKFILE)
    set(HAVE_GETC_UNLOCKED TRUE)
endif()
check_function_exists(getentropy HAVE_GETENTROPY)
check_function_exists(getgrgid_r HAVE_GETGRGID_R)
check_function_exists(getgrnam_r HAVE_GETGRNAM_R)
check_function_exists(getgrouplist HAVE_GETGROUPLIST)
check_function_exists(getgroups HAVE_GETGROUPS)
check_function_exists(gethostbyname HAVE_GETHOSTBYNAME)
check_function_exists(gethostbyname_r HAVE_GETHOSTBYNAME_R)
check_c_source_compiles("
#include <netdb.h>

int main() {
    char *name;
    struct hostent *he;
    struct hostent_data data;
    (void) gethostbyname_r(name, he, &data);
    return 0;
}
" HAVE_GETHOSTBYNAME_R_3_ARG)
check_c_source_compiles("
#include <netdb.h>

int main() {
    char *name;
    struct hostent *he;
    char buffer[2048];
    int buflen = 2048;
    int h_errnop;

    (void) gethostbyname_r(name, he, buffer, buflen, &h_errnop);
    return 0;
}
" HAVE_GETHOSTBYNAME_R_5_ARG)
check_c_source_compiles("
#include <netdb.h>

int main() {
    char *name;
    struct hostent *he, *res;
    char buffer[2048];
    int buflen = 2048;
    int h_errnop;
    (void) gethostbyname_r(name, he, buffer, buflen, &res, &h_errnop);
    return 0;
}
" HAVE_GETHOSTBYNAME_R_6_ARG)
check_function_exists(getitimer HAVE_GETITIMER)
check_function_exists(getloadavg HAVE_GETLOADAVG)
check_function_exists(getlogin HAVE_GETLOGIN)
check_function_exists(getnameinfo HAVE_GETNAMEINFO)
check_symbol_exists(getpagesize unistd.h HAVE_GETPAGESIZE)
check_function_exists(getpeername HAVE_GETPEERNAME)
check_function_exists(getpgid HAVE_GETPGID)
check_function_exists(getpgrp HAVE_GETPGRP)
check_function_exists(getpid HAVE_GETPID)
check_function_exists(getpriority HAVE_GETPRIORITY)
check_function_exists(getpwent HAVE_GETPWENT)
check_function_exists(getpwnam_r HAVE_GETPWNAM_R)
check_function_exists(getpwuid_r HAVE_GETPWUID_R)
check_function_exists(getrandom HAVE_GETRANDOM)
check_c_source_compiles("
#include <unistd.h>
#include <sys/syscall.h>
#include <linux/random.h>

int main() {
    char buffer[1];
    const size_t buflen = sizeof(buffer);
    const int flags = GRND_NONBLOCK;
    /* ignore the result, Python checks for ENOSYS and EAGAIN at runtime */
    (void) syscall(SYS_getrandom, buffer, buflen, flags);
    return 0;
}
" HAVE_GETRANDOM_SYSCALL)
if(HAVE_GETRANDOM_SYSCALL)
    add_definitions(-DHAVE_SYSCALL_GETRANDOM)
endif()
check_function_exists(getresgid HAVE_GETRESGID)
check_function_exists(getresuid HAVE_GETRESUID)
check_function_exists(getsid HAVE_GETSID)
check_function_exists(getspent HAVE_GETSPENT)
check_function_exists(getspnam HAVE_GETSPNAM)
check_function_exists(getwd HAVE_GETWD)
check_include_file(grp.h HAVE_GRP_H)
check_function_exists(hstrerror HAVE_HSTRERROR)
check_symbol_exists(le64toh sys/endian.h HAVE_HTOLE64)
check_function_exists(hypot HAVE_HYPOT)
check_include_file(ieeefp.h HAVE_IEEEFP_H)
check_function_exists(if_nameindex HAVE_IF_NAMEINDEX)
check_function_exists(inet_aton HAVE_INET_ATON)
check_function_exists(inet_pton HAVE_INET_PTON)
check_function_exists(initgroups HAVE_INITGROUPS)
check_include_file(inttypes.h HAVE_INTTYPES_H)
check_include_file(io.h HAVE_IO_H)
check_function_exists(kill HAVE_KILL)
check_function_exists(killpg HAVE_KILLPG)
check_function_exists(kqueue HAVE_KQUEUE)
check_include_file(langinfo.h HAVE_LANGINFO_H)
check_type_size(off_t SIZEOF_OFF_T LANGUAGE C)
check_type_size(long SIZEOF_LONG LANGUAGE C)
check_type_size("long long" SIZEOF_LONG_LONG LANGUAGE C)
if(HAVE_SIZEOF_OFF_T AND HAVE_SIZEOF_LONG_LONG AND SIZEOF_OFF_T GREATER SIZEOF_LONG
        AND SIZEOF_LONG_LONG GREATER_EQUAL SIZEOF_OFF_T)
    set(HAVE_LARGEFILE_SUPPORT TRUE)
endif()
check_function_exists(lchflags HAVE_LCHFLAGS)
check_function_exists(lchmod HAVE_LCHMOD)
check_function_exists(lchown HAVE_LCHOWN)
check_function_exists(lgamma HAVE_LGAMMA)
set(HAVE_LIBDL TRUE)
check_include_file(libintl.h HAVE_LIBINTL_H)
set(HAVE_LIBREADLINE TRUE)
check_include_file(libutil.h HAVE_LIBUTIL_H)
check_function_exists(link HAVE_LINK)
check_function_exists(linkat HAVE_LINKAT)
check_include_file(linux/auxvec.h HAVE_LINUX_AUXVEC_H)
check_include_file(linux/can/bcm.h HAVE_LINUX_CAN_BCM_H)
check_include_file(linux/can.h HAVE_LINUX_CAN_H)
check_include_file(linux/can/j1939.h HAVE_LINUX_CAN_J1939_H)
check_include_file(linux/can/raw.h HAVE_LINUX_CAN_RAW_FD_FRAMES)
check_symbol_exists(CAN_RAW_FD_FRAMES linux/can/raw.h HAVE_LINUX_CAN_RAW_FD_FRAMES)
check_include_file(linux/can/raw.h HAVE_LINUX_CAN_RAW_H)
check_symbol_exists(CAN_RAW_JOIN_FILTERS linux/can/raw.h HAVE_LINUX_CAN_RAW_JOIN_FILTERS)
check_include_file(linux/memfd.h HAVE_LINUX_MEMFD_H)
check_include_file(linux/netlink.h HAVE_LINUX_NETLINK_H)
check_include_file(linux/qrtr.h HAVE_LINUX_QRTR_H)
check_include_file(linux/random.h HAVE_LINUX_RANDOM_H)
check_include_file(linux/tipc.h HAVE_LINUX_TIPC_H)
check_include_file(linux/vm_sockets.h HAVE_LINUX_VM_SOCKETS_H)
check_include_file(linux/wait.h HAVE_LINUX_WAIT_H)
check_function_exists(lockf HAVE_LOCKF)
check_function_exists(log1p HAVE_LOG1P)
check_function_exists(log2 HAVE_LOG2)
check_type_size("long double" SIZEOF_LONG_DOUBLE LANGUAGE C)
set(HAVE_LONG_DOUBLE ${HAVE_SIZEOF_LONG_DOUBLE})
check_function_exists(lstat HAVE_LSTAT)
check_function_exists(lutimes HAVE_LUTIMES)
check_function_exists(madvise HAVE_MADVISE)
check_symbol_exists(makedev sys/sysmacros.h HAVE_MAKEDEV)
check_function_exists(mbrtowc HAVE_MBRTOWC)
check_function_exists(memfd_create HAVE_MEMFD_CREATE)
check_include_file(memory.h HAVE_MEMORY_H)
check_function_exists(memrchr HAVE_MEMRCHR)
check_function_exists(mkdirat HAVE_MKDIRAT)
check_function_exists(mkfifo HAVE_MKFIFO)
check_function_exists(mkfifoat HAVE_MKFIFOAT)
check_function_exists(mknod HAVE_MKNOD)
check_function_exists(mknodat HAVE_MKNODAT)
check_function_exists(mktime HAVE_MKTIME)
check_function_exists(mmap HAVE_MMAP)
check_function_exists(mremap HAVE_MREMAP)
set(HAVE_NCURSES_H TRUE)
check_include_file(ndir.h HAVE_NDIR_HEADER)
if(HAVE_NDIR_HEADER)
    check_c_source_compiles("
#include <ndir.h>
int main() {
    DIR dir;
    return 0;
}
" HAVE_NDIR_H)
endif()
check_include_file(netpacket/packet.h HAVE_NETPACKET_PACKET_H)
check_include_file(net/if.h HAVE_NET_IF_H)
check_function_exists(nice HAVE_NICE)
check_function_exists(openat HAVE_OPENAT)
check_function_exists(openpty HAVE_OPENPTY)
check_function_exists(pathconf HAVE_PATHCONF)
check_function_exists(pause HAVE_PAUSE)
check_function_exists(pipe2 HAVE_PIPE2)
check_function_exists(plock HAVE_PLOCK)
check_function_exists(poll HAVE_POLL)
check_include_file(poll.h HAVE_POLL_H)
check_function_exists(posix_fadvise HAVE_POSIX_FADVISE)
check_function_exists(posix_fallocate HAVE_POSIX_FALLOCATE)
check_function_exists(posix_spawn HAVE_POSIX_SPAWN)
check_function_exists(posix_spawnp HAVE_POSIX_SPAWNP)
check_function_exists(pread HAVE_PREAD)
check_function_exists(preadv HAVE_PREADV)
check_function_exists(preadv2 HAVE_PREADV2)
check_function_exists(prlimit HAVE_PRLIMIT)
check_include_file(process.h HAVE_PROCESS_H)
check_c_source_compiles("
int foo(int x) {
    return 0;
}

int main (){
    return foo(10);
}
" HAVE_PROTOTYPES)
check_function_exists(pthread_condattr_setclock HAVE_PTHREAD_CONDATTR_SETCLOCK)
check_function_exists(pthread_getcpuclockid HAVE_PTHREAD_GETCPUCLOCKID)
check_include_file(pthread.h HAVE_PTHREAD_H)
check_function_exists(pthread_init HAVE_PTHREAD_INIT)
check_function_exists(pthread_kill HAVE_PTHREAD_KILL)
check_function_exists(pthread_sigmask HAVE_PTHREAD_SIGMASK)
check_include_file(pty.h HAVE_PTY_H)
check_function_exists(pwrite HAVE_PWRITE)
check_function_exists(pwritev HAVE_PWRITEV)
check_function_exists(pwritev2 HAVE_PWRITEV2)
check_function_exists(readlink HAVE_READLINK)
check_function_exists(readlinkat HAVE_READLINKAT)
check_function_exists(readv HAVE_READV)
check_function_exists(realpath HAVE_REALPATH)
check_function_exists(renameat HAVE_RENAMEAT)
set(HAVE_RL_APPEND_HISTORY TRUE)
set(HAVE_RL_CATCH_SIGNAL TRUE)
set(HAVE_RL_COMPLETION_APPEND_CHARACTER TRUE)
set(HAVE_RL_COMPLETION_DISPLAY_MATCHES_HOOK TRUE)
set(HAVE_RL_COMPLETION_MATCHES TRUE)
set(HAVE_RL_COMPLETION_SUPPRESS_APPEND TRUE)
set(HAVE_RL_PRE_INPUT_HOOK TRUE)
set(HAVE_RL_RESIZE_TERMINAL TRUE)
check_function_exists(round HAVE_ROUND)
check_function_exists(rtpSpawn HAVE_RTPSPAWN)
check_function_exists(sched_get_priority_max HAVE_SCHED_GET_PRIORITY_MAX)
check_include_file(sched.h HAVE_SCHED_H)
check_function_exists(sched_rr_get_interval HAVE_SCHED_RR_GET_INTERVAL)
check_function_exists(sched_setaffinity HAVE_SCHED_SETAFFINITY)
check_function_exists(sched_setparam HAVE_SCHED_SETPARAM)
check_function_exists(sched_setscheduler HAVE_SCHED_SETSCHEDULER)
check_function_exists(sem_clockwait HAVE_SEM_CLOCKWAIT)
check_function_exists(sem_getvalue HAVE_SEM_GETVALUE)
check_function_exists(sem_open HAVE_SEM_OPEN)
check_function_exists(sem_timedwait HAVE_SEM_TIMEDWAIT)
check_function_exists(sem_unlink HAVE_SEM_UNLINK)
check_function_exists(sendfile HAVE_SENDFILE)
check_function_exists(setegid HAVE_SETEGID)
check_function_exists(seteuid HAVE_SETEUID)
check_function_exists(setgid HAVE_SETGID)
check_function_exists(setgroups HAVE_SETGROUPS)
check_function_exists(sethostname HAVE_SETHOSTNAME)
check_function_exists(setitimer HAVE_SETITIMER)
check_function_exists(setlocale HAVE_SETLOCALE)
check_function_exists(setpgid HAVE_SETPGID)
check_function_exists(setpgrp HAVE_SETPGRP)
check_function_exists(setpriority HAVE_SETPRIORITY)
check_function_exists(setregid HAVE_SETREGID)
check_function_exists(setresgid HAVE_SETRESGID)
check_function_exists(setresuid HAVE_SETRESUID)
check_function_exists(setreuid HAVE_SETREUID)
check_function_exists(setsid HAVE_SETSID)
check_function_exists(setuid HAVE_SETUID)
check_function_exists(setvbuf HAVE_SETVBUF)
check_include_file(shadow.h HAVE_SHADOW_H)
check_function_exists(shm_open HAVE_SHM_OPEN)
check_function_exists(shm_unlink HAVE_SHM_UNLINK)
check_function_exists(sigaction HAVE_SIGACTION)
check_function_exists(sigaltstack HAVE_SIGALTSTACK)
check_function_exists(sigfillset HAVE_SIGFILLSET)
check_struct_has_member("struct siginfo_t" si_band signal.h HAVE_SIGINFO_T_SI_BAND)
check_function_exists(siginterrupt HAVE_SIGINTERRUPT)
check_include_file(signal.h HAVE_SIGNAL_H)
check_function_exists(sigpending HAVE_SIGPENDING)
check_function_exists(sigrelse HAVE_SIGRELSE)
check_function_exists(sigtimedwait HAVE_SIGTIMEDWAIT)
check_function_exists(sigwait HAVE_SIGWAIT)
check_function_exists(sigwaitinfo HAVE_SIGWAITINFO)
check_function_exists(snprintf HAVE_SNPRINTF)
check_symbol_exists(sockaddr_alg linux/if_alg.h HAVE_SOCKADDR_ALG)
check_struct_has_member("struct sockaddr" sa_len sys/socket.h HAVE_SOCKADDR_SA_LEN)
check_include_file(sys/socket.h HAVE_SYS_SOCKET_H)
if(HAVE_SYS_SOCKET_H)
    list(APPEND CMAKE_EXTRA_INCLUDE_FILES sys/socket.h)
    check_type_size("struct sockaddr_storage" SIZEOF_SOCKADDR_STORAGE LANGUAGE C)
    set(HAVE_SOCKADDR_STORAGE ${HAVE_SIZEOF_SOCKADDR_STORAGE})
    list(REMOVE_AT CMAKE_EXTRA_INCLUDE_FILES -1)
endif()
check_function_exists(socketpair HAVE_SOCKETPAIR)
check_include_file(spawn.h HAVE_SPAWN_H)
check_function_exists(splice HAVE_SPLICE)
check_type_size(ssize_t SIZEOF_SSIZE_T LANGUAGE C)
set(HAVE_SSIZE_T ${HAVE_SIZEOF_SSIZE_T})
check_function_exists(statvfs HAVE_STATVFS)
check_struct_has_member("struct stat" st_mtim.tv_nsec sys/stat.h HAVE_STAT_TV_NSEC)
check_struct_has_member("struct stat" st_mtimensec sys/stat.h HAVE_STAT_TV_NSEC2)
check_include_file(stdarg.h HAVE_STDARG_H)
if(HAVE_STDARG_H)
    check_c_source_compiles("
#include <stdarg.h>
int foo(int x, ...) {
	va_list va;
	va_start(va, x);
	va_arg(va, int);
	va_arg(va, char *);
	va_arg(va, double);
	return 0;
}

int main (){
    return foo(10, \"\", 3.14);
}
" HAVE_STDARG_PROTOTYPES)
endif()
check_include_file(stdint.h HAVE_STDINT_H)
check_include_file(stdlib.h HAVE_STDLIB_H)
check_include_file(stdatomic.h HAVE_STDATOMIC_H)
check_type_size(atomic_uintptr_t SIZEOF_ATOMIC_UINTPTR_T LANGUAGE C)
check_type_size(atomic_int SIZEOF_ATOMIC_INT LANGUAGE C)
if(HAVE_STDATOMIC_H AND HAVE_SIZEOF_ATOMIC_UINTPTR_T AND HAVE_SIZEOF_ATOMIC_INT)
    set(HAVE_STD_ATOMIC TRUE)
endif()
check_function_exists(strftime HAVE_STRFTIME)
check_include_file(strings.h HAVE_STRINGS_H)
check_include_file(string.h HAVE_STRING_H)
check_function_exists(strlcpy HAVE_STRLCPY)
check_include_file(stropts.h HAVE_STROPTS_H)
check_function_exists(strsignal HAVE_STRSIGNAL)
check_struct_has_member("struct passwd" pw_gecos pwd.h HAVE_STRUCT_PASSWD_PW_GECOS)
check_struct_has_member("struct passwd" pw_passwd pwd.h HAVE_STRUCT_PASSWD_PW_PASSWD)
check_struct_has_member("struct stat" st_birthtime sys/stat.h HAVE_STRUCT_STAT_ST_BIRTHTIME)
check_struct_has_member("struct stat" st_blksize sys/stat.h HAVE_STRUCT_STAT_ST_BLKSIZE)
check_struct_has_member("struct stat" st_blocks sys/stat.h HAVE_STRUCT_STAT_ST_BLOCKS)
check_struct_has_member("struct stat" st_flags sys/stat.h HAVE_STRUCT_STAT_ST_FLAGS)
check_struct_has_member("struct stat" st_gen sys/stat.h HAVE_STRUCT_STAT_ST_GEN)
check_struct_has_member("struct stat" st_rdev sys/stat.h HAVE_STRUCT_STAT_ST_RDEV)
check_struct_has_member("struct tm" tm_zone time.h HAVE_STRUCT_TM_TM_ZONE)
check_function_exists(symlink HAVE_SYMLINK)
check_function_exists(symlinkat HAVE_SYMLINKAT)
check_function_exists(symlinkat HAVE_SYMLINKAT)
check_function_exists(sync HAVE_SYNC)
check_function_exists(sysconf HAVE_SYSCONF)
check_include_file(sysexits.h HAVE_SYSEXITS_H)
check_include_file(sys/audioio.h HAVE_SYS_AUDIOIO_H)
check_include_file(sys/auxv.h HAVE_SYS_AUXV_H)
check_include_file(sys/bsdtty.h HAVE_SYS_BSDTTY_H)
check_include_file(sys/devpoll.h HAVE_SYS_DEVPOLL_H)
check_include_file(sys/dir.h HAVE_SYS_DIR_HEADER)
if(HAVE_SYS_DIR_HEADER)
    check_c_source_compiles("
#include <sys/dir.h>
int main() {
    DIR dir;
    return 0;
}
" HAVE_SYS_DIR_H)
endif()
check_include_file(sys/endian.h HAVE_SYS_ENDIAN_H)
check_include_file(sys/epoll.h HAVE_SYS_EPOLL_H)
check_include_file(sys/eventfd.h HAVE_SYS_EVENTFD_H)
check_include_file(sys/event.h HAVE_SYS_EVENT_H)
check_include_file(sys/file.h HAVE_SYS_FILE_H)
check_include_file(sys/ioctl.h HAVE_SYS_IOCTL_H)
check_include_file(sys/kern_control.h HAVE_SYS_KERN_CONTROL_H)
check_include_file(sys/loadavg.h HAVE_SYS_LOADAVG_H)
check_include_file(sys/lock.h HAVE_SYS_LOCK_H)
check_include_file(sys/memfd.h HAVE_SYS_MEMFD_H)
check_include_file(sys/mkdev.h HAVE_SYS_MKDEV_H)
check_include_file(sys/mman.h HAVE_SYS_MMAN_H)
check_include_file(sys/modem.h HAVE_SYS_MODEM_H)
check_include_file(sys/ndir.h HAVE_SYS_NDIR_HEADER)
if(HAVE_SYS_NDIR_HEADER)
    check_c_source_compiles("
#include <sys/ndir.h>
int main() {
    DIR dir;
    return 0;
}
" HAVE_SYS_NDIR_H)
endif()
check_include_file(sys/param.h HAVE_SYS_PARAM_H)
check_include_file(sys/poll.h HAVE_SYS_POLL_H)
check_include_file(sys/random.h HAVE_SYS_RANDOM_H)
check_include_file(sys/resource.h HAVE_SYS_RESOURCE_H)
check_include_file(sys/select.h HAVE_SYS_SELECT_H)
check_include_file(sys/sendfile.h HAVE_SYS_SENDFILE_H)
check_include_file(sys/statvfs.h HAVE_SYS_STATVFS_H)
check_include_file(sys/stat.h HAVE_SYS_STAT_H)
check_include_file(sys/syscall.h HAVE_SYS_SYSCALL_H)
check_include_file(sys/sysmacros.h HAVE_SYS_SYSMACROS_H)
check_include_file(sys/sys_domain.h HAVE_SYS_SYS_DOMAIN_H)
check_include_file(sys/termio.h HAVE_SYS_TERMIO_H)
check_include_file(sys/times.h HAVE_SYS_TIMES_H)
check_include_file(sys/time.h HAVE_SYS_TIME_H)
check_include_file(sys/types.h HAVE_SYS_TYPES_H)
check_include_file(sys/uio.h HAVE_SYS_UIO_H)
check_include_file(sys/un.h HAVE_SYS_UN_H)
check_include_file(sys/utsname.h HAVE_SYS_UTSNAME_H)
check_include_file(sys/wait.h HAVE_SYS_WAIT_H)
check_include_file(sys/xattr.h HAVE_SYS_XATTR_H)
check_function_exists(tcgetpgrp HAVE_TCGETPGRP)
check_function_exists(tcsetpgrp HAVE_TCSETPGRP)
check_function_exists(tempnam HAVE_TEMPNAM)
check_include_file(termios.h HAVE_TERMIOS_H)
check_include_file(term.h HAVE_TERM_H)
check_function_exists(tgamma HAVE_TGAMMA)
check_function_exists(timegm HAVE_TIMEGM)
check_function_exists(times HAVE_TIMES)
check_function_exists(tmpfile HAVE_TMPFILE)
check_function_exists(tmpnam HAVE_TMPNAM)
check_function_exists(tmpnam_r HAVE_TMPNAM_R)
set(HAVE_TM_ZONE ${HAVE_STRUCT_TM_TM_ZONE})
check_function_exists(truncate HAVE_TRUNCATE)
if(NOT HAVE_STRUCT_TM_TM_ZONE)
    check_symbol_exists(tzname time.h HAVE_TZNAME)
endif()
check_function_exists(uname HAVE_UNAME)
check_include_file(unistd.h HAVE_UNISTD_H)
check_function_exists(unlinkat HAVE_UNLINKAT)
check_type_size(wchar_t SIZEOF_WCHAR_T LANGUAGE C)
if(SIZEOF_WCHAR_T GREATER_EQUAL 2)
    # TODO: Check WCHAR_T is unsigned
    set(HAVE_USABLE_WCHAR_T False)
endif()
check_include_file(util.h HAVE_UTIL_H)
check_function_exists(utimensat HAVE_UTIMENSAT)
check_function_exists(utimes HAVE_UTIMES)
check_include_file(utime.h HAVE_UTIME_H)
check_function_exists(uuid_create HAVE_UUID_CREATE)
check_function_exists(uuid_enc_be HAVE_UUID_ENC_BE)
check_function_exists(uuid_generate_time_safe HAVE_UUID_GENERATE_TIME_SAFE)
check_include_file(uuid.h HAVE_UUID_H)
check_include_file(uuid/uuid.h HAVE_UUID_UUID_H)
check_function_exists(vfork HAVE_VFORK)
check_function_exists(wait3 HAVE_WAIT3)
check_symbol_exists(wait4 sys/wait.h HAVE_WAIT4)
check_function_exists(waitid HAVE_WAITID)
check_function_exists(waitpid HAVE_WAITPID)
check_include_file(wchar.h HAVE_WCHAR_H)
check_function_exists(wcscoll HAVE_WCSCOLL)
check_function_exists(wcsftime HAVE_WCSFTIME)
check_function_exists(wcsxfrm HAVE_WCSXFRM)
check_function_exists(wmemcmp HAVE_WMEMCMP)
set(HAVE_WORKING_TZSET TRUE)
check_function_exists(writev HAVE_WRITEV)
list(APPEND CMAKE_REQUIRED_LIBRARIES ${z-lib})
check_symbol_exists(inflateCopy zlib.h HAVE_ZLIB_COPY)
list(REMOVE_AT CMAKE_REQUIRED_LIBRARIES -1)
check_function_exists(_getpty HAVE__GETPTY)
check_symbol_exists(major mkdev.h HAVE_MAJOR_IN_MKDEV)
check_symbol_exists(minor mkdev.h HAVE_MINOR_IN_MKDEV)
check_symbol_exists(makedev mkdev.h HAVE_MAKEDEV_IN_MKDEV)
if(HAVE_MAJOR_IN_MKDEV AND HAVE_MINOR_IN_MKDEV AND HAVE_MAKEDEV_IN_MKDEV)
    set(MAJOR_IN_MKDEV TRUE)
endif()
check_symbol_exists(major sys/sysmacros.h HAVE_MAJOR_IN_SYSMACROS)
check_symbol_exists(minor sys/sysmacros.h HAVE_MINOR_IN_SYSMACROS)
check_symbol_exists(makedev sys/sysmacros.h HAVE_MAKEDEV_IN_SYSMACROS)

if(HAVE_MAJOR_IN_SYSMACROS AND HAVE_MINOR_IN_SYSMACROS AND HAVE_MAKEDEV_IN_SYSMACROS)
    set(MAJOR_IN_SYSMACROS TRUE)
endif()
check_c_source_compiles("
#include <curses.h>

int main (){
    int rtn;
    rtn = mvwdelch(0,0,0);
    return 0;
}
" MVWDELCH_IS_EXPRESSION)
set(POSIX_SEMAPHORES_NOT_ENABLED False)
check_c_source_compiles("
#include <pthread.h>
int main (){
    pthread_key_t k;
    k * 1;
    return 0;
}
" PTHREAD_KEY_T_IS_COMPATIBLE_WITH_INT)
set(PTHREAD_SYSTEM_SCHED_SUPPORTED TRUE)
set(PY_BUILTIN_HASHLIB_HASHES \"md5,sha1,sha256,sha512,sha3,blake2\")
set(PY_COERCE_C_LOCALE TRUE)
set(PY_FORMAT_SIZE_T \"z\")
set(Py_DEBUG False)
set(Py_ENABLE_SHARED TRUE)
set(Py_TRACE_REFS False)
set(RETSIGTYPE void)
check_c_source_compiles("
#include <unistd.h>
int main (){
    setpgrp(0,0);
    return 0;
}
" SETPGRP_HAVE_ARG)
set(SHM_NEEDS_LIBRT False)
set(SIGNED_RIGHT_SHIFT_ZERO_FILLS False)
check_type_size(double SIZEOF_DOUBLE LANGUAGE C)
check_type_size(float SIZEOF_FLOAT LANGUAGE C)
list(APPEND CMAKE_EXTRA_INCLUDE_FILES stdio.h)
check_type_size(fpos_t SIZEOF_FPOS_T LANGUAGE C)
list(REMOVE_AT CMAKE_EXTRA_INCLUDE_FILES -1)
check_type_size(int SIZEOF_INT LANGUAGE C)
check_type_size(pid_t SIZEOF_PID_T LANGUAGE C)
check_type_size(pthread_key_t SIZEOF_PTHREAD_KEY_T LANGUAGE C)
check_type_size(pthread_t SIZEOF_PTHREAD_T LANGUAGE C)
check_type_size(short SIZEOF_SHORT LANGUAGE C)
check_type_size(size_t SIZEOF_SIZE_T LANGUAGE C)
check_type_size(time_t SIZEOF_TIME_T LANGUAGE C)
check_type_size(uintptr_t SIZEOF_UINTPTR_T LANGUAGE C)
check_type_size("void *" SIZEOF_VOID_P LANGUAGE C)
check_type_size(_Bool SIZEOF__BOOL LANGUAGE C)
set(STDC_HEADERS TRUE)
check_c_source_compiles("
#include <sys/types.h>
#include <sys/select.h>
#include <sys/time.h>
int main () {
    return 0;
}
" SYS_SELECT_WITH_SYS_TIME)
check_c_source_compiles("
#include <sys/types.h>
#include <sys/time.h>
#include <time.h>
int main () {
    return 0;
}
" TIME_WITH_SYS_TIME)
check_c_source_compiles("
#include <sys/types.h>
#include <time.h>
int main() {
    struct tm tm;
    int *p = &tm.tm_sec;
    return !p;
}
" TM_IN_SYS_TIME)
set(USE_COMPUTED_GOTOS TRUE)
check_c_source_compiles("
#define NCURSES_OPAQUE 0
#include <curses.h>
int main() {
    WINDOW *w;
    w->_flags = 0;
    return 0;
}
" WINDOW_HAS_FLAGS)
set(WITH_DECIMAL_CONTEXTVAR TRUE)
set(WITH_DOC_STRINGS TRUE)
set(WITH_DTRACE False)
set(WITH_DYLD False)
set(WITH_EDITLINE False)
set(WITH_LIBINTL False)
set(WITH_NEXT_FRAMEWORK False)
set(WITH_PYMALLOC TRUE)
set(WITH_VALGRIND False)
test_big_endian(WORDS_BIGENDIAN)
set(X87_DOUBLE_ROUNDING False)
set(_FILE_OFFSET_BITS 64)
set(_GNU_SOURCE TRUE)
set(_LARGEFILE_SOURCE TRUE)
set(_POSIX_C_SOURCE 200809L)
set(_PYTHONFRAMEWORK \"\")
set(_REENTRANT TRUE)
set(_XOPEN_SOURCE 700)
set(_XOPEN_SOURCE_EXTENDED 1)


file(READ ${CMAKE_CURRENT_SOURCE_DIR}/source/pyconfig.h.in PY_CONFIG_TEMPLATE)
string(REGEX REPLACE "#( *)undef ([A-Za-z0-9_]+)(\r?\n)" "#\\1cmakedefine \\2 \@\\2\@\\3"
        PY_CONFIG_TEMPLATE "${PY_CONFIG_TEMPLATE}")
file(WRITE ${PROJECT_BINARY_DIR}/tmp/pyconfig.h.in "${PY_CONFIG_TEMPLATE}")
configure_file(${PROJECT_BINARY_DIR}/tmp/pyconfig.h.in ${PROJECT_BINARY_DIR}/tmp/pyconfig.h)
file(READ ${PROJECT_BINARY_DIR}/tmp/pyconfig.h PY_CONFIG_TEMPLATE)
string(REGEX REPLACE "#( *)define ([A-Za-z0-9_]+) TRUE(\r?\n)" "#\\1define \\2 1\\3"
        PY_CONFIG_TEMPLATE "${PY_CONFIG_TEMPLATE}")
file(WRITE ${PROJECT_BINARY_DIR}/include/pyconfig.h "${PY_CONFIG_TEMPLATE}")

set(mappedModuleNames
        _hashopenssl _hashlib
        symtable _symtable
        socket _socket
        signal _signal
        sha1 _sha1
        sha256 _sha256
        sha512 _sha512
        md5 _md5
        multibytecodec _multibytecodec)
set(moduleDir "${CMAKE_CURRENT_SOURCE_DIR}/source/Modules")
set(modules "")
file(GLOB moduleSources RELATIVE ${moduleDir} ${moduleDir}/*)
foreach(moduleFileName ${moduleSources})
    if(IS_DIRECTORY "${moduleDir}/${moduleFileName}")
        list(APPEND modules ${moduleFileName})
    elseif("${moduleFileName}" MATCHES ".*\\.c$")
        STRING(REGEX REPLACE "(module)?\\.c$" "" moduleName ${moduleFileName})
        list(FIND mappedModuleNames ${moduleName} mappedModuleNameIndex)
        if(NOT ${mappedModuleNameIndex} EQUAL -1)
            math(EXPR mappedModuleNameIndex "${mappedModuleNameIndex} + 1")
            list(GET mappedModuleNames ${mappedModuleNameIndex} moduleName)
        endif()
        list(APPEND modules ${moduleName})
    endif()
endforeach()
file(GLOB moduleSources RELATIVE ${moduleDir}/cjkcodecs ${moduleDir}/cjkcodecs/*)
foreach(moduleFileName ${moduleSources})
    if(NOT IS_DIRECTORY "${moduleDir}/cjkcodecs/${moduleFileName}"
            AND "${moduleFileName}" MATCHES ".*\\.c$")
        STRING(REGEX REPLACE "(module)?\\.c$" "" moduleName ${moduleFileName})
        list(FIND mappedModuleNames ${moduleName} mappedModuleNameIndex)
        if(NOT ${mappedModuleNameIndex} EQUAL -1)
            math(EXPR mappedModuleNameIndex "${mappedModuleNameIndex} + 1")
            list(GET mappedModuleNames ${mappedModuleNameIndex} moduleName)
        endif()
        list(APPEND modules ${moduleName})
    endif()
endforeach()
list(REMOVE_DUPLICATES modules)

# All modules that are not supported on Android
set(excludedModules
        _bsddb
        _dbm
        _freeze_importlib
        _gdbm
        _lzma
        _math # Not a real module
        _scproxy
        _sqlite # TODO: https://www.sqlite.org/download.html 
        _testbuffer
        _testcapi
        _testembed
        _testimportmultiple
        _testmultiphase
        _uuid
        _winapi
        al
        bsddb
        cd
        cjkcodecs # Not a real module
        cl
        clinic # Not a real module
        dbm
        expat # Not a real module
        fl
        fm
        fpectl
        fpetest
        gdbm # TODO: http://www.gnu.org.ua/software/gdbm/
        getaddrinfo
        getbuildinfo # Not a real module
        getnameinfo
        getpath # Not a real module
        gl
        grp # TODO
        imgfile
        main # Not a real module
        nis
        overlapped
        rotatingtree # Not a real module
        sgi
        spwd
        sunaudiodev
        sv
        tkappinit
        xxlimited
        xx
        xxsubtype)

list(REMOVE_ITEM modules ${excludedModules})

# Separate Modules #
unset(additionalModuleSources)
unset(additionalModules)
unset(additionalModuleNames)
unset(additionalModuleDependencies)
function(addModule name)
    cmake_parse_arguments(ARG "" "" "DEPS;SOURCES" ${ARGN})
    add_library(modulePython${PYTHON_SHORT_VERSION}_${name} SHARED ${ARG_SOURCES})
    target_include_directories(modulePython${PYTHON_SHORT_VERSION}_${name}
            PRIVATE
            $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/source/Include/internal>
            $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/source/Modules>)
    set_target_properties(modulePython${PYTHON_SHORT_VERSION}_${name} PROPERTIES
            PREFIX "" OUTPUT_NAME ${name}
            LIBRARY_OUTPUT_DIRECTORY
            ${CMAKE_LIBRARY_OUTPUT_DIRECTORY}/python${PYTHON_SHORT_VERSION}Modules)
    target_link_libraries(modulePython${PYTHON_SHORT_VERSION}_${name}
            python${PYTHON_SHORT_VERSION} ${pythonPatch-lib} ${ARG_DEPS})
    list(APPEND additionalModuleSources ${ARG_SOURCES})
    set(additionalModuleSources ${additionalModuleSources} PARENT_SCOPE)
    list(APPEND additionalModules modulePython${PYTHON_SHORT_VERSION}_${name})
    set(additionalModules ${additionalModules} PARENT_SCOPE)
    list(APPEND additionalModulesNames ${name})
    set(additionalModulesNames ${additionalModulesNames} PARENT_SCOPE)
    list(APPEND additionalModuleDependencies ${ARG_DEPS})
    set(additionalModuleDependencies ${additionalModuleDependencies} PARENT_SCOPE)
endfunction()

# _ssl
addModule(_ssl DEPS ssl SOURCES source/Modules/_ssl.c)

# _hashlib
addModule(_hashlib DEPS crypto SOURCES source/Modules/_hashopenssl.c)

# _bz2 or bz2
if(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/source/Modules/bz2module.c)
    addModule(bz2 DEPS bzip SOURCES source/Modules/bz2module.c)
else()
    addModule(_bz2 DEPS bzip SOURCES source/Modules/_bz2module.c)
endif()

# _tkinter
addModule(_tkinter DEPS tk tcl SOURCES source/Modules/_tkinter.c)

# crypt or _crypt
if(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/source/Modules/cryptmodule.c)
    addModule(crypt DEPS crypto SOURCES source/Modules/cryptmodule.c)
    target_compile_definitions(modulePython${PYTHON_SHORT_VERSION}_crypt PRIVATE -Dcrypt=DES_crypt)
else()
    addModule(_crypt DEPS crypto SOURCES source/Modules/_cryptmodule.c)
    target_compile_definitions(modulePython${PYTHON_SHORT_VERSION}__crypt PRIVATE -Dcrypt=DES_crypt)
endif()

# _curses
addModule(_curses DEPS ncurses SOURCES source/Modules/_cursesmodule.c)

# _curses_panel
addModule(_curses_panel DEPS ncurses SOURCES source/Modules/_curses_panel.c)

# readline
addModule(readline DEPS readline SOURCES source/Modules/readline.c)

# _ctypes
addModule(_ctypes DEPS ffi SOURCES
        source/Modules/_ctypes/cfield.c source/Modules/_ctypes/malloc_closure.c
        source/Modules/_ctypes/_ctypes.c source/Modules/_ctypes/stgdict.c
        source/Modules/_ctypes/ctypes_dlfcn.h source/Modules/_ctypes/callbacks.c
        source/Modules/_ctypes/callproc.c source/Modules/_ctypes/ctypes.h)

list(REMOVE_ITEM modules ${additionalModulesNames})
set(MODULE_INIT_DECLARATIONS "")
set(MODULE_ENTRIES "")
set(moduleSources "")
foreach(module ${modules})
    set(MODULE_INIT_DECLARATIONS "${MODULE_INIT_DECLARATIONS}
extern PyObject* PyInit_${module}(void);")
    set(MODULE_ENTRIES "${MODULE_ENTRIES}
    {\"${module}\", PyInit_${module}},")
    list(FIND mappedModuleNames ${module} mappedModuleNameIndex)
    if(NOT ${mappedModuleNameIndex} EQUAL -1)
        math(EXPR mappedModuleNameIndex "${mappedModuleNameIndex} - 1")
        list(GET mappedModuleNames ${mappedModuleNameIndex} module)
    endif()
    if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/source/Modules/cjkcodecs/${module}.c")
        set(module "cjkcodecs/${module}")
    endif()
    list(APPEND moduleSources "source/Modules/${module}.[ch]" "source/Modules/${module}module.[ch]"
            "source/Modules/${module}/*.[ch]" "source/Modules/${module}/*/*.[ch]")
endforeach()
set(MODULE_INIT_DECLARATIONS "${MODULE_INIT_DECLARATIONS}
#ifdef COMPILE_WITH_ADDITIONAL_PYTHON_MODULES")
set(MODULE_ENTRIES "${MODULE_ENTRIES}
#ifdef COMPILE_WITH_ADDITIONAL_PYTHON_MODULES")
foreach(module ${additionalModulesNames})
    set(MODULE_INIT_DECLARATIONS "${MODULE_INIT_DECLARATIONS}
extern PyObject* PyInit_${module}(void);")
    set(MODULE_ENTRIES "${MODULE_ENTRIES}
    {\"${module}\", PyInit_${module}},")
endforeach()
if(${COMPILE_WITH_ADDITIONAL_PYTHON_MODULES})
    list(APPEND moduleSources ${additionalModuleSources})
endif()
set(MODULE_INIT_DECLARATIONS "${MODULE_INIT_DECLARATIONS}
#endif /* COMPILE_WITH_ADDITIONAL_PYTHON_MODULES */")
set(MODULE_ENTRIES "${MODULE_ENTRIES}
#endif /* COMPILE_WITH_ADDITIONAL_PYTHON_MODULES */")

file(READ ${CMAKE_CURRENT_SOURCE_DIR}/source/Modules/config.c.in PY_CONFIG_TEMPLATE)
string(REPLACE "/* -- ADDMODULE MARKER 1 -- */" "\@MODULE_INIT_DECLARATIONS\@"
        PY_CONFIG_TEMPLATE "${PY_CONFIG_TEMPLATE}")
string(REPLACE "/* -- ADDMODULE MARKER 2 -- */" "\@MODULE_ENTRIES\@"
        PY_CONFIG_TEMPLATE "${PY_CONFIG_TEMPLATE}")
file(WRITE ${PROJECT_BINARY_DIR}/tmp/config.c.in "${PY_CONFIG_TEMPLATE}")
configure_file(${PROJECT_BINARY_DIR}/tmp/config.c.in ${PROJECT_BINARY_DIR}/src/config.c)

# General source files
file(GLOB SOURCE_FILES RELATIVE ${CMAKE_CURRENT_SOURCE_DIR}
        ${PROJECT_BINARY_DIR}/include/pyconfig.h
        ${PROJECT_BINARY_DIR}/src/config.c
        source/Include/*.h
        source/Include/*/*.h
        source/Modules/*.h
        source/Modules/_math.c
        source/Modules/clinic/*.[ch]
        source/Modules/expat/*.[ch]
        source/Modules/getbuildinfo.c
        source/Modules/getpath.c
        source/Modules/main.c
        source/Modules/rotatingtree.c
        source/Modules/*/*.h
        source/Objects/*.[ch]
        source/Objects/stringlib/*.[ch]
        source/Parser/*.[ch]
        source/Python/*.[ch])

# Module files
file(GLOB MODULE_FILES RELATIVE ${CMAKE_CURRENT_SOURCE_DIR} ${moduleSources})
list(APPEND SOURCE_FILES ${MODULE_FILES})

set(excludedSources
        source/Modules/_blake2/impl/blake2-dispatch.c
        source/Modules/_blake2/impl/blake2b-ref.c
        source/Modules/_blake2/impl/blake2b.c
        source/Modules/_blake2/impl/blake2bp.c
        source/Modules/_blake2/impl/blake2s-ref.c
        source/Modules/_blake2/impl/blake2s.c
        source/Modules/_blake2/impl/blake2sp.c
        source/Modules/_ctypes/darwin/dlfcn_simple.c
        source/Modules/_decimal/libmpdec/bench.c
        source/Modules/_decimal/libmpdec/bench_full.c
        source/Modules/_multiprocessing/pipe_connection.c
        source/Modules/_multiprocessing/win32_functions.c
        source/Modules/_sha3/kcp/KeccakHash.c
        source/Modules/_sha3/kcp/KeccakP-1600-inplace32BI.c
        source/Modules/_sha3/kcp/KeccakP-1600-opt64.c
        source/Modules/_sha3/kcp/KeccakSponge.c
        source/Modules/expat/xmltok_impl.c
        source/Modules/expat/xmltok_ns.c
        source/Parser/intrcheck.c
        source/Parser/parsetok_pgen.c
        source/Parser/tokenizer_pgen.c
        source/Python/dynload_aix.c
        source/Python/dynload_atheos.c
        source/Python/dynload_beos.c
        source/Python/dynload_dl.c
        source/Python/dynload_hpux.c
        source/Python/dynload_next.c
        source/Python/dynload_os2.c
        source/Python/dynload_stub.c
        source/Python/dynload_win.c
        source/Python/getcwd.c
        source/Python/mactoolboxglue.c
        source/Python/sigcheck.c)

# Test, example or template source files and source files defining main
set(otherExcluded
        source/Modules/_blake2/impl/blake2b-test.c
        source/Modules/_blake2/impl/blake2bp-test.c
        source/Modules/_blake2/impl/blake2s-test.c
        source/Modules/_blake2/impl/blake2sp-test.c
        source/Modules/_ctypes/_ctypes_test.c
        source/Modules/_hashlib.c
        source/Modules/zlib/example.c
        source/Modules/zlib/minigzip.c
        source/Parser/pgenmain.c)

list(REMOVE_ITEM SOURCE_FILES ${excludedSources})
list(REMOVE_ITEM SOURCE_FILES ${otherExcluded})

# Link additional module if requested
if(${COMPILE_WITH_ADDITIONAL_PYTHON_MODULES})
    target_link_libraries(python${PYTHON_SHORT_VERSION} ${additionalModuleDependencies})
    add_definitions(-Dcrypt=DES_crypt -DCOMPILE_WITH_ADDITIONAL_PYTHON_MODULES)
endif()

target_sources(python${PYTHON_SHORT_VERSION} PRIVATE ${SOURCE_FILES})
set(GET_PATH_DEFINES VPATH="." PREFIX="/usr/local" EXEC_PREFIX="/usr/local"
        PYTHONPATH="/usr/local/lib/python${PYTHON_SHORT_VERSION}:/usr/local/lib/python${PYTHON_SHORT_VERSION}/lib-dynload")
set_source_files_properties(source/Modules/getpath.c APPEND PROPERTIES
        COMPILE_DEFINITIONS "${GET_PATH_DEFINES}")
set_source_files_properties(source/Modules/_tkinter.c APPEND PROPERTIES
        COMPILE_DEFINITIONS WITH_APPINIT)

target_include_directories(python${PYTHON_SHORT_VERSION}
        PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/source/Include>
        $<BUILD_INTERFACE:${PROJECT_BINARY_DIR}/include>
        PRIVATE
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/source/Include/internal>
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/source/Modules>
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/source/Modules/_io>
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/source/Modules/expat>
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/source/Modules/cjkcodecs>
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/source/Modules/_sha3/kcp>
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/source/Modules/_decimal>
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/source/Modules/_decimal/libmpdec>)

target_link_libraries(python${PYTHON_SHORT_VERSION} ${pythonPatch-lib} ${z-lib})
