import os
import logging
import asyncio
import time
import traceback
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters,
    ConversationHandler
)
import yt_dlp

# Logging sozlash
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# States
MAIN_MENU, TEXT_STYLE, TEXT_STYLE_SELECT, VIDEO_ROUND, MUSIC_SEARCH = range(5)

# User data storage
user_data = {}

# Kategoriyalar
categories = {
    "1": "📝 Matn Stilizatsiyasi",
    "2": "⭕️ Video Dumaloq qilish",
    "3": "🎵 Musiqa/Video Qidiruv"
}

CONTACT = "📞 Murojat uchun: @zzb050"

# ==================== MATN STILLARI ====================
def apply_text_style(text, style):
    cleaned_text = ''
    for char in text:
        if char not in ['\u0336', '\u0332']:
            if ('A' <= char <= 'Z' or 'a' <= char <= 'z' or
                    '0' <= char <= '9' or char.isspace() or
                    char in ',.!?;:"\'-'):
                cleaned_text += char
    text = cleaned_text

    fonts = {
        "thick": lambda t: ''.join(
            chr(0x1D5D4 + ord(c) - ord('A')) if 'A' <= c <= 'Z' else
            chr(0x1D5EE + ord(c) - ord('a')) if 'a' <= c <= 'z' else
            chr(0x1D7CE + ord(c) - ord('0')) if '0' <= c <= '9' else c for c in t),
        "slant": lambda t: ''.join(
            chr(0x1D608 + ord(c) - ord('A')) if 'A' <= c <= 'Z' else
            chr(0x1D622 + ord(c) - ord('a')) if 'a' <= c <= 'z' else c for c in t),
        "sans": lambda t: ''.join(
            chr(0x1D5A0 + ord(c) - ord('A')) if 'A' <= c <= 'Z' else
            chr(0x1D5BA + ord(c) - ord('a')) if 'a' <= c <= 'z' else
            chr(0x1D7E2 + ord(c) - ord('0')) if '0' <= c <= '9' else c for c in t),
        "monospace": lambda t: ''.join(
            chr(0x1D670 + ord(c) - ord('A')) if 'A' <= c <= 'Z' else
            chr(0x1D68A + ord(c) - ord('a')) if 'a' <= c <= 'z' else
            chr(0x1D7F6 + ord(c) - ord('0')) if '0' <= c <= '9' else c for c in t),
        "script": lambda t: ''.join(
            chr(0x1D49C + ord(c) - ord('A')) if 'A' <= c <= 'Z' and c not in 'BEFHILMR' else
            {'B': '𝓑', 'E': '𝓔', 'F': '𝓕', 'H': '𝓗', 'I': '𝓘',
             'L': '𝓛', 'M': '𝓜', 'R': '𝓡'}.get(c, c) if 'A' <= c <= 'Z' else
            chr(0x1D4B6 + ord(c) - ord('a')) if 'a' <= c <= 'z' and c not in 'ego' else
            {'e': '𝑒', 'g': '𝑔', 'o': '𝑜'}.get(c, c) if 'a' <= c <= 'z' else c for c in t),
        "double": lambda t: ''.join(
            chr(0x1D538 + ord(c) - ord('A')) if 'A' <= c <= 'Z' and c not in 'CHNPQRZ' else
            {'C': 'ℂ', 'H': 'ℍ', 'N': 'ℕ', 'P': 'ℙ', 'Q': 'ℚ',
             'R': 'ℝ', 'Z': 'ℤ'}.get(c, c) if 'A' <= c <= 'Z' else
            chr(0x1D552 + ord(c) - ord('a')) if 'a' <= c <= 'z' else
            chr(0x1D7D8 + ord(c) - ord('0')) if '0' <= c <= '9' else c for c in t),
        "fraktur": lambda t: ''.join(
            chr(0x1D504 + ord(c) - ord('A')) if 'A' <= c <= 'Z' and c not in 'CHIRZ' else
            {'C': 'ℭ', 'H': 'ℌ', 'I': 'ℑ', 'R': 'ℜ', 'Z': 'ℨ'}.get(c, c) if 'A' <= c <= 'Z' else
            chr(0x1D51E + ord(c) - ord('a')) if 'a' <= c <= 'z' else c for c in t),
        "thin": lambda t: ''.join(
            chr(0x1D5A0 + ord(c) - ord('A')) if 'A' <= c <= 'Z' else
            chr(0x1D5BA + ord(c) - ord('a')) if 'a' <= c <= 'z' else c for c in t),
        "strikethrough": lambda t: ''.join(c + '\u0336' for c in t),
        "underline": lambda t: ''.join(c + '\u0332' for c in t),
    }

    return fonts.get(style, lambda t: t)(text)


