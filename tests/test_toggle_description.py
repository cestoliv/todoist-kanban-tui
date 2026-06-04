from __future__ import annotations

from todoist_kanban_tui.widgets.task_card import TaskCard


class TestKeyboardToggle:
    async def test_d_key_expands_description(self, app):
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            card = app.query(TaskCard).first(TaskCard)
            card.focus()
            await pilot.pause()

            assert not card.expanded
            await pilot.press("d")
            await pilot.pause()
            assert card.expanded

    async def test_d_key_collapses_description(self, app):
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            card = app.query(TaskCard).first(TaskCard)
            card.focus()
            await pilot.pause()

            await pilot.press("d")
            await pilot.pause()
            await pilot.press("d")
            await pilot.pause()
            assert not card.expanded

    async def test_focus_alone_does_not_expand(self, app):
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            card = app.query(TaskCard).first(TaskCard)
            card.focus()
            await pilot.pause()
            assert not card.expanded

    async def test_description_persists_after_navigating_away(self, app):
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            cards = list(app.query(TaskCard))
            cards[0].focus()
            await pilot.pause()

            await pilot.press("d")
            await pilot.pause()
            assert cards[0].expanded

            await pilot.press("down")
            await pilot.pause()
            assert cards[0].expanded


class TestDescriptionContent:
    async def test_description_shown_when_expanded(self, app):
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            card = app.query(TaskCard).first(TaskCard)
            assert card.task_data.description
            card.focus()
            await pilot.pause()

            await pilot.press("d")
            await pilot.pause()
            rendered = str(card.render())
            assert "Detailed description" in rendered

    async def test_placeholder_when_no_description(self, app):
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            cards = list(app.query(TaskCard))
            no_desc_card = next(c for c in cards if not c.task_data.description)
            no_desc_card.focus()
            await pilot.pause()

            await pilot.press("d")
            await pilot.pause()
            rendered = str(no_desc_card.render())
            assert "No description" in rendered

    async def test_description_hidden_when_collapsed(self, app):
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            card = app.query(TaskCard).first(TaskCard)
            card.focus()
            await pilot.pause()

            rendered = str(card.render())
            assert "Detailed description" not in rendered


class TestClickToggle:
    async def test_click_expands_card(self, app):
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            card = app.query(TaskCard).first(TaskCard)

            await pilot.click(TaskCard)
            await pilot.pause()
            assert card.expanded

    async def test_click_again_collapses_card(self, app):
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause()
            card = app.query(TaskCard).first(TaskCard)

            await pilot.click(TaskCard)
            await pilot.pause()
            await pilot.click(TaskCard)
            await pilot.pause()
            assert not card.expanded
