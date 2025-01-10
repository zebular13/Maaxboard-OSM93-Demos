import time

class InferenceTimeLogger:

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(InferenceTimeLogger, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.sample_size = 10
        self.inference_averages = []
        self.face_detection_inf_time = 0
        self.face_landmark_inf_time = 0
        self.iris_inf_time = 0

    def calculate_total_model_averages(self):
        average = ((self.face_detection_inf_time + self.face_landmark_inf_time + self.iris_inf_time)/3)
        self.inference_averages.append(average)

        if len(self.inference_averages) > self.sample_size:
            self.inference_averages.pop(0)


    def get_models_inf_average(self):
        return sum(self.inference_averages) / len(self.inference_averages) if self.inference_averages else 0