# ==================== YUKLAB OLISH FUNKSIYALARI ====================
def get_ydl_opts_base():
    """Asosiy yt-dlp sozlamalari"""
    return {
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36'
        }
    }


def search_youtube(query):
    """YouTube'dan tezkor qidiruv"""
    try:
        opts = get_ydl_opts_base()
        opts.update({
            'extract_flat': True,
            'skip_download': True,
        })
        with yt_dlp.YoutubeDL(opts) as ydl:
            result = ydl.extract_info(f"ytsearch5:{query}", download=False)
            if 'entries' in result:
                videos = []
                for entry in result['entries'][:5]:
                    if entry and entry.get('id'):
                        videos.append({
                            'title': entry.get('title', 'Unknown'),
                            'url': f"https://youtube.com/watch?v={entry['id']}",
                            'duration': entry.get('duration', 0)
                        })
                return videos
    except Exception as e:
        logger.error(f"YouTube search error: {e}")
    return []


def download_mp3(url):
    """MP3 yuklab olish"""
    try:
        timestamp = int(time.time())
        base_path = f'downloads/audio_{timestamp}'
        output_template = f'{base_path}.%(ext)s'

        opts = get_ydl_opts_base()
        opts.update({
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })

        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

        # Faylni topish
        for ext in ['mp3', 'm4a', 'webm', 'opus']:
            path = f'{base_path}.{ext}'
            if os.path.exists(path) and os.path.getsize(path) > 0:
                return path

        return None
    except Exception as e:
        logger.error(f"MP3 download error: {e}")
        return None


def download_video(url, quality):
    """Video yuklab olish"""
    try:
        timestamp = int(time.time())
        base_path = f'downloads/video_{timestamp}'
        output_template = f'{base_path}.%(ext)s'

        quality_map = {
            '360': 'bestvideo[height<=360]+bestaudio/best[height<=360]/best[height<=360]',
            '720': 'bestvideo[height<=720]+bestaudio/best[height<=720]/best[height<=720]',
            '1080': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]/best[height<=1080]'
        }

        opts = get_ydl_opts_base()
        opts.update({
            'format': quality_map.get(quality, 'best'),
            'outtmpl': output_template,
            'merge_output_format': 'mp4',
        })

        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

        # Faylni topish
        for ext in ['mp4', 'webm', 'mkv']:
            path = f'{base_path}.{ext}'
            if os.path.exists(path) and os.path.getsize(path) > 0:
                return path

        return None
    except Exception as e:
        logger.error(f"Video download error: {e}")
        return None


def download_link_video(url):
    """Social media link yuklab olish"""
    try:
        timestamp = int(time.time())
        base_path = f'downloads/link_{timestamp}'
        output_template = f'{base_path}.%(ext)s'

        opts = get_ydl_opts_base()
        opts.update({
            'format': 'best[filesize<50M]/bestvideo[filesize<45M]+bestaudio/best',
            'outtmpl': output_template,
            'merge_output_format': 'mp4',
        })

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                return None

        # Faylni topish
        for ext in ['mp4', 'webm', 'mkv', 'm4a']:
            path = f'{base_path}.{ext}'
            if os.path.exists(path) and os.path.getsize(path) > 0:
                return path

        return None
    except Exception as e:
        logger.error(f"Link download error: {e}")
        return None


