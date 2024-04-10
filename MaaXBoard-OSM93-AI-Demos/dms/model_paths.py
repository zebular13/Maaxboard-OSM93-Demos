import os

# get current directory (dms folder)
current_dir = os.path.dirname(os.path.abspath(__file__))

# set as dms directory / models
model_dir = parent_dir = os.path.join(current_dir, "models/")

MODEL_DIR = model_dir

CPU_MODELS = {
    'DETECT_MODEL': 'face_detection_front_128_full_integer_quant.tflite',
    'LANDMARK_MODEL': 'face_landmark_192_integer_quant.tflite',
    'EYE_MODEL': 'iris_landmark_quant.tflite'
}

NPU_MODELS = {
    'DETECT_MODEL': 'face_detection_front_128_full_integer_quant_vela.tflite',
    'LANDMARK_MODEL': 'face_landmark_192_integer_quant_vela.tflite',
    'EYE_MODEL': 'iris_landmark_quant_vela.tflite'
}