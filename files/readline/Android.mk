LOCAL_PATH := $(call my-dir)
include $(CLEAR_VARS)

LOCAL_MODULE := readline
RL_LIBRARY_VERSION = 7.0
FILE_LIST := $(wildcard $(LOCAL_PATH)/*.c)
EXCLUDED_FILES := emacs_keymap.c \
                  vi_keymap.c

LOCAL_SRC_FILES := $(filter-out $(EXCLUDED_FILES), $(FILE_LIST:$(LOCAL_PATH)/%=%))

LOCAL_C_INCLUDES := $(LOCAL_PATH) $(LOCAL_PATH)/inc
LOCAL_CFLAGS += -D RL_LIBRARY_VERSION='"$(RL_LIBRARY_VERSION)"' \
                -D HAVE_CONFIG_H

LOCAL_SHARED_LIBRARIES := ncurses IPC
LOCAL_EXPORT_C_INCLUDES += $(LOCAL_PATH)/inc
include $(BUILD_SHARED_LIBRARY)
