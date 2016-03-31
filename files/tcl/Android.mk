LOCAL_PATH := $(call my-dir)
include $(CLEAR_VARS)

LOCAL_MODULE := tcl

FILE_LIST := $(wildcard $(LOCAL_PATH)/generic/*.c) $(wildcard $(LOCAL_PATH)/unix/*.c) $(wildcard $(LOCAL_PATH)/libtommath/*.c)

EXCLUDED_FILES := unix/tclLoadAix.c \
                  unix/tclLoadDyld.c \
                  unix/tclLoadNext.c \
                  unix/tclLoadOSF.c \
                  unix/tclLoadShl.c \
                  unix/tclXtNotify.c \
                  unix/tclXtTest.c \
                  generic/regc_color.c \
                  generic/regc_cvec.c \
                  generic/regc_lex.c \
                  generic/regc_locale.c \
                  generic/regc_nfa.c \
                  generic/rege_dfa.c \
                  generic/tclLoadNone.c \
                  generic/regfronts.c \

LOCAL_SRC_FILES := $(filter-out $(EXCLUDED_FILES), $(FILE_LIST:$(LOCAL_PATH)/%=%))

LOCAL_CFLAGS := -D HAVE_TCL_CONFIG_H -include stdio.h \
                -D TCL_LIBRARY=\"library/\" \
                -D TCL_PACKAGE_PATH=\"library/Tcl/\" \
                -D CFG_RUNTIME_LIBDIR=\"\" -D CFG_RUNTIME_BINDIR=\"\" \
                -D CFG_RUNTIME_SCRDIR=\"\" -D CFG_RUNTIME_INCDIR=\"\" \
                -D CFG_RUNTIME_DOCDIR=\"\" -D CFG_INSTALL_LIBDIR=\"\" \
                -D CFG_INSTALL_BINDIR=\"\" -D CFG_INSTALL_SCRDIR=\"\" \
                -D CFG_INSTALL_INCDIR=\"\" -D CFG_INSTALL_DOCDIR=\"\" \

ifneq (,$(filter $(TARGET_ARCH), arm64 x86_64 mips64))
  LOCAL_CFLAGS += -D ABI_64_BIT
else
  LOCAL_CFLAGS += -U ABI_64_BIT
endif

LOCAL_C_INCLUDES := $(LOCAL_PATH)/generic $(LOCAL_PATH)/unix $(LOCAL_PATH)/libtommath
LOCAL_EXPORT_C_INCLUDES += $(LOCAL_PATH)/generic
LOCAL_LDLIBS := -lz
LOCAL_SHARED_LIBRARIES := pythonPatch

include $(BUILD_SHARED_LIBRARY)
