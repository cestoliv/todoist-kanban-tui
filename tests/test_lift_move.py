from __future__ import annotations

from unittest.mock import AsyncMock, patch

from todoist_kanban_tui.widgets.section_column import SectionColumn
from todoist_kanban_tui.widgets.status_bar import StatusBar
from todoist_kanban_tui.widgets.task_card import TaskCard


def get_focused_col(app) -> SectionColumn:
    focused = app.focused
    return next(a for a in focused.ancestors_with_self if isinstance(a, SectionColumn))


class TestLiftCard:
    async def test_space_lifts_focused_card(self, app):
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            cards = list(app.query(SectionColumn).first(SectionColumn).query(TaskCard))
            cards[0].focus()
            await pilot.pause()

            await pilot.press("space")
            await pilot.pause()

            assert app._lifted_card is cards[0]
            assert cards[0].has_class("lifted")

    async def test_space_no_op_without_focus(self, app):
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()

            await pilot.press("space")
            await pilot.pause()

            assert app._lifted_card is None

    async def test_lift_adds_drop_target_to_column(self, app):
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            columns = list(app.query(SectionColumn))
            cards = list(columns[0].query(TaskCard))
            cards[0].focus()
            await pilot.pause()

            await pilot.press("space")
            await pilot.pause()

            assert columns[0].has_class("drop-target")


class TestMoveCard:
    async def test_right_moves_card_to_next_column(self, app):
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            columns = list(app.query(SectionColumn))
            cards = list(columns[0].query(TaskCard))
            cards[0].focus()
            await pilot.pause()

            await pilot.press("space")
            await pilot.pause()
            await pilot.press("right")
            await pilot.pause()

            assert get_focused_col(app) is columns[1]

    async def test_left_moves_card_to_previous_column(self, app):
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            columns = list(app.query(SectionColumn))
            cards = list(columns[1].query(TaskCard))
            cards[0].focus()
            await pilot.pause()

            await pilot.press("space")
            await pilot.pause()
            await pilot.press("left")
            await pilot.pause()

            assert get_focused_col(app) is columns[0]

    async def test_move_stops_at_left_edge(self, app):
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            columns = list(app.query(SectionColumn))
            cards = list(columns[0].query(TaskCard))
            cards[0].focus()
            await pilot.pause()

            await pilot.press("space")
            await pilot.pause()
            await pilot.press("left")
            await pilot.pause()

            assert get_focused_col(app) is columns[0]

    async def test_move_stops_at_right_edge(self, app):
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            columns = list(app.query(SectionColumn))
            cards = list(columns[-1].query(TaskCard))
            cards[0].focus()
            await pilot.pause()

            await pilot.press("space")
            await pilot.pause()
            await pilot.press("right")
            await pilot.pause()

            assert get_focused_col(app) is columns[-1]

    async def test_up_down_ignored_during_lift(self, app):
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            columns = list(app.query(SectionColumn))
            cards = list(columns[0].query(TaskCard))
            cards[0].focus()
            await pilot.pause()

            await pilot.press("space")
            await pilot.pause()
            await pilot.press("down")
            await pilot.pause()

            assert app.focused is cards[0]
            assert get_focused_col(app) is columns[0]

    async def test_column_headers_update_after_move(self, app):
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            columns = list(app.query(SectionColumn))
            cards = list(columns[0].query(TaskCard))
            original_count_col0 = len(cards)
            original_count_col1 = len(list(columns[1].query(TaskCard)))
            cards[0].focus()
            await pilot.pause()

            await pilot.press("space")
            await pilot.pause()
            await pilot.press("right")
            await pilot.pause()

            header0 = columns[0].query_one(".column-header").render()
            header1 = columns[1].query_one(".column-header").render()
            assert str(original_count_col0 - 1) in str(header0)
            assert str(original_count_col1 + 1) in str(header1)