# ==================== YORDAMCHI FUNKSIYALAR ====================
def main_keyboard():
    keyboard = []
    for key, value in categories.items():
        keyboard.append([InlineKeyboardButton(value, callback_data=f"cat_{key}")])
    return InlineKeyboardMarkup(keyboard)


def after_download_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎵 MP3 yuklab olish", callback_data="mp3")],
        [InlineKeyboardButton("🔄 Boshqa qidiruv", callback_data="cat_3")],
        [InlineKeyboardButton("🏠 Bosh sahifa", callback_data="back_to_main")]
    ])


def after_mp3_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Boshqa qidiruv", callback_data="cat_3")],
        [InlineKeyboardButton("🏠 Bosh sahifa", callback_data="back_to_main")]
    ])


def error_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Bosh sahifa", callback_data="back_to_main")]
    ])


async def safe_delete(msg):
    try:
        await msg.delete()
    except:
        pass


# ==================== START ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text(
            "🤖 Botga xush kelibsiz!\n\nKerakli kategoriyani tanlang:",
            reply_markup=main_keyboard()
        )
    elif update.callback_query:
        await update.callback_query.message.edit_text(
            "🤖 Botga xush kelibsiz!\n\nKerakli kategoriyani tanlang:",
            reply_markup=main_keyboard()
        )
    return MAIN_MENU


async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.edit_text(
        "🤖 Botga xush kelibsiz!\n\nKerakli kategoriyani tanlang:",
        reply_markup=main_keyboard()
    )
    return MAIN_MENU


# ==================== KATEGORIYA ====================
async def category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "cat_1":
        await query.message.edit_text("📝 Matn yozing:")
        return TEXT_STYLE
    elif data == "cat_2":
        await query.message.edit_text("⭕️ Dumaloq qilish uchun video yuboring:")
        return VIDEO_ROUND
    elif data == "cat_3":
        await query.message.edit_text(
            "🎵 Qo'shiq/video nomini yozing\n"
            "yoki Instagram/TikTok/YouTube linkini yuboring:"
        )
        return MUSIC_SEARCH

    return MAIN_MENU


# ==================== 1. MATN STILLARI ====================
STYLE_KEYBOARD = [
    [InlineKeyboardButton("🔤 Bold (Qalin)", callback_data="style_thick")],
    [InlineKeyboardButton("📐 Italic (Yotiq)", callback_data="style_slant")],
    [InlineKeyboardButton("🔠 Sans Serif", callback_data="style_sans")],
    [InlineKeyboardButton("🔡 Monospace", callback_data="style_monospace")],
    [InlineKeyboardButton("✍️ Script (Qo'lyozma)", callback_data="style_script")],
    [InlineKeyboardButton("🎯 Fraktur (Gothic)", callback_data="style_fraktur")],
    [InlineKeyboardButton("⚡️ Double-struck", callback_data="style_double")],
    [InlineKeyboardButton("🔲 Ingichka", callback_data="style_thin")],
    [InlineKeyboardButton("➖ Strikethrough", callback_data="style_strikethrough")],
    [InlineKeyboardButton("__Underline", callback_data="style_underline")],
    [InlineKeyboardButton("📊 Barchasi", callback_data="style_all")],
    [InlineKeyboardButton("🏠 Bosh sahifa", callback_data="back_to_main")]
]

STYLE_NAMES = {
    "thick": "Qalin (Bold)", "slant": "Yotiq (Italic)",
    "sans": "Sans Serif", "monospace": "Monospace",
    "script": "Script (Qo'lyozma)", "fraktur": "Fraktur (Gothic)",
    "double": "Double-struck", "thin": "Ingichka (Thin)",
    "strikethrough": "Strikethrough", "underline": "Underline"
}


async def text_style_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    context.user_data['original_text'] = text
    await update.message.reply_text(
        f"📝 Sizning matningiz:\n\"{text}\"\n\nQaysi shriftni tanlaysiz?",
        reply_markup=InlineKeyboardMarkup(STYLE_KEYBOARD)
    )
    return TEXT_STYLE_SELECT


