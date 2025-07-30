from PyQt5.QtWidgets import QWidget, QVBoxLayout, QRadioButton, QButtonGroup

class SingleChoiceWidget(QWidget):
    def __init__(self, qobj, answer_data, show_answer, save_callback):
        super().__init__()
        self.qobj = qobj
        self.save_callback = save_callback
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.options = []
        self.bg = QButtonGroup(self)
        self.bg.setExclusive(True)
        for idx, opt in enumerate(qobj["options"]):
            rb = QRadioButton(opt)
            rb.setChecked(answer_data == idx)
            rb.setEnabled(not show_answer)
            rb.toggled.connect(self.save_callback)
            self.bg.addButton(rb, idx)
            self.options.append(rb)
            layout.addWidget(rb)
        if show_answer and answer_data != qobj["answer"]:
            self.options[qobj["answer"]].setStyleSheet("color: green; font-weight: bold;")
