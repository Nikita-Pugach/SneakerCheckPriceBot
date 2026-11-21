from aiogram.fsm.context import FSMContext


async def delete_last_prompt_on_reply(state: FSMContext, bot, chat_id: int) -> bool:
    """Delete the last prompt the bot sent before the user answered it.

    Uses state['prompt_refs']; returns False when there is nothing to delete.
    """
    data = await state.get_data()
    prompts = data.get("prompt_refs", [])
    if not prompts:
        return False

    last = prompts.pop()
    await state.update_data(prompt_refs=prompts)

    try:
        await bot.delete_message(chat_id=last["chat_id"], message_id=last["message_id"])
        return True
    except Exception:
        return False
