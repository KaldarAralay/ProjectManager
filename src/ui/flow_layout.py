"""Flow layout that wraps widgets like text."""

from PyQt6.QtWidgets import QLayout, QWidgetItem, QSizePolicy
from PyQt6.QtCore import Qt, QRect, QSize, QPoint


class FlowLayout(QLayout):
    """A layout that arranges widgets in a flowing grid, wrapping to new rows."""

    def __init__(self, parent=None, margin=0, spacing=-1):
        """Initialize the flow layout.

        Args:
            parent: Parent widget.
            margin: Layout margin.
            spacing: Spacing between items.
        """
        super().__init__(parent)
        self._item_list = []
        self._h_spacing = spacing
        self._v_spacing = spacing

        if margin >= 0:
            self.setContentsMargins(margin, margin, margin, margin)

    def __del__(self):
        """Clean up items."""
        while self.count():
            self.takeAt(0)

    def addItem(self, item):
        """Add an item to the layout."""
        self._item_list.append(item)

    def horizontalSpacing(self):
        """Get horizontal spacing."""
        if self._h_spacing >= 0:
            return self._h_spacing
        return self._smart_spacing(QSizePolicy.ControlType.PushButton)

    def verticalSpacing(self):
        """Get vertical spacing."""
        if self._v_spacing >= 0:
            return self._v_spacing
        return self._smart_spacing(QSizePolicy.ControlType.PushButton)

    def setSpacing(self, spacing):
        """Set both horizontal and vertical spacing."""
        self._h_spacing = spacing
        self._v_spacing = spacing

    def count(self):
        """Return number of items."""
        return len(self._item_list)

    def itemAt(self, index):
        """Return item at index."""
        if 0 <= index < len(self._item_list):
            return self._item_list[index]
        return None

    def takeAt(self, index):
        """Remove and return item at index."""
        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)
        return None

    def expandingDirections(self):
        """Return expanding directions."""
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        """This layout's height depends on its width."""
        return True

    def heightForWidth(self, width):
        """Calculate height for given width."""
        return self._do_layout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        """Set the layout geometry."""
        super().setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):
        """Return the preferred size."""
        return self.minimumSize()

    def minimumSize(self):
        """Return the minimum size."""
        size = QSize()
        for item in self._item_list:
            size = size.expandedTo(item.minimumSize())

        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size

    def _do_layout(self, rect, test_only):
        """Arrange items in the layout.

        Args:
            rect: Available rectangle.
            test_only: If True, only calculate height without moving widgets.

        Returns:
            The height of the layout.
        """
        margins = self.contentsMargins()
        effective_rect = rect.adjusted(margins.left(), margins.top(), -margins.right(), -margins.bottom())
        x = effective_rect.x()
        y = effective_rect.y()
        line_height = 0

        for item in self._item_list:
            widget = item.widget()
            if widget is None or not widget.isVisible():
                continue

            h_space = self.horizontalSpacing()
            v_space = self.verticalSpacing()

            next_x = x + item.sizeHint().width() + h_space

            if next_x - h_space > effective_rect.right() and line_height > 0:
                x = effective_rect.x()
                y = y + line_height + v_space
                next_x = x + item.sizeHint().width() + h_space
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - rect.y() + margins.bottom()

    def _smart_spacing(self, control_type):
        """Calculate smart spacing based on parent."""
        parent = self.parent()
        if parent is None:
            return -1
        if parent.isWidgetType():
            return parent.style().pixelMetric(
                parent.style().PixelMetric.PM_LayoutHorizontalSpacing,
                None,
                parent
            )
        return parent.spacing()
