LOCAL_PATH := $(call my-dir)
include $(CLEAR_VARS)

LOCAL_MODULE := openSSL
FILE_LIST := $(wildcard $(LOCAL_PATH)/ssl/*.c) \
             $(wildcard $(LOCAL_PATH)/ssl/*/*.c) \
             $(wildcard $(LOCAL_PATH)/crypto/*.c) \
             $(wildcard $(LOCAL_PATH)/crypto/*/*.c) \
             $(wildcard $(LOCAL_PATH)/crypto/*/*/*.c)

LOCAL_SRC_FILES := $(FILE_LIST:$(LOCAL_PATH)/%=%)
EXCLUDED_DIRS := crypto/engine \
                 crypto/md2 \
                 crypto/rc5 \

EXCLUDED_FILES := crypto/LPdir_nyi.c \
                  crypto/LPdir_vms.c \
                  crypto/LPdir_win.c \
                  crypto/LPdir_win32.c \
                  crypto/LPdir_wince.c \
                  crypto/LPdir_unix.c \
                  crypto/ppccap.c \
                  crypto/s390xcap.c \
                  crypto/sparcv9cap.c \
                  crypto/bn/asm/x86_64-gcc.c \
                  crypto/bf/bf_cbc.c \
                  crypto/des/ncbc_enc.c \
                  crypto/ec/ecp_nistz256_table.c \
                  crypto/poly1305/poly1305_ieee754.c \
                  crypto/pkcs7/pk7_enc.c \
                  crypto/rc2/tab.c \
                  crypto/x509v3/tabtest.c \
                  crypto/x509v3/v3conf.c \
                  crypto/x509v3/v3prin.c

ifeq ($(TARGET_ARCH), x86_64)
  EXCLUDED_FILES += crypto/aes/aes_cbc.c \
                    crypto/camellia/camellia.c \
                    crypto/camellia/cmll_cbc.c \
                    crypto/rc4/rc4_enc.c \
                    crypto/rc4/rc4_skey.c \
                    crypto/whrlpool/wp_block.c
endif
ifeq ($(TARGET_ARCH), x86)
  EXCLUDED_DIRS += crypto/camellia
else
  EXCLUDED_FILES += crypto/aes/aes_x86core.c
endif
ifneq ($(TARGET_ARCH), arm64)
  EXCLUDED_FILES += crypto/aes/aes_core.c
endif
ifeq (,$(filter $(TARGET_ARCH), arm64 arm)) #If not arm
  EXCLUDED_FILES += crypto/armcap.c
endif
ifneq (,$(filter $(TARGET_ARCH), mips mips64))
  EXCLUDED_FILES += crypto/bn/bn_asm.c \
                    crypto/ec/ecp_nistz256.c
else
  EXCLUDED_FILES += crypto/mem_clr.c \
                    crypto/chacha/chacha_enc.c
endif

