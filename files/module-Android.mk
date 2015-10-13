LOCAL_PATH := $(call my-dir)
include $(CLEAR_VARS)

LOCAL_MODULE := $(notdir $(LOCAL_PATH))Module
LOCAL_SRC_FILES := {moduleSourceWildcards}

LOCAL_SHARED_LIBRARIES := pythonPatch python$(PYTHON_SHORT_VERSION) {libDependencies}
LOCAL_MODULE_FILENAME := $(notdir $(LOCAL_PATH))

LOCAL_SHORT_COMMANDS = true
include $(BUILD_SHARED_LIBRARY)
