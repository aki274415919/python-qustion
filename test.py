import sys
import json
import random
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QCheckBox, QPushButton, QHeaderView, QMessageBox, QAbstractItemView
)
from PyQt5.QtGui import QFont, QColor, QBrush, QFontMetrics
from PyQt5.QtCore import Qt

def get_text_pixel_width(text, font):
    """获取文本的像素宽度（含缓冲）"""
    metrics = QFontMetrics(font)
    return metrics.width(str(text)) + 28  # 加宽一点，避免贴边

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

class CrossTableQuiz(QWidget):
    def __init__(self, questions):
        super().__init__()
        self.setWindowTitle("交叉表练习考试系统")
        self.resize(1100, 650)
        self.questions = random.sample(questions, len(questions))
        self.user_answers = []
        for q in self.questions:
            ans = []
            for i in range(len(q['row_names'])):
                ans.append([False]*len(q['col_names'][0]['items']))
            self.user_answers.append(ans)
        self.cur_idx = 0
        self.show_answer = False

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.header = QLabel()
        self.header.setWordWrap(True)
        self.layout.addWidget(self.header)

        # 顶部大表头
        self.big_header = QLabel()
        font = QFont()
        font.setBold(True)
        font.setPointSize(16)
        self.big_header.setFont(font)
        self.big_header.setAlignment(Qt.AlignCenter)
        self.big_header.setStyleSheet("background-color: #F2F2F2; border: 1px solid #aaa; padding: 8px;")
        self.layout.addWidget(self.big_header)

        # ---- 已去除 self.table_group 那一行 ----

        self.table = QTableWidget()
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.layout.addWidget(self.table)

        self.btns = QHBoxLayout()
        self.prev_btn = QPushButton("上一题")
        self.next_btn = QPushButton("下一题")
        self.commit_btn = QPushButton("提交本题")
        self.finish_btn = QPushButton("交卷并批改")
        self.btns.addWidget(self.prev_btn)
        self.btns.addWidget(self.next_btn)
        self.btns.addWidget(self.commit_btn)
        self.btns.addWidget(self.finish_btn)
        self.layout.addLayout(self.btns)

        self.prev_btn.clicked.connect(self.prev_q)
        self.next_btn.clicked.connect(self.next_q)
        self.commit_btn.clicked.connect(self.commit_q)
        self.finish_btn.clicked.connect(self.finish_all)
        self.update_ui()

    def update_ui(self):
        q = self.questions[self.cur_idx]
        self.header.setText(f"第{self.cur_idx+1}题 / 共{len(self.questions)}题\n{q['question']}")

        # 大表头（如“Security Capabilities”）
        col_group = q.get('col_names')[0].get('group', '')
        self.big_header.setText(col_group if col_group else "")

        # 表格设置
        rows, cols = len(q['row_names']), len(q['col_names'][0]['items'])
        self.table.clear()
        self.table.setRowCount(rows)
        self.table.setColumnCount(cols+1)  # +1 for row header
        h_headers = [q.get('row_header', '')] + q['col_names'][0]['items']
        self.table.setHorizontalHeaderLabels(h_headers)
        self.table.setVerticalHeaderLabels([""]*rows)

        # 加粗表头加底色
        font = QFont()
        font.setBold(True)
        self.table.horizontalHeader().setFont(font)
        self.table.verticalHeader().setFont(font)
        header_bg = QBrush(QColor(220, 230, 241))
        for c in range(self.table.columnCount()):
            item = self.table.horizontalHeaderItem(c)
            if item:
                item.setBackground(header_bg)

        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        # 填充第0列（行名/分组名）
        for i, name in enumerate(q['row_names']):
            item = QTableWidgetItem(name)
            item.setFont(font)
            item.setBackground(QColor("#f9f9f9"))
            item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.table.setItem(i, 0, item)

        # 填内容（checkbox 居中）
        for i in range(rows):
            for j in range(cols):
                if self.show_answer:
                    widget = create_centered_checkbox(q['answer'][i][j] == 1, enabled=False)
                else:
                    widget = create_centered_checkbox(self.user_answers[self.cur_idx][i][j], enabled=True, stateChangedSlot=self.save_check)
                self.table.setCellWidget(i, j+1, widget)  # j+1, 因为第0列是行名

        # 列宽全部跟最长单元格走（表头、行头、列头所有内容）
        max_width = 0
        font_normal = self.table.font()
        # 横向表头
        for c in range(self.table.columnCount()):
            h = self.table.horizontalHeaderItem(c)
            if h:
                max_width = max(max_width, get_text_pixel_width(h.text(), font))
        # 纵向行头（第0列内容）
        for r in range(self.table.rowCount()):
            v = self.table.item(r, 0)
            if v:
                max_width = max(max_width, get_text_pixel_width(v.text(), font))
        # 统一设置
        for c in range(self.table.columnCount()):
            self.table.setColumnWidth(c, max_width)

        # 按钮状态
        self.prev_btn.setEnabled(self.cur_idx > 0)
        self.next_btn.setEnabled(self.cur_idx < len(self.questions)-1)
        self.commit_btn.setEnabled(not self.show_answer)
        self.finish_btn.setEnabled(not self.show_answer)

    def save_check(self):
        q = self.questions[self.cur_idx]
        rows, cols = len(q['row_names']), len(q['col_names'][0]['items'])
        for i in range(rows):
            for j in range(cols):
                w = self.table.cellWidget(i, j+1)
                if w is not None:
                    cb = w.findChild(QCheckBox)
                    self.user_answers[self.cur_idx][i][j] = cb.isChecked()

    def prev_q(self):
        self.save_check()
        self.cur_idx = max(0, self.cur_idx - 1)
        self.show_answer = False
        self.update_ui()

    def next_q(self):
        self.save_check()
        self.cur_idx = min(len(self.questions) - 1, self.cur_idx + 1)
        self.show_answer = False
        self.update_ui()

    def commit_q(self):
        q = self.questions[self.cur_idx]
        u = self.user_answers[self.cur_idx]
        score, total, missed, over = self.grade(q['answer'], u)
        QMessageBox.information(self, "本题批改", f"本题得分：{score}/{total}\n漏选：{missed}，多选：{over}")
        self.show_answer = True
        self.update_ui()

    def finish_all(self):
        res = []
        total_score, total_count = 0, 0
        for idx, q in enumerate(self.questions):
            u = self.user_answers[idx]
            score, total, missed, over = self.grade(q['answer'], u)
            res.append(f"第{idx+1}题：得分{score}/{total}（漏{missed}，多{over}）")
            total_score += score
            total_count += total
        QMessageBox.information(self, "交卷结果", f"总分：{total_score}/{total_count}\n\n" + "\n".join(res))
        self.show_answer = True
        self.update_ui()

    @staticmethod
    def grade(ans, user):
        total = 0
        correct = 0
        missed = 0
        over = 0
        for i in range(len(ans)):
            for j in range(len(ans[0])):
                if ans[i][j]:
                    total += 1
                    if user[i][j]:
                        correct += 1
                    else:
                        missed += 1
                else:
                    if user[i][j]:
                        over += 1
        return correct, total, missed, over

if __name__ == '__main__':
    app = QApplication(sys.argv)
    with open('questions.json', encoding='utf-8') as f:
        questions = json.load(f)
    win = CrossTableQuiz(questions)
    win.show()
    sys.exit(app.exec_())
