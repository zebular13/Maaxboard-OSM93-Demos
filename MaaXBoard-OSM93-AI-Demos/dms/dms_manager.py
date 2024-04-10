#
# Copyright 2020-2023 NXP
#
# SPDX-License-Identifier: Apache-2.0
#

import pathlib
import sys
import time
import cv2

from dms import model_paths
from dms.face_detection import FaceDetector
from dms.eye_landmark import EyeMesher
from dms.face_landmark import FaceMesher
from dms.utils import *

class DMSManager:
    def __init__(self, run_on_hardware=False, use_npu=False):
        self.run_on_hardware = run_on_hardware
        self.use_npu = use_npu
        self.path_to_models = model_paths.MODEL_DIR
        self.face_detector = None
        self.face_mesher = None
        self.eye_mesher = None
        self.target_dim = (320,240)
        self.attention_status = None
        self.yawning_status = None
        self.eye_status = None
        self.inference_speed = None

        model_selector = model_paths.NPU_MODELS if self.use_npu else model_paths.CPU_MODELS

        print(self.path_to_models)

        self.face_detector = FaceDetector(model_path = str(self.path_to_models + model_selector['DETECT_MODEL']), 
                                          delegate_path = None, 
                                          img_size=self.target_dim,
                                          run_on_hardware=self.run_on_hardware)
        
        self.face_mesher = FaceMesher(model_path=str((self.path_to_models + model_selector['LANDMARK_MODEL'])), 
                                      delegate_path = None,
                                      run_on_hardware=self.run_on_hardware)
        
        self.eye_mesher = EyeMesher(model_path=str((self.path_to_models + model_selector['EYE_MODEL'])),
                                    delegate_path = None,
                                    run_on_hardware=self.run_on_hardware)

    def draw_face_box(self, image, bboxes, landmarks, scores):
        for bbox, landmark, score in zip(bboxes.astype(int), landmarks.astype(int), scores):
            image = cv2.rectangle(image, tuple(bbox[:2]), tuple(bbox[2:]), color=(255, 0, 0), thickness=2)
            landmark = landmark.reshape(-1, 2)

            score_label = "{:.2f}".format(score)
            (label_width, label_height), baseline = cv2.getTextSize(score_label,
                                                                    cv2.FONT_HERSHEY_SIMPLEX,
                                                                    fontScale=0.4,
                                                                    thickness=1)
            label_btmleft = bbox[:2].copy() + 10
            label_btmleft[0] += label_width
            label_btmleft[1] += label_height
            cv2.rectangle(image, tuple(bbox[:2]), tuple(label_btmleft), color=(255, 0, 0), thickness=cv2.FILLED)
            cv2.putText(image, score_label, (bbox[0] + 5, label_btmleft[1] - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.4, color=(255, 255, 255), thickness=1)
        return image

    # detect single frame
    def process_frame_dms(self, image):

        h, w, _ = image.shape
        # print("DMS image shape", image.shape)

        target_dim = max(w, h)
        padded_size = [(target_dim - h) // 2, (target_dim - h + 1) // 2,
                    (target_dim - w) // 2, (target_dim - w + 1) // 2]
        padded = cv2.copyMakeBorder(image.copy(),
                                    *padded_size,
                                    cv2.BORDER_CONSTANT,
                                    value=[0, 0, 0])
        padded = cv2.flip(padded, 3)

        # face detection
        start = time.time()
        bboxes_decoded, landmarks, scores = self.face_detector.inference(padded)
        end = time.time()
        delta = (end-start)*1000
        self.inference_speed = "{:.2f}".format(delta)

        mesh_landmarks_inverse = []
        r_vecs, t_vecs = [], []

        for i, (bbox, landmark) in enumerate(zip(bboxes_decoded, landmarks)):
            # landmark detection
            aligned_face, M, angel = self.face_detector.align(padded, landmark)
            mesh_landmark, mesh_scores = self.face_mesher.inference(aligned_face)
            mesh_landmark_inverse = self.face_detector.inverse(mesh_landmark, M)
            mesh_landmarks_inverse.append(mesh_landmark_inverse)

            # pose detection
            r_vec, t_vec = self.face_detector.decode_pose(landmark)
            r_vecs.append(r_vec)
            t_vecs.append(t_vec)

        # draw
        image_show = padded.copy()
        self.draw_face_box(image_show, bboxes_decoded, landmarks, scores)
        for i, (mesh_landmark, r_vec, t_vec) in enumerate(zip(mesh_landmarks_inverse, r_vecs, t_vecs)):
            mouth_ratio = get_mouth_ratio(mesh_landmark, image_show)
            left_box, right_box = get_eye_boxes(mesh_landmark, padded.shape)

            left_eye_img = padded[left_box[0][1]:left_box[1][1], left_box[0][0]:left_box[1][0]]
            right_eye_img = padded[right_box[0][1]:right_box[1][1], right_box[0][0]:right_box[1][0]]

            if np.any(left_eye_img) == False or np.any(right_eye_img) == False:
                break

            left_eye_landmarks, left_iris_landmarks = self.eye_mesher.inference(left_eye_img)
            right_eye_landmarks, right_iris_landmarks = self.eye_mesher.inference(right_eye_img)
            

            # Adds boxes around the eyes
            # cv2.rectangle(image_show, left_box[0], left_box[1], color=(255, 0, 0), thickness=2)
            # cv2.rectangle(image_show, right_box[0], right_box[1], color=(255, 0, 0), thickness=2)
            
            
            left_eye_ratio = get_eye_ratio(left_eye_landmarks, image_show, left_box[0])
            right_eye_ratio = get_eye_ratio(right_eye_landmarks, image_show, right_box[0])


            pitch, roll, yaw = get_face_angle(r_vec, t_vec)
            iris_ratio = get_iris_ratio(left_eye_landmarks, right_eye_landmarks)

            if mouth_ratio > 0.25:
                #cv2.putText(image_show, "Yawning: Detected", (padded_size[2] + 70, padded_size[0] + 70),
                #        fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1.0, color=(255, 0, 0), thickness=2)
                self.yawning_status = True
            else:
                #cv2.putText(image_show, "Yawning: No", (padded_size[2] + 70, padded_size[0] + 70),
                #        fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1.0, color=(0, 255, 0), thickness=2)
                self.yawning_status = False

            if left_eye_ratio < 0.3 and right_eye_ratio < 0.3:
                #cv2.putText(image_show, "Eye: Closed", (padded_size[2] + 70, padded_size[0] + 100),
                #        fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1.0, color=(255, 0, 0), thickness=2)
                self.eye_status = True
            else:
                #cv2.putText(image_show, "Eye: Open", (padded_size[2] + 70, padded_size[0] + 100),
                #        fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1.0, color=(0, 255, 0), thickness=2)
                self.eye_status = False

            if yaw > 15 and iris_ratio > 1.15:
                #cv2.putText(image_show, "Face: Left",(padded_size[2] + 70, padded_size[0] + 130),
                #    fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1, color=[255, 0, 0], thickness=2)
                self.attention_status = "Left"
            elif yaw < -15 and iris_ratio < 0.85:
                #cv2.putText(image_show, "Face: Right",(padded_size[2] + 70, padded_size[0] + 130),
                #    fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1, color=[255, 0, 0], thickness=2)
                self.attention_status = "Right"
            elif pitch > 30:
                #cv2.putText(image_show, "Face: UP",(padded_size[2] + 70, padded_size[0] + 130),
                #    fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1, color=[255, 0, 0], thickness=2)
                self.attention_status = "Up"
            elif pitch < -13:
                #cv2.putText(image_show, "Face: Down",(padded_size[2] + 70, padded_size[0] + 130),
                #    fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1, color=[255, 0, 0], thickness=2)
                self.attention_status = "Down"
            else:
                #cv2.putText(image_show, "Face: Forward",(padded_size[2] + 70, padded_size[0] + 130),
                #    fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1, color=[0, 255, 0], thickness=2)
                self.attention_status = "Forward"


        # remove pad
        image_show = image_show[padded_size[0]:target_dim - padded_size[1], padded_size[2]:target_dim - padded_size[3]]
        image_show = cv2.flip(image_show, 1)
        return image_show, self.attention_status, self.yawning_status, self.eye_status, self.inference_speed

