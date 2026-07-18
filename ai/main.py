import streamlit as st
from streamlit_webrtc import webrtc_streamer
import av
import cv2
import mediapipe as mp
import numpy as np
import math
import random
import time

# --- STREAMLIT UI SETUP ---
st.set_page_config(page_title="A Special Message", layout="wide")
st.title("💕 For Chavi ✨")
st.write("Please click 'Start' below and allow camera permissions to begin this special moment.")

# Base resolution for processing
WIDTH, HEIGHT = 1280, 720
SMOOTHING = 0.08

# BGR Colors
COLOR_GOLD = (180, 220, 255)
COLOR_PINK = (180, 105, 255)
COLOR_RED = (50, 50, 255)
COLOR_WHITE = (245, 245, 245)
COLOR_SOFT_BG = (20, 15, 20)

class WebLoveEngine:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=1, 
            min_detection_confidence=0.6, 
            min_tracking_confidence=0.6
        )
        self.hearts = []
        self.sparkles = []
        
        self.state = "INTRO_1"
        self.start_time = time.time()
        self.frame_count = 0
        
        self.heart_x = float(WIDTH // 2)
        self.heart_y = float(HEIGHT // 2 + 50)
        self.fist_was_closed = False
        self.fade_in = 0.0

    def get_centered_pos(self, text, font_scale, thickness):
        size, _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_TRIPLEX, font_scale, thickness)
        return max(20, (WIDTH - size[0]) // 2)

    def draw_text_cinematic(self, frame, text, y_pos, color, font_scale, thickness, alpha=1.0):
        x_pos = self.get_centered_pos(text, font_scale, thickness)
        if alpha >= 1.0:
            cv2.putText(frame, text, (x_pos + 3, y_pos + 3), cv2.FONT_HERSHEY_TRIPLEX, font_scale, (10, 10, 10), thickness + 2, cv2.LINE_AA)
            cv2.putText(frame, text, (x_pos, y_pos), cv2.FONT_HERSHEY_TRIPLEX, font_scale, color, thickness, cv2.LINE_AA)
        elif alpha > 0:
            overlay = frame.copy()
            cv2.putText(overlay, text, (x_pos + 3, y_pos + 3), cv2.FONT_HERSHEY_TRIPLEX, font_scale, (10, 10, 10), thickness + 2, cv2.LINE_AA)
            cv2.putText(overlay, text, (x_pos, y_pos), cv2.FONT_HERSHEY_TRIPLEX, font_scale, color, thickness, cv2.LINE_AA)
            cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

    def spawn_heart(self, x, y, scale=1.0, explosion=False):
        t_range = np.linspace(0, 2 * math.pi, 40)
        points = []
        for t in t_range:
            hx = 16 * math.sin(t)**3
            hy = 13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t)
            points.append((hx * scale, -hy * scale))
        
        self.hearts.append({
            "points": points, "x": x, "y": y,
            "vy": random.uniform(-6, 4) if explosion else random.uniform(2.0, 5.0),
            "vx": random.uniform(-6, 6) if explosion else random.uniform(-1.5, 1.5),
            "color": random.choice([COLOR_RED, COLOR_PINK, COLOR_GOLD]),
            "life": random.uniform(4.0, 8.0),
            "rotation": random.uniform(0, 360),
            "speed_rot": random.uniform(-3.0, 3.0)
        })

    def spawn_sparkles(self, x, y, count, mult=1.0):
        for _ in range(count):
            self.sparkles.append({
                "x": x, "y": y,
                "vx": random.uniform(-5, 5) * mult, "vy": random.uniform(-5, 5) * mult,
                "life": random.uniform(1.0, 3.0),
                "size": random.randint(2, 5),
                "color": random.choice([COLOR_GOLD, COLOR_WHITE, COLOR_PINK])
            })

    def is_open_palm(self, lm):
        return all(lm.landmark[t].y < lm.landmark[j].y for t, j in zip([8, 12, 16, 20], [6, 10, 14, 18]))

    def is_fist(self, lm):
        return all(lm.landmark[t].y > lm.landmark[j].y for t, j in zip([8, 12, 16, 20], [6, 10, 14, 18]))

    def apply_grade(self, frame):
        blurred = cv2.GaussianBlur(frame, (5, 5), 0)
        overlay = frame.copy()
        overlay[:, :] = [20, 15, 30]
        graded = cv2.addWeighted(blurred, 0.85, frame, 0.15, 0)
        return cv2.addWeighted(overlay, 0.12, graded, 0.88, 0)

    def process_frame(self, frame):
        self.frame_count += 1
        elapsed = time.time() - self.start_time
        
        # --- SCENE 1, 2, 3: POETRY OVERLAYS ---
        if self.state in ["INTRO_1", "INTRO_2", "INTRO_3"]:
            out_frame = np.full((HEIGHT, WIDTH, 3), COLOR_SOFT_BG, dtype=np.uint8)
            alpha = min(1.0, elapsed / 1.5) if elapsed < 3.5 else max(0.0, (5.0 - elapsed) / 1.5)
            
            if self.state == "INTRO_1":
                self.draw_text_cinematic(out_frame, "In a universe spinning through shadows and space...", HEIGHT//2 - 30, COLOR_WHITE, 1.1, 2, alpha)
                self.draw_text_cinematic(out_frame, "I was searching for meaning, a path, or a trace.", HEIGHT//2 + 40, COLOR_GOLD, 0.9, 2, alpha)
                if elapsed > 5.0:
                    self.state = "INTRO_2"
                    self.start_time = time.time()
                    
            elif self.state == "INTRO_2":
                self.draw_text_cinematic(out_frame, "Then the stars repositioned, the chaos grew still...", HEIGHT//2 - 30, COLOR_WHITE, 1.1, 2, alpha)
                self.draw_text_cinematic(out_frame, "And a warmth pulled me in with a beautiful thrill.", HEIGHT//2 + 40, COLOR_PINK, 0.9, 2, alpha)
                if elapsed > 5.0:
                    self.state = "INTRO_3"
                    self.start_time = time.time()
                    
            elif self.state == "INTRO_3":
                self.draw_text_cinematic(out_frame, "Every question found answer, the moment I knew...", HEIGHT//2 - 50, COLOR_WHITE, 1.1, 2, alpha)
                self.draw_text_cinematic(out_frame, "That my world had completely realigned around you.", HEIGHT//2, COLOR_WHITE, 1.1, 2, alpha)
                self.draw_text_cinematic(out_frame, "Chavi.", HEIGHT//2 + 80, COLOR_PINK, 2.0, 4, alpha)
                if self.frame_count % 6 == 0 and alpha > 0.3:
                    self.spawn_sparkles(WIDTH//2 + random.randint(-100, 100), HEIGHT//2 + 80, 2)
                if elapsed > 5.0:
                    self.state = "CAMERA_REVEAL"
                    self.start_time = time.time()
                    
            return out_frame

        # --- CAMERA DEPENDENT SCENES ---
        out_frame = self.apply_grade(frame)
        rgb = cv2.cvtColor(out_frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb)
        
        # --- SCENE 4: CAMERA UNLOCK ---
        if self.state == "CAMERA_REVEAL":
            if self.fade_in < 1.0:
                self.fade_in += 0.015
                out_frame = cv2.addWeighted(out_frame, self.fade_in, np.full_like(out_frame, 10), 1 - self.fade_in, 0)
                
            if results.multi_hand_landmarks:
                for hl in results.multi_hand_landmarks:
                    if self.is_open_palm(hl) and elapsed > 4.0:
                        hx = int(hl.landmark[9].x * WIDTH)
                        hy = int(hl.landmark[9].y * HEIGHT)
                        self.spawn_sparkles(hx, hy, 100, 2.5)
                        self.state = "THE_PROPOSAL"
                        self.start_time = time.time()
            
            if self.frame_count % 12 == 0: 
                self.spawn_heart(random.randint(50, WIDTH-50), -20, 0.6)
            if elapsed < 4.0:
                self.draw_text_cinematic(out_frame, "Look closely at the screen...", HEIGHT - 100, COLOR_WHITE, 1.2, 2)
            else:
                p_alpha = 0.5 + 0.5 * math.sin(time.time() * 3)
                self.draw_text_cinematic(out_frame, "Raise your hand open to the screen to unlock my heart...", HEIGHT - 100, COLOR_PINK, 1.0, 2, p_alpha)

        # --- SCENE 5: THE PROPOSAL ---
        elif self.state == "THE_PROPOSAL":
            tx, ty = WIDTH // 2, HEIGHT // 2 + 50
            if results.multi_hand_landmarks:
                for hl in results.multi_hand_landmarks:
                    tx, ty = hl.landmark[9].x * WIDTH, hl.landmark[9].y * HEIGHT
                    if elapsed > 3.0 and self.is_fist(hl):
                        for _ in range(40): 
                            self.spawn_heart(int(tx), int(ty), random.uniform(0.5, 1.2), True)
                        self.spawn_sparkles(int(tx), int(ty), 150, 3.5)
                        self.state = "SHE_SAID_YES"
                        self.start_time = time.time()
                        
            self.heart_x += (tx - self.heart_x) * SMOOTHING
            self.heart_y += (ty - self.heart_y) * SMOOTHING
            
            p_scale = 55 + math.sin(time.time() * 4) * 8
            pts = []
            for t in np.linspace(0, 2 * math.pi, 60):
                hx = 16 * math.sin(t)**3
                hy = 13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t)
                pts.append((int(self.heart_x + hx * p_scale), int(self.heart_y - hy * p_scale)))
            if len(pts) > 2:
                cv2.fillPoly(out_frame, [np.array(pts, dtype=np.int32)], COLOR_RED, cv2.LINE_AA)
                cv2.polylines(out_frame, [np.array(pts, dtype=np.int32)], True, COLOR_WHITE, 2, cv2.LINE_AA)

            if self.frame_count % 5 == 0: 
                self.spawn_heart(random.randint(20, WIDTH-20), -20, random.uniform(0.5, 1.0))
            self.draw_text_cinematic(out_frame, "CHAVI", HEIGHT//2 - 160, COLOR_PINK, 2.2, 4)
            self.draw_text_cinematic(out_frame, "Will You Be Mine?", HEIGHT//2 - 80, COLOR_WHITE, 2.5, 5)
            if elapsed > 2.5:
                p_alpha = 0.5 + 0.5 * math.sin(time.time() * 3)
                self.draw_text_cinematic(out_frame, "Close your hand into a fist to say YES", HEIGHT - 80, COLOR_GOLD, 0.9, 2, p_alpha)

        # --- SCENE 6: GRAND FINALE ---
        elif self.state == "SHE_SAID_YES":
            flash = max(0.0, 1.0 - (elapsed / 1.5))
            if flash > 0:
                out_frame = cv2.addWeighted(np.full_like(out_frame, 255), flash, out_frame, 1 - flash, 0)
                
            if results.multi_hand_landmarks:
                for hl in results.multi_hand_landmarks:
                    hx, hy = int(hl.landmark[9].x * WIDTH), int(hl.landmark[9].y * HEIGHT)
                    if self.is_fist(hl):
                        if not self.fist_was_closed:
                            for _ in range(35): 
                                self.spawn_heart(hx, hy, scale=random.uniform(0.5, 1.5), explosion=True)
                            self.spawn_sparkles(hx, hy, 60, 2.5)
                            self.fist_was_closed = True
                    else:
                        self.fist_was_closed = False
                        
            if self.frame_count % 3 == 0: 
                self.spawn_heart(random.randint(0, WIDTH), HEIGHT + 20, random.uniform(0.6, 1.5), True)
            self.draw_text_cinematic(out_frame, "SHE SAID YES!", HEIGHT//2 - 40, COLOR_WHITE, 3.0, 6)
            self.draw_text_cinematic(out_frame, "My Forever Chapter Begins Now.", HEIGHT//2 + 50, COLOR_PINK, 1.3, 3)

        # --- PARTICLE RENDER ENGINE ---
        for h in self.hearts[:]:
            h["life"] -= 0.02
            h["y"] += h["vy"]
            h["x"] += h["vx"]
            h["rotation"] += h["speed_rot"]
            if h["life"] <= 0 or h["y"] > HEIGHT + 100 or h["x"] < -50 or h["x"] > WIDTH + 50:
                self.hearts.remove(h)
                continue
            r_pts = []
            rad = math.radians(h["rotation"])
            c_r, s_r = math.cos(rad), math.sin(rad)
            for px, py in h["points"]:
                r_pts.append((int(h["x"] + (px*c_r - py*s_r)), int(h["y"] + (px*s_r + py*c_r))))
            if len(r_pts) > 2:
                cv2.fillPoly(out_frame, [np.array(r_pts, dtype=np.int32)], h["color"], cv2.LINE_AA)

        for p in self.sparkles[:]:
            p["life"] -= 0.04
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            if p["life"] <= 0:
                self.sparkles.remove(p)
                continue
            if 0 < p["x"] < WIDTH and 0 < p["y"] < HEIGHT:
                cv2.circle(out_frame, (int(p["x"]), int(p["y"])), p["size"], p["color"], -1, cv2.LINE_AA)

        return out_frame

# Persistent session state
if "engine" not in st.session_state:
    st.session_state.engine = WebLoveEngine()

def video_frame_callback(frame):
    img = frame.to_ndarray(format="bgr24")
    img_flipped = cv2.flip(img, 1)
    img_resized = cv2.resize(img_flipped, (WIDTH, HEIGHT))
    
    processed_img = st.session_state.engine.process_frame(img_resized)
    
    return av.VideoFrame.from_ndarray(processed_img, format="bgr24")

# WebRTC Streamer
webrtc_streamer(
    key="cinematic-proposal",
    video_frame_callback=video_frame_callback,
    media_stream_constraints={"video": True, "audio": False},
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    desired_playing_state=True
)