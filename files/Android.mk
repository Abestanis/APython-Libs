LOCAL_PATH := $(call my-dir)
include $(CLEAR_VARS)

LOCAL_MODULE := python$(PYTHON_SHORT_VERSION)
FILE_LIST := $(wildcard $(LOCAL_PATH)/*/*.c) $(wildcard $(LOCAL_PATH)/*/*/*.c) $(wildcard $(LOCAL_PATH)/Modules/_decimal/libmpdec/*.c)

# Filter out all modules that are not supported on Android
EXCLUDED_FILES := Modules/almodule.c \
                  Modules/bsddbmodule.c \
                  Modules/cdmodule.c \
                  Modules/clmodule.c \
                  Modules/dbmmodule.c \
                  Modules/expat/xmltok_impl.c \
                  Modules/expat/xmltok_ns.c \
                  Modules/flmodule.c \
                  Modules/fmmodule.c \
                  Modules/fpectlmodule.c \
                  Modules/gdbmmodule.c \
                  Modules/getaddrinfo.c \
                  Modules/getnameinfo.c \
                  Modules/glmodule.c \
                  Modules/grpmodule.c \
                  Modules/imgfile.c \
                  Modules/nismodule.c \
                  Modules/overlapped.c \
                  Modules/readline.c \
                  Modules/sgimodule.c \
                  Modules/spwdmodule.c \
                  Modules/sunaudiodev.c \
                  Modules/svmodule.c \
                  Modules/_bsddb.c \
                  Modules/_ctypes/darwin/dlfcn_simple.c \
                  Modules/_curses_panel.c \
                  Modules/_cursesmodule.c \
                  Modules/_dbmmodule.c \
                  Modules/_gdbmmodule.c \
                  Modules/_lzmamodule.c \
                  Modules/_multiprocessing/pipe_connection.c \
                  Modules/_multiprocessing/win32_functions.c \
                  Modules/_scproxy.c \
                  Modules/_sqlite/cache.c \
                  Modules/_sqlite/connection.c \
                  Modules/_sqlite/cursor.c \
                  Modules/_sqlite/microprotocols.c \
                  Modules/_sqlite/module.c \
                  Modules/_sqlite/prepare_protocol.c \
                  Modules/_sqlite/row.c \
                  Modules/_sqlite/statement.c \
                  Modules/_sqlite/util.c \
                  Modules/_winapi.c \
                  Parser/intrcheck.c \
                  Parser/parsetok_pgen.c \
                  Parser/tokenizer_pgen.c \
                  Python/dynload_aix.c \
                  Python/dynload_atheos.c \
                  Python/dynload_beos.c \
                  Python/dynload_dl.c \
                  Python/dynload_hpux.c \
                  Python/dynload_next.c \
                  Python/dynload_os2.c \
                  Python/dynload_stub.c \
                  Python/dynload_win.c \
                  Python/getcwd.c \
                  Python/mactoolboxglue.c \
                  Python/sigcheck.c \


# Test, example or template source files and source files defining main
EXCLUDED_FILES += Modules/_ctypes/_ctypes_test.c \
                  Modules/_freeze_importlib.c \
                  Modules/_testbuffer.c \
                  Modules/_testcapimodule.c \
                  Modules/_testembed.c \
                  Modules/_testimportmultiple.c \
                  Modules/fpetestmodule.c \
                  Modules/xxlimited.c \
                  Modules/xxmodule.c \
                  Modules/xxsubtype.c \
                  Modules/zlib/example.c \
                  Modules/zlib/minigzip.c \
                  Parser/pgenmain.c \

LOCAL_SRC_FILES := $(filter-out $(EXCLUDED_FILES), $(FILE_LIST:$(LOCAL_PATH)/%=%))

# Filter out all modules that are separate in their own additional library
EXCLUDED_FILES := $(LOCAL_PATH)/Modules/_ssl.c \
                  $(LOCAL_PATH)/Modules/_hashopenssl.c \
                  $(LOCAL_PATH)/Modules/_hashlib.c \
                  $(LOCAL_PATH)/Modules/bz2module.c \
                  $(LOCAL_PATH)/Modules/_bz2module.c \
                  $(LOCAL_PATH)/Modules/_tkinter.c \
                  $(LOCAL_PATH)/Modules/tkappinit.c \
                  $(LOCAL_PATH)/Modules/cryptmodule.c \
                  $(LOCAL_PATH)/Modules/_cryptmodule.c \
                  $(wildcard $(LOCAL_PATH)/Modules/_ctypes/*) \
                  $(wildcard $(LOCAL_PATH)/Modules/_ctypes/*/*) \

LOCAL_SRC_FILES := $(filter-out $(EXCLUDED_FILES:$(LOCAL_PATH)/%=%), $(LOCAL_SRC_FILES))

LOCAL_CFLAGS := -D 'PLATFORM=\"android\"' \
                -D 'VERSION=\"$(PYTHON_SHORT_VERSION)\"' \
                -D HAVE_EXPAT_CONFIG_H \
                -D 'SOABI=\"apython-$(TARGET_ARCH_ABI)\"' \
                -D __ANDROID__ \
                -D EXTRA_FUNCTIONALITY \
                -D HAVE_UINT128_T \
                -D crypt=DES_crypt \

ifneq (,$(filter $(TARGET_ARCH), arm64 x86_64 mips64))
  LOCAL_CFLAGS += -D ABI_64_BIT -D CONFIG_64 -D HAVE_LINUX_CAN_H
else
  LOCAL_CFLAGS += -U ABI_64_BIT -D CONFIG_32 -U HAVE_LINUX_CAN_H
endif
ifneq (,$(filter $(TARGET_ARCH_ABI), arm64-v8a x86_64 mips64))
  LOCAL_CFLAGS += -U HAVE_FTIME -U HAVE_WAIT3
else
  LOCAL_CFLAGS += -D HAVE_SYS_TYPES_H -D HAVE_WAIT3
endif

ifneq (,$(filter $(TARGET_ARCH), arm arm64 mips64 mips))
    LOCAL_CFLAGS += -D ANSI
endif
ifneq (,$(filter $(TARGET_ARCH), x86_64 x86))
    LOCAL_CFLAGS += -D ASM
endif

ifeq ($(TARGET_ARCH), x86)
    LOCAL_CFLAGS += -U CONFIG_64 -D PPRO
endif
ifneq (,$(filter $(TARGET_ARCH_ABI), armeabi armeabi-v7a x86 mips))
  LOCAL_CFLAGS += -U HAVE_WAIT3
endif

LOCAL_C_INCLUDES := $(LOCAL_PATH)/Include $(LOCAL_PATH)/Modules $(LOCAL_PATH)/Modules/_io $(LOCAL_PATH)/Modules/expat $(LOCAL_PATH)/Modules/cjkcodecs $(LOCAL_PATH)/Modules/_decimal $(LOCAL_PATH)/Modules/_decimal/libmpdec
LOCAL_EXPORT_C_INCLUDES += $(LOCAL_PATH)/Include
LOCAL_SHARED_LIBRARIES := pythonPatch
LOCAL_LDLIBS := -lz

LOCAL_SHORT_COMMANDS = true
include $(BUILD_SHARED_LIBRARY)

include $(call all-subdir-makefiles)
