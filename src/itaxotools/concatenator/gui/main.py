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

"""Long module description"""

from PySide6 import QtCore
from PySide6 import QtWidgets
from PySide6 import QtStateMachine
from PySide6 import QtGui

import tempfile
import pathlib
import shutil
import sys

from itaxotools.common import utility
from itaxotools.common import widgets
from itaxotools.common import resources
from itaxotools.common import io

from . import StepProgressBar


try:
    import importlib.resources
    _resource_path = importlib.resources.files(resources)
    _package_path = importlib.resources.files(__package__)
except Exception:
    if hasattr(sys, '_MEIPASS'):
        _resource_path = (pathlib.Path(sys._MEIPASS) /
            'itaxotools' / 'common' / 'resources')
        _package_path = (pathlib.Path(sys._MEIPASS) /
            'itaxotools' / 'fasttreepy' / 'gui')
    else:
        import os
        _resource_path = pathlib.Path(os.path.dirname(resources.__file__))
        _package_path = pathlib.Path(os.path.dirname(__file__))

def get_resource(path):
    return str(_resource_path / path)
def get_icon(path):
    return str(_resource_path / 'icons/svg' / path)


class Main(widgets.ToolDialog):
    """Main window, handles everything"""

    def __init__(self, parent=None, init=None):
        super(Main, self).__init__(parent)

        self.title = 'Concatenator'
        self._temp = None
        self.temp = None

        icon = QtGui.QIcon(get_resource('logos/ico/concatenator.ico'))
        self.setWindowIcon(icon)
        self.setWindowTitle(self.title)
        self.resize(840, 540)

        self.process = None
        self.machine = None
        self.skin()
        self.draw()
        self.act()
        self.cog()

        if init is not None:
            self.machine.started.connect(init)

    def __getstate__(self):
        return (None,)

    def __setstate__(self, state):
        pass

    def cog(self):
        """Initialize state machine"""

        self.machine = QtStateMachine.QStateMachine(self)
        # self.machine.start()

    def skin(self):
        """Configure widget appearance"""
        color = {
            'white':  '#ffffff',
            'light':  '#eff1ee',
            'beige':  '#e1e0de',
            'gray':   '#abaaa8',
            'iron':   '#8b8d8a',
            'black':  '#454241',
            'red':    '#ee4e5f',
            'pink':   '#eb9597',
            'orange': '#eb6a4a',
            'brown':  '#655c5d',
            'green':  '#00ff00',
            }
        # using green for debugging
        palette = QtGui.QGuiApplication.palette()
        scheme = {
            QtGui.QPalette.Active: {
                QtGui.QPalette.Window: 'light',
                QtGui.QPalette.WindowText: 'black',
                QtGui.QPalette.Base: 'white',
                QtGui.QPalette.AlternateBase: 'light',
                QtGui.QPalette.PlaceholderText: 'brown',
                QtGui.QPalette.Text: 'black',
                QtGui.QPalette.Button: 'light',
                QtGui.QPalette.ButtonText: 'black',
                QtGui.QPalette.Light: 'white',
                QtGui.QPalette.Midlight: 'beige',
                QtGui.QPalette.Mid: 'gray',
                QtGui.QPalette.Dark: 'iron',
                QtGui.QPalette.Shadow: 'brown',
                QtGui.QPalette.Highlight: 'red',
                QtGui.QPalette.HighlightedText: 'white',
                # These work on linux only?
                QtGui.QPalette.ToolTipBase: 'beige',
                QtGui.QPalette.ToolTipText: 'brown',
                # These seem bugged anyway
                QtGui.QPalette.BrightText: 'green',
                QtGui.QPalette.Link: 'red',
                QtGui.QPalette.LinkVisited: 'pink',
                },
            QtGui.QPalette.Disabled: {
                QtGui.QPalette.Window: 'light',
                QtGui.QPalette.WindowText: 'iron',
                QtGui.QPalette.Base: 'white',
                QtGui.QPalette.AlternateBase: 'light',
                QtGui.QPalette.PlaceholderText: 'green',
                QtGui.QPalette.Text: 'iron',
                QtGui.QPalette.Button: 'light',
                QtGui.QPalette.ButtonText: 'gray',
                QtGui.QPalette.Light: 'white',
                QtGui.QPalette.Midlight: 'beige',
                QtGui.QPalette.Mid: 'gray',
                QtGui.QPalette.Dark: 'iron',
                QtGui.QPalette.Shadow: 'brown',
                QtGui.QPalette.Highlight: 'pink',
                QtGui.QPalette.HighlightedText: 'white',
                # These seem bugged anyway
                QtGui.QPalette.BrightText: 'green',
                QtGui.QPalette.ToolTipBase: 'green',
                QtGui.QPalette.ToolTipText: 'green',
                QtGui.QPalette.Link: 'green',
                QtGui.QPalette.LinkVisited: 'green',
                },
            }
        scheme[QtGui.QPalette.Inactive] = scheme[QtGui.QPalette.Active]
        for group in scheme:
            for role in scheme[group]:
                palette.setColor(group, role,
                    QtGui.QColor(color[scheme[group][role]]))
        QtGui.QGuiApplication.setPalette(palette)

        self.colormap = {
            widgets.VectorIcon.Normal: {
                '#000': color['black'],
                '#f00': color['red'],
                },
            widgets.VectorIcon.Disabled: {
                '#000': color['gray'],
                '#f00': color['orange'],
                },
            }
        self.colormap_icon = {
            '#000': color['black'],
            '#f00': color['red'],
            '#f88': color['pink'],
            }
        self.colormap_icon_light = {
            '#000': color['iron'],
            '#ff0000': color['red'],
            '#ffa500': color['pink'],
            }

    def draw(self):
        """Draw all widgets"""

        self.header = widgets.Header()
        self.header.logoTool = widgets.VectorPixmap(
            get_resource('logos/svg/concatenator.svg'),
            size=QtCore.QSize(48, 48), colormap=self.colormap_icon)
        self.header.logoProject = QtGui.QPixmap(
            get_resource('logos/png/itaxotools-micrologo.png'))
        self.header.title = 'Concatenator'
        self.header.citation = (
            'by V. Kharchev and S. Patmanidis'
            )
        self.header.description = (
            'Convert between sequence file formats'
        )

        from .StepProgressBar import states
        self.stepProgressBar = StepProgressBar.StepProgressBar()
        font = QtGui.QGuiApplication.font()
        font.setPointSize(9)
        font.setLetterSpacing(QtGui.QFont.AbsoluteSpacing, 1)
        font.setBold(True)
        self.stepProgressBar.font = font
        self.stepProgressBar.addStep('input', 'Input Files', 1)
        self.stepProgressBar.addStep('align', 'Sequence Alignment', 3)
        self.stepProgressBar.addStep('codons', 'Codon Positions', 2)
        self.stepProgressBar.addStep('filters', 'Filters')
        self.stepProgressBar.addStep('export', 'Export')
        self.stepProgressBar.activateKey('filters')
        self.stepProgressBar.activatePrevious()
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.stepProgressBar)
        layout.setContentsMargins(0, 8, 0, 8)
        # self.header.widget.setStyleSheet("background: magenta;")
        self.header.widget.setLayout(layout)

        self.body = QtWidgets.QHBoxLayout()
        self.body.addSpacing(4)
        # self.body.setContentsMargins(8, 4, 8, 4)

        self.footer = QtWidgets.QLabel()
        self.footer.setStyleSheet("""
            QLabel {
                color: palette(Shadow);
                font-size: 12px;
                background: palette(Window);
                border-top: 1px solid palette(Mid);
                padding: 6px 8px 8px 8px;
                }
            QLabel:disabled {
                color: palette(Mid);
                background: palette(Window);
                border: 1px solid palette(Mid);
                }
            """)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.header, 0)
        layout.addSpacing(8)
        layout.addLayout(self.body, 1)
        layout.addSpacing(8)
        layout.addWidget(self.footer, 0)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def act(self):
        """Populate dialog actions"""
        self.action = {}
