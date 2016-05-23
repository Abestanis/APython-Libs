LOCAL_PATH := $(call my-dir)
include $(CLEAR_VARS)

LOCAL_MODULE := $(notdir $(LOCAL_PATH))Module
LOCAL_SRC_FILES := {moduleSourceWildcards}

LOCAL_SHARED_LIBRARIES := pythonPatch python$(PYTHON_SHORT_VERSION) {libDependencies}
LOCAL_MODULE_FILENAME := $(notdir $(LOCAL_PATH))

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

LOCAL_C_INCLUDES := $(LOCAL_PATH)/../{pythonDir}/Modules
LOCAL_SHORT_COMMANDS = true
include $(BUILD_SHARED_LIBRARY)
