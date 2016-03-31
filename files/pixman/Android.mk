LOCAL_PATH := $(call my-dir)
include $(CLEAR_VARS)

LOCAL_MODULE := pixman
FILE_LIST := $(wildcard $(LOCAL_PATH)/pixman/*.[c|S])

EXCLUDED_FILES := pixman-region.c pixman-sse2.c pixman-ssse3.c pixman-vmx.c pixman-mips-dspr2.c \
                  pixman-mips-memcpy-asm.S pixman-mips-dspr2-asm.S

ifneq ($(TARGET_ARCH), arm)
    EXCLUDED_FILES += pixman-arm-neon-asm-bilinear.S pixman-arm-neon-asm.S \
                      pixman-arm-simd-asm-scaled.S pixman-arm-simd-asm.S \
                      pixman-arm-simd.c pixman-arm-neon.c
endif


EXCLUDED_FILES := $(addprefix pixman/, $(EXCLUDED_FILES))
LOCAL_SRC_FILES := $(filter-out $(EXCLUDED_FILES), $(FILE_LIST:$(LOCAL_PATH)/%=%))

LOCAL_CFLAGS := -D HAVE_CONFIG_H -U ANDROID -U __ANDROID__
LOCAL_CFLAGS += -D __ARM__=2 -D __X86__=3

ifeq ($(TARGET_ARCH), arm)
    LOCAL_CFLAGS += -D TARGET_ARCH=__ARM__
endif
ifneq (,$(filter $(TARGET_ARCH), x86_64 x86))
    LOCAL_CFLAGS += -D TARGET_ARCH=__X86__
endif

LOCAL_C_INCLUDES := $(LOCAL_PATH)/pixman
LOCAL_EXPORT_C_INCLUDES += $(LOCAL_PATH)/pixman
#LOCAL_SHARED_LIBRARIES := pythonPatch

include $(BUILD_SHARED_LIBRARY)