async def style_select_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    original_text = context.user_data.get('original_text', '')
    style = query.data.replace("style_", "")

    if style == "all":
        response = "🎨 Barcha shriftlar:\n\n"
        for name, key in STYLE_NAMES.items():
            styled = apply_text_style(original_text, name)
            response += f"{key}:\n{styled}\n\n"
    else:
        styled_text = apply_text_style(original_text, style)
        response = f"🎨 {STYLE_NAMES.get(style, 'Styled')} shrift:\n\n{styled_text}"

    response += f"\n\n{CONTACT}"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Boshqa shrift", callback_data="more_styles")],
        [InlineKeyboardButton("🏠 Bosh sahifa", callback_data="back_to_main")]
    ])

    await query.message.reply_text(response, reply_markup=keyboard)
    return TEXT_STYLE_SELECT


async def more_styles_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    original_text = context.user_data.get('original_text', '')
    await query.message.reply_text(
        f"📝 Sizning matningiz:\n\"{original_text}\"\n\nQaysi shriftni tanlaysiz?",
        reply_markup=InlineKeyboardMarkup(STYLE_KEYBOARD)
    )
    return TEXT_STYLE_SELECT


# ==================== 2. VIDEO DUMALOQ ====================
async def video_round_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = await update.message.reply_text("⏳ Video qayta ishlanmoqda...")
    try:
        import subprocess

        file = await update.message.video.get_file()
        video_path = f"downloads/temp_{int(time.time())}.mp4"
        output_path = f"downloads/round_{int(time.time())}.mp4"

        await file.download_to_drive(video_path)

        cmd = [
            'ffmpeg', '-i', video_path,
            '-vf', 'scale=640:640:force_original_aspect_ratio=increase,crop=640:640',
            '-c:v', 'libx264', '-c:a', 'copy', '-y', output_path
        ]
        subprocess.run(cmd, check=True, capture_output=True)

        with open(output_path, 'rb') as video:
            await update.message.reply_video_note(video_note=video)

        await safe_delete(status)

        for f in [video_path, output_path]:
            try:
                os.remove(f)
            except:
                pass

        await update.message.reply_text(
            f"✅ Video dumaloq qilindi!\n\n{CONTACT}",
            reply_markup=error_keyboard()
        )

    except Exception as e:
        logger.error(f"Video round error: {e}")
        await status.edit_text(f"❌ Xatolik: {str(e)}\n\n{CONTACT}")

    return MAIN_MENU


