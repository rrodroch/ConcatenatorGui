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

"""StepFilter"""

from PySide6 import QtCore
from PySide6 import QtWidgets
from PySide6 import QtGui

from lorem_text import lorem
from random import randint

from itaxotools import common
import itaxotools.common.widgets
import itaxotools.common.resources # noqa

from .. import widgets
from .. import step_state_machine as ssm


class ItemDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, view, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.view = view

    def createEditor(self, parent, option, index):
        if index.column() == 0:
            return super().createEditor(parent, option, index)
        else:
            item = self.view.itemFromIndex(index)
            self.view.itemActivated.emit(item, index.column())
            return None


class FilterItem(widgets.WidgetItem):
    fields = [
        'name',
        'action',
        'samples',
        'nucleotides',
        'missing',
        'uniform',
        ]
    actions = {
        'Delete': 'deleted',
        'Rename': 'renamed',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFlags(QtCore.Qt.ItemIsSelectable |
                      QtCore.Qt.ItemIsEnabled |
                      QtCore.Qt.ItemIsEditable |
                      QtCore.Qt.ItemNeverHasChildren)
        self.file = None
        self.name = lorem.words(randint(2, 6)).replace(' ', '_')
        self.name_original = self.name
        self.action = '-'
        self.samples = randint(6, 300)
        self.nucleotides = randint(200, 3000000)
        self.uniform = ['Yes', 'No'][randint(0, 1)]
        self.missing = randint(0, 9999) / 10000

    def setData(self, column, role, value):
        if role == QtCore.Qt.ItemDataRole.EditRole:
            if column > 0:
                raise RuntimeError(f'Cannot edit FilterItem column: {column}')
            if not value:
                return False
            if value != self.name:
                self.rename(value)
        return super().setData(column, role, value)

    def rename(self, value):
        self.name = value
        if self.name != self.name_original:
            self.setAction('Rename')
            self.setBold(True)
        else:
            self.setAction('-')
            self.setBold(False)
        self.setStrikeOut(False)

    def delete(self):
        self.setAction('Delete')
        self.setStrikeOut(True)
        self.setBold(True)

    def clear(self):
        self.name = self.name_original
        self.setAction('-')
        self.setStrikeOut(False)
        self.setBold(False)

    def setAction(self, value):
        signal = self.treeWidget().signalSummaryUpdate
        if self.action != value:
            if self.action in self.actions:
                signal.emit(self.actions[self.action], -1)
            if value in self.actions:
                signal.emit(self.actions[value], 1)
        self.action = value

    def setBold(self, value):
        font = self.font(0)
        font.setBold(value)
        self.setFont(0, font)

    def setStrikeOut(self, value):
        font = self.font(0)
        font.setStrikeOut(value)
        self.setFont(0, font)


class TreeWidget(widgets.TreeWidget):
    signalSummaryUpdate = QtCore.Signal(str, int)


class DataObject(object):
    pass


class StepFilter(ssm.StepState):

    title = 'Filter Character Sets'
    description = 'Rename or delete character sets'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = DataObject()
        self.add_dummy_contents()

    def add_dummy_contents(self):
        count = randint(50, 301)
        items = []
        for i in range(0, count):
            items.append(FilterItem())
        self.view.addTopLevelItems(items)
        self.view.resizeColumnsToContents()
        self.sets.setValue(count)

    def work(self):
        time = randint(500, 2000)
        for i in range(0, int(time/10)):
            QtCore.QThread.msleep(10)
            self.worker.check()

    def draw(self):
        widget = QtWidgets.QWidget()

        text = (
            'Select multiple sets by drag-and-click or '
            'by clicking while holding Ctrl/Shift. '
            'Sort by column by clicking on the headers.')
        label = QtWidgets.QLabel(text)

        frame = self.draw_frame()

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(frame, 1)
        layout.setSpacing(24)
        layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(layout)

        return widget

    def draw_summary(self):
        sets = widgets.InfoLabel('Total Sets')
        renamed = widgets.InfoLabel('Renamed', 0)
        deleted = widgets.InfoLabel('Deleted', 0)

        sets.setToolTip('Total number of character sets.')
        renamed.setToolTip('Character sets pending renaming.')
        deleted.setToolTip('Character sets pending deletion.')

        summary = QtWidgets.QHBoxLayout()
        summary.addWidget(sets)
        summary.addWidget(renamed)
        summary.addWidget(deleted)
        summary.addStretch(1)
        summary.setSpacing(24)
        summary.setContentsMargins(4, 0, 4, 0)

        self.sets = sets
        self.renamed = renamed
        self.deleted = deleted

        return summary

    def draw_frame(self):
        frame = common.widgets.Frame()

        view = TreeWidget()
        view.setItemDelegate(ItemDelegate(view))
        view.signalSummaryUpdate.connect(self.handleSummaryUpdate)
        view.itemActivated.connect(self.handleActivated)
        view.setIndentation(0)
        view.setColumnCount(6, 2)
        view.setHeaderLabels([
            'Name', 'Action', 'Samples',
            'Nucleotides', 'Missing', 'Uniform'])

        headerItem = view.headerItem()
        headerItem.setToolTip(0, 'Character set name')
        headerItem.setToolTip(1, 'Pending action')
        headerItem.setToolTip(2, 'Total number of sequences')
        headerItem.setToolTip(3, 'Total number of nucleotide characters')
        headerItem.setToolTip(4, 'Proportion of missing data')
        headerItem.setToolTip(5, 'Are all sequences of the same length?')

        rename = common.widgets.PushButton('Rename', onclick=self.handleRename)
        delete = common.widgets.PushButton('Delete', onclick=self.handleDelete)
        clear = common.widgets.PushButton('Clear', onclick=self.handleClear)

        QtGui.QShortcut(QtGui.QKeySequence('F2'), view, self.handleRename)
        QtGui.QShortcut(QtGui.QKeySequence.Delete, view, self.handleDelete)
        QtGui.QShortcut(QtGui.QKeySequence.Undo, view, self.handleClear)

        search = widgets.ViewSearchWidget(self, view)

        controls = QtWidgets.QHBoxLayout()
        controls.addWidget(rename)
        controls.addWidget(delete)
        controls.addWidget(clear)
        controls.addStretch(1)
        controls.addWidget(search)
        controls.setSpacing(8)
        controls.setContentsMargins(0, 0, 0, 0)

        summary = self.draw_summary()

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(controls)
        layout.addWidget(view, 1)
        layout.addLayout(summary)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 12)
        frame.setLayout(layout)

        self.view = view
        self.frame = frame
        self.delete = delete
        self.search = search

        return frame

    def handleRename(self, checked=False):
        index = self.view.currentIndex().siblingAtColumn(0)
        self.view.edit(index)
        self.view.scrollToItem(self.view.itemFromIndex(index))

    def handleDelete(self, checked=False):
        for item in self.view.selectedItems():
            item.delete()
        self.view.scrollToItem(item)

    def handleClear(self, checked=False):
        for item in self.view.selectedItems():
            item.clear()
        self.view.scrollToItem(item)

    def handleActivated(self, item, column):
        index = self.view.indexFromItem(item).siblingAtColumn(0)
        self.view.edit(index)

    def handleSummaryUpdate(self, field, change):
        item = getattr(self, field)
        item.setValue(item.value + change)