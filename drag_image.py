from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel

class DragImageWidget(QWidget):
    def __init__(self, qobj, answer_data, show_answer, save_callback):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)
        label = QLabel(f"【拖图题】{qobj.get('question', '')}\n(后续实现图片和拖放功能)")
        label.setStyleSheet("color:blue;font-size:18px;")
        layout.addWidget(label)