class TestDropCard:
    async def test_space_drops_card_and_calls_api(self, app):
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            columns = list(app.query(SectionColumn))
            cards = list(columns[0].query(TaskCard))
            task_id = cards[0].task_data.id
            cards[0].focus()
            await pilot.pause()

            await pilot.press("space")
            await pilot.pause()
            await pilot.press("right")
            await pilot.pause()
            await pilot.press("space")
            await pilot.pause()

            assert app._lifted_card is None
            app.client.move_task.assert_called_once_with(task_id, columns[1]._section.id)

    async def test_drop_without_move_no_api_call(self, app):
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            cards = list(app.query(SectionColumn).first(SectionColumn).query(TaskCard))
            cards[0].focus()
            await pilot.pause()

            await pilot.press("space")
            await pilot.pause()
            await pilot.press("space")
            await pilot.pause()

            assert app._lifted_card is None
            app.client.move_task.assert_not_called()

    async def test_drop_removes_lifted_class(self, app):
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            columns = list(app.query(SectionColumn))
            cards = list(columns[0].query(TaskCard))
            cards[0].focus()
            await pilot.pause()

            await pilot.press("space")
            await pilot.pause()
            await pilot.press("right")
            await pilot.pause()
            await pilot.press("space")
            await pilot.pause()

            assert not cards[0].has_class("lifted")
            assert not any(col.has_class("drop-target") for col in app.query(SectionColumn))

    async def test_drop_updates_board_data(self, app):
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            columns = list(app.query(SectionColumn))
            cards = list(columns[0].query(TaskCard))
            task_id = cards[0].task_data.id
            target_section_id = columns[1]._section.id
            cards[0].focus()
            await pilot.pause()

            await pilot.press("space")
            await pilot.pause()
            await pilot.press("right")
            await pilot.pause()
            await pilot.press("space")
            await pilot.pause()

            source_tasks = app.board_data.tasks_by_section.get("s1", [])
            target_tasks = app.board_data.tasks_by_section.get(target_section_id, [])
            assert not any(t.id == task_id for t in source_tasks)
            assert any(t.id == task_id for t in target_tasks)

    async def test_api_failure_triggers_refresh(self, app):
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            columns = list(app.query(SectionColumn))
            cards = list(columns[0].query(TaskCard))
            app.client.move_task = AsyncMock(side_effect=Exception("Network error"))
            cards[0].focus()
            await pilot.pause()

            await pilot.press("space")
            await pilot.pause()
            await pilot.press("right")
            await pilot.pause()
            await pilot.press("space")
            await pilot.pause()

            assert app.client.move_task.call_count == 1


class TestCancelLift:
    async def test_escape_cancels_lift(self, app):
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            columns = list(app.query(SectionColumn))
            cards = list(columns[0].query(TaskCard))
            cards[0].focus()
            await pilot.pause()

            await pilot.press("space")
            await pilot.pause()
            await pilot.press("right")
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()

            assert app._lifted_card is None
            assert get_focused_col(app) is columns[0]
            app.client.move_task.assert_not_called()

    async def test_escape_no_op_when_not_lifting(self, app):
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            cards = list(app.query(SectionColumn).first(SectionColumn).query(TaskCard))
            cards[0].focus()
            await pilot.pause()

            await pilot.press("escape")
            await pilot.pause()

            assert app._lifted_card is None

    async def test_cancel_removes_visual_classes(self, app):
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            columns = list(app.query(SectionColumn))
            cards = list(columns[0].query(TaskCard))
            cards[0].focus()
            await pilot.pause()

            await pilot.press("space")
            await pilot.pause()
            await pilot.press("right")
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()

            assert not cards[0].has_class("lifted")
            assert not any(col.has_class("drop-target") for col in app.query(SectionColumn))

    async def test_board_refresh_clears_lift_state(self, app):
        from conftest import make_board

        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            cards = list(app.query(SectionColumn).first(SectionColumn).query(TaskCard))
            cards[0].focus()
            await pilot.pause()

            await pilot.press("space")
            await pilot.pause()
            assert app._lifted_card is not None

            app.board_data = make_board()
            await pilot.pause()

            assert app._lifted_card is None


class TestLiftModeGuards:
    async def test_description_toggle_blocked_during_lift(self, app):
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            cards = list(app.query(SectionColumn).first(SectionColumn).query(TaskCard))
            cards[0].focus()
            await pilot.pause()

            await pilot.press("space")
            await pilot.pause()
            await pilot.press("d")
            await pilot.pause()

            assert not cards[0].expanded

    async def test_open_browser_blocked_during_lift(self, app):
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            cards = list(app.query(SectionColumn).first(SectionColumn).query(TaskCard))
            cards[0].focus()
            await pilot.pause()

            await pilot.press("space")
            await pilot.pause()
            with patch("todoist_kanban_tui.app.webbrowser.open") as mock_open:
                await pilot.press("o")
                await pilot.pause()
                mock_open.assert_not_called()


class TestStatusBarLiftMode:
    async def test_status_bar_shows_lift_mode(self, app):
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            cards = list(app.query(SectionColumn).first(SectionColumn).query(TaskCard))
            cards[0].focus()
            await pilot.pause()

            await pilot.press("space")
            await pilot.pause()

            status = app.query_one(StatusBar)
            rendered = str(status.render())
            assert "MOVING" in rendered

    async def test_status_bar_returns_to_normal_after_drop(self, app):
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            cards = list(app.query(SectionColumn).first(SectionColumn).query(TaskCard))
            cards[0].focus()
            await pilot.pause()

            await pilot.press("space")
            await pilot.pause()
            await pilot.press("space")
            await pilot.pause()

            status = app.query_one(StatusBar)
            rendered = str(status.render())
            assert "MOVING" not in rendered
