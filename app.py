import sys
import os
import sqlite3

from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QVBoxLayout, QLineEdit, QMessageBox, QProgressBar
)
from PySide6.QtGui import QMovie
from PySide6.QtCore import Qt, QSize, QPoint
from PySide6.QtCore import QPropertyAnimation
from PySide6.QtWidgets import QGraphicsOpacityEffect
from PySide6.QtCore import QEasingCurve
from PySide6.QtWidgets import QSizePolicy


SAVINGS_GOAL = 500  # change this anytime


def get_db_path() -> str:
    """Return absolute path to db/bloomgarden.db"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "db", "bloomgarden.db")


def init_db():
    """Create savings table if it doesn't exist."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS savings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def is_goal_reached() -> bool:
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS app_state (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    cur.execute("SELECT value FROM app_state WHERE key='goal_reached'")
    row = cur.fetchone()
    conn.close()
    return row is not None and row[0] == "true"


def set_goal_reached():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO app_state (key, value)
        VALUES ('goal_reached', 'true')
    """)
    conn.commit()
    conn.close()


def add_savings(amount: int):
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO savings (amount) VALUES (?)",
        (amount,)
    )
    last_id = cur.lastrowid
    conn.commit()
    conn.close()
    return last_id
    

def get_total_savings() -> int:
    """Return sum of all savings entries."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(SUM(amount), 0) FROM savings")
    total = cur.fetchone()[0]
    conn.close()
    return int(total)

def delete_saving_row(row_id: int):
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("DELETE FROM savings WHERE id = ?", (row_id,))
    conn.commit()
    conn.close()


def get_plant_stage(total: int) -> str:
    """Pick stage name based on progress."""
    progress = total / SAVINGS_GOAL if SAVINGS_GOAL > 0 else 0

    if progress < 0.25:
        return "seed"
    elif progress < 0.5:
        return "small"
    elif progress < 0.75:
        return "growing"
    elif progress < 1.0:
        return "almost"
    else:
        return "bloom"


def get_plant_image_path(stage: str) -> str:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "assets", "plant", f"{stage}.gif")


def get_motivational_message(stage: str) -> str:
    messages = {
        "seed": "Every journey begins with a seed 🌱",
        "small": "Nice start — keep going 💧",
        "growing": "Growing stronger every day 🌿",
        "almost": "Almost there ✨",
        "bloom": "In full bloom 🌸",
    }
    return messages.get(stage, "")


class BloomGardenApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("BloomGarden 🌸")
        self.resize(520, 650)
        self.setMinimumSize(480, 600)

        # 🌸 Main background
        self.setStyleSheet("""
            QWidget {
                background-color: #F5F7F4;
                font-family: Segoe UI;
            }
        """)


        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        self.image_label.setStyleSheet("background: transparent;")

        #plant_layout.addWidget(self.image_label)

        self.opacity_effect = QGraphicsOpacityEffect()
        self.image_label.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(1.0)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, SAVINGS_GOAL)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setStyleSheet("""
         QProgressBar {
            background-color: #E6EFEA;
            border-radius: 7px;
        }
        QProgressBar::chunk {
             background-color: #9FBEA1;
             border-radius: 7px;
         }
        """)


        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 15px; color: #4F6F6F; font-weight: 500;")

        self.motivation_label = QLabel()
        self.motivation_label.setAlignment(Qt.AlignCenter)
        self.motivation_label.setWordWrap(True)
        self.motivation_label.setFixedWidth(260)

        self.motivation_label.setStyleSheet("""
           QLabel {
              font-size: 14px;
              color: #6B8E8E;
              line-height: 22px;
            }
        """)

        self.motivation_opacity = QGraphicsOpacityEffect()
        self.motivation_label.setGraphicsEffect(self.motivation_opacity)
        self.motivation_opacity.setOpacity(1.0)


        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Enter savings amount (e.g., 50)")
        self.input_box.setFixedHeight(40)
        self.input_box.setStyleSheet("""
           QLineEdit {
               background-color: #FFFFFF;
               color: #2E4F4F;              /* typed text color */
               border: 1px solid #C7D6D5;
             border-radius: 10px;
             padding: 10px;
             font-size: 15px;
             }

             QLineEdit::placeholder {
                color: #9AA6A5;              /* placeholder text */
              }
         """)

        #add button
        self.add_button = QPushButton("➕ Add Savings")
        self.add_button.setFixedHeight(45)
        self.add_button.setStyleSheet("""
            QPushButton {
                background-color: #A7C7A5;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 12px;
                padding: 12px;
            }
            QPushButton:hover {
                background-color: #93B893;
            }
        """)
        self.add_button.clicked.connect(self.handle_add_savings)

        self.add_button.pressed.connect(
          lambda: self.animate_button_press(self.add_button)
        )
        self.add_button.released.connect(
          lambda: self.animate_button_release(self.add_button)
        )

        #subtract button
        self.subtract_button = QPushButton("➖ Subtract Savings")
        self.subtract_button.setFixedHeight(45)
        self.subtract_button.setStyleSheet("""
             QPushButton {
                 background-color: #E6B8B7;
                 color: white;
                 font-size: 16px;
                 font-weight: bold;
                 border-radius: 12px;
                 padding: 12px;
             }
             QPushButton:hover {
                background-color: #D99A99;
             }
        """)
        self.subtract_button.clicked.connect(self.handle_subtract_savings)

        self.subtract_button.pressed.connect(
          lambda: self.animate_button_press(self.subtract_button)
        )
        self.subtract_button.released.connect(
          lambda: self.animate_button_release(self.subtract_button)
        )


        #Reset Button
        self.reset_button = QPushButton("🔄 Reset (Test)")
        self.reset_button.setFixedHeight(35)
        self.reset_button.setStyleSheet("""
             QPushButton {
                 background-color: transparent;
                 color: #888888;
                 font-size: 13px;
                 border: none;
             }
             QPushButton:hover {
                 color: #555555;
                 text-decoration: underline;
             }
        """)
        self.reset_button.clicked.connect(self.handle_reset_savings)
        
        #undo button
        self.undo_button = QPushButton("↩ Undo Last Action")
        self.undo_button.setFixedHeight(36)
        self.undo_button.setStyleSheet("""
             QPushButton {
               background-color: #EEE;
               color: #555;
               border-radius: 8px;
             }
             QPushButton:hover {
             background-color: #DDD;
             }
        """)
        self.undo_button.clicked.connect(self.handle_undo)


