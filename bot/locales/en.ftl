# English locale — V2

welcome = 🎬 Welcome!

    📎 Send a video link — I'll download it
    🔍 Type a song name — I'll find it
    🎤 Send audio/video — I'll identify the song

lang-select = 🌐 Select language:
lang-changed = ✅ Language changed: English

hint-url = 📎 Send a link or type a song name.
hint-unsupported = ❓ Send a video/audio file — I'll identify the song.\nOr send a link — I'll download the video.

downloading = ⏬ Downloading...
processing = ⚙️ Preparing...
uploading = 📤 Uploading to Telegram...

error-private = 🔒 This video is private or has been deleted.
error-geo = 🌍 This video is not available in your region.
error-age = 🔞 This video has age restrictions.
error-too-large = 📦 File too large (max { $max } MB).
error-unsupported = ❌ This link is not supported.
error-download = ❌ Download failed. Please try again later.
error-generic = ❌ An error occurred. Please try again later.

caption-video = 🎬 { $title }
    📺 { $platform }

    🤖 @vidyuklaydi_bot
caption-audio = 🎵 { $title }
    👤 { $artist }

    🤖 @vidyuklaydi_bot

shazam-send-media = 🎤 Send an audio file, voice message, or video — I'll identify the song.
shazam-recognizing = 🎵 Recognizing song...
shazam-not-found = 😕 Song not found. Try a different audio.
shazam-not-found-tip = 💡 Try sending a clear 10–15 second musical clip.
shazam-result =
    🎵 <b>{ $title }</b>
    👤 { $artist }
    💿 { $album }
shazam-listen = 🎧 Listen
shazam-lyrics-btn = 📝 Lyrics
shazam-try-again = 🔁 Try again
shazam-no-lyrics = 📝 Lyrics not found.
shazam-lyrics-header = 📝 <b>{ $title }</b> — { $artist }
shazam-lyrics-page = 📄 { $current }/{ $total }
shazam-next-page = ▶️ Next
shazam-prev-page = ◀️ Back
shazam-error = ❌ An error occurred. Please try again later.

searching = 🔍 Searching...
search-results-header = 🎵 <b>Results for "{ $query }":</b>
search-empty = 😕 Nothing found. Try a different query.
search-pick = Tap a number — I'll download the MP3.
search-downloading = ⏬ Downloading <b>{ $title }</b>...
search-error = ❌ Download error. Please try again.
mp3-downloading = 🎧 Preparing MP3...

channel-required = 📢 Please subscribe to the channel to use this bot!
channel-check-failed = ❌ You haven't subscribed yet. Please join the channel first.
channel-check-ok = ✅ Thank you! You can now use the bot.

throttle-slow-down = ⏱ Slow down! Please wait { $seconds } seconds.
admin-only = 🚫 This command is for admins only.

admin-panel = 👮 <b>Admin panel:</b>

admin-stats =
    📊 <b>Statistics</b>

    👥 Total users: <b>{ $total }</b>
    📅 New today: <b>{ $today }</b>
    📆 New this week: <b>{ $week }</b>
    🟢 Active 7 days: <b>{ $active7 }</b>

    📥 Total downloads: <b>{ $downloads }</b>
    📥 Downloads today: <b>{ $dl_today }</b>
    🎵 Total recognitions: <b>{ $recognitions }</b>
    🔍 Total searches: <b>{ $searches }</b>
    ⚡ Cache hits today: <b>{ $cache_hits }</b>

admin-broadcast-ask = 📢 Send a message, photo, video, or audio to broadcast:
admin-broadcast-btn-ask = 🔗 Add a button?\nFormat: <code>Label | https://...</code>\n\nPress "Skip" to send without a button.
admin-broadcast-preview = 👀 <b>Preview:</b>
admin-broadcast-confirm = ✅ Send now?
admin-broadcast-sending = 📢 Broadcasting...
admin-broadcast-done = ✅ Broadcast complete.\n✅ Sent: { $ok }\n❌ Failed: { $fail }
admin-broadcast-cancelled = ❌ Cancelled.

admin-welcome-ask = ✏️ Select language:
admin-welcome-current = 📝 Current message ({ $lang }):\n\n{ $text }\n\nSend new text:
admin-welcome-confirm = Preview:\n\n{ $text }\n\nSave?
admin-welcome-saved = ✅ Saved.
admin-welcome-cancelled = ❌ Cancelled.

admin-export-generating = ⏳ Generating file...
admin-export-done = ✅ Exported { $count } users.

admin-ban-ask = 🚫 Ban or unban:
admin-ban-id-ask = 🔢 Send the user ID:
admin-ban-done = ✅ User { $id } banned.
admin-unban-done = ✅ User { $id } unbanned.
admin-ban-not-found = ❌ User not found.

admin-channel-current = 📺 Current channel: <code>{ $channel }</code>
admin-channel-none = 📺 No required channel set.
admin-channel-ask = 🔗 Send a channel username or link (@channel or https://t.me/...):
admin-channel-saved = ✅ Channel set: <code>{ $channel }</code>
admin-channel-removed = ✅ Channel removed.

not-url = 📎 Send a link or a video/audio file.
worker-processing = ⚙️ Processing...
download-cached = ⚡ Done! (cached)
download-done = ✅ Done!
