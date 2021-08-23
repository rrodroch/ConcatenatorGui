# -----------------------------------------------------------------------------
# StepProgressBar - A simple step progress widget for PySide6
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

"""StepProgressBar widget definition"""


from PySide6 import QtCore
from PySide6 import QtWidgets
from PySide6 import QtGui

from dataclasses import dataclass, field

from . import states
from . import palette


@palette.palette
class Palette():
    """Theme-aware three-color palette"""

    def bold(self):
        """For active parts"""
        qt_palette = QtGui.QGuiApplication.palette()
        color = qt_palette.color(QtGui.QPalette.Shadow)
        return color

    def base(self):
        """For inactive parts"""
        qt_palette = QtGui.QGuiApplication.palette()
        color = qt_palette.color(QtGui.QPalette.Dark)
        return color

    def weak(self):
        """For background parts"""
        qt_palette = QtGui.QGuiApplication.palette()
        color = qt_palette.color(QtGui.QPalette.Dark).lighter(140)
        return color


@dataclass
class Step():
    """
    Holds information for each step:
    - `text` will be visible on the bar
    - `weight` affects the length of the line after the step
    - `status` affects text and indicator style
    The following are used internally by StepProgressBar:
    - `width` is the minimum required for the text
    - `pos` holds the step horizontal position
    """
    text: str = ''
    weight: int = 1
    status: states.AbstractStatus = states.Pending
    width: int = field(repr=False, default=0)
    pos: int = field(repr=False, default=0)

    def drawText(self, painter, palette):
        self.status.drawText(painter, palette, self.text)

    def drawIndicator(self, painter, palette):
        self.status.drawIndicator(painter, palette)


class StepProgressBar(QtWidgets.QWidget):
    """
    Shows user progress in a series of steps towards a goal.
    The active step is highlighted as either active, ongoing or failed.

    Text font, color style and spacing are configurable.
    Ongoing status is animated.

    Usage example
    -------------
    import stepprogressbar
    stepProgressBar = stepprogressbar.StepProgressBar()
    stepProgressBar.addStep('a', 'A', 1)
    stepProgressBar.addStep('b', 'B', 2)
    stepProgressBar.addStep('c', 'C', 0)
    stepProgressBar.activateKey('b')
    stepProgressBar.setOngoing()
    """

    def __init__(self, steps=[], font=None, *args, **kwargs):
        """Steps and font may be set on construction"""
        super().__init__(*args, **kwargs)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Minimum)
        self.palette = Palette()
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.handleTimer)
        self.timerStep = 10
        self.textPadding = 20
        self.verticalPadding = 4
        self.indicatorPadding = 6
        self.steps = []
        self.keys = {}
        self.active = -1
        self.font = font if font is not None else QtGui.QGuiApplication.font()
        self.setSteps(steps)

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

    def addStep(self, key=None, text='', weight=1):
        """Steps may be added along with a key for faster reference."""
        step = Step(text=text, weight=weight)
        self.updateStepWidth(step)
        self.steps.append(step)
        if key is not None:
            self.keys[key] = len(self.steps) - 1

    def setSteps(self, strings):
        self.steps = []
        self.keys = {}
        for string in strings:
            self.addStep(string)

    def activateKey(self, key):
        """Activates the Step identified by given key"""
        index = self.keys[key] if key is not None else -1
        self.activateIndex(index)

    def activateIndex(self, index):
        """Activates the Step identified by given index"""
        index = min(max(index, -1), len(self.steps))
        self.steps[-1].status = states.Final
        for i in range(0, index):
            self.steps[i].status = states.Complete
        for i in range(index + 1, len(self.steps) - 1):
            self.steps[i].status = states.Pending
        self.active = index
        self.setActive()
        self.repaint()

    def activateNext(self):
        self.activateIndex(self.active + 1)

    def activatePrevious(self):
        self.activateIndex(self.active - 1)

    def setStatus(self, status=states.Active):
        index = self.active
        if index >= 0 and index < len(self.steps):
            self.steps[index].status = status
        self.timer.stop()

    def setActive(self):
        """Current step is marked as Active"""
        self.setStatus(states.Active)
        self.timer.stop()

    def setFailed(self):
        """Current step is marked as Failed"""
        self.setStatus(states.Failed)
        self.timer.stop()

    def setOngoing(self):
        """Current step is marked as Ongoing (animated)"""
        self.setStatus(states.Ongoing)
        self.timer.start(self.timerStep)

    def handleTimer(self):
        self.repaint()

    def paintEvent(self, event):
        painter = QtGui.QPainter()
        painter.begin(self)
        self.draw(painter)
        painter.end()

    def draw(self, painter):

        width = self.size().width()
        height = self.size().height()

        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        totalStepWeight = sum(step.weight for step in self.steps[:-1])
        extraWidth = width - self.minimumWidth()
        extraHeight = height - self.minimumHeight()

        cursor = 0
        for step in self.steps:
            cursor += self.textPadding
            cursor += step.width / 2
            step.pos = int(cursor)
            cursor += step.width / 2
            cursor += (step.weight / totalStepWeight) * extraWidth

        textY = extraHeight / 2
        textY += self.verticalPadding
        textY += self.metrics.ascent()
        textY = int(textY)
        lineY = height - extraHeight / 2
        lineY -= self.verticalPadding
        lineY -= states.AbstractStatus.indicatorRadius
        lineY = int(lineY)

        painter.setBrush(QtCore.Qt.NoBrush)
        painter.setPen(QtCore.Qt.NoPen)
        painter.setFont(self.font)

        self.drawStepTexts(painter, textY)
        self.drawStepIndicators(painter, lineY)
        self.drawStepLines(painter, lineY)

    def drawStepTexts(self, painter, textY):
        for step in self.steps:
            painter.save()
            point = QtCore.QPoint(step.pos, textY)
            painter.translate(point)
            step.drawText(painter, self.palette)
            painter.restore()

    def drawStepIndicators(self, painter, lineY):
        for step in self.steps:
            painter.save()
            point = QtCore.QPoint(step.pos, lineY)
            painter.translate(point)
            step.drawIndicator(painter, self.palette)
            painter.restore()

    def drawStepLines(self, painter, lineY):
        x = self.steps[self.active].pos
        for step1, step2 in zip(self.steps[:-1], self.steps[1:]):
            x1 = step1.pos
            x1 += step1.status.indicatorRadius
            x1 += self.indicatorPadding
            x2 = step2.pos
            x2 -= step2.status.indicatorRadius
            x2 -= self.indicatorPadding
            self.drawStepLine(painter, x2 < x, x1, x2, lineY)

    def drawStepLine(self, painter, isComplete, x1, x2, y):
        if isComplete:
            color = self.palette.bold
            pen = QtGui.QPen(color, 2, QtCore.Qt.SolidLine)
            painter.setPen(pen)
        else:
            color = self.palette.base
            pen = QtGui.QPen(color, 1, QtCore.Qt.SolidLine)
            painter.setPen(pen)
        painter.drawLine(x1, y, x2, y)

    def minimumWidth(self):
        width = sum(step.width for step in self.steps)
        width += self.textPadding * (len(self.steps) + 1)
        return width

    def minimumHeight(self):
        height = self.metrics.height()
        height += states.AbstractStatus.indicatorRadius * 2
        height += 3 * self.verticalPadding
        return height

    def sizeHint(self):
        return QtCore.QSize(self.minimumWidth(), self.minimumHeight())
