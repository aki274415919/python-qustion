from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QCheckBox, QLabel, QPushButton, QSizePolicy, QHeaderView
)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt
import random

def create_centered_checkbox(checked=False, enabled=True, stateChangedSlot=None, font=None, item=None):
    w = QWidget()
    layout = QHBoxLayout(w)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setAlignment(Qt.AlignCenter)
    chk = QCheckBox()
    if font:
        chk.setFont(font)
    chk.setChecked(checked)
    chk.setEnabled(enabled)

    def on_state_changed(*args, **kwargs):
        # 高亮同步
        if item is not None:
            if chk.isChecked():
                item.setBackground(QColor("#d5f7c6"))
            else:
                item.setBackground(QColor("white"))
        if stateChangedSlot:
            stateChangedSlot(*args, **kwargs)
    chk.stateChanged.connect(on_state_changed)
    layout.addWidget(chk)
    # 初始化高亮色
    if item is not None:
        if chk.isChecked():
            item.setBackground(QColor("#d5f7c6"))
        else:
            item.setBackground(QColor("white"))
    return w

class CrossTableWidget(QWidget):
    def __init__(self, qobj, answer_data, show_answer, save_callback):
        super().__init__()
        self.qobj = qobj
        self.show_answer = show_answer
        self.save_callback = save_callback
        self.cell_font_pt = 13   # 默认比15小2
        self.setMinimumSize(1200, 800)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)

        # 放大缩小按钮
        zoom_box = QHBoxLayout()
        zoom_box.setContentsMargins(0, 0, 0, 0)
        zoom_box.addStretch(1)
        zoom_in_btn = QPushButton("放大")
        zoom_out_btn = QPushButton("缩小")
        zoom_in_btn.clicked.connect(lambda: self.adjust_zoom(1))
        zoom_out_btn.clicked.connect(lambda: self.adjust_zoom(-1))
        zoom_box.addWidget(zoom_in_btn)
        zoom_box.addWidget(zoom_out_btn)
        zoom_box.addStretch(1)
        main_layout.addLayout(zoom_box)

        # 大表头（群组名）
        big_header = QLabel(qobj['col_names'][0].get('group', ''))
        font = QFont()
        font.setBold(True)
        font.setPointSize(20)
        big_header.setFont(font)
        big_header.setAlignment(Qt.AlignCenter)
        big_header.setStyleSheet("background-color: #F2F2F2; border: 1px solid #aaa; padding: 6px;")
        main_layout.addWidget(big_header)

        # 数据乱序
        row_cnt = len(qobj['row_names'])
        col_cnt = len(qobj['col_names'][0]['items'])
        self.row_indices = list(range(row_cnt))
        self.col_indices = list(range(col_cnt))
        random.shuffle(self.row_indices)
        random.shuffle(self.col_indices)
        shuffled_row_names = [qobj['row_names'][i] for i in self.row_indices]
        shuffled_col_names = [qobj['col_names'][0]['items'][j] for j in self.col_indices]
        self.shuffled_answer = [
            [qobj['answer'][i][j] for j in self.col_indices]
            for i in self.row_indices
        ]
        self.answer_data = answer_data

        # +1行：首行为“伪表头”，内容区再n行
        table = QTableWidget(row_cnt+1, col_cnt+1)
        self.table = table

        # 隐藏真实表头
        table.setHorizontalHeaderLabels([""] * (col_cnt + 1))
        table.horizontalHeader().setFixedHeight(2)
        table.horizontalHeader().hide()
        table.setVerticalHeaderLabels([""] * (row_cnt + 1))
        table.verticalHeader().setFixedWidth(2)
        table.verticalHeader().hide()

        table.setEditTriggers(table.NoEditTriggers)
        table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        table.setWordWrap(True)
        table.setShowGrid(True)
        table.setFocusPolicy(Qt.NoFocus)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 让所有列等宽撑满
        for c in range(table.columnCount()):
            table.horizontalHeader().setSectionResizeMode(c, QHeaderView.Stretch)

        font_bold = QFont()
        font_bold.setBold(True)
        font_bold.setPointSize(self.cell_font_pt+2)

        # 伪表头：左上角空白
        head_item = QTableWidgetItem("")
        table.setItem(0, 0, head_item)
        # 伪表头：设置表头内容，允许换行
        for j, col_name in enumerate(shuffled_col_names):
            item = QTableWidgetItem(col_name)
            item.setTextAlignment(Qt.AlignCenter)
            item.setFont(font_bold)
            item.setFlags(Qt.ItemIsEnabled)
            item.setData(Qt.DisplayRole, col_name)
            table.setItem(0, j+1, item)

        # 伪表头：设置左侧“行头”内容
        for i, row_name in enumerate(shuffled_row_names):
            item = QTableWidgetItem(row_name)
            item.setTextAlignment(Qt.AlignCenter)
            item.setFont(font_bold)
            item.setFlags(Qt.ItemIsEnabled)
            item.setData(Qt.DisplayRole, row_name)
            table.setItem(i+1, 0, item)

        # 填充内容区：checkbox
        font_cell = QFont()
        font_cell.setPointSize(self.cell_font_pt)
        self.checkbox_widgets = {}
        for i in range(row_cnt):
            for j in range(col_cnt):
                checked = (self.shuffled_answer[i][j] == 1) if self.show_answer else self.answer_data[self.row_indices[i]][self.col_indices[j]]
                item = QTableWidgetItem()
                item.setFlags(Qt.ItemIsEnabled)
                item.setTextAlignment(Qt.AlignCenter)
                table.setItem(i+1, j+1, item)
                widget = create_centered_checkbox(
                    checked,
                    enabled=not self.show_answer,
                    stateChangedSlot=self.save_callback,
                    font=font_cell,
                    item=item
                )
                table.setCellWidget(i+1, j+1, widget)
                self.checkbox_widgets[(i, j)] = widget

        # 自动适应所有内容（表头支持换行，内容区根据字体自动行高）
        self.sync_row_heights(table)
        table.resizeColumnsToContents()

        main_layout.addWidget(table, stretch=1)

    def adjust_zoom(self, delta):
        self.cell_font_pt = max(9, min(28, self.cell_font_pt + delta))
        self.update_fonts()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_fonts()

    def update_fonts(self):
        table = self.table
        font_bold = QFont()
        font_bold.setBold(True)
        font_bold.setPointSize(self.cell_font_pt+2)
        col_cnt = table.columnCount()
        for j in range(col_cnt):
            item = table.item(0, j)
            if item:
                item.setFont(font_bold)
        for i in range(1, table.rowCount()):
            item = table.item(i, 0)
            if item:
                item.setFont(font_bold)
        font = QFont()
        font.setPointSize(self.cell_font_pt)
        for (i, j), widget in self.checkbox_widgets.items():
            cb = widget.findChild(QCheckBox)
            if cb:
                cb.setFont(font)
        self.sync_row_heights(table)
        table.resizeColumnsToContents()

    def sync_row_heights(self, table):
        """让所有内容行的行高和表头行高一致（最大）"""
        table.resizeRowsToContents()
        max_height = max(table.rowHeight(r) for r in range(table.rowCount()))
        for r in range(table.rowCount()):
            table.setRowHeight(r, max_height)

    def get_current_answer(self):
        rows = len(self.qobj['row_names'])
        cols = len(self.qobj['col_names'][0]['items'])
        result = [[False]*cols for _ in range(rows)]
        for i, ri in enumerate(self.row_indices):
            for j, cj in enumerate(self.col_indices):
                w = self.table.cellWidget(i+1, j+1)  # +1 因为首行为表头
                if w is not None:
                    cb = w.findChild(QCheckBox)
                    if cb:
                        result[ri][cj] = cb.isChecked()
        return result
    def set_review_mode(self, std_answer, user_answer):
        row_cnt = len(self.row_indices)
        col_cnt = len(self.col_indices)
        for i in range(row_cnt):
            for j in range(col_cnt):
                grid_i, grid_j = i+1, j+1
                item = self.table.item(grid_i, grid_j)
                should = std_answer[self.row_indices[i]][self.col_indices[j]]
                user = user_answer[self.row_indices[i]][self.col_indices[j]]
                if should and user:
                    item.setBackground(QColor("#a3f5ac"))   # 正确：绿色
                elif should and not user:
                    item.setBackground(QColor("#ffb3b3"))   # 漏选：红色
                elif not should and user:
                    item.setBackground(QColor("#ffb3b3"))   # 多选：红色
                else:
                    item.setBackground(QColor("white"))     # 空白
