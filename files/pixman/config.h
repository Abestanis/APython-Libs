/* config.h  */

/* Define if building universal (internal helper macro) */
#undef AC_APPLE_UNIVERSAL_BUILD

/* Whether we have alarm() */
#define HAVE_ALARM 1

/* Whether the compiler supports __builtin_clz */
#define HAVE_BUILTIN_CLZ 1

/* Define to 1 if you have the <dlfcn.h> header file. */
#define HAVE_DLFCN_H 1

/* Whether we have FE_DIVBYZERO */
#define HAVE_FEDIVBYZERO 1

/* Whether we have feenableexcept() */
#define HAVE_FEENABLEEXCEPT 1

/* Define to 1 if we have <fenv.h> */
#define HAVE_FENV_H 1

/* Whether the tool chain supports __float128 */
#define HAVE_FLOAT128 1

/* Whether the compiler supports GCC vector extensions */
#define HAVE_GCC_VECTOR_EXTENSIONS 1

/* Define to 1 if you have the `getisax' function. */
#undef HAVE_GETISAX

/* Whether we have getpagesize() */
#define HAVE_GETPAGESIZE 1

/* Whether we have gettimeofday() */
#define HAVE_GETTIMEOFDAY 1

/* Define to 1 if you have the <inttypes.h> header file. */
#define HAVE_INTTYPES_H 1

/* Define to 1 if you have the `pixman-1' library (-lpixman-1). */
#undef HAVE_LIBPIXMAN_1

/* Whether we have libpng */
#undef HAVE_LIBPNG

/* Define to 1 if you have the <memory.h> header file. */
#define HAVE_MEMORY_H 1

/* Whether we have mmap() */
#define HAVE_MMAP 1

/* Whether we have mprotect() */
#define HAVE_MPROTECT 1

/* Whether we have posix_memalign() */
#define HAVE_POSIX_MEMALIGN 1

/* Whether pthreads is supported */
#define HAVE_PTHREADS 1

/* Whether we have sigaction() */
#define HAVE_SIGACTION 1

/* Define to 1 if you have the <stdint.h> header file. */
#define HAVE_STDINT_H 1

/* Define to 1 if you have the <stdlib.h> header file. */
#define HAVE_STDLIB_H 1

/* Define to 1 if you have the <strings.h> header file. */
#define HAVE_STRINGS_H 1

/* Define to 1 if you have the <string.h> header file. */
#define HAVE_STRING_H 1

/* Define to 1 if we have <sys/mman.h> */
#define HAVE_SYS_MMAN_H 1

/* Define to 1 if you have the <sys/stat.h> header file. */
#define HAVE_SYS_STAT_H 1

/* Define to 1 if you have the <sys/types.h> header file. */
#define HAVE_SYS_TYPES_H 1

/* Define to 1 if you have the <unistd.h> header file. */
#define HAVE_UNISTD_H 1

/* Define to the sub-directory where libtool stores uninstalled libraries. */
#define LT_OBJDIR "/"

/* Name of package */
#define PACKAGE "pixman"

/* Define to the address where bug reports for this package should be sent. */
#define PACKAGE_BUGREPORT "http://lists.freedesktop.org/mailman/listinfo/pixman"

/* Define to the full name of this package. */
#define PACKAGE_NAME "libpixman"

/* Define to the full name and version of this package. */
#define PACKAGE_STRING "libpixman.0.34.0"

/* Define to the one symbol short name of this package. */
#define PACKAGE_TARNAME

/* Define to the home page for this package. */
#define PACKAGE_URL "http://cairographics.org/releases/pixman-0.32.8.tar.gz"

/* Define to the version of this package. */
#define PACKAGE_VERSION "0.34.0"

/* enable TIMER_BEGIN/TIMER_END macros */
#if TARGET_ARCH == __X86__
#  define PIXMAN_TIMERS 1
#endif

/* The size of `long', as computed by sizeof. */
#define SIZEOF_LONG __sizeof_long__

/* Define to 1 if you have the ANSI C header files. */
#define STDC_HEADERS 1

/* The compiler supported TLS storage class */
#undef TLS

/* Whether the tool chain supports __attribute__((constructor)) */
#define TOOLCHAIN_SUPPORTS_ATTRIBUTE_CONSTRUCTOR 1

/* use ARM IWMMXT compiler intrinsics */
#undef USE_ARM_IWMMXT

/* use ARM NEON assembly optimizations */
#if TARGET_ARCH == __ARM__
#  define USE_ARM_NEON 1
#else
#  undef USE_ARM_NEON
#endif
/* use ARM SIMD assembly optimizations */
#if TARGET_ARCH == __ARM__
#  define USE_ARM_SIMD 1
#else
#  undef USE_ARM_SIMD
#endif

/* use GNU-style inline assembler */
#define USE_GCC_INLINE_ASM 1

/* use Loongson Multimedia Instructions */
#undef USE_LOONGSON_MMI

/* use MIPS DSPr2 assembly optimizations */
#undef USE_MIPS_DSPR2

/* use OpenMP in the test suite */
#undef USE_OPENMP

/* use SSE2 compiler intrinsics */
#undef USE_SSE2

/* use SSSE3 compiler intrinsics */
#undef USE_SSSE3

/* use VMX compiler intrinsics */
#undef USE_VMX

/* use x86 MMX compiler intrinsics */
#if TARGET_ARCH == __X86__
#  define USE_X86_MMX 1
#else
#  undef USE_X86_MMX
#endif

/* Version number of package */
#define VERSION "0.34.0"

/* Define WORDS_BIGENDIAN to 1 if your processor stores words with the most
   significant byte first (like Motorola and SPARC, unlike Intel). */
#if defined AC_APPLE_UNIVERSAL_BUILD
# if defined __BIG_ENDIAN__
#  define WORDS_BIGENDIAN 1
# endif
#else
# ifndef WORDS_BIGENDIAN
#  define WORDS_BIGENDIAN
# endif
#endif

/* Define to `__inline__' or `__inline' if that's what the C compiler
   calls it, or to nothing if 'inline' is not supported under any name.  */
#ifndef __cplusplus
//#undef inline
#endif

/* Define to sqrt if you do not have the `sqrtf' function. */
#undef sqrtf
