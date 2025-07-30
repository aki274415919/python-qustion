import sys
import json
import random
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox, QCheckBox
)

from cross_table import CrossTableWidget
from single_choice import SingleChoiceWidget
from multi_choice import MultiChoiceWidget
from drag_image import DragImageWidget   # 拖图题

class QuizMain(QWidget):
    def __init__(self, questions):
        super().__init__()
        self.setWindowTitle("多题型练习考试系统")
        self.resize(1600, 900)
        self.questions = random.sample(questions, len(questions))
        self.user_answers = []
        for q in self.questions:
            if q["type"] == "cross_table":
                ans = []
                for i in range(len(q['row_names'])):
                    ans.append([False]*len(q['col_names'][0]['items']))
                self.user_answers.append(ans)
            elif q["type"] == "single_choice":
                self.user_answers.append(None)
            elif q["type"] == "multi_choice":
                self.user_answers.append([False] * len(q["options"]))
            elif q["type"] == "drag_image":
                self.user_answers.append(None)  # 或 []，实际交互后续细化
        self.cur_idx = 0
        self.show_answer = False

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.header = QLabel()
        self.header.setWordWrap(True)
        self.layout.addWidget(self.header)

        self.widget_area = QVBoxLayout()
        self.layout.addLayout(self.widget_area)
        self.cur_widget = None

        # 按钮
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

    def clear_widget_area(self):
        while self.widget_area.count():
            child = self.widget_area.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def update_ui(self):
        q = self.questions[self.cur_idx]
        self.header.setText(f"第{self.cur_idx+1}题 / 共{len(self.questions)}题\n{q['question']}")

        self.clear_widget_area()
        # 题型调度
        if q["type"] == "cross_table":
            widget = CrossTableWidget(q, self.user_answers[self.cur_idx], self.show_answer, self.save_check)
        elif q["type"] == "single_choice":
            widget = SingleChoiceWidget(q, self.user_answers[self.cur_idx], self.show_answer, self.save_check)
        elif q["type"] == "multi_choice":
            widget = MultiChoiceWidget(q, self.user_answers[self.cur_idx], self.show_answer, self.save_check)
        elif q["type"] == "drag_image":
            widget = DragImageWidget(q, self.user_answers[self.cur_idx], self.show_answer, self.save_check)
        else:
            widget = QLabel("未知题型")
        self.cur_widget = widget
        self.widget_area.addWidget(widget)

        self.prev_btn.setEnabled(self.cur_idx > 0)
        self.next_btn.setEnabled(self.cur_idx < len(self.questions)-1)
        self.commit_btn.setEnabled(not self.show_answer)
        self.finish_btn.setEnabled(not self.show_answer)

    def save_check(self):
        q = self.questions[self.cur_idx]
        if q["type"] == "cross_table":
            widget = self.cur_widget.table
            rows, cols = widget.rowCount(), widget.columnCount()-1
            for i in range(rows):
                for j in range(cols):
                    w = widget.cellWidget(i, j+1)
                    if w is not None:
                        cb = w.findChild(QCheckBox)
                        self.user_answers[self.cur_idx][i][j] = cb.isChecked()
        elif q["type"] == "single_choice":
            widget = self.cur_widget
            selected = widget.bg.checkedId()
            self.user_answers[self.cur_idx] = selected
        elif q["type"] == "multi_choice":
            widget = self.cur_widget
            self.user_answers[self.cur_idx] = [cb.isChecked() for cb in widget.checkboxes]
        elif q["type"] == "drag_image":
            # 拖图题保存交互，后续实现，现在不处理
            pass

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
        user = self.user_answers[self.cur_idx]
        if q["type"] == "cross_table":
            score, total, missed, over = self.grade(q['answer'], user)
            QMessageBox.information(self, "本题批改", f"本题得分：{score}/{total}\n漏选：{missed}，多选：{over}")
        elif q["type"] == "single_choice":
            score = 1 if user == q["answer"] else 0
            QMessageBox.information(self, "本题批改", f"本题得分：{score}/1")
        elif q["type"] == "multi_choice":
            ans_set = set(q["answer"])
            user_set = set(idx for idx, checked in enumerate(user) if checked)
            correct = len(ans_set & user_set)
            missed = len(ans_set - user_set)
            over = len(user_set - ans_set)
            total = len(ans_set)
            QMessageBox.information(self, "本题批改", f"本题得分：{correct}/{total}\n漏选：{missed}，多选：{over}")
        elif q["type"] == "drag_image":
            QMessageBox.information(self, "本题批改", f"拖图题批改功能开发中~")
        self.show_answer = True
        self.update_ui()

    def finish_all(self):
        res = []
        total_score, total_count = 0, 0
        for idx, q in enumerate(self.questions):
            user = self.user_answers[idx]
            if q["type"] == "cross_table":
                score, total, missed, over = self.grade(q['answer'], user)
                res.append(f"第{idx+1}题：得分{score}/{total}（漏{missed}，多{over}）")
                total_score += score
                total_count += total
            elif q["type"] == "single_choice":
                score = 1 if user == q["answer"] else 0
                res.append(f"第{idx+1}题：得分{score}/1")
                total_score += score
                total_count += 1
            elif q["type"] == "multi_choice":
                ans_set = set(q["answer"])
                user_set = set(idx for idx, checked in enumerate(user) if checked)
                correct = len(ans_set & user_set)
                total = len(ans_set)
                res.append(f"第{idx+1}题：得分{correct}/{total}（漏{len(ans_set-user_set)}，多{len(user_set-ans_set)}）")
                total_score += correct
                total_count += total
            elif q["type"] == "drag_image":
                res.append(f"第{idx+1}题：拖图题批改暂未实现")
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
    win = QuizMain(questions)
    win.show()
    sys.exit(app.exec_())
