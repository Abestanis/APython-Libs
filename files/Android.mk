LOCAL_PATH := $(call my-dir)
include $(CLEAR_VARS)

LOCAL_MODULE := python$(PYTHON_SHORT_VERSION)
FILE_LIST := $(wildcard $(LOCAL_PATH)/*/*.c) $(wildcard $(LOCAL_PATH)/*/*/*.c) #$(wildcard $(LOCAL_PATH)/Modules/_decimal/*/*.c)
EXCLUDED_FILES := Modules/almodule.c \
                  Modules/bsddbmodule.c \
                  Modules/cdmodule.c \
                  Modules/clmodule.c \
                  Modules/dbmmodule.c \
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
                  Modules/ossaudiodev.c \
                  Modules/readline.c \
                  Modules/sgimodule.c \
                  Modules/spwdmodule.c \
                  Modules/sunaudiodev.c \
                  Modules/svmodule.c \
                  Modules/tkappinit.c \
                  Modules/_bsddb.c \
                  Modules/_bz2module.c \
                  Modules/_cryptmodule.c \
                  Modules/cryptmodule.c \
                  Modules/_cursesmodule.c \
                  Modules/_curses_panel.c \
                  Modules/_dbmmodule.c \
                  Modules/_elementtree.c \
                  Modules/_freeze_importlib.c \
                  Modules/_gdbmmodule.c \
                  Modules/_hashopenssl.c \
                  Modules/_lzmamodule.c \
                  Modules/_scproxy.c \
                  Modules/_ssl.c \
                  Modules/_tkinter.c \
                  Modules/_testembed.c \
                  Modules/_ctypes/darwin/dlfcn_simple.c \
                  Modules/_decimal/_decimal.c \
                  Modules/_multiprocessing/multiprocessing.c \
                  Modules/_multiprocessing/pipe_connection.c \
                  Modules/_multiprocessing/win32_functions.c \
                  Modules/_multiprocessing/socket_connection.c \
                  Modules/_multiprocessing/semaphore.c \
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
                  Modules/audioop.c \
                  Modules/expat/xmltok_impl.c \
                  Modules/expat/xmltok_ns.c \
                  Modules/overlapped.c \
                  Modules/zlib/example.c \
                  Modules/zlib/minigzip.c \
                  Parser/intrcheck.c \
                  Parser/pgenmain.c \
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

LOCAL_SRC_FILES := $(filter-out $(EXCLUDED_FILES), $(FILE_LIST:$(LOCAL_PATH)/%=%))


LOCAL_CFLAGS = -D 'PLATFORM=\"android\"' \
               -D 'VERSION=\"$(PYTHON_SHORT_VERSION)\"' \
               -D HAVE_EXPAT_CONFIG_H \
               -D 'SOABI=\"apython-$(TARGET_ARCH)\"' \
               -D CONFIG_32 \

LOCAL_C_INCLUDES := $(LOCAL_PATH)/Include $(LOCAL_PATH)/Modules/_io $(LOCAL_PATH)/Modules/expat $(LOCAL_PATH)/Modules/cjkcodecs $(LOCAL_PATH)Modules/_decimal/libmpdec
LOCAL_EXPORT_C_INCLUDES += $(LOCAL_PATH)Include
LOCAL_SHARED_LIBRARIES := pythonPatch ffi openSSL bzip # TODO: This is Temp
LOCAL_LDLIBS := -lz

LOCAL_SHORT_COMMANDS = true
include $(BUILD_SHARED_LIBRARY)

include $(call all-subdir-makefiles)
