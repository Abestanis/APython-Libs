LOCAL_PATH := $(call my-dir)
include $(CLEAR_VARS)

LOCAL_MODULE := tk
FILE_LIST := $(wildcard $(LOCAL_PATH)/generic/*.c) \
             $(wildcard $(LOCAL_PATH)/generic/*/*.c) \
             $(wildcard $(LOCAL_PATH)/unix/*.c)

EXCLUDED_FILES := generic/tkPointer.c \
                  generic/tkOldTest.c \
                  generic/tkTest.c \
                  unix/tkUnixRFont.c

LOCAL_SRC_FILES := $(filter-out $(EXCLUDED_FILES), $(FILE_LIST:$(LOCAL_PATH)/%=%))

LOCAL_CFLAGS += -DHAVE_TK_CONFIG_H -imacros tkConfig.h

LOCAL_C_INCLUDES := $(LOCAL_PATH)/generic $(LOCAL_PATH)/unix $(LOCAL_PATH)/bitmaps
LOCAL_EXPORT_C_INCLUDES += $(LOCAL_PATH)/generic
LOCAL_SHARED_LIBRARIES := tcl sdl2X11Emulation

ifeq ($(TARGET_ARCH_ABI), armeabi)
  LOCAL_CFLAGS += -O0 # TODO: This is a workaround for a compiler crash (see https://github.com/android-ndk/ndk/issues/429)
endif

include $(BUILD_SHARED_LIBRARY)
