LOCAL_PATH := $(call my-dir)
include $(CLEAR_VARS)

LOCAL_MODULE := $(notdir $(LOCAL_PATH))Module
LOCAL_SRC_FILES := {moduleSourceWildcards}
LOCAL_SRC_FILES := $(LOCAL_SRC_FILES:$(LOCAL_PATH)/%=%)

LOCAL_SHARED_LIBRARIES := python$(PYTHON_SHORT_VERSION) {libDependencies}
LOCAL_WHOLE_STATIC_LIBRARIES := pythonPatch
LOCAL_MODULE_FILENAME := $(notdir $(LOCAL_PATH))

LOCAL_CFLAGS := -D 'PLATFORM=\"android\"' \
                -D 'VERSION=\"$(PYTHON_SHORT_VERSION)\"' \
                -D HAVE_EXPAT_CONFIG_H \
                -D 'SOABI=\"apython-$(TARGET_ARCH_ABI)\"' \
                -D EXTRA_FUNCTIONALITY \
                -D HAVE_UINT128_T \
                -D crypt=DES_crypt \
                -D NDEBUG \

ifneq (,$(filter $(TARGET_ARCH), arm64 x86_64 mips64))
  LOCAL_CFLAGS += -D ABI_64_BIT -D CONFIG_64
else
  LOCAL_CFLAGS += -U ABI_64_BIT -D CONFIG_32
endif

ifneq (,$(filter $(TARGET_ARCH), arm arm64 mips64 mips))
    LOCAL_CFLAGS += -D ANSI
endif
ifneq (,$(filter $(TARGET_ARCH), x86_64 x86))
    LOCAL_CFLAGS += -D ASM
endif
ifeq ($(TARGET_ARCH), x86)
    LOCAL_CFLAGS += -U CONFIG_64 -D PPRO
endif


LOCAL_C_INCLUDES := $(LOCAL_PATH)/../{pythonDir}/Modules
LOCAL_SHORT_COMMANDS = true
include $(BUILD_SHARED_LIBRARY)
