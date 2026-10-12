import os
import random
import math
from PyQt6.QtCore import Qt, QTimer, QRect, QPoint
from PyQt6.QtGui import QPixmap, QPainter, QTransform, QCursor, QImage, QColor
from PyQt6.QtWidgets import QWidget, QApplication

from utils import resource_path
from actions.run.run_action import RunAction
from actions.sleep.sleep_action import SleepAction
from actions.sit.sit_action import SitAction
from actions.eat.eat_action import EatAction
from actions.idle.idle_action import IdleAction
from actions.jump.jump_action import JumpAction
from actions.meow.meow_action import MeowAction

# 📍 벽 타기 전용 모듈 연결 (파일이 없을 경우 자동 예외 처리)
try:
    from actions.climb.climb_action import ClimbAction
except ImportError:
    ClimbAction = None


class CatWidget(QWidget):
    def __init__(self, name, start_x, start_y, furnitures=None, speed_factor=1.0, head_darkness=1.0):
        super().__init__()
        self.name = name
        self.furnitures = furnitures if furnitures else {}
        self.speed_factor = speed_factor        # 장난감 놀이 전용 속도 계수
        self.head_darkness = head_darkness      # 머리 어둡기 계수 (1.0: 원본, 0.6: 어두운 머리)

        # --- 1. 창 설정 ---
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMouseTracking(True)

        # --- 2. 행동 모듈 연결 ---
        self.actions = {
            "RUN": RunAction(),
            "SLEEP": SleepAction(),
            "SIT": SitAction(),
            "EAT": EatAction(),
            "IDLE": IdleAction(),
            "JUMP": JumpAction(),
            "MEOW": MeowAction()
        }

        # 벽 타기 모듈이 등록되어 있다면 추가
        if ClimbAction is not None:
            self.actions["CLIMB"] = ClimbAction()

        self.frame_counts = {
            "RUN": 6,
            "SLEEP": 4,
            "SIT": 7,
            "EAT": 7,
            "IDLE": 13,
            "JUMP": 15,
            "MEOW": 7,
            "CLIMB": 6  # 벽 타기 모션 프레임 수
        }

        self.single_frame_w = 48
        self.scale = 2.5
        self.widget_w = 160
        self.widget_h = 160
        self.resize(self.widget_w, self.widget_h)

        # 이미지 캐싱 (head_darkness 적용)
        self.pixmaps = {}
        for state, action in self.actions.items():
            pix = QPixmap(action.image_path)
            if not pix.isNull():
                if self.head_darkness < 1.0:
                    pix = self.apply_head_darkening(pix, self.head_darkness)
                self.pixmaps[state] = pix

        # --- 3. 화면 및 위치 자동 계산 ---
        screen = QApplication.primaryScreen().availableGeometry()
        self.screen_w = screen.width()
        self.screen_h = screen.height()

        # 작업표시줄 제외 바닥 높이
        self.ground_y = float(self.screen_h - self.widget_h)

        self.start_x = float(start_x)
        self.start_y = min(float(start_y), self.ground_y)

        self.x_pos = self.start_x
        self.y_pos = self.ground_y

        self.state = "IDLE"
        self.current_frame = 0
        self.direction = random.choice([1, -1])
        self.speed = 0.0

        # [벽 타기 관련 변수]
        self.climb_wall = "LEFT"         # "LEFT" 또는 "RIGHT"
        self.climb_dir = -1              # -1: 위로 올라감, 1: 아래로 내려옴
        self.is_jumping_to_wall = False  # 벽으로 점프 도약 중인지 여부

        # [점프 사냥 변수]
        self.is_hunting = False
        self.hunt_cooldown = 0
        self.shake_gauge = 0.0
        self.jump_count = 0

        self.jump_start_x = 0.0
        self.jump_start_y = 0.0
        self.jump_target_x = 0.0
        self.jump_target_y = 0.0
        self.jump_height = 120.0
        self.jump_progress = 0.0

        self.last_cursor_pos = QCursor.pos()
        self.idle_ticks = 0
        self.meow_ticks = 0
        self.sleep_ticks = 0

        # 밥 먹기 관련 변수
        self.is_going_to_eat = False
        self.eat_side = -1

        if "FOOD" in self.furnitures and hasattr(self.furnitures["FOOD"], "register_cat"):
            self.furnitures["FOOD"].register_cat(self)

        self.move(int(self.x_pos), int(self.y_pos))

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_behavior)
        self.timer.start(80)

        self.show()

    def apply_head_darkening(self, pixmap, factor, head_on_right=True):
        """ 고양이 이마/귀 주변의 매우 작고 구체적인 영역만 어둡게 처리하는 메서드 """
        img = pixmap.toImage().convertToFormat(QImage.Format.Format_ARGB32)
        w, h = img.width(), img.height()
        frame_w = self.single_frame_w  # 48px

        # 세로(Y축) 범위를 상단 40% 영역(정수리/귀/이마)으로만 제한
        head_top_y = int(h * 0.40)

        for y in range(h):
            for x in range(w):
                color = img.pixelColor(x, y)
                if color.alpha() > 0:
                    x_in_frame = x % frame_w  # 0 ~ 47px

                    is_x_head = (x_in_frame >= 38) if head_on_right else (x_in_frame <= 15)
                    is_y_top = (y <= head_top_y)

                    if is_x_head and is_y_top:
                        new_r = int(color.red() * factor)
                        new_g = int(color.green() * factor)
                        new_b = int(color.blue() * factor)
                        img.setPixelColor(x, y, QColor(new_r, new_g, new_b, color.alpha()))

        return QPixmap.fromImage(img)

    def go_to_eat(self, side=-1):
        """ 1순위로 다른 모든 상태를 강제 해제하고 밥그릇으로 이동 """
        self.eat_side = side
        self.is_going_to_eat = True
        self.is_hunting = False
        self.is_jumping_to_wall = False
        self.shake_gauge = 0.0
        self.state = "RUN"
        self.speed = random.uniform(5.5, 7.5)

    def get_valid_pixmap(self, state):
        pix = self.pixmaps.get(state)
        if pix and not pix.isNull():
            return pix
        # CLIMB 전용 이미지가 없는 경우 RUN 모션으로 안전하게 대체
        if state == "CLIMB":
            pix = self.pixmaps.get("RUN")
            if pix and not pix.isNull():
                return pix
        pix = self.pixmaps.get("IDLE")
        if pix and not pix.isNull():
            return pix
        return self.pixmaps.get("RUN")

    def is_in_room(self):
        return self.x_pos >= (self.screen_w - 320)

    def trigger_meow(self):
        """ 클릭 또는 자율 판단으로 야옹 모션과 음성을 동시 실행 """
        self.state = "MEOW"
        self.speed = 0.0
        self.meow_ticks = 0
        self.current_frame = 0
        self.is_hunting = False
        self.is_jumping_to_wall = False
        self.is_going_to_eat = False
        self.update()

        if "MEOW" in self.actions and hasattr(self.actions["MEOW"], "play_sound"):
            QTimer.singleShot(0, self.actions["MEOW"].play_sound)

    def start_wall_jump(self, wall_side):
        """ 배경화면 좌/우 경계 벽을 향해 도약하는 점프 시작 """
        self.is_jumping_to_wall = True
        self.state = "JUMP"
        self.climb_wall = wall_side
        self.jump_start_x = self.x_pos
        self.jump_start_y = self.y_pos

        if wall_side == "LEFT":
            self.jump_target_x = 0.0
        else:
            self.jump_target_x = float(self.screen_w - self.widget_w)

        self.jump_target_y = max(100.0, self.ground_y - 180.0)
        self.jump_height = 140.0
        self.jump_progress = 0.0

    def update_behavior(self):
        current_pixmap = self.get_valid_pixmap(self.state)

        if current_pixmap and not current_pixmap.isNull():
            total_frames = self.frame_counts.get(self.state, max(1, current_pixmap.width() // self.single_frame_w))

            if self.state == "SLEEP":
                self.sleep_ticks += 1
                frame_delay = 4
                self.current_frame = (self.sleep_ticks // frame_delay) % total_frames
            elif self.state != "MEOW":
                self.sleep_ticks = 0
                self.current_frame = (self.current_frame + 1) % total_frames

        cursor_pos = QCursor.pos()
        cat_center_x = self.x_pos + self.widget_w / 2
        cat_center_y = self.y_pos + self.widget_h / 2

        dx = cursor_pos.x() - cat_center_x
        dy = cursor_pos.y() - cat_center_y
        distance = math.hypot(dx, dy)

        is_toy_active = "TOY" in self.furnitures and getattr(self.furnitures["TOY"], "is_active", False)

        if self.hunt_cooldown > 0:
            self.hunt_cooldown -= 1

        # -------------------------------------------------------------
        # 🔥 0-A) [장난감 버튼 클릭 시] 초고속 추격 및 점프 (벽타기 즉시 취소)
        # -------------------------------------------------------------
        if is_toy_active:
            self.is_going_to_eat = False
            self.is_jumping_to_wall = False
            self.sleep_ticks = 0
            self.idle_ticks = 0

            if self.is_hunting:
                self.state = "JUMP"
                self.jump_progress += 0.08 * min(1.2, max(0.7, self.speed_factor))

                self.x_pos = self.jump_start_x + (self.jump_target_x - self.jump_start_x) * self.jump_progress
                t = self.jump_progress
                parabola = 4 * t * (1 - t)

                linear_y = self.jump_start_y + (self.jump_target_y - self.jump_start_y) * t
                self.y_pos = linear_y - (self.jump_height * parabola)

                self.direction = 1 if (self.jump_target_x - self.jump_start_x) > 0 else -1

                if self.jump_progress >= 1.0:
                    self.jump_progress = 1.0
                    self.y_pos = self.ground_y
                    self.is_hunting = False

            else:
                target_x = max(0.0, min(cursor_pos.x() - self.widget_w / 2, float(self.screen_w - self.widget_w)))
                self.y_pos = self.ground_y

                self.direction = 1 if target_x > self.x_pos else -1
                fast_run_speed = random.uniform(12.0, 15.0) * self.speed_factor

                if abs(self.x_pos - target_x) < 140 and abs(self.y_pos - (cursor_pos.y() - self.widget_h / 2)) < 300:
                    self.is_hunting = True
                    self.state = "JUMP"
                    self.jump_start_x = self.x_pos
                    self.jump_start_y = self.y_pos

                    self.jump_target_x = target_x
                    self.jump_target_y = self.ground_y

                    cursor_y_target = cursor_pos.y() - self.widget_h / 2
                    self.jump_height = max(130.0, self.jump_start_y - cursor_y_target + 40.0)
                    self.jump_progress = 0.0
                else:
                    self.state = "RUN"
                    self.x_pos += fast_run_speed * self.direction

        # -------------------------------------------------------------
        # 🔥 0-B) 밥 먹으러 가기
        # -------------------------------------------------------------
        elif self.is_going_to_eat:
            self.state = "RUN"
            self.is_hunting = False
            self.is_jumping_to_wall = False
            self.shake_gauge = 0.0

            if "FOOD" in self.furnitures:
                food = self.furnitures["FOOD"]
                food_x = food.x_pos
                food_w = food.width()

                if self.eat_side == -1:
                    target_x = food_x - 110
                    desired_direction = 1
                else:
                    target_x = food_x + food_w - 30
                    desired_direction = -1

                if abs(self.x_pos - target_x) <= self.speed + 5:
                    self.x_pos = target_x
                    self.direction = desired_direction
                    self.state = "EAT"
                    self.current_frame = 0
                    self.speed = 0.0
                    self.is_going_to_eat = False

                    if "EAT" in self.actions and hasattr(self.actions["EAT"], "play_sound"):
                        self.actions["EAT"].play_sound()
                else:
                    self.direction = 1 if target_x > self.x_pos else -1
                    self.x_pos += self.speed * self.direction

        # -------------------------------------------------------------
        # 🧱 1) 벽을 향해 점프 중
        # -------------------------------------------------------------
        elif self.is_jumping_to_wall:
            self.state = "JUMP"
            self.jump_progress += 0.08

            self.x_pos = self.jump_start_x + (self.jump_target_x - self.jump_start_x) * self.jump_progress
            t = self.jump_progress
            parabola = 4 * t * (1 - t)

            linear_y = self.jump_start_y + (self.jump_target_y - self.jump_start_y) * t
            self.y_pos = linear_y - (self.jump_height * parabola)

            self.direction = 1 if (self.jump_target_x - self.jump_start_x) > 0 else -1

            if self.jump_progress >= 1.0:
                self.is_jumping_to_wall = False
                self.state = "CLIMB"
                self.climb_dir = -1  # 위로 등반
                self.speed = random.uniform(3.0, 4.5)
                self.current_frame = 0

        # -------------------------------------------------------------
        # 🧱 2) 벽 타기 진행
        # -------------------------------------------------------------
        elif self.state == "CLIMB":
            self.y_pos += self.speed * self.climb_dir

            if self.climb_wall == "LEFT":
                self.x_pos = 0.0
            else:
                self.x_pos = float(self.screen_w - self.widget_w)

            if self.y_pos <= 0:
                self.y_pos = 0.0
                self.climb_dir = 1

            elif self.y_pos >= self.ground_y:
                self.y_pos = self.ground_y
                self.state = "RUN"
                self.speed = random.uniform(3.0, 5.0)
                self.direction = 1 if self.climb_wall == "LEFT" else -1

            elif random.random() < 0.005:
                self.state = "RUN"
                self.y_pos = self.ground_y
                self.speed = random.uniform(3.0, 5.0)
                self.direction = 1 if self.climb_wall == "LEFT" else -1

        # -------------------------------------------------------------
        # 3) 일반 마우스 점프 진행 중 처리
        # -------------------------------------------------------------
        elif self.is_hunting:
            self.state = "JUMP"
            self.jump_progress += 0.07

            self.x_pos = self.jump_start_x + (self.jump_target_x - self.jump_start_x) * self.jump_progress
            t = self.jump_progress
            parabola = 4 * t * (1 - t)

            linear_y = self.jump_start_y + (self.jump_target_y - self.jump_start_y) * t
            self.y_pos = linear_y - (self.jump_height * parabola)

            target_cursor_x = int(self.x_pos + self.widget_w / 2)
            target_cursor_y = int(self.y_pos + self.widget_h)
            QCursor.setPos(target_cursor_x, target_cursor_y)

            self.direction = 1 if (self.jump_target_x - self.jump_start_x) > 0 else -1

            if self.jump_progress >= 1.0:
                self.jump_progress = 1.0
                self.y_pos = self.jump_target_y
                self.is_hunting = False
                self.shake_gauge = 0.0
                self.last_cursor_pos = QCursor.pos()

                self.jump_count += 1
                if self.jump_count >= 3:
                    self.hunt_cooldown = 750
                    self.jump_count = 0
                else:
                    self.hunt_cooldown = 100

                r = random.random()
                if r < 0.2:
                    self.state = "SIT"
                    self.speed = 0.0
                elif r < 0.6:
                    self.state = "IDLE"
                    self.speed = 0.0
                else:
                    self.state = "RUN"
                    self.speed = random.uniform(3.0, 5.0)
                    self.direction = random.choice([1, -1])

        # -------------------------------------------------------------
        # 4) 야옹 모션
        # -------------------------------------------------------------
        elif self.state == "MEOW":
            self.meow_ticks += 1
            frame_delay = 2
            total_frames = self.frame_counts.get("MEOW", 7)

            self.current_frame = self.meow_ticks // frame_delay

            if self.current_frame >= total_frames:
                self.state = "IDLE"
                self.current_frame = 0
                self.meow_ticks = 0

            self.last_cursor_pos = cursor_pos

        # -------------------------------------------------------------
        # 5) 평상시 마우스 흔들기 감지
        # -------------------------------------------------------------
        elif self.hunt_cooldown == 0 and distance < 180 and self.state != "SLEEP":
            self.idle_ticks = 0
            self.direction = 1 if dx > 0 else -1

            move_dist = math.hypot(cursor_pos.x() - self.last_cursor_pos.x(), cursor_pos.y() - self.last_cursor_pos.y())
            self.last_cursor_pos = cursor_pos

            if move_dist > 5:
                self.shake_gauge += move_dist * 0.15
            else:
                self.shake_gauge = max(0.0, self.shake_gauge - 3.5)

            if self.shake_gauge >= 250.0:
                self.is_hunting = True
                self.shake_gauge = 0.0
                self.jump_start_x = self.x_pos
                self.jump_start_y = self.y_pos

                self.jump_target_x = max(0.0, min(cursor_pos.x() - self.widget_w / 2, float(self.screen_w - self.widget_w)))
                if self.is_in_room():
                    self.jump_target_y = self.start_y
                else:
                    self.jump_target_y = self.ground_y

                cursor_y_target = cursor_pos.y() - self.widget_h / 2
                self.jump_height = max(120.0, self.jump_start_y - cursor_y_target + 40.0)
                self.jump_progress = 0.0

        # -------------------------------------------------------------
        # 6) 평상시 기본 자율 AI (💡 혼자서 야옹할 확률 상향 조정)
        # -------------------------------------------------------------
        else:
            self.shake_gauge = max(0.0, self.shake_gauge - 3.0)
            self.is_hunting = False
            self.last_cursor_pos = cursor_pos

            if self.state == "RUN":
                self.idle_ticks = 0
                self.y_pos = self.ground_y

                if self.speed <= 0.5:
                    self.speed = random.uniform(3.0, 5.0)
                if self.direction == 0:
                    self.direction = random.choice([1, -1])

                self.x_pos += self.speed * self.direction

                # 💡 산책 중 가끔 멈춰서 야옹할 확률 추가
                if random.random() < 0.008:
                    self.trigger_meow()

                elif random.random() < 0.01:
                    self.direction *= -1
                    self.speed = random.uniform(2.5, 5.0)

                # 오른쪽 벽 근처 (180px) 도달 시 확률적 벽 점프
                if self.x_pos >= self.screen_w - self.widget_w - 180 and self.direction == 1:
                    if random.random() < 0.07:
                        self.start_wall_jump("RIGHT")

                # 왼쪽 벽 근처 (180px) 도달 시 확률적 벽 점프
                elif self.x_pos <= 180 and self.direction == -1:
                    if random.random() < 0.07:
                        self.start_wall_jump("LEFT")

                if self.x_pos >= self.screen_w - self.widget_w:
                    self.x_pos = float(self.screen_w - self.widget_w)
                    self.direction = -1
                elif self.x_pos <= 0:
                    self.x_pos = 0.0
                    self.direction = 1

                if self.is_in_room() and random.random() < 0.0099:
                    self.state = "SLEEP"
                    self.speed = 0.0
                    self.y_pos = self.start_y
                elif random.random() < 0.0058:
                    self.state = "IDLE"
                    self.speed = 0.0

            elif self.state == "EAT":
                if random.random() < 0.012:
                    self.state = "IDLE"

            elif self.state == "SIT":
                # 💡 앉아 있을 때 울 확률 추가
                if random.random() < 0.015:
                    self.trigger_meow()

                elif random.random() < 0.06:
                    r = random.random()
                    if r < 0.5:
                        self.state = "RUN"
                        self.speed = random.uniform(3.0, 5.0)
                        self.direction = random.choice([1, -1])
                    elif r < 0.8:
                        self.state = "IDLE"
                    else:
                        if self.is_in_room():
                            self.state = "SLEEP"
                            self.speed = 0.0
                            self.y_pos = self.start_y
                        else:
                            self.state = "IDLE"

            elif self.state == "IDLE":
                self.idle_ticks += 1

                # 💡 가만히 서 있을 때 가끔 야옹하기 (매 tick 약 2.5% 확률)
                if random.random() < 0.025:
                    self.trigger_meow()

                elif self.idle_ticks >= 80:
                    self.idle_ticks = 0
                    r = random.random()
                    if r < 0.35:  # 정지 후 야옹할 확률 추가
                        self.trigger_meow()
                    elif r < 0.5:
                        self.state = "SLEEP"
                        self.speed = 0.0
                    elif r < 0.7:
                        self.state = "SIT"
                        self.speed = 0.0
                    else:
                        self.state = "RUN"
                        self.speed = random.uniform(3.0, 5.0)
                        self.direction = random.choice([1, -1])

                elif random.random() < 0.01:
                    if random.random() < 0.75:
                        self.state = "RUN"
                        self.speed = random.uniform(3.0, 5.0)
                        self.direction = random.choice([1, -1])
                        self.idle_ticks = 0
                    else:
                        self.state = "SIT"

            elif self.state == "SLEEP":
                self.idle_ticks = 0
                if random.random() < 0.002:
                    self.state = "IDLE"

        # Y 좌표 유효성 제한
        self.x_pos = max(0.0, min(self.x_pos, float(self.screen_w - self.widget_w)))

        if not self.is_hunting and not self.is_jumping_to_wall and self.state not in ["JUMP", "CLIMB"]:
            if self.is_in_room() and self.state == "SLEEP":
                self.y_pos = self.start_y
            else:
                self.y_pos = self.ground_y
        else:
            self.y_pos = min(self.y_pos, self.ground_y)

        self.move(int(self.x_pos), int(self.y_pos))
        self.update()

    def wake_up_or_turn(self):
        self.idle_ticks = 0
        if self.state in ["IDLE", "SIT", "SLEEP", "EAT"]:
            if random.random() < 0.4:  # 깨어날 때 야옹할 확률 증가
                self.trigger_meow()
            else:
                self.state = "RUN"
                self.speed = random.randint(4, 7)
                if not self.is_in_room():
                    self.y_pos = self.ground_y
        else:
            self.direction *= -1

    def enterEvent(self, event):
        super().enterEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.raise_()
            self.trigger_meow()
            super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.GlobalColor.transparent)

        current_pixmap = self.get_valid_pixmap(self.state)

        if current_pixmap is None or current_pixmap.isNull():
            return

        frame_h = current_pixmap.height()

        crop_x = self.current_frame * self.single_frame_w
        if crop_x + self.single_frame_w > current_pixmap.width():
            crop_x = 0

        crop_rect = QRect(crop_x, 0, self.single_frame_w, frame_h)
        cropped = current_pixmap.copy(crop_rect)

        # -------------------------------------------------------------
        # 🧱 [좌/우 벽타기 변환식]
        # -------------------------------------------------------------
        if self.state == "CLIMB":
            transform = QTransform()
            if self.climb_wall == "LEFT":
                if self.climb_dir == -1:  # 오를 때
                    transform.scale(-1, 1).rotate(-90)
                else:                     # 내려올 때
                    transform.scale(-1, -1).rotate(-90)
            else:  # RIGHT wall
                if self.climb_dir == -1:  # 오를 때
                    transform.rotate(-90)
                else:                     # 내려올 때
                    transform.scale(1, -1).rotate(-90)

            cropped = cropped.transformed(transform)

        # 평상시 수평 방향 반전
        elif self.direction == -1:
            transform = QTransform().scale(-1, 1)
            cropped = cropped.transformed(transform)

        scaled_w = int(self.single_frame_w * self.scale)
        scaled_h = int(frame_h * self.scale)

        scaled = cropped.scaled(
            scaled_w, scaled_h,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation
        )

        draw_x = 10
        draw_y = self.height() - scaled_h

        painter.drawPixmap(draw_x, draw_y, scaled)