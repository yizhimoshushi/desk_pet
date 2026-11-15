import sys
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QMenu,
                             QAction, QSystemTrayIcon, QGraphicsDropShadowEffect,
                             QSlider, QHBoxLayout, QVBoxLayout, QPushButton)
from PyQt5.QtGui import QPixmap, QMovie, QIcon, QCursor
from PyQt5.QtCore import Qt, QTimer, QPoint, QSize

from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl

from PyQt5.QtCore import QElapsedTimer

class SizeSliderPopup(QWidget):
    """横向滑块弹窗：拖动球实时调整桌宠大小"""

    MIN_SIZE = 32
    MAX_SIZE = 1024

    def __init__(self, pet):
        super().__init__()
        self.pet = pet

        # 无边框 + 置顶 + 半透明背景
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 外层卡片（白底圆角）
        self.card = QWidget(self)
        self.card.setObjectName("card")
        self.card.setStyleSheet("""
            QWidget#card {
                background-color: rgba(255, 255, 255, 235);
                border-radius: 14px;
                border: 1px solid rgba(0, 0, 0, 40);
            }
        """)

        # 布局：标题 + 滑块 + 数值 + 关闭按钮
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self.card)

        lay = QVBoxLayout(self.card)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(8)

        self.title = QLabel(f"📏 调整大小：{pet.pet_size} px")
        self.title.setStyleSheet("font-size: 13px; color: #333;")
        lay.addWidget(self.title)

        row = QHBoxLayout()
        row.setSpacing(8)

        # 小图标
        lbl_small = QLabel("🐭")
        lbl_big = QLabel("🐘")
        lbl_small.setStyleSheet("font-size: 16px;")
        lbl_big.setStyleSheet("font-size: 20px;")

        # === 核心：QSlider ===
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(self.MIN_SIZE)
        self.slider.setMaximum(self.MAX_SIZE)
        self.slider.setValue(pet.pet_size)
        self.slider.setFixedWidth(260)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 6px;
                background: #d0d0d0;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #4a9eff;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                width: 20px;
                height: 20px;
                margin: -8px 0;
                border-radius: 10px;
                background: qradialgradient(
                    cx:0.4, cy:0.4, radius:0.8,
                    fx:0.4, fy:0.4,
                    stop:0 #ffffff,
                    stop:0.6 #4a9eff,
                    stop:1 #2f7be0
                );
                border: 2px solid #2f7be0;
            }
            QSlider::handle:horizontal:hover {
                background: qradialgradient(
                    cx:0.4, cy:0.4, radius:0.8,
                    fx:0.4, fy:0.4,
                    stop:0 #ffffff,
                    stop:0.6 #6db3ff,
                    stop:1 #4a9eff
                );
            }
        """)
        self.slider.valueChanged.connect(self._on_value_changed)

        # 鼠标滚轮也能微调
        self.slider.wheelEvent = self._slider_wheel

        row.addWidget(lbl_small)
        row.addWidget(self.slider)
        row.addWidget(lbl_big)
        lay.addLayout(row)

        # 关闭按钮
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_close = QPushButton("关闭")
        btn_close.setFixedWidth(60)
        btn_close.setStyleSheet("""
            QPushButton {
                background: #f0f0f0; border-radius: 6px;
                padding: 4px 8px; color: #444;
            }
            QPushButton:hover { background: #e0e0e0; }
        """)
        btn_close.clicked.connect(self.close)
        btn_row.addWidget(btn_close)
        lay.addLayout(btn_row)

        self.adjustSize()

    # 拖动球 → 实时改大小
    def _on_value_changed(self, value):
        # 吸附到 16 的倍数，视觉更整
        snapped = int(round(value / 16.0)) * 16
        snapped = max(self.MIN_SIZE, min(self.MAX_SIZE, snapped))
        self.title.setText(f"📏 调整大小：{snapped} px")
        self.pet.resize_pet(snapped)

    # 滚轮微调 ±16
    def _slider_wheel(self, event):
        step = 16 if event.angleDelta().y() > 0 else -16
        new_val = max(self.MIN_SIZE, min(self.MAX_SIZE, self.slider.value() + step))
        self.slider.setValue(new_val)
        event.accept()

    # 在桌宠旁边弹出
    def show_near(self, pet):
        # 先显示再定位，拿到实际尺寸
        self.adjustSize()
        gx = pet.geometry()
        screen = QApplication.primaryScreen().availableGeometry()

        # 默认在桌宠左上方
        x = gx.center().x() - self.width() // 2
        y = gx.top() - self.height() - 10

        # 防出屏
        if y < screen.top() + 10:
            y = gx.bottom() + 10
        if x < screen.left() + 10:
            x = screen.left() + 10
        if x + self.width() > screen.right() - 10:
            x = screen.right() - self.width() - 10

        self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()


class DesktopPet(QWidget):
    def __init__(self):
        super().__init__()

        # === 基础配置 ===
        self.pet_size = 128
        self.current_state = "idle"

        # === 窗口属性设置 ===
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(self.pet_size, self.pet_size)

        # === 动画标签 ===
        self.label = QLabel(self)
        self.label.setGeometry(0, 0, self.pet_size, self.pet_size)
        self.label.setAlignment(Qt.AlignCenter)

        # === 拖拽相关变量 ===
        self._is_dragging = False
        self._drag_pos = QPoint()

        # === 单击判定定时器 ===
        self._click_timer = QTimer(self)
        self._click_timer.setSingleShot(True)
        self._click_timer.timeout.connect(self._on_single_click)
        self._pending_click_pos = QPoint()

        # === 音频播放器 ===
        self.player = QMediaPlayer(self)
        self.audio_shout = os.path.abspath("assets/dagou.mp3")
        self.audio_jiao = os.path.abspath("assets/jiao.mp3")

        if os.path.exists(self.audio_shout):
            self.player.setMedia(QMediaContent(QUrl.fromLocalFile(self.audio_shout)))
        else:
            print(f"[警告] 未找到音频文件: {self.audio_shout}")

        self.PLAYBACK_RATE = 1.0

        self.player.mediaStatusChanged.connect(self._on_media_status_changed)
        self.player.durationChanged.connect(self._on_duration_changed)

        # 🆕 动态时长追踪：替代固定 base_duration
        self._current_shout_duration = 0       # 当前 shout 实际时长(ms)
        self._shout_fallback_duration = 2000   # 兜底时长(ms)，当 duration() 返回 0 时使用
        self.player.durationChanged.connect(self._on_duration_changed)

        # === 连击判定定时器 ===
        self._combo_timer = QTimer(self)
        self._combo_timer.setSingleShot(True)
        self._combo_timer.timeout.connect(self._on_combo_timeout)
        self._in_combo = False
        self._combo_num = 0
        self._is_playing_jiao = False

        self.add_rate = 0.05

        # === 长按/单击判定变量 ===
        self._press_time = 0  # 鼠标按下的时间戳(ms)
        self.LONG_PRESS_THRESHOLD = 300  # 长按阈值(ms)，超过此值不算单击

        self._press_timer = QElapsedTimer()

        # === 点击缓存机制（Buffer）===
        self._click_buffer = 0
        self._is_action_playing = False
        self.MAX_BUFFER_SIZE = 1

        # === 加载初始动画 ===
        self.load_animation("idle")

        # === 随机行为定时器 ===
        self.behavior_timer = QTimer(self)
        self.behavior_timer.timeout.connect(self.random_behavior)
        self.behavior_timer.start(5000)

        self.show()

    # ---------- 🆕 动态时长回调 ----------
    def _on_media_status_changed(self, status):
        if status == QMediaPlayer.EndOfMedia:

            # ① jiao 播完
            if self._is_playing_jiao:
                self._is_playing_jiao = False
                self.load_animation("idle")
                return

            # ② shout 播完：交给 _on_action_finished（它内部会幂等判断并消费 buffer）
            if self._is_action_playing:
                self._on_action_finished()

    def _on_duration_changed(self, duration_ms: int):
        """duration_ms 是原始时长，需按倍率换算"""
        if self._is_action_playing and duration_ms > 0:
            self._current_shout_duration = int(duration_ms / self.PLAYBACK_RATE)

    # ---------- 单击入口：仅负责缓存或触发 ----------
    def _on_single_click(self):
        """单击触发：不直接打断，而是缓存或排队执行"""
        if self._is_dragging:
            return

        if self._is_playing_jiao:
            pass

            # ② shout 播放期间点击：入缓存 + 加速 + 刷新 combo 窗口
        if self._is_action_playing:
            if self._click_buffer < self.MAX_BUFFER_SIZE:
                self._click_buffer += 1
                if self._in_combo:
                    self._combo_num += 1
                    self.PLAYBACK_RATE += self.add_rate
                # ✅ 每次点击都刷新 combo timer，才能实现"停手后才播 jiao"
                self._combo_timer.start(700)
            return
        else:
            self._execute_shout_action(is_first=not self._in_combo)

    # ---------- 实际执行 shout 动作（原子操作）----------
    def _execute_shout_action(self, is_first=False):
        """执行一次完整的 shout 动画+音频，结束后自动检查缓存"""

        if self._is_playing_jiao:
            return

        self._is_action_playing = True
        self._current_shout_duration = 0  # 重置，等待 durationChanged 信号填充

        # 连击倍率处理
        if is_first:
            self._in_combo = True
            self._combo_num = 0
            self.PLAYBACK_RATE = 1.0
        elif self._in_combo:
            self.PLAYBACK_RATE += self.add_rate
            self._combo_num += 1

        # 确保音频源正确
        audio_path = self.audio_shout
        current_url = self.player.media().canonicalUrl().toLocalFile()
        if os.path.normpath(current_url) != os.path.normpath(audio_path):
            if os.path.exists(audio_path):
                self.player.setMedia(QMediaContent(QUrl.fromLocalFile(audio_path)))
            else:
                print(f"[警告] 未找到音频文件: {audio_path}")

        if self.player.mediaStatus() != QMediaPlayer.NoMedia:
            self.player.setPlaybackRate(self.PLAYBACK_RATE)
            self.player.stop()
            self.player.play()

        #QTimer.singleShot(40, lambda: self.load_animation("shout"))
        self.load_animation("shout")

        # ⏱️ 连击窗口刷新
        self._combo_timer.start(700)

        # 🆕 使用动态时长调度动作结束回调
        # setPlaybackRate 会触发 durationChanged，但为防信号延迟，
        # 这里用 singleShot 做兜底：如果 durationChanged 先到则以它为准，
        # 如果没到则用 fallback 保证不会卡死
        #fallback = self._shout_fallback_duration
        #QTimer.singleShot(fallback, self._try_finish_with_fallback)

    # ---------- 🆕 兜底完成检查 ----------
    def _try_finish_with_fallback(self):
        """
        兜底定时器触发时检查：
        - 如果 durationChanged 已经更新了有效时长 → 忽略此次兜底，等真正的时长到期
        - 如果仍然是 0 → 说明确实获取不到时长，强制用兜底值结束
        """
        if self._current_shout_duration <= 0 and self._is_action_playing:
            print("[提示] durationChanged 未触发，使用兜底时长结束动作")
            self._on_action_finished()
        elif self._current_shout_duration > 0 and self._is_action_playing:
            # durationChanged 已生效，用真实时长重新调度精确的结束回调
            # （减去已经过去的 fallback 时间，避免双重等待）
            remaining = max(0, self._current_shout_duration - self._shout_fallback_duration)
            if remaining > 0:
                QTimer.singleShot(remaining, self._on_action_finished)
            else:
                # 真实时长比兜底还短，说明已经超时了，立即结束
                self._on_action_finished()

    # ---------- 动作结束回调：检查缓存队列 ----------
    def _on_action_finished(self):
        """一次 shout 播放完毕，检查是否有缓存的点击需要消费"""
        # 防止重复触发（兜底 + durationChanged 可能都触发）
        if not self._is_action_playing:
            return
        self._is_action_playing = False

        if self._click_buffer > 0:
            self._click_buffer -= 1
            #self.load_animation("idle")
            self._execute_shout_action(is_first=False)
        else:
            self.load_animation("idle")


    # ---------- 连击超时：播放收尾音效 ----------
    def _on_combo_timeout(self):
        # jiao 已在播放中，忽略
        if self._is_playing_jiao:
            return

        # shout 还在播或有缓存：说明用户还在连击，继续等
        if self._is_action_playing or self._click_buffer > 0:
            self._combo_timer.start(700)
            return

        self._in_combo = False
        self.PLAYBACK_RATE = 1.0

        #jiao需要连击超过3次才会触发
        if not self._combo_num > 3:
            return
        else:
            self._combo_num = 0

        # 真正进入 jiao 阶段
        self._is_playing_jiao = True


        if not os.path.exists(self.audio_jiao):
            print(f"[警告] 未找到音频文件: {self.audio_jiao}")
            self._is_playing_jiao = False
            self.load_animation("idle")
            return

        self.player.setMedia(QMediaContent(QUrl.fromLocalFile(self.audio_jiao)))
        self.player.setPlaybackRate(1.0)
        self.player.stop()
        self.player.play()

        self.load_animation("jiao")

    # ---------- 🆕 调整桌宠大小 ----------
    def resize_pet(self, new_size: int):
        if new_size == self.pet_size:
            return
        self.pet_size = new_size
        self.setFixedSize(new_size, new_size)
        self.label.setGeometry(0, 0, new_size, new_size)

        # 🆕 节流：拖动中只改尺寸，松手 150ms 后统一重载动画
        if not hasattr(self, "_resize_reload_timer"):
            self._resize_reload_timer = QTimer(self)
            self._resize_reload_timer.setSingleShot(True)
            self._resize_reload_timer.timeout.connect(
                lambda: self.load_animation(self.current_state)
            )
        self._resize_reload_timer.start(150)

    def open_size_slider(self):
        # 已存在则复用，避免开多个
        if getattr(self, "_size_popup", None) is not None:
            try:
                if self._size_popup.isVisible():
                    self._size_popup.close()
                    return
            except RuntimeError:
                self._size_popup = None

        self._size_popup = SizeSliderPopup(self)
        self._size_popup.show_near(self)

    # ---------- 动画管理 ----------
    def load_animation(self, state: str):
        path = f"assets/{state}.gif"
        if not os.path.exists(path):
            static_path = f"assets/{state}.png"
            if os.path.exists(static_path):
                pixmap = QPixmap(static_path).scaled(
                    self.pet_size, self.pet_size,
                    Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self.label.setPixmap(pixmap)
                self.current_state = state
                return
            print(f"[警告] 未找到素材: {path}")
            return

        movie = QMovie(path)
        movie.setScaledSize(QSize(self.pet_size, self.pet_size))
        self.label.setMovie(movie)
        movie.start()
        self.current_state = state

    def random_behavior(self):
        import random
        if self._is_dragging:
            return
        if random.random() < 0.1:
            pass

    # ---------- 鼠标事件 ----------
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._pending_click_pos = event.globalPos()
            self._press_timer.restart()
            #self._click_timer.start(10)
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            delta = event.globalPos() - self._pending_click_pos
            if delta.manhattanLength() > 5 and not self._is_dragging:
                #self._click_timer.stop()
                self._is_dragging = True
                self.setCursor(QCursor(Qt.ClosedHandCursor))
                #self.load_animation("drag")

            if self._is_dragging:
                new_pos = event.globalPos() - self._drag_pos
                self.move(new_pos)
        event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self._is_dragging:
                #self._click_timer.stop()
                self._is_dragging = False
                self.setCursor(QCursor(Qt.ArrowCursor))
                #self.load_animation("idle")
            else:
                # ✅ 未拖拽 → 检查按压时长
                elapsed = self._press_timer.elapsed()
                if elapsed < self.LONG_PRESS_THRESHOLD:
                    # 短按 → 确认为单击
                    self._on_single_click()
                # else: 长按 → 什么都不做（或可在此处添加长按专属逻辑）

                # 更新拖拽参考点（保留原有逻辑）
                self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def contextMenuEvent(self, event):
        menu = QMenu(self)

        act_size = QAction("📏 调整大小…", self)
        act_size.triggered.connect(self.open_size_slider)
        menu.addAction(act_size)

        menu.addSeparator()

        act_reset = QAction("🔄 回到屏幕中央", self)
        act_reset.triggered.connect(lambda: self.move(
            QApplication.primaryScreen().geometry().center() - self.rect().center()
        ))
        menu.addAction(act_reset)

        menu.addSeparator()
        act_quit = QAction("👋 退出", self)
        act_quit.triggered.connect(QApplication.quit)
        menu.addAction(act_quit)

        menu.exec_(event.globalPos())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    pet = DesktopPet()
    screen = QApplication.primaryScreen().geometry()
    pet.move(screen.width() - 150, screen.height() - 180)
    sys.exit(app.exec_())
