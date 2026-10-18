import sys
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QMenu,
                             QAction, QSystemTrayIcon, QGraphicsDropShadowEffect)
from PyQt5.QtGui import QPixmap, QMovie, QIcon, QCursor
from PyQt5.QtCore import Qt, QTimer, QPoint, QSize


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

        # === 🆕 单击判定定时器（区分单击/双击/拖拽）===
        self._click_timer = QTimer(self)
        self._click_timer.setSingleShot(True)
        self._click_timer.timeout.connect(self._on_single_click)
        self._pending_click_pos = QPoint()  # 记录按下位置，防止拖拽误判

        # === 加载初始动画 ===
        self.load_animation("idle")

        # === 随机行为定时器 ===
        self.behavior_timer = QTimer(self)
        self.behavior_timer.timeout.connect(self.random_behavior)
        self.behavior_timer.start(5000)

        self.show()

    # ---------- 🆕 单击处理：shout 0.3秒 ----------
    def _on_single_click(self):
        """确认为单击后触发 shout 动画，0.3秒后恢复 idle"""
        if self._is_dragging:
            return
        print("📢 Shout!")
        self.load_animation("shout")
        # 0.3秒 = 300ms 后自动恢复 idle
        QTimer.singleShot(300, lambda: self.load_animation("idle"))

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

            # ---------- 🔄 鼠标拖拽 + 单击判定 ----------

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._pending_click_pos = event.globalPos()
            # 🆕 启动单击判定计时器（等待看是否是双击或拖拽）
            # 200ms 内如果没有双击/拖拽发生，则确认为单击
            self._click_timer.start(200)
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            # 🆕 如果移动距离超过阈值，取消单击判定，进入拖拽模式
            delta = event.globalPos() - self._pending_click_pos
            if delta.manhattanLength() > 5 and not self._is_dragging:
                self._click_timer.stop()  # 取消单击
                self._is_dragging = True
                self.setCursor(QCursor(Qt.ClosedHandCursor))
                self.load_animation("drag")

            if self._is_dragging:
                new_pos = event.globalPos() - self._drag_pos
                self.move(new_pos)
        event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            # 🆕 如果是拖拽释放，确保单击定时器已停止
            if self._is_dragging:
                self._click_timer.stop()
                self._is_dragging = False
                self.setCursor(QCursor(Qt.ArrowCursor))
                self.load_animation("idle")
            else:
                # 非拖拽释放时，更新拖拽偏移量以备下次使用
                self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    # ---------- 双击互动（会阻止单击定时器触发）----------
    def mouseDoubleClickEvent(self, event):
        """双击时取消待处理的单击，执行双击逻辑"""
        self._click_timer.stop()  # 🆕 关键：阻止单击触发
        print("💕 你摸了我！")
        # self.load_animation("happy")
        # QTimer.singleShot(2000, lambda: self.load_animation("idle"))

    # ---------- 右键菜单 ----------
    def contextMenuEvent(self, event):
        menu = QMenu(self)
        act_quit = QAction("👋 退出", self)
        act_quit.triggered.connect(QApplication.quit)
        act_reset = QAction("🔄 回到屏幕中央", self)
        act_reset.triggered.connect(lambda: self.move(
            QApplication.primaryScreen().geometry().center() - self.rect().center()
        ))
        menu.addAction(act_reset)
        menu.addSeparator()
        menu.addAction(act_quit)
        menu.exec_(event.globalPos())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    pet = DesktopPet()
    screen = QApplication.primaryScreen().geometry()
    pet.move(screen.width() - 150, screen.height() - 180)
    sys.exit(app.exec_())