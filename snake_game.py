#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
貪吃蛇遊戲 - 使用 PyQt5 實現
採用莫蘭迪色系設計，具有文青風格
"""

import sys
import random
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QPainter, QBrush, QPen, QFont, QColor
from PyQt5.QtCore import QRect

# 遊戲常數
MIN_CELL_SIZE = 15
MAX_CELL_SIZE = 35
PREFERRED_CELL_SIZE = 24
MIN_GRID_SIZE = 15  # 最小格子數量
SCORE_BAR_HEIGHT = 60
MARGIN = 20

# 莫蘭迪色系配色
COLORS = {
    'background': '#EAE0D5',  # 米白
    'snake': '#A3B18A',      # 灰綠
    'food': '#E5989B',       # 莫蘭迪粉
    'text': '#6C584C',       # 深棕
    'grid': '#9B8B6B'        # 更深的棕灰色（確保可見）
}

# 方向常數
DIRECTIONS = {
    'UP': (0, -1),
    'DOWN': (0, 1),
    'LEFT': (-1, 0),
    'RIGHT': (1, 0)
}


class Snake:
    """蛇的資料結構，儲存位置列表和移動方向"""
    
    def __init__(self, grid_width, grid_height):
        # 初始蛇的位置（從中間開始，長度為3）
        start_x = grid_width // 2
        start_y = grid_height // 2
        self.body = [
            (start_x, start_y),
            (start_x - 1, start_y),
            (start_x - 2, start_y)
        ]
        self.direction = DIRECTIONS['RIGHT']
        self.grow = False
        self.grid_width = grid_width
        self.grid_height = grid_height
    
    def move(self):
        """移動蛇，如果需要成長則不移除尾巴"""
        head_x, head_y = self.body[0]
        new_head = (head_x + self.direction[0], head_y + self.direction[1])
        
        self.body.insert(0, new_head)
        
        if not self.grow:
            self.body.pop()
        else:
            self.grow = False
    
    def change_direction(self, new_direction):
        """改變移動方向，避免反向移動"""
        # 防止蛇反向移動
        if (self.direction[0] * -1, self.direction[1] * -1) != new_direction:
            self.direction = new_direction
    
    def check_collision(self):
        """檢查是否撞到邊界或自己"""
        head_x, head_y = self.body[0]
        
        # 檢查邊界
        if (head_x < 0 or head_x >= self.grid_width or 
            head_y < 0 or head_y >= self.grid_height):
            return True
        
        # 檢查是否撞到自己
        if self.body[0] in self.body[1:]:
            return True
        
        return False
    
    def eat_food(self):
        """吃到食物，下次移動時會成長"""
        self.grow = True
    
    def update_grid_size(self, new_grid_width, new_grid_height):
        """更新網格尺寸"""
        self.grid_width = new_grid_width
        self.grid_height = new_grid_height


class Food:
    """食物位置管理"""
    
    def __init__(self, grid_width, grid_height):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.position = self.generate_position()
    
    def generate_position(self):
        """隨機生成食物位置"""
        x = random.randint(0, self.grid_width - 1)
        y = random.randint(0, self.grid_height - 1)
        return (x, y)
    
    def respawn(self, snake_body):
        """重新生成食物位置，避免出現在蛇身上"""
        while True:
            self.position = self.generate_position()
            if self.position not in snake_body:
                break
    
    def update_grid_size(self, new_grid_width, new_grid_height):
        """更新網格尺寸並重新生成食物位置"""
        self.grid_width = new_grid_width
        self.grid_height = new_grid_height
        self.position = self.generate_position()


class GameBoard(QWidget):
    """遊戲畫板，負責繪製蛇和食物"""
    
    game_over = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.cell_size = PREFERRED_CELL_SIZE
        self.grid_width = MIN_GRID_SIZE
        self.grid_height = MIN_GRID_SIZE
        self.board_width = self.grid_width * self.cell_size
        self.board_height = self.grid_height * self.cell_size
        
        self.init_ui()
        self.init_game()
        
        # 設定定時器控制遊戲更新
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_game)
        self.timer.start(150)  # 150ms 更新一次
    
    def init_ui(self):
        """初始化 UI"""
        self.setMinimumSize(300, 300)
        self.setStyleSheet(f"""
            background-color: {COLORS['background']};
            border: 2px solid {COLORS['text']};
            border-radius: 8px;
        """)
        self.setFocusPolicy(Qt.StrongFocus)  # 允許接收鍵盤事件
    
    def calculate_dimensions(self, width, height):
        """根據給定的寬高計算最佳的格子大小和數量"""
        # 保留邊距
        available_width = width - 4  # 邊框寬度
        available_height = height - 4
        
        # 計算可能的格子大小
        max_grid_width = available_width // MIN_CELL_SIZE
        max_grid_height = available_height // MIN_CELL_SIZE
        
        # 確保最小格子數量
        max_grid_width = max(max_grid_width, MIN_GRID_SIZE)
        max_grid_height = max(max_grid_height, MIN_GRID_SIZE)
        
        # 計算最佳cell_size
        cell_size_w = available_width // max_grid_width
        cell_size_h = available_height // max_grid_height
        cell_size = min(cell_size_w, cell_size_h)
        
        # 限制cell_size範圍
        cell_size = max(MIN_CELL_SIZE, min(MAX_CELL_SIZE, cell_size))
        
        # 重新計算格子數量
        grid_width = available_width // cell_size
        grid_height = available_height // cell_size
        
        # 確保最小格子數量
        grid_width = max(grid_width, MIN_GRID_SIZE)
        grid_height = max(grid_height, MIN_GRID_SIZE)
        
        return cell_size, grid_width, grid_height
    
    def resizeEvent(self, event):
        """視窗大小改變時的處理"""
        super().resizeEvent(event)
        
        new_cell_size, new_grid_width, new_grid_height = self.calculate_dimensions(
            event.size().width(), event.size().height()
        )
        
        # 如果尺寸有變化，智能更新遊戲參數
        if (new_cell_size != self.cell_size or 
            new_grid_width != self.grid_width or 
            new_grid_height != self.grid_height):
            
            # 暫停遊戲
            was_running = self.timer.isActive()
            if was_running:
                self.timer.stop()
            
            # 保存當前遊戲狀態
            old_game_active = self.game_active
            old_score = self.score
            
            self.cell_size = new_cell_size
            self.grid_width = new_grid_width
            self.grid_height = new_grid_height
            self.board_width = self.grid_width * self.cell_size
            self.board_height = self.grid_height * self.cell_size
            
            # 如果有現有的遊戲物件，智能更新而不是重建
            if hasattr(self, 'snake') and hasattr(self, 'food'):
                # 檢查蛇是否還在有效範圍內
                snake_valid = all(0 <= pos[0] < new_grid_width and 0 <= pos[1] < new_grid_height 
                                for pos in self.snake.body)
                
                if snake_valid:
                    # 更新現有物件的網格尺寸
                    self.snake.update_grid_size(new_grid_width, new_grid_height)
                    self.food.update_grid_size(new_grid_width, new_grid_height)
                    # 確保食物不在蛇身上
                    self.food.respawn(self.snake.body)
                else:
                    # 蛇超出邊界，重新初始化
                    self.init_game()
            else:
                # 第一次初始化
                self.init_game()
            
            # 恢復遊戲狀態
            self.score = old_score
            self.game_active = old_game_active
            
            # 如果遊戲原本在運行，重新啟動
            if was_running and self.game_active:
                self.timer.start(150)
            
            # 確保焦點不丟失
            self.setFocus()
    
    def init_game(self):
        """初始化遊戲物件"""
        self.snake = Snake(self.grid_width, self.grid_height)
        self.food = Food(self.grid_width, self.grid_height)
        self.score = 0
        self.game_active = True
    
    def paintEvent(self, event):
        """繪製遊戲畫面"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 計算居中位置
        widget_width = self.width()
        widget_height = self.height()
        
        offset_x = (widget_width - self.board_width) // 2
        offset_y = (widget_height - self.board_height) // 2
        
        # 移動繪圖原點到居中位置
        painter.translate(offset_x, offset_y)
        
        # 先填充背景色
        painter.fillRect(0, 0, self.board_width, self.board_height, QColor(COLORS['background']))
        
        # 繪製格線
        self.draw_grid(painter)
        
        # 繪製食物
        self.draw_food(painter)
        
        # 繪製蛇
        self.draw_snake(painter)
        
        # 如果遊戲結束，顯示結束畫面
        if not self.game_active:
            painter.translate(-offset_x, -offset_y)  # 重置平移
            self.draw_game_over(painter)
    
    def draw_grid(self, painter):
        """繪製背景格線"""
        pen = QPen()
        pen.setColor(QColor(COLORS['grid']))
        pen.setWidth(1)
        pen.setStyle(Qt.SolidLine)
        painter.setPen(pen)
        
        # 設定透明背景，只畫邊框
        painter.setBrush(Qt.NoBrush)
        
        # 設定抗鋸齒關閉，讓線條更清晰
        painter.setRenderHint(QPainter.Antialiasing, False)
        
        # 繪製每個格子的邊框
        for x in range(0, self.grid_width):
            for y in range(0, self.grid_height):
                rect = QRect(x * self.cell_size, y * self.cell_size, 
                           self.cell_size, self.cell_size)
                painter.drawRect(rect)
        
        # 恢復抗鋸齒設定
        painter.setRenderHint(QPainter.Antialiasing, True)
    
    def draw_snake(self, painter):
        """繪製蛇"""
        brush = QBrush()
        brush.setColor(QColor(COLORS['snake']))
        brush.setStyle(Qt.SolidPattern)
        
        pen = QPen()
        pen.setColor(QColor(COLORS['snake']).darker(120))
        pen.setWidth(2)
        
        painter.setBrush(brush)
        painter.setPen(pen)
        
        for segment in self.snake.body:
            x = segment[0] * self.cell_size
            y = segment[1] * self.cell_size
            rect = QRect(x + 1, y + 1, self.cell_size - 2, self.cell_size - 2)
            painter.drawRoundedRect(rect, 3, 3)
    
    def draw_food(self, painter):
        """繪製食物"""
        brush = QBrush()
        brush.setColor(QColor(COLORS['food']))
        brush.setStyle(Qt.SolidPattern)
        
        pen = QPen()
        pen.setColor(QColor(COLORS['food']).darker(120))
        pen.setWidth(2)
        
        painter.setBrush(brush)
        painter.setPen(pen)
        
        x = self.food.position[0] * self.cell_size
        y = self.food.position[1] * self.cell_size
        rect = QRect(x + 2, y + 2, self.cell_size - 4, self.cell_size - 4)
        painter.drawEllipse(rect)
    
    def draw_game_over(self, painter):
        """繪製遊戲結束畫面"""
        widget_width = self.width()
        widget_height = self.height()
        
        # 半透明覆蓋層
        brush = QBrush()
        brush.setColor(QColor(COLORS['text']))
        brush.setStyle(Qt.SolidPattern)
        painter.setBrush(brush)
        painter.setOpacity(0.8)
        painter.drawRect(0, 0, widget_width, widget_height)
        
        # 遊戲結束文字
        painter.setOpacity(1.0)
        font = QFont('Arial', 24, QFont.Bold)
        painter.setFont(font)
        pen = QPen()
        pen.setColor(QColor(COLORS['background']))
        painter.setPen(pen)
        
        text_rect = QRect(0, widget_height // 2 - 60, widget_width, 60)
        painter.drawText(text_rect, Qt.AlignCenter, "遊戲結束")
        
        font.setPointSize(16)
        painter.setFont(font)
        text_rect = QRect(0, widget_height // 2, widget_width, 40)
        painter.drawText(text_rect, Qt.AlignCenter, f"最終分數: {self.score}")
        
        font.setPointSize(12)
        painter.setFont(font)
        text_rect = QRect(0, widget_height // 2 + 40, widget_width, 30)
        painter.drawText(text_rect, Qt.AlignCenter, "按空白鍵重新開始")
    
    def update_game(self):
        """更新遊戲狀態"""
        if not self.game_active:
            return
        
        # 移動蛇
        self.snake.move()
        
        # 檢查碰撞
        if self.snake.check_collision():
            self.game_active = False
            self.timer.stop()
            self.game_over.emit()
            self.update()
            return
        
        # 檢查是否吃到食物
        if self.snake.body[0] == self.food.position:
            self.snake.eat_food()
            self.food.respawn(self.snake.body)
            self.score += 10
        
        self.update()  # 重繪畫面
    
    def keyPressEvent(self, event):
        """處理按鍵事件"""
        if event.key() == Qt.Key_Up:
            self.snake.change_direction(DIRECTIONS['UP'])
        elif event.key() == Qt.Key_Down:
            self.snake.change_direction(DIRECTIONS['DOWN'])
        elif event.key() == Qt.Key_Left:
            self.snake.change_direction(DIRECTIONS['LEFT'])
        elif event.key() == Qt.Key_Right:
            self.snake.change_direction(DIRECTIONS['RIGHT'])
        elif event.key() == Qt.Key_Space and not self.game_active:
            # 重新開始遊戲
            self.restart_game()
    
    def restart_game(self):
        """重新開始遊戲"""
        self.init_game()
        self.timer.start(150)
        self.update()


class SnakeGameWindow(QMainWindow):
    """主視窗，管理整個遊戲介面"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """初始化使用者介面"""
        self.setWindowTitle('貪吃蛇遊戲')
        self.setMinimumSize(400, 500)  # 設定最小視窗大小
        self.resize(600, 700)  # 設定預設大小
        
        # 建立主要部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 建立佈局
        layout = QVBoxLayout()
        layout.setContentsMargins(MARGIN, MARGIN, MARGIN, MARGIN)  # 設定對稱邊距
        layout.setSpacing(15)  # 設定元件間距
        central_widget.setLayout(layout)
        
        # 分數標籤
        self.score_label = QLabel('分數: 0')
        self.score_label.setAlignment(Qt.AlignCenter)
        self.score_label.setFixedHeight(50)
        self.score_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text']};
                font-size: 20px;
                font-weight: bold;
                padding: 10px;
                background-color: {COLORS['background']};
                border: 2px solid {COLORS['text']};
                border-radius: 8px;
            }}
        """)
        layout.addWidget(self.score_label)
        
        # 遊戲畫板
        self.game_board = GameBoard()
        self.game_board.game_over.connect(self.on_game_over)
        layout.addWidget(self.game_board)
        
        # 設定視窗樣式
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLORS['grid']};
            }}
            QWidget {{
                background-color: {COLORS['grid']};
            }}
        """)
        
        # 更新分數顯示的定時器
        self.score_timer = QTimer()
        self.score_timer.timeout.connect(self.update_score)
        self.score_timer.start(100)
        
        # 確保遊戲畫板有焦點
        self.game_board.setFocus()
    
    def update_score(self):
        """更新分數顯示"""
        self.score_label.setText(f'分數: {self.game_board.score}')
    
    def on_game_over(self):
        """處理遊戲結束事件"""
        self.score_timer.stop()


def main():
    """主程式進入點"""
    app = QApplication(sys.argv)
    
    # 設定應用程式樣式
    app.setStyle('Fusion')
    
    # 建立並顯示主視窗
    game_window = SnakeGameWindow()
    game_window.show()
    
    # 確保遊戲畫板有焦點，可以接收鍵盤事件
    game_window.game_board.setFocus()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
