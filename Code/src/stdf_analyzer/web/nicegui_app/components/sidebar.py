"""
Sidebar Component - Wafer Selection.

Wie in Desktop-App:
- Header "Wafer Selection"
- Info-Text (z.B. "Single Select (Heatmap)")
- Navigation Buttons: Prev, Next, All, Unload All
- Wafer Count Label
- Wafer Listbox
"""

from nicegui import ui
from typing import Callable, List, Optional


class WaferSidebar:
    """
    Linke Sidebar für Wafer-Auswahl.

    Layout:
    ┌─────────────────────┐
    │ ▼ Wafer Selection   │  (Collapse-Header)
    ├─────────────────────┤
    │ • Single Select     │  (Mode-Info)
    ├─────────────────────┤
    │ [◀Prev] [Next▶]     │
    │ [All] [Unload All]  │
    │                     │
    │ 0 Wafer             │  (Count)
    ├─────────────────────┤
    │ ┌─────────────────┐ │
    │ │ wafer_001.stdf  │ │  (Listbox)
    │ │ wafer_002.stdf  │ │
    │ │ wafer_003.stdf  │ │
    │ └─────────────────┘ │
    └─────────────────────┘
    """

    def __init__(
        self,
        on_prev: Optional[Callable] = None,
        on_next: Optional[Callable] = None,
        on_select_all: Optional[Callable] = None,
        on_unload_all: Optional[Callable] = None,
        on_wafer_select: Optional[Callable] = None,
    ):
        self.on_prev = on_prev
        self.on_next = on_next
        self.on_select_all = on_select_all
        self.on_unload_all = on_unload_all
        self.on_wafer_select = on_wafer_select

        # UI Elements
        self.mode_label = None
        self.count_label = None
        self.wafer_list = None
        self.container = None

        # State
        self.wafers: List[str] = []
        self.selected_index: int = -1

    def build(self) -> None:
        """Sidebar UI erstellen."""
        with ui.column().classes('w-52 bg-blue-50 border-r h-full') as self.container:
            # Header
            with ui.expansion('Wafer Selection', icon='folder', value=True).classes(
                'w-full bg-blue-100'
            ):
                # Mode Info
                self.mode_label = ui.label('• Single Select (Heatmap)').classes(
                    'text-xs text-blue-700 px-2'
                )

                # Navigation Buttons
                with ui.row().classes('gap-1 px-2 py-1'):
                    ui.button('◀ Prev', on_click=self._handle_prev).classes(
                        'bg-blue-500 text-white text-xs'
                    ).props('dense size=sm')
                    ui.button('Next ▶', on_click=self._handle_next).classes(
                        'bg-blue-500 text-white text-xs'
                    ).props('dense size=sm')

                with ui.row().classes('gap-1 px-2 py-1'):
                    ui.button('All', on_click=self._handle_select_all).classes(
                        'bg-green-500 text-white text-xs'
                    ).props('dense size=sm')
                    ui.button('Unload All', on_click=self._handle_unload_all).classes(
                        'bg-red-500 text-white text-xs'
                    ).props('dense size=sm')

                # Count Label
                self.count_label = ui.label('0 Wafer').classes('text-sm text-gray-600 px-2 py-1')

                # Wafer List
                self.wafer_list = ui.select(
                    options=[],
                    on_change=self._handle_wafer_select,
                    multiple=False
                ).classes('w-full').props('dense outlined options-dense')

    def update_wafers(self, wafers: List[str], selected: Optional[str] = None) -> None:
        """Wafer-Liste aktualisieren."""
        self.wafers = wafers
        self.wafer_list.options = wafers

        if selected and selected in wafers:
            self.wafer_list.value = selected
            self.selected_index = wafers.index(selected)
        elif wafers:
            self.wafer_list.value = wafers[0]
            self.selected_index = 0
        else:
            self.wafer_list.value = None
            self.selected_index = -1

        self.count_label.text = f'{len(wafers)} Wafer'
        self.wafer_list.update()

    def set_mode(self, mode: str) -> None:
        """Modus-Label aktualisieren."""
        self.mode_label.text = f'• {mode}'

    def get_selected(self) -> Optional[str]:
        """Aktuell ausgewählten Wafer zurückgeben."""
        return self.wafer_list.value

    def select_next(self) -> Optional[str]:
        """Nächsten Wafer auswählen."""
        if not self.wafers:
            return None
        self.selected_index = (self.selected_index + 1) % len(self.wafers)
        self.wafer_list.value = self.wafers[self.selected_index]
        self.wafer_list.update()
        return self.wafer_list.value

    def select_prev(self) -> Optional[str]:
        """Vorherigen Wafer auswählen."""
        if not self.wafers:
            return None
        self.selected_index = (self.selected_index - 1) % len(self.wafers)
        self.wafer_list.value = self.wafers[self.selected_index]
        self.wafer_list.update()
        return self.wafer_list.value

    def _handle_prev(self) -> None:
        selected = self.select_prev()
        if self.on_prev and selected:
            self.on_prev(selected)

    def _handle_next(self) -> None:
        selected = self.select_next()
        if self.on_next and selected:
            self.on_next(selected)

    def _handle_select_all(self) -> None:
        if self.on_select_all:
            self.on_select_all(self.wafers)

    def _handle_unload_all(self) -> None:
        if self.on_unload_all:
            self.on_unload_all()

    def _handle_wafer_select(self, e) -> None:
        if e.value and e.value in self.wafers:
            self.selected_index = self.wafers.index(e.value)
            if self.on_wafer_select:
                self.on_wafer_select(e.value)
