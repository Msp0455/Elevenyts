# ==============================================================================
# seek.py - Seek to Timestamp Command
# ==============================================================================

from pyrogram import filters, types

from Elevenyts import tune, app, db, lang, queue
from Elevenyts.helpers import can_manage_vc


@app.on_message(filters.command(["seek", "seekback", "cseek", "cseekback"]) & filters.group & ~app.bl_users)
@lang.language()
@can_manage_vc
async def _seek(_, m: types.Message):
    try:
        await m.delete()
    except Exception:
        pass
    
    if len(m.command) < 2:
        return await m.reply_text(f"Usage: {m.command[0]} <seconds>")

    try:
        to_seek = int(m.command[1])
    except ValueError:
        return await m.reply_text(f"Usage: {m.command[0]} <seconds>")
    
    if to_seek < 10:
        return await m.reply_text("Minimum seek is 10 seconds")

    # Check for channel play mode
    is_channel = m.command[0].lower() in ["cseek", "cseekback"]
    chat_id = m.chat.id
    
    if is_channel:
        channel_id = await db.get_cmode(m.chat.id)
        if channel_id is None:
            return await m.reply_text("Channel play is not enabled. Use /channelplay to enable.")
        chat_id = channel_id

    if not await db.get_call(chat_id):
        return await m.reply_text("Nothing is playing.")

    if not await db.playing(chat_id):
        return await m.reply_text("Playback is paused. Resume first.")

    media = queue.get_current(chat_id)
    if not media.duration_sec:
        return await m.reply_text("Cannot seek in live streams.")

    sent = await m.reply_text("Seeking...")
    
    current_time = getattr(media, 'time', 0)
    if m.command[0] in ["seekback", "cseekback"]:
        stype = "backward"
        start_from = max(1, current_time - to_seek)
    else:
        stype = "forward"
        start_from = min(current_time + to_seek, media.duration_sec - 5)

    success = await tune.seek_stream(chat_id, int(start_from))
    
    if success:
        await sent.edit_text(f"Seeked {stype} to {start_from} seconds by {m.from_user.mention}")
    else:
        await sent.edit_text("Failed to seek!")
