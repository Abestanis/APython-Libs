LOCAL_PATH := $(call my-dir)
include $(CLEAR_VARS)

LOCAL_MODULE := tk
FILE_LIST := $(wildcard $(LOCAL_PATH)/generic/*.c) $(wildcard $(LOCAL_PATH)/generic/*/*.c) $(wildcard $(LOCAL_PATH)/xlib/*.c) $(wildcard $(LOCAL_PATH)/unix/*.c)

EXCLUDED_FILES := generic/tkPointer.c unix/tkUnixRFont.c

LOCAL_SRC_FILES := $(filter-out $(EXCLUDED_FILES), $(FILE_LIST:$(LOCAL_PATH)/%=%))

LOCAL_CFLAGS := -D 'TkpGetPixel(p)=((((((p)->red & 0xFF) << 24) & 0xFF000000) | ((((p)->green & 0xFF) << 16) & 0x00FF0000) | ((((p)->blue & 0xFF) << 8) & 0x0000FF00)) | 0x000000FF)'

LOCAL_C_INCLUDES := $(LOCAL_PATH)/generic $(LOCAL_PATH)/unix $(LOCAL_PATH)/bitmaps
LOCAL_EXPORT_C_INCLUDES += $(LOCAL_PATH)/generic
LOCAL_SHARED_LIBRARIES := tcl sdl2X11Emulation pythonPatch

include $(BUILD_SHARED_LIBRARY)
