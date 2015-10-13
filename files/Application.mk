LOCAL_PATH := $(call my-dir)

# The minimum API version we support is 8
APP_PLATFORM := android-8

PYTHON_SHORT_VERSION := {pyShortVersion}
APP_ABI := armeabi-v7a#all

APP_BUILD_SCRIPT := $(LOCAL_PATH)/Android.mk
