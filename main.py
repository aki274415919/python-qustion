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

        # 判题高亮（show_answer为True，且cross_table）
        if self.show_answer and q["type"] == "cross_table":
            self.cur_widget.set_review_mode(q["answer"], self.user_answers[self.cur_idx])

    def save_check(self, *args, **kwargs):
        q = self.questions[self.cur_idx]
        if q["type"] == "cross_table":
            # ✅ 修复点：直接调用 widget 内部提供的恢复顺序答案方法
            self.user_answers[self.cur_idx] = self.cur_widget.get_current_answer()
        elif q["type"] == "single_choice":
            widget = self.cur_widget
            selected = widget.bg.checkedId()
            self.user_answers[self.cur_idx] = selected
        elif q["type"] == "multi_choice":
            widget = self.cur_widget
            self.user_answers[self.cur_idx] = [cb.isChecked() for cb in widget.checkboxes]
        elif q["type"] == "drag_image":
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
            if score == total and missed == 0 and over == 0:
                msg = "🎉 全部选对！"
            elif score == 0:
                msg = "❌ 全部做错"
            else:
                msg_list = []
                if score > 0:
                    msg_list.append(f"选对：{score}")
                if missed > 0:
                    msg_list.append(f"漏选：{missed}")
                if over > 0:
                    msg_list.append(f"多选：{over}")
                msg = ",".join(msg_list)
            QMessageBox.information(self, "本题批改", msg)
            self.show_answer = True
            self.update_ui()
        elif q["type"] == "single_choice":
            score = 1 if user == q["answer"] else 0
            msg = "🎉 答对了！" if score else "❌ 答错了！"
            QMessageBox.information(self, "本题批改", msg)
            self.show_answer = True
            self.update_ui()
        elif q["type"] == "multi_choice":
            ans_set = set(q["answer"])
            user_set = set(idx for idx, checked in enumerate(user) if checked)
            correct = len(ans_set & user_set)
            missed = len(ans_set - user_set)
            over = len(user_set - ans_set)
            if correct == len(ans_set) and missed == 0 and over == 0:
                msg = "🎉 全部选对！"
            elif correct == 0:
                msg = "❌ 全部做错"
            else:
                msg_list = []
                if correct > 0:
                    msg_list.append(f"选对：{correct}")
                if missed > 0:
                    msg_list.append(f"漏选：{missed}")
                if over > 0:
                    msg_list.append(f"多选：{over}")
                msg = ",".join(msg_list)
            QMessageBox.information(self, "本题批改", msg)
            self.show_answer = True
            self.update_ui()
        elif q["type"] == "drag_image":
            QMessageBox.information(self, "本题批改", f"拖图题批改功能开发中~")
            self.show_answer = True
            self.update_ui()


    def finish_all(self):
        total_q = len(self.questions)
        correct_q = 0
        wrong_detail = []
        for idx, q in enumerate(self.questions):
            user = self.user_answers[idx]
            if q["type"] == "cross_table":
                score, total, missed, over = self.grade(q['answer'], user)
                if score == total and missed == 0 and over == 0:
                    correct_q += 1
                else:
                    wrong_detail.append(f"第{idx+1}题")
            elif q["type"] == "single_choice":
                if user == q["answer"]:
                    correct_q += 1
                else:
                    wrong_detail.append(f"第{idx+1}题")
            elif q["type"] == "multi_choice":
                ans_set = set(q["answer"])
                user_set = set(idx for idx, checked in enumerate(user) if checked)
                correct = len(ans_set & user_set)
                missed = len(ans_set - user_set)
                over = len(user_set - ans_set)
                if correct == len(ans_set) and missed == 0 and over == 0:
                    correct_q += 1
                else:
                    wrong_detail.append(f"第{idx+1}题")
            elif q["type"] == "drag_image":
                # 这里按全错处理，后续补充
                wrong_detail.append(f"第{idx+1}题")
        # 总分、合格判断
        score = int(correct_q / total_q * 1000)
        result = "✅ 合格" if score >= 800 else "❌ 不合格"
        msg = f"总分：{score}/1000\n\n正确题数：{correct_q}/{total_q}\n{result}"
        if wrong_detail:
            msg += "\n\n错题：" + ",".join(wrong_detail)
        QMessageBox.information(self, "交卷结果", msg)
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
