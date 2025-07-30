from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QCheckBox, QHBoxLayout, QHeaderView, QLabel
from PyQt5.QtGui import QFont, QColor, QBrush, QFontMetrics
from PyQt5.QtCore import Qt
import random

def get_text_pixel_width(text, font):
    metrics = QFontMetrics(font)
    return metrics.width(str(text)) + 28

def create_centered_checkbox(checked=False, enabled=True, stateChangedSlot=None):
    w = QWidget()
    layout = QHBoxLayout(w)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setAlignment(Qt.AlignCenter)
    chk = QCheckBox()
    chk.setChecked(checked)
    chk.setEnabled(enabled)
    if stateChangedSlot:
        chk.stateChanged.connect(stateChangedSlot)
    layout.addWidget(chk)
    return w

class CrossTableWidget(QWidget):
    def __init__(self, qobj, answer_data, show_answer, save_callback):
        super().__init__()
        self.qobj = qobj
        self.show_answer = show_answer
        self.save_callback = save_callback

        # 行列乱序
        row_cnt = len(qobj['row_names'])
        col_cnt = len(qobj['col_names'][0]['items'])
        self.row_indices = list(range(row_cnt))
        self.col_indices = list(range(col_cnt))
        random.shuffle(self.row_indices)
        random.shuffle(self.col_indices)

        # 乱序后的表头
        shuffled_row_names = [qobj['row_names'][i] for i in self.row_indices]
        shuffled_col_names = [qobj['col_names'][0]['items'][j] for j in self.col_indices]

        # 答案矩阵也要乱序
        self.shuffled_answer = [
            [qobj['answer'][i][j] for j in self.col_indices]
            for i in self.row_indices
        ]
        # 用户答案也跟着同步乱序映射
        self.answer_data = answer_data

        layout = QVBoxLayout()
        self.setLayout(layout)

        # 大表头
        big_header = QLabel(qobj['col_names'][0].get('group', ''))
        font = QFont()
        font.setBold(True)
        font.setPointSize(16)
        big_header.setFont(font)
        big_header.setAlignment(Qt.AlignCenter)
        big_header.setStyleSheet("background-color: #F2F2F2; border: 1px solid #aaa; padding: 8px;")
        layout.addWidget(big_header)

        rows, cols = row_cnt, col_cnt
        table = QTableWidget(rows, cols+1)
        self.table = table
        table.setStyleSheet("""
            QTableWidget, QTableView {
                gridline-color: #000;
                font-size: 15px;
            }
            QTableWidget::item {
                border: 2px solid #000;
            }
        """)
        table.setEditTriggers(table.NoEditTriggers)
        h_headers = [qobj.get('row_header', '')] + shuffled_col_names
        table.setHorizontalHeaderLabels(h_headers)
        table.setVerticalHeaderLabels([""]*rows)

        # 行头加粗
        font_bold = QFont()
        font_bold.setBold(True)
        table.horizontalHeader().setFont(font_bold)
        table.verticalHeader().setFont(font_bold)
        header_bg = QBrush(QColor(220, 230, 241))
        for c in range(table.columnCount()):
            item = table.horizontalHeaderItem(c)
            if item:
                item.setBackground(header_bg)

        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        # 设置左边行为乱序
        for i, name in enumerate(shuffled_row_names):
            item = QTableWidgetItem(name)
            item.setFont(font_bold)
            item.setBackground(QColor("#f9f9f9"))
            item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            table.setItem(i, 0, item)

        # 设置交叉格内容（同步乱序映射）
        for i in range(rows):
            for j in range(cols):
                if show_answer:
                    widget = create_centered_checkbox(self.shuffled_answer[i][j] == 1, enabled=False)
                else:
                    # 用户答案要按乱序对应
                    orig_row = self.row_indices[i]
                    orig_col = self.col_indices[j]
                    widget = create_centered_checkbox(self.answer_data[orig_row][orig_col], enabled=True, stateChangedSlot=self.save_callback)
                table.setCellWidget(i, j+1, widget)

        # 统一列宽
        max_width = 0
        for c in range(table.columnCount()):
            h = table.horizontalHeaderItem(c)
            if h:
                max_width = max(max_width, get_text_pixel_width(h.text(), font_bold))
        for r in range(table.rowCount()):
            v = table.item(r, 0)
            if v:
                max_width = max(max_width, get_text_pixel_width(v.text(), font_bold))
        for c in range(table.columnCount()):
            table.setColumnWidth(c, max_width)
        layout.addWidget(table)

    def get_current_answer(self):
        """恢复成原顺序的作答结果（给判分用）"""
        # 还原成原始顺序的二维数组
        rows = len(self.qobj['row_names'])
        cols = len(self.qobj['col_names'][0]['items'])
        result = [[False]*cols for _ in range(rows)]
        for i, ri in enumerate(self.row_indices):
            for j, cj in enumerate(self.col_indices):
                w = self.table.cellWidget(i, j+1)
                if w is not None:
                    cb = w.findChild(QCheckBox)
                    if cb:
                        result[ri][cj] = cb.isChecked()
        return result