# 🌼 Card container
        card = QWidget()
        card.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 24px;
            }
        """)
        card.setFixedWidth(360)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(20)

# 🌱 Image container
        image_container = QWidget()
        image_container.setMinimumHeight(240)  # instead of FixedHeight
        image_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)


        image_layout = QVBoxLayout(image_container)
        image_layout.setContentsMargins(0, 0, 0, 0)
        image_layout.setSpacing(0)

        image_layout.addStretch()
        image_layout.addWidget(self.image_label, 0, Qt.AlignBottom | Qt.AlignHCenter)

        card_layout.addWidget(image_container)


# 🌈 Progress bar
        card_layout.addWidget(self.progress_bar)
        card_layout.addSpacing(8)

# 🌱 Status text
        card_layout.addWidget(self.status_label, alignment=Qt.AlignCenter)

# 💬 Motivation message 
        card_layout.addSpacing(2)
        card_layout.addWidget(self.motivation_label, alignment=Qt.AlignCenter)

# ✏️ Inputs & buttons
        card_layout.addSpacing(18)
        card_layout.addWidget(self.input_box)
        card_layout.addWidget(self.add_button)
        card_layout.addWidget(self.subtract_button)
        card_layout.addWidget(self.reset_button)
        card_layout.addWidget(self.undo_button)


        # 🌸 Center card on window
        main_layout = QVBoxLayout()
        main_layout.addStretch(1)
        main_layout.addWidget(card, alignment=Qt.AlignCenter)
        main_layout.addStretch(2)


        self.setLayout(main_layout)

# initialize animation state
        self.last_progress_value = 0
        self.last_action_id = None


# initialize view
        self.show()
        QApplication.processEvents()  # 🔹 FORCE layout to settle
        self.refresh_ui()



    
    def refresh_ui(self):
        if hasattr(self, "movie") and self.movie:
         self.movie.stop()

        total = get_total_savings()
        stage = get_plant_stage(total)
        img_path = get_plant_image_path(stage)

        # 🎯 Different heights per stage (fix overlap)
        if stage in ["seed", "small"]:
            self.image_label.setFixedSize(260, 180)
        elif stage == "growing":
            self.image_label.setFixedSize(260, 200)
        elif stage == "almost":
            self.image_label.setFixedSize(260, 220)
        else:  # bloom
            self.image_label.setFixedSize(260, 240)


        """print("Stage:", stage)
        print("GIF path:", img_path)
        print("GIF exists:", os.path.exists(img_path))
        """
        new_value = min(total, SAVINGS_GOAL)

        goal_already_reached = is_goal_reached()

        if total >= SAVINGS_GOAL and not goal_already_reached:
         set_goal_reached()
         self.play_celebration()


        delta = abs(new_value - self.last_progress_value)

        self.progress_anim = QPropertyAnimation(self.progress_bar, b"value")

      # 🎚 Dynamic duration (big jumps feel heavier)
        if delta < 50:
         duration = 300
        elif delta < 150:
         duration = 450
        else:
         duration = 600

        self.progress_anim.setDuration(duration)

     # 🌿 Natural easing (smooth + premium feel)
        self.progress_anim.setEasingCurve(QEasingCurve.OutCubic)

        self.progress_anim.setStartValue(self.last_progress_value)
        self.progress_anim.setEndValue(new_value)
        self.progress_anim.start()

        self.last_progress_value = new_value


        self.animate_motivation_text(get_motivational_message(stage))


        self.image_label.setMinimumSize(240, 180)
        self.image_label.setMaximumSize(260, 200)

        self.movie = QMovie(img_path)
        self.movie.setScaledSize(self.image_label.size())
        self.movie.setScaledSize(QSize(240, 180))

        if not self.movie.isValid():
          self.image_label.setText("❌ GIF failed to load")
          self.image_label.setStyleSheet("color: red;")
          return
      
        self.image_label.setStyleSheet("")
        self.image_label.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)

# Fade out
        self.fade_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out.setDuration(200)
        self.fade_out.setStartValue(1.0)
        self.fade_out.setEndValue(0.0)

# Fade in
        self.fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in.setDuration(300)
        self.fade_in.setStartValue(0.0)
        self.fade_in.setEndValue(1.0)

        #def swap_movie():
        #    self.image_label.setMovie(self.movie)
        #    self.movie.setScaledSize(QSize(260, 220))
        #    self.movie.start()
        #   self.fade_in.start()

        def swap_movie():
             self.image_label.setMovie(self.movie)
             self.movie.start()
             self.fade_in.start()


        self.fade_out.finished.connect(swap_movie)
        self.fade_out.start()

        self.status_label.setText(
          f"🌱 Savings: {total} / {SAVINGS_GOAL}  |  Stage: {stage}"
        )


        if total >= SAVINGS_GOAL:
         self.add_button.setEnabled(False)
         self.add_button.setText("🌸 Goal Reached!")
        else:
         self.add_button.setEnabled(True)
         self.add_button.setText("➕ Add Savings")

      # Subtract must ALWAYS work
         self.subtract_button.setEnabled(True)

    def play_celebration(self):
        self.status_label.setText("🌸 You did it! Goal achieved!")

        anim = QPropertyAnimation(self.image_label, b"geometry")
        anim.setDuration(600)
        anim.setEasingCurve(QEasingCurve.OutBounce)

        rect = self.image_label.geometry()
        anim.setStartValue(rect.adjusted(-10, -10, 10, 10))
        anim.setEndValue(rect)

        anim.start()
        self._celebration_anim = anim


    def animate_button_press(self, button: QPushButton):
        anim = QPropertyAnimation(button, b"geometry")
        anim.setDuration(120)
        anim.setEasingCurve(QEasingCurve.OutQuad)

        rect = button.geometry()
        anim.setStartValue(rect)
        anim.setEndValue(rect.adjusted(3, 3, -3, -3))

        anim.start()
        button._press_anim = anim  # keep reference

    def animate_button_release(self, button: QPushButton):
        anim = QPropertyAnimation(button, b"geometry")
        anim.setDuration(160)
        anim.setEasingCurve(QEasingCurve.OutBounce)

        rect = button.geometry()
        anim.setStartValue(rect.adjusted(3, 3, -3, -3))
        anim.setEndValue(rect)

        anim.start()
        button._release_anim = anim


    def handle_add_savings(self):
        text = self.input_box.text().strip()

        if text == "":
           self.show_warning("Oops!", "Please enter an amount first 😊")
           self.shake_widget(self.input_box)
           return


        try:
          amount = int(text)
        except ValueError:
           self.show_warning("Oops!", "Please enter a whole number like 50 or 200.")
           self.shake_widget(self.input_box)
           return

        if amount <= 0:
           self.show_warning("Oops!", "Amount must be greater than 0.")
           self.shake_widget(self.input_box)
           return
        if get_total_savings() >= SAVINGS_GOAL:
           self.show_warning(
             "Goal already reached 🌸",
             "You’ve already reached your savings goal!"
            )
           self.shake_widget(self.input_box)
           self.input_box.clear()
           return

        self.last_action_id = add_savings(amount)

        self.input_box.clear()
        self.refresh_ui()



    def handle_subtract_savings(self):
        text = self.input_box.text().strip()

        if text == "":
          self.show_warning("Oops!", "Please enter an amount to subtract 😊")
          self.shake_widget(self.input_box)
          return

        try:
          amount = int(text)
        except ValueError:
          self.show_warning("Oops!", "Please enter a whole number like 50.")
          return

        if amount <= 0:
          self.show_warning("Oops!", "Amount must be greater than 0.")
          return

        current_total = get_total_savings()

    # 🚫 Prevent going below zero
        if amount > current_total:
           self.show_warning(
             "Not enough savings 💭",
             f"You have {current_total} saved, try a smaller amount."
            )
           self.shake_widget(self.input_box)
           self.input_box.clear()
           return


        self.last_action_id = add_savings(-amount)

        self.input_box.clear()
        self.refresh_ui()

    
    def handle_reset_savings(self):
         msg = QMessageBox(self)
         msg.setIcon(QMessageBox.Question)
         msg.setWindowTitle("Reset Savings")
         msg.setText(
          "This will reset savings to 0.\n"
          "(For testing plant stages)\n\n"
          "Continue?"
        )

         yes_btn = msg.addButton("Yes", QMessageBox.YesRole)
         no_btn = msg.addButton("No", QMessageBox.NoRole)

         msg.setStyleSheet("""
          QMessageBox {
           background-color: #F9FBFA;
         }
          QLabel {
           color: #2E4F4F;
           font-size: 14px;
         }
          QPushButton {
           background-color: #A7C7A5;
           color: white;
           border-radius: 6px;
           padding: 6px 14px;
           min-width: 80px;
         }
          QPushButton:hover {
           background-color: #93B893;
         }
        """)

         msg.exec()

         if msg.clickedButton() == yes_btn:
          db_path = get_db_path()
          conn = sqlite3.connect(db_path)
          cur = conn.cursor()
          cur.execute("DELETE FROM savings")
          conn.commit()
          conn.close()

          self.refresh_ui()

    def handle_undo(self):
         if self.last_action_id is None:
          self.show_warning("Nothing to undo", "No recent action to undo.")
          return

         delete_saving_row(self.last_action_id)
         self.last_action_id = None
         self.refresh_ui()
    

    def show_warning(self, title: str, message: str):
         msg = QMessageBox(self)
         msg.setIcon(QMessageBox.Warning)
         msg.setWindowTitle(title)
         msg.setText(message)

         msg.setStyleSheet("""
          QMessageBox {
            background-color: #F9FBFA;
          }
          QLabel {
            color: #2E4F4F;
            font-size: 14px;
          }
          QPushButton {
            background-color: #A7C7A5;
            color: white;
            border-radius: 6px;
            padding: 6px 14px;
            min-width: 80px;
          }
          QPushButton:hover {
            background-color: #93B893;
          }
        """)

         msg.exec()


    def shake_widget(self, widget):
        start = widget.pos()

        anim = QPropertyAnimation(widget, b"pos")
        anim.setDuration(300)
        anim.setKeyValueAt(0.0, start)
        anim.setKeyValueAt(0.25, start + QPoint(-6, 0))
        anim.setKeyValueAt(0.5, start + QPoint(6, 0))
        anim.setKeyValueAt(0.75, start + QPoint(-6, 0))
        anim.setKeyValueAt(1.0, start)

        anim.start()
        widget._shake_anim = anim  # keep reference


    def animate_motivation_text(self, new_text: str):
       fade_out = QPropertyAnimation(self.motivation_opacity, b"opacity")
       fade_out.setDuration(150)
       fade_out.setStartValue(1.0)
       fade_out.setEndValue(0.0)

       def update_text():
        self.motivation_label.setText(new_text)

        fade_in = QPropertyAnimation(self.motivation_opacity, b"opacity")
        fade_in.setDuration(250)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.start()

        self._motivation_fade_in = fade_in

       fade_out.finished.connect(update_text)
       fade_out.start()

       self._motivation_fade_out = fade_out



if __name__ == "__main__":
    init_db()

    app = QApplication(sys.argv)
    window = BloomGardenApp()
    window.show()
    sys.exit(app.exec())
