from __future__ import annotations

from todoist_kanban_tui.widgets.section_column import SectionColumn
from todoist_kanban_tui.widgets.task_card import TaskCard


def get_focused_col(app) -> SectionColumn:
    focused = app.focused
    return next(a for a in focused.ancestors_with_self if isinstance(a, SectionColumn))


class TestVerticalNavigation:
    async def test_down_focuses_next_card(self, app):
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            cards = list(app.query(SectionColumn).first(SectionColumn).query(TaskCard))
            cards[0].focus()
            await pilot.pause()

            await pilot.press("down")
            await pilot.pause()
            assert app.focused is cards[1]

    async def test_up_focuses_previous_card(self, app):
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            cards = list(app.query(SectionColumn).first(SectionColumn).query(TaskCard))
            cards[1].focus()
            await pilot.pause()

            await pilot.press("up")
            await pilot.pause()
            assert app.focused is cards[0]

    async def test_down_wraps_to_first_card(self, app):
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            cards = list(app.query(SectionColumn).first(SectionColumn).query(TaskCard))
            cards[-1].focus()
            await pilot.pause()

            await pilot.press("down")
            await pilot.pause()
            assert app.focused is cards[0]

    async def test_up_wraps_to_last_card(self, app):
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            cards = list(app.query(SectionColumn).first(SectionColumn).query(TaskCard))
            cards[0].focus()
            await pilot.pause()

            await pilot.press("up")
            await pilot.pause()
            assert app.focused is cards[-1]


class TestHorizontalNavigation:
    async def test_right_moves_to_next_column(self, app):
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            columns = list(app.query(SectionColumn))
            first_card = columns[0].query(TaskCard).first(TaskCard)
            first_card.focus()
            await pilot.pause()

            await pilot.press("right")
            await pilot.pause()
            assert get_focused_col(app) is columns[1]

    async def test_left_moves_to_previous_column(self, app):
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            columns = list(app.query(SectionColumn))
            second_col_card = columns[1].query(TaskCard).first(TaskCard)
            second_col_card.focus()
            await pilot.pause()

            await pilot.press("left")
            await pilot.pause()
            assert get_focused_col(app) is columns[0]

    async def test_right_wraps_to_first_column(self, app):
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            columns = list(app.query(SectionColumn))
            last_col_card = columns[-1].query(TaskCard).first(TaskCard)
            last_col_card.focus()
            await pilot.pause()

            await pilot.press("right")
            await pilot.pause()
            assert get_focused_col(app) is columns[0]

    async def test_left_wraps_to_last_column(self, app):
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            columns = list(app.query(SectionColumn))
            first_card = columns[0].query(TaskCard).first(TaskCard)
            first_card.focus()
            await pilot.pause()

            await pilot.press("left")
            await pilot.pause()
            assert get_focused_col(app) is columns[-1]

    async def test_right_preserves_row_index(self, app):
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            columns = list(app.query(SectionColumn))
            col1_cards = list(columns[0].query(TaskCard))
            col1_cards[1].focus()
            await pilot.pause()

            await pilot.press("right")
            await pilot.pause()
            col2_cards = list(columns[1].query(TaskCard))
            assert app.focused is col2_cards[1]

    async def test_right_clamps_to_last_card_in_shorter_column(self, app):
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            columns = list(app.query(SectionColumn))
            col1_cards = list(columns[0].query(TaskCard))
            col1_cards[2].focus()
            await pilot.pause()

            await pilot.press("right")
            await pilot.pause()
            col2_cards = list(columns[1].query(TaskCard))
            assert app.focused is col2_cards[min(2, len(col2_cards) - 1)]


class TestVimKeys:
    async def test_j_moves_down(self, app):
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            cards = list(app.query(SectionColumn).first(SectionColumn).query(TaskCard))
            cards[0].focus()
            await pilot.pause()

            await pilot.press("j")
            await pilot.pause()
            assert app.focused is cards[1]

    async def test_k_moves_up(self, app):
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            cards = list(app.query(SectionColumn).first(SectionColumn).query(TaskCard))
            cards[1].focus()
            await pilot.pause()

            await pilot.press("k")
            await pilot.pause()
            assert app.focused is cards[0]

    async def test_l_moves_right(self, app):
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            columns = list(app.query(SectionColumn))
            columns[0].query(TaskCard).first(TaskCard).focus()
            await pilot.pause()

            await pilot.press("l")
            await pilot.pause()
            assert get_focused_col(app) is columns[1]

    async def test_h_moves_left(self, app):
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            columns = list(app.query(SectionColumn))
            columns[1].query(TaskCard).first(TaskCard).focus()
            await pilot.pause()

            await pilot.press("h")
            await pilot.pause()
            assert get_focused_col(app) is columns[0]


class TestInitialFocus:
    async def test_navigate_with_no_focus_selects_first_card(self, app):
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            columns = list(app.query(SectionColumn))
            first_card = columns[0].query(TaskCard).first(TaskCard)

            await pilot.press("down")
            await pilot.pause()
            assert app.focused is first_card