EXCLUDED_FILES_FROM_DIRS := $(foreach DIR, $(EXCLUDED_DIRS), $(wildcard $(LOCAL_PATH)/$(DIR)/*.c))
EXCLUDED_FILES += $(EXCLUDED_FILES_FROM_DIRS:$(LOCAL_PATH)/%=%)

LOCAL_SRC_FILES := $(filter-out $(EXCLUDED_FILES), $(FILE_LIST:$(LOCAL_PATH)/%=%))

ifeq ($(TARGET_ARCH), arm64)
  LOCAL_CFLAGS += -D__aarch64__ -D__ARM_ARCH__=8
  LOCAL_EXPORT_CFLAGS += -D__aarch64__ -D__ARM_ARCH__=8
endif
ifeq ($(TARGET_ARCH), x86_64)
  LOCAL_CFLAGS += -D__x86_64__
  LOCAL_EXPORT_CFLAGS += -D__x86_64__
endif
ifeq ($(TARGET_ARCH), x86)
  LOCAL_CFLAGS += -D__x86__
  LOCAL_EXPORT_CFLAGS += -D__x86__
endif
ifeq ($(TARGET_ARCH), mips64)
  LOCAL_CFLAGS += -D__mips64
  LOCAL_EXPORT_CFLAGS += -D__mips64
endif
ifeq ($(TARGET_ARCH), arm)
  LOCAL_CFLAGS += -D__arm__
  LOCAL_EXPORT_CFLAGS += -D__arm__
endif

ifeq ($(TARGET_ARCH_ABI), armeabi)
  LOCAL_CFLAGS += -D__ARM_ARCH__=5
  LOCAL_EXPORT_CFLAGS += -D__ARM_ARCH__=5
endif
ifeq ($(TARGET_ARCH_ABI), armeabi-v7a)
  LOCAL_CFLAGS += -D__ARM_ARCH__=7
  LOCAL_EXPORT_CFLAGS += -D__ARM_ARCH__=7
endif

ifeq ($(TARGET_ARCH), arm)
  ASSEMBLY_SOURCE_FILES := crypto/ec/ecp_nistz256-armv4.s \
                           crypto/modes/ghashv8-armx.s
  ifeq ($(TARGET_ARCH_ABI), armeabi)
    LOCAL_LDLIBS += -latomic
    ASSEMBLY_SOURCE_FILES += crypto/armv4cpuid.s \
                             crypto/aes/aes-armv4.s \
                             crypto/bn/armv4-gf2m.s \
                             crypto/bn/armv4-mont.s \
                             crypto/chacha/chacha-armv4.s \
                             crypto/modes/ghash-armv4.s \
                             crypto/poly1305/poly1305-armv4.s \
                             crypto/sha/sha1-armv4-large.s \
                             crypto/sha/sha256-armv4.s \
                             crypto/sha/sha512-armv4.s
  endif
  ifeq ($(TARGET_ARCH_ABI), armeabi-v7a)
    ASSEMBLY_SOURCE_FILES += crypto/armv4cpuid_v7a.s \
                             crypto/aes/aes-armv4_v7a.s \
                             crypto/aes/aesv8-armx.s \
                             crypto/aes/bsaes-armv7.s \
                             crypto/bn/armv4-gf2m_v7a.s \
                             crypto/bn/armv4-mont_v7a.s \
                             crypto/chacha/chacha-armv4_v7a.s \
                             crypto/modes/ghash-armv4_v7a.s \
                             crypto/poly1305/poly1305-armv4_v7a.s \
                             crypto/sha/sha1-armv4-large_v7a.s \
                             crypto/sha/sha256-armv4_v7a.s \
                             crypto/sha/sha512-armv4_v7a.s
  endif
endif

ifeq ($(TARGET_ARCH), mips)
  ASSEMBLY_SOURCE_FILES := crypto/aes/aes-mips.s \
                           crypto/bn/bn-mips.s \
                           crypto/bn/mips-mont.s \
                           crypto/sha/sha1-mips.s \
                           crypto/sha/sha256-mips.s
  LOCAL_ASFLAGS += -fno-integrated-as
endif
ifeq ($(TARGET_ARCH), mips64)
  ASSEMBLY_SOURCE_FILES := crypto/aes/aes-mips64.s \
                           crypto/bn/bn-mips64.s \
                           crypto/bn/mips64-mont.s \
                           crypto/sha/sha1-mips64.s \
                           crypto/sha/sha256-mips64.s \
                           crypto/sha/sha512-mips.s \
                           crypto/poly1305/poly1305-mips.s
  LOCAL_ASFLAGS += -fno-integrated-as
endif

ifeq ($(TARGET_ARCH), x86)
  ASSEMBLY_SOURCE_FILES := crypto/x86cpuid.s \
                           crypto/aes/aesni-x86.s \
                           crypto/aes/vpaes-x86.s \
                           crypto/bn/x86-gf2m.s \
                           crypto/bn/x86-mont.s \
                           crypto/camellia/cmll-x86.s \
                           crypto/chacha/chacha-x86.s \
                           crypto/ec/ecp_nistz256-x86.s \
                           crypto/md5/md5-586.s \
                           crypto/modes/ghash-x86.s \
                           crypto/poly1305/poly1305-x86.s \
                           crypto/ripemd/rmd-586.s \
                           crypto/sha/sha1-586.s \
                           crypto/sha/sha256-586.s \
                           crypto/sha/sha512-586.s \
                           crypto/whrlpool/wp-mmx.s
endif
ifeq ($(TARGET_ARCH), x86_64)
  ASSEMBLY_SOURCE_FILES := crypto/x86_64cpuid.s \
                           crypto/aes/aes-x86_64.s \
                           crypto/aes/aesni-mb-x86_64.s \
                           crypto/aes/aesni-sha1-x86_64.s \
                           crypto/aes/aesni-sha256-x86_64.s \
                           crypto/aes/aesni-x86_64.s \
                           crypto/aes/bsaes-x86_64.s \
                           crypto/aes/vpaes-x86_64.s \
                           crypto/bn/rsaz-avx2.s \
                           crypto/bn/rsaz-x86_64.s \
                           crypto/bn/x86_64-gf2m.s \
                           crypto/bn/x86_64-mont.s \
                           crypto/bn/x86_64-mont5.s \
                           crypto/camellia/cmll-x86_64.s \
                           crypto/chacha/chacha-x86_64.s \
                           crypto/ec/ecp_nistz256-x86_64.s \
                           crypto/md5/md5-x86_64.s \
                           crypto/modes/aesni-gcm-x86_64.s \
                           crypto/modes/ghash-x86_64.s \
                           crypto/poly1305/poly1305-x86_64.s \
                           crypto/rc4/rc4-md5-x86_64.s \
                           crypto/rc4/rc4-x86_64.s \
                           crypto/sha/sha1-mb-x86_64.s \
                           crypto/sha/sha1-x86_64.s \
                           crypto/sha/sha256-mb-x86_64.s \
                           crypto/sha/sha256-x86_64.s \
                           crypto/sha/sha512-x86_64.s \
                           crypto/whrlpool/wp-x86_64.s
endif

ifeq ($(TARGET_ARCH), arm64)
  ASSEMBLY_SOURCE_FILES := crypto/arm64cpuid.s \
                           crypto/modes/ghashv8-armx-aarch64.s \
                           crypto/aes/vpaes-armv8.s \
                           crypto/bn/armv8-mont.s \
                           crypto/chacha/chacha-armv8.s \
                           crypto/ec/ecp_nistz256-armv8.s \
                           crypto/poly1305/poly1305-armv8.s \
                           crypto/sha/sha1-armv8.s \
                           crypto/sha/sha256-armv8.s \
                           crypto/sha/sha512-armv8.s \
                           crypto/aes/aesv8-armx_v8a.s
endif

LOCAL_SRC_FILES += $(ASSEMBLY_SOURCE_FILES)


LOCAL_CFLAGS += -DOPENSSLDIR=\\\"/usr/local/ssl/\\\" -DOPENSSL_NO_FILENAMES

LOCAL_C_INCLUDES := $(LOCAL_PATH) \
                    $(LOCAL_PATH)/include \
                    $(LOCAL_PATH)/ssl \
                    $(dir $(wildcard $(LOCAL_PATH)/ssl/*/*.h)) \
                    $(LOCAL_PATH)/crypto \
                    $(LOCAL_PATH)/crypto/include \
                    $(dir $(wildcard $(LOCAL_PATH)/crypto/*/*.h))
LOCAL_EXPORT_C_INCLUDES += $(LOCAL_PATH)/include

LOCAL_SHORT_COMMANDS = true
include $(BUILD_SHARED_LIBRARY)
