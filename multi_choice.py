from PyQt5.QtWidgets import QWidget, QVBoxLayout, QCheckBox

class MultiChoiceWidget(QWidget):
    def __init__(self, qobj, answer_data, show_answer, save_callback):
        super().__init__()
        self.qobj = qobj
        self.save_callback = save_callback
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.checkboxes = []
        for idx, opt in enumerate(qobj["options"]):
            cb = QCheckBox(opt)
            cb.setChecked(answer_data[idx])
            cb.setEnabled(not show_answer)
            cb.stateChanged.connect(save_callback)
            self.checkboxes.append(cb)
            layout.addWidget(cb)
        # 显示正确答案提示（答题后）
        if show_answer:
            for idx in qobj["answer"]:
                self.checkboxes[idx].setStyleSheet("color: green; font-weight: bold;")
