LOCAL_PATH := $(call my-dir)
include $(CLEAR_VARS)

LOCAL_MODULE := ncurses
FILE_LIST := $(wildcard $(LOCAL_PATH)/ncurses/*.c) \
             $(wildcard $(LOCAL_PATH)/ncurses/base/*.c) \
             $(wildcard $(LOCAL_PATH)/ncurses/tinfo/*.c) \
             $(wildcard $(LOCAL_PATH)/ncurses/trace/*.c) \
             $(wildcard $(LOCAL_PATH)/ncurses/tty/*.c) \
             $(wildcard $(LOCAL_PATH)/ncurses/widechar/*.c) \
             $(wildcard $(LOCAL_PATH)/form/*.c) \
             $(wildcard $(LOCAL_PATH)/menu/*.c) \
             $(wildcard $(LOCAL_PATH)/panel/*.c)
EXCLUDED_FILES := ncurses/link_test.c \
                  ncurses/base/lib_driver.c \
                  ncurses/base/sigaction.c \
                  ncurses/tinfo/tinfo_driver.c \
                  ncurses/tinfo/make_keys.c \
                  ncurses/tinfo/doalloc.c

LOCAL_SRC_FILES := $(filter-out $(EXCLUDED_FILES), $(FILE_LIST:$(LOCAL_PATH)/%=%))

LOCAL_CFLAGS := -D HAVE_CONFIG_H -D NDEBUG
LOCAL_C_INCLUDES := $(LOCAL_PATH) \
        		    $(LOCAL_PATH)/include \
        		    $(LOCAL_PATH)/ncurses \

LOCAL_EXPORT_C_INCLUDES += $(LOCAL_PATH)/inc $(LOCAL_PATH)/inc/ncurses

LOCAL_SHORT_COMMANDS = true
include $(BUILD_SHARED_LIBRARY)
