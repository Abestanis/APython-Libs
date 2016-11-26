LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)

LOCAL_MODULE := SDL2_gpu

SDL_GPU_DIR := ./
STB_IMAGE_DIR := $(SDL_GPU_DIR)/src/externals/stb_image
STB_IMAGE_WRITE_DIR := $(SDL_GPU_DIR)/src/externals/stb_image_write

LOCAL_SRC_FILES := $(SDL_GPU_DIR)/src/SDL_gpu.c \
				   $(SDL_GPU_DIR)/src/SDL_gpu_matrix.c \
				   $(SDL_GPU_DIR)/src/SDL_gpu_renderer.c \
				   $(SDL_GPU_DIR)/src/SDL_gpu_shapes.c \
				   $(SDL_GPU_DIR)/src/renderer_GLES_1.c \
				   $(SDL_GPU_DIR)/src/renderer_GLES_2.c \
				   $(SDL_GPU_DIR)/src/renderer_GLES_3.c \
				   $(STB_IMAGE_DIR)/stb_image.c \
				   $(STB_IMAGE_WRITE_DIR)/stb_image_write.c


LOCAL_CFLAGS += -DSDL_GPU_DISABLE_OPENGL -DSTBI_FAILURE_USERMSG -O3

LOCAL_LDLIBS += -llog -lGLESv1_CM
LOCAL_LDLIBS += -lGLESv2

# Disable GLES version 3 support for now, since some environments aren't set up for it yet
# Enable it if you want it!
LOCAL_CFLAGS += -DSDL_GPU_DISABLE_GLES_3
#LOCAL_LDLIBS += -lGLESv3

LOCAL_SHARED_LIBRARIES := SDL2
LOCAL_C_INCLUDES := $(LOCAL_PATH)/include $(LOCAL_PATH)/src $(LOCAL_PATH)/$(STB_IMAGE_DIR) $(LOCAL_PATH)/$(STB_IMAGE_WRITE_DIR)
LOCAL_EXPORT_C_INCLUDES += $(LOCAL_PATH)/include

include $(BUILD_SHARED_LIBRARY)
