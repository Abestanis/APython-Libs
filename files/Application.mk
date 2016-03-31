LOCAL_PATH := $(call my-dir)

# The minimum API version we support is 8
APP_PLATFORM := android-{androidSdkVersion}

PYTHON_SHORT_VERSION := {pyShortVersion}
#APP_ABI := all
# The value of APP_ABI is given via the command line.

APP_BUILD_SCRIPT := $(LOCAL_PATH)/Android.mk