# ==================== 3. MUSIQA/VIDEO ====================
async def music_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query_text = update.message.text
    uid = update.message.from_user.id

    is_link = any(d in query_text.lower() for d in [
        'youtube.com', 'youtu.be', 'instagram.com',
        'tiktok.com', 'instagr.am', 'vm.tiktok.com'
    ])

    if is_link:
        status_msg = await update.message.reply_text("⏳ Video yuklanmoqda...")
        try:
            # Async thread'da yuklab olish (botni bloklamamaydi)
            loop = asyncio.get_event_loop()
            filename = await loop.run_in_executor(None, download_link_video, query_text)

            if not filename:
                raise Exception("Fayl yuklanmadi")

            await status_msg.edit_text("📤 Yuborilmoqda...")

            try:
                with open(filename, 'rb') as f:
                    await update.message.reply_video(
                        video=f,
                        supports_streaming=True,
                        read_timeout=180,
                        write_timeout=180,
                        connect_timeout=60,
                        pool_timeout=60
                    )
            except Exception as se:
                if "timed out" not in str(se).lower():
                    raise se

            try:
                os.remove(filename)
            except:
                pass

            await safe_delete(status_msg)

            # URL saqlash MP3 uchun
            if uid not in user_data:
                user_data[uid] = {}
            user_data[uid]["selected_url"] = query_text
            user_data[uid].pop("results", None)  # Oldingi natijalarni tozalash

            await update.message.reply_text(
                f"✅ Video yuklandi!\n\nYana yuklab olishni xohlaysizmi?\n\n{CONTACT}",
                reply_markup=after_download_keyboard()
            )

        except Exception as e:
            logger.error(f"Link download error: {e}")
            await safe_delete(status_msg)
            await update.message.reply_text(
                f"❌ Video yuklanmadi.\n\n"
                f"Sabablari:\n"
                f"• Video 50MB dan katta\n"
                f"• Link noto'g'ri yoki o'chirilgan\n"
                f"• Video private\n\n"
                f"{CONTACT}",
                reply_markup=error_keyboard()
            )

        return MUSIC_SEARCH

    else:
        status_msg = await update.message.reply_text("🔍 Qidirilmoqda...")

        # Async thread'da qidirish
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, search_youtube, query_text)

        await safe_delete(status_msg)

        if not results:
            await update.message.reply_text(
                f"❌ Hech narsa topilmadi.\n\n{CONTACT}",
                reply_markup=error_keyboard()
            )
            return MUSIC_SEARCH

        if uid not in user_data:
            user_data[uid] = {}
        user_data[uid]['results'] = results

        keyboard = []
        for i, video in enumerate(results):
            dur = int(video['duration']) if video['duration'] else 0
            duration = f"{dur // 60}:{dur % 60:02d}" if dur > 0 else "?"
            title = video['title'][:38]
            keyboard.append([InlineKeyboardButton(
                f"🎵 {title}... ({duration})",
                callback_data=f"select_{i}"
            )])

        keyboard.append([InlineKeyboardButton("🏠 Bosh sahifa", callback_data="back_to_main")])

        await update.message.reply_text(
            f"🎶 Natijalar:\n\nBirini tanlang 👇\n\n{CONTACT}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return MUSIC_SEARCH


async def select_song(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = query.from_user.id
    index = int(query.data.split("_")[1])

    results = user_data.get(uid, {}).get("results", [])
    if not results or index >= len(results):
        await query.message.reply_text(f"❌ Xatolik. Qaytadan qidiring.\n\n{CONTACT}")
        return MUSIC_SEARCH

    selected = results[index]
    user_data[uid]["selected_url"] = selected["url"]
    user_data[uid]["selected_title"] = selected["title"]

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎵 MP3", callback_data="mp3")],
        [
            InlineKeyboardButton("360p", callback_data="v_360"),
            InlineKeyboardButton("720p", callback_data="v_720"),
            InlineKeyboardButton("1080p", callback_data="v_1080")
        ],
        [InlineKeyboardButton("🏠 Bosh sahifa", callback_data="back_to_main")]
    ])

    await query.message.reply_text(
        f"🎶 {selected['title']}\n\nFormatni tanlang 👇",
        reply_markup=keyboard
    )
    return MUSIC_SEARCH


async def send_mp3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = query.from_user.id
    url = user_data.get(uid, {}).get("selected_url")

    if not url:
        await query.message.reply_text(
            f"❌ URL topilmadi. Qaytadan qidiring.\n\n{CONTACT}",
            reply_markup=error_keyboard()
        )
        return MUSIC_SEARCH

    status_msg = await query.message.reply_text("🎧 MP3 yuklanmoqda...")

    try:
        # Async thread'da yuklab olish
        loop = asyncio.get_event_loop()
        file_path = await loop.run_in_executor(None, download_mp3, url)

        if not file_path or not os.path.exists(file_path):
            await status_msg.edit_text(
                f"❌ MP3 yuklanmadi. Qaytadan urinib ko'ring.\n\n{CONTACT}"
            )
            return MUSIC_SEARCH

        await status_msg.edit_text("📤 Yuborilmoqda...")

        title = user_data.get(uid, {}).get("selected_title", "Audio")

        with open(file_path, 'rb') as f:
            await query.message.reply_audio(
                audio=f,
                title=title,
                read_timeout=120,
                write_timeout=120
            )

        try:
            os.remove(file_path)
        except:
            pass

        await safe_delete(status_msg)

        await query.message.reply_text(
            f"✅ MP3 tayyor!\n\n{CONTACT}",
            reply_markup=after_mp3_keyboard()
        )

    except Exception as e:
        logger.error(f"Send MP3 error: {e}")
        try:
            await status_msg.edit_text(f"❌ Xatolik yuz berdi.\n\n{CONTACT}")
        except:
            pass

    return MUSIC_SEARCH


