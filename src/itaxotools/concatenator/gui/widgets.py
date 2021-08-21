# -----------------------------------------------------------------------------
# ConcatenatorQt - GUI for Concatenator
# Copyright (C) 2021  Patmanidis Stefanos
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# -----------------------------------------------------------------------------

"""Custom widgets for Concatenator"""

from PySide6 import QtCore
from PySide6 import QtWidgets
from PySide6 import QtGui

from enum import Enum, auto
from dataclasses import dataclass, field

from . import indicators


@dataclass
class Step():
    text: str = ''
    weight: int = 1
    indicator: indicators.AbstractIndicator = indicators.Pending
    width: int = field(repr=False, default=0)


class StepProgressBar(QtWidgets.QWidget):

    def __init__(self, steps=[], font=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Minimum)
        self.textPadding = 15
        self.verticalPadding = 10
        self.steps = []
        self.font = font if font is not None else QtGui.QGuiApplication.font()
        self.setSteps(steps)
        self.setStyleSheet("background: cyan;")

    @property
    def font(self):
        return self._font

    @font.setter
    def font(self, font):
        self._font = font
        self.metrics = QtGui.QFontMetrics(self.font)
        for step in self.steps:
            self.updateStepWidth(step)

    def updateStepWidth(self, step):
        step.width = self.metrics.horizontalAdvance(step.text)

    def addStep(self, *args, **kwargs):
        step = Step(*args, **kwargs)
        self.updateStepWidth(step)
        self.steps.append(step)

    def setSteps(self, strings):
        self.steps = []
        for string in strings:
            self.addStep(string)

    def paintEvent(self, event):
        painter = QtGui.QPainter()
        painter.begin(self)
        self.draw(painter)
        painter.end()

    def draw(self, painter):


        width = self.size().width()
        height = self.size().height()

        painter.setPen(QtGui.QColor(255, 255, 255))
        painter.setBrush(QtGui.QColor(255, 255, 184))
        painter.drawRect(0, 0, width, height)

        totalStepWeight = sum(step.weight for step in self.steps[:-1])
        extraWidth = width - self.minimumWidth()
        extraHeight = height - self.minimumHeight()

        cursor = 0
        stepXs = []
        for step in self.steps:
            cursor += self.textPadding
            cursor += step.width / 2
            stepXs.append(cursor)
            cursor += step.width / 2
            cursor += (step.weight / totalStepWeight) * extraWidth

        textY = extraHeight / 2
        textY += self.verticalPadding / 2
        textY += self.metrics.height()
        lineY = height - extraHeight / 2
        lineY -= self.verticalPadding / 2
        lineY -= indicators.AbstractIndicator.radius /2

        self.drawStepTexts(painter, stepXs, textY)
        self.drawStepLines(painter, stepXs, lineY)

    def drawStepTexts(self, painter, stepXs, textY):
        painter.setFont(self.font)
        palette = QtGui.QGuiApplication.palette()
        painter.setPen(palette.color(QtGui.QPalette.Shadow))
        for count, step in enumerate(self.steps):
            self.drawStepText(painter, step, stepXs[count], textY)

    def drawStepText(self, painter, step, x, y):
        # painter.save()
        width = painter.fontMetrics().horizontalAdvance(step.text)
        painter.drawText(x - width/2, y, step.text)
        # painter.restore()

    def drawStepLines(self, painter, stepXs, lineY):
        palette = QtGui.QGuiApplication.palette()
        color = palette.color(QtGui.QPalette.Shadow)
        pen = QtGui.QPen(color, 2, QtCore.Qt.SolidLine)
        painter.setPen(pen)

        pairs = zip(self.steps[:-1], self.steps[1:])
        for count, (step1, step2) in enumerate(pairs):
            x1 = stepXs[count] + step1.indicator.radius / 2
            x2 = stepXs[count + 1] - step2.indicator.radius / 2
            painter.drawLine(x1, lineY, x2, lineY)

    def minimumWidth(self):
        width = sum(step.width for step in self.steps)
        width += self.textPadding * (len(self.steps) + 1)
        return width

    def minimumHeight(self):
        height = self.metrics.height()
        height = indicators.AbstractIndicator.radius
        height += 3 * self.verticalPadding
        return height

    def sizeHint(self):
        return QtCore.QSize(self.minimumWidth(), self.minimumHeight())
