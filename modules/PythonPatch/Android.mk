LOCAL_PATH := $(call my-dir)
include $(CLEAR_VARS)

LOCAL_MODULE := pythonPatch
LOCAL_SRC_FILES := redirects.c
LOCAL_EXPORT_LDFLAGS := -Wl,--wrap,exit \
                        -Wl,--wrap,setlocale \
                        -Wl,--wrap,mbstowcs \
                        -Wl,--wrap,ttyname 

LOCAL_EXPORT_C_INCLUDES := $(LOCAL_PATH)

include $(BUILD_STATIC_LIBRARY)
