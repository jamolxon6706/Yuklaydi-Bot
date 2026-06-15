# Russian locale — V2

welcome = 🎬 Добро пожаловать!

    📎 Отправьте ссылку на видео — скачаю
    🔍 Напишите название песни — найду
    🎤 Отправьте аудио/видео — определю песню

lang-select = 🌐 Выберите язык:
lang-changed = ✅ Язык изменён: Русский

hint-url = 📎 Отправьте ссылку или напишите название песни.
hint-unsupported = ❓ Отправьте видео/аудио — определю песню.\nИли ссылку — скачаю видео.

downloading = ⏬ Скачивается...
processing = ⚙️ Подготовка...
uploading = 📤 Отправка в Telegram...

error-private = 🔒 Это видео приватное или удалено.
error-geo = 🌍 Это видео недоступно в вашем регионе.
error-age = 🔞 Это видео имеет возрастное ограничение.
error-too-large = 📦 Файл слишком большой (макс { $max } МБ).
error-unsupported = ❌ Эта ссылка не поддерживается.
error-download = ❌ Не удалось скачать. Попробуйте позже.
error-generic = ❌ Произошла ошибка. Попробуйте позже.

caption-video = 🎬 { $title }
    📺 { $platform }

    🤖 @vidyuklaydi_bot
caption-audio = 🎵 { $title }
    👤 { $artist }

    🤖 @vidyuklaydi_bot

shazam-send-media = 🎤 Отправьте аудио, голосовое сообщение или видео — определю песню.
shazam-recognizing = 🎵 Определяю песню...
shazam-not-found = 😕 Песня не найдена. Попробуйте другое аудио.
shazam-not-found-tip = 💡 Попробуйте отправить чёткий 10–15 секундный музыкальный фрагмент.
shazam-result =
    🎵 <b>{ $title }</b>
    👤 { $artist }
    💿 { $album }
shazam-listen = 🎧 Слушать
shazam-lyrics-btn = 📝 Текст песни
shazam-try-again = 🔁 Попробовать снова
shazam-no-lyrics = 📝 Текст песни не найден.
shazam-lyrics-header = 📝 <b>{ $title }</b> — { $artist }
shazam-lyrics-page = 📄 { $current }/{ $total }
shazam-next-page = ▶️ Далее
shazam-prev-page = ◀️ Назад
shazam-error = ❌ Произошла ошибка. Попробуйте позже.

searching = 🔍 Ищу...
search-results-header = 🎵 <b>Результаты по "{ $query }":</b>
search-empty = 😕 Ничего не найдено. Попробуйте другой запрос.
search-pick = Нажмите на номер — скачаю MP3.
search-downloading = ⏬ Скачиваю <b>{ $title }</b>...
search-error = ❌ Ошибка загрузки. Попробуйте позже.
mp3-downloading = 🎧 Готовлю MP3...

channel-required = 📢 Для использования бота подпишитесь на канал!
channel-check-failed = ❌ Вы ещё не подписались. Пожалуйста, подпишитесь на канал.
channel-check-ok = ✅ Спасибо! Теперь вы можете пользоваться ботом.

throttle-slow-down = ⏱ Помедленнее! Подождите { $seconds } секунд.
admin-only = 🚫 Эта команда только для администраторов.

admin-panel = 👮 <b>Панель администратора:</b>

admin-stats =
    📊 <b>Статистика</b>

    👥 Всего пользователей: <b>{ $total }</b>
    📅 Новых сегодня: <b>{ $today }</b>
    📆 Новых за неделю: <b>{ $week }</b>
    🟢 Активных за 7 дней: <b>{ $active7 }</b>

    📥 Всего загрузок: <b>{ $downloads }</b>
    📥 Загрузок сегодня: <b>{ $dl_today }</b>
    🎵 Всего распознаваний: <b>{ $recognitions }</b>
    🔍 Всего поисков: <b>{ $searches }</b>
    ⚡ Кэш сегодня: <b>{ $cache_hits }</b>

admin-broadcast-ask = 📢 Отправьте текст, фото, видео или аудио для рассылки:
admin-broadcast-btn-ask = 🔗 Добавить кнопку?\nФормат: <code>Текст | https://...</code>\n\nНажмите "Пропустить" — отправить без кнопки.
admin-broadcast-preview = 👀 <b>Предварительный просмотр:</b>
admin-broadcast-confirm = ✅ Отправить?
admin-broadcast-sending = 📢 Рассылка...
admin-broadcast-done = ✅ Рассылка завершена.\n✅ Отправлено: { $ok }\n❌ Ошибок: { $fail }
admin-broadcast-cancelled = ❌ Отменено.

admin-welcome-ask = ✏️ Выберите язык:
admin-welcome-current = 📝 Текущее сообщение ({ $lang }):\n\n{ $text }\n\nОтправьте новый текст:
admin-welcome-confirm = Предпросмотр:\n\n{ $text }\n\nСохранить?
admin-welcome-saved = ✅ Сохранено.
admin-welcome-cancelled = ❌ Отменено.

admin-export-generating = ⏳ Генерирую файл...
admin-export-done = ✅ Экспортировано { $count } пользователей.

admin-ban-ask = 🚫 Бан или разбан:
admin-ban-id-ask = 🔢 Отправьте ID пользователя:
admin-ban-done = ✅ Пользователь { $id } заблокирован.
admin-unban-done = ✅ Пользователь { $id } разблокирован.
admin-ban-not-found = ❌ Пользователь не найден.

admin-channel-current = 📺 Текущий канал: <code>{ $channel }</code>
admin-channel-none = 📺 Обязательный канал не задан.
admin-channel-ask = 🔗 Отправьте username или ссылку на канал (@channel или https://t.me/...):
admin-channel-saved = ✅ Канал установлен: <code>{ $channel }</code>
admin-channel-removed = ✅ Канал удалён.

not-url = 📎 Отправьте ссылку или файл видео/аудио.
worker-processing = ⚙️ Обрабатывается...
download-cached = ⚡ Готово! (из кэша)
download-done = ✅ Готово!
