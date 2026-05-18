# ==============================================================================
# pause.py - Pause Playback Command
# ==============================================================================

import logging
from pyrogram import filters, types
from pyrogram.errors import ChatSendPlainForbidden, ChatWriteForbidden

from Elevenyts import tune, app, db, lang
from Elevenyts.helpers import buttons, can_manage_vc

logger = logging.getLogger(__name__)


@app.on_message(filters.command(["pause", "cpause"]) & filters.group & ~app.bl_users)
@lang.language()
@can_manage_vc
async def _pause(_, m: types.Message):
    try:
        await m.delete()
    except Exception:
        pass
    
    # Check for channel play mode
    is_channel = m.command[0].lower() == "cpause"
    chat_id = m.chat.id
    
    if is_channel:
        channel_id = await db.get_cmode(m.chat.id)
        if channel_id is None:
            return await m.reply_text("Channel play is not enabled. Use /channelplay to enable.")
        chat_id = channel_id
    
    if not await db.get_call(chat_id):
        try:
            return await m.reply_text("Nothing is playing.")
        except (ChatSendPlainForbidden, ChatWriteForbidden):
            return

    if not await db.playing(chat_id):
        try:
            return await m.reply_text("Playback is already paused.")
        except (ChatSendPlainForbidden, ChatWriteForbidden):
            return

    await tune.pause(chat_id)
    try:
        await m.reply_text(
            f"Paused by {m.from_user.mention}",
            reply_markup=buttons.controls(chat_id),
        )
    except (ChatSendPlainForbidden, ChatWriteForbidden):
        logger.warning("Cannot send text in media-only chat")
