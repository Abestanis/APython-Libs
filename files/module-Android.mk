LOCAL_PATH := $(call my-dir)
include $(CLEAR_VARS)

LOCAL_MODULE := $(notdir $(LOCAL_PATH))Module
LOCAL_SRC_FILES := {moduleSourceWildcards}

LOCAL_SHARED_LIBRARIES := pythonPatch python$(PYTHON_SHORT_VERSION) {libDependencies}
LOCAL_MODULE_FILENAME := $(notdir $(LOCAL_PATH))

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

LOCAL_SHORT_COMMANDS = true
include $(BUILD_SHARED_LIBRARY)
