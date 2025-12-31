from PyQt6.QtWidgets import QPushButton, QStyleOptionButton
from PyQt6.QtCore import QRect, QSize, Qt
from PyQt6.QtGui import QFontMetrics, QPainter, QPalette

class WrappingButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        
    def sizeHint(self):
        # Calculate size hint based on text and font, allowing for word wrap
        metrics = QFontMetrics(self.font())
        # Use a large height to allow for wrapping calculation
        rect = metrics.boundingRect(QRect(0, 0, self.width() if self.width() > 0 else 100, 5000), 
                                    Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignCenter, self.text())
        return QSize(rect.width() + 10, rect.height() + 10) # Add padding

    def heightForWidth(self, width):
        # Calculate height needed for given width, allowing for word wrap
        metrics = QFontMetrics(self.font())
        rect = metrics.boundingRect(QRect(0, 0, width - 10, 5000), # Subtract padding
                                    Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignCenter, self.text())
        return rect.height() + 10 # Add padding

    def paintEvent(self, event):
        # Draw the button background and frame
        super().paintEvent(event)
        
        painter = QPainter(self)
        
        # Get current text color from stylesheet or palette
        opt = QStyleOptionButton()
        self.initStyleOption(opt)
        text_color = opt.palette.color(QPalette.ColorRole.ButtonText)
        
        painter.setPen(text_color)
        painter.setFont(self.font())
        
        # Draw text with word wrap
        rect = self.contentsRect().adjusted(5, 5, -5, -5)
        painter.drawText(rect, Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignCenter, self.text())
