LOCAL_PATH := $(call my-dir)
include $(CLEAR_VARS)

LOCAL_MODULE := ffi
BUILD_TARGET := $(TARGET_ARCH)

ifeq ($(BUILD_TARGET), arm64)
  BUILD_TARGET := aarch64
endif
ifeq ($(BUILD_TARGET), x86_64)
  BUILD_TARGET := x86
  LOCAL_CFLAGS += -D __x86_64__
endif
ifeq ($(BUILD_TARGET), mips64)
  BUILD_TARGET := mips
endif

FILE_LIST := $(wildcard $(LOCAL_PATH)/src/*.c) $(wildcard $(LOCAL_PATH)/src/$(BUILD_TARGET)/*.c) $(wildcard $(LOCAL_PATH)/src/$(BUILD_TARGET)/*.S)
EXCLUDED_FILES := src/dlmalloc.c src/x86/darwin64.S src/x86/darwin.S src/x86/freebsd.S src/x86/win64.S

ifneq ($(TARGET_ARCH), x86)
  EXCLUDED_FILES += src/x86/win32.S
endif

LOCAL_SRC_FILES := $(filter-out $(EXCLUDED_FILES), $(FILE_LIST:$(LOCAL_PATH)/%=%))

LOCAL_C_INCLUDES := $(LOCAL_PATH)/include $(LOCAL_PATH)/src/$(BUILD_TARGET)

ifneq (,$(filter $(TARGET_ARCH), arm64 x86_64 mips64))
  LOCAL_CFLAGS += -D ABI_64_BIT
endif
LOCAL_CFLAGS += -D HAVE_LONG_DOUBLE=1

LOCAL_EXPORT_C_INCLUDES += $(LOCAL_PATH)/include $(LOCAL_PATH)/src/$(BUILD_TARGET)
include $(BUILD_SHARED_LIBRARY)