async def send_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = query.from_user.id
    quality = query.data.split("_")[1]
    url = user_data.get(uid, {}).get("selected_url")

    if not url:
        await query.message.reply_text(
            f"❌ URL topilmadi. Qaytadan qidiring.\n\n{CONTACT}",
            reply_markup=error_keyboard()
        )
        return MUSIC_SEARCH

    status_msg = await query.message.reply_text(f"🎬 {quality}p yuklanmoqda...")

    try:
        # Async thread'da yuklab olish
        loop = asyncio.get_event_loop()
        file_path = await loop.run_in_executor(None, download_video, url, quality)

        if not file_path or not os.path.exists(file_path):
            await status_msg.edit_text(
                f"❌ {quality}p yuklanmadi. Boshqa sifatni tanlang.\n\n{CONTACT}"
            )
            return MUSIC_SEARCH

        await status_msg.edit_text("📤 Yuborilmoqda...")

        try:
            with open(file_path, 'rb') as f:
                await query.message.reply_video(
                    video=f,
                    caption=f"🎥 {quality}p tayyor!",
                    supports_streaming=True,
                    read_timeout=180,
                    write_timeout=180,
                    connect_timeout=60,
                    pool_timeout=60
                )
        except Exception as se:
            if "timed out" not in str(se).lower():
                raise se

        try:
            os.remove(file_path)
        except:
            pass

        await safe_delete(status_msg)

        await query.message.reply_text(
            f"✅ Video yuklandi!\n\nYana yuklab olishni xohlaysizmi?\n\n{CONTACT}",
            reply_markup=after_download_keyboard()
        )

    except Exception as e:
        logger.error(f"Send video error: {e}")
        try:
            await status_msg.edit_text(f"❌ Xatolik yuz berdi.\n\n{CONTACT}")
        except:
            pass

    return MUSIC_SEARCH


# ==================== BEKOR QILISH ====================
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Bekor qilindi.")
    return ConversationHandler.END


# ==================== MAIN ====================
def main():
    TOKEN = "8318843317:AAFLmqq_x_qn57btjj_HZS2yvNqowK4OYrw"

    os.makedirs("downloads", exist_ok=True)

    print("🔄 Bot yuklanmoqda...")

    try:
        application = (
            Application.builder()
            .token(TOKEN)
            .read_timeout(30)
            .write_timeout(30)
            .connect_timeout(30)
            .pool_timeout(30)
            .build()
        )

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={
                MAIN_MENU: [
                    CallbackQueryHandler(back_to_main, pattern="^back_to_main$"),
                    CallbackQueryHandler(category_handler)
                ],
                TEXT_STYLE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, text_style_handler)
                ],
                TEXT_STYLE_SELECT: [
                    CallbackQueryHandler(back_to_main, pattern="^back_to_main$"),
                    CallbackQueryHandler(more_styles_handler, pattern="^more_styles$"),
                    CallbackQueryHandler(style_select_handler, pattern="^style_")
                ],
                VIDEO_ROUND: [
                    MessageHandler(filters.VIDEO, video_round_handler)
                ],
                MUSIC_SEARCH: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, music_search_handler),
                    CallbackQueryHandler(back_to_main, pattern="^back_to_main$"),
                    CallbackQueryHandler(select_song, pattern="^select_"),
                    CallbackQueryHandler(send_mp3, pattern="^mp3$"),
                    CallbackQueryHandler(send_video, pattern="^v_"),
                    CallbackQueryHandler(category_handler, pattern="^cat_3$")
                ],
            },
            fallbacks=[CommandHandler('cancel', cancel)],
            allow_reentry=True
        )

        application.add_handler(conv_handler)

        print("🤖 Bot ishga tushdi!")

        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True  # Eski xabarlarni o'tkazib yuborish
        )

    except Exception as e:
        print(f"❌ Xatolik: {e}")
        traceback.print_exc()


if __name__ == '__main__':
    main()