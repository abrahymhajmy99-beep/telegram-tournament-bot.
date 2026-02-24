import logging
import random
import sqlite3
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from datetime import datetime, timedelta

# ================== إعداد البوت ==================
TOKEN = "8693180386:AAFH_gjjxXSXxDemM1nRgUc-9VFEfhSLZko"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

DB_PATH = "tournament.db"

# ================== قاعدة البيانات ==================
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS teams (
            name TEXT PRIMARY KEY
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS players (
            name TEXT,
            team TEXT,
            goals INTEGER DEFAULT 0,
            PRIMARY KEY(name, team)
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team1 TEXT,
            team2 TEXT,
            score1 INTEGER,
            score2 INTEGER,
            stage TEXT,
            date TEXT
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY
        )""")

# ================== دوال مساعدة ==================
def get_all_teams():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        return [row[0] for row in c.fetchall() if c.execute("SELECT name FROM teams")]

def reset_tournament():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM matches")

def get_players(team):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT name FROM players WHERE team=?", (team,))
        return [row[0] for row in c.fetchall()]

def get_match(match_id):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT id, team1, team2, score1, score2 FROM matches WHERE id=?", (match_id,))
        return c.fetchone()

# ================== أوامر البوت ==================
def start(update: Update, context: CallbackContext):
    msg = (
        "🏆 بطولة الدفعة الاحترافية!\n"
        "الأوامر:\n"
        "/addteam اسم_الفريق\n"
        "/removeteam اسم_الفريق\n"
        "/addplayer اسم_الفريق اسم_اللاعب\n"
        "/players اسم_الفريق\n"
        "/groups\n"
        "/schedule - عرض جدول المباريات\n"
        "/result match_id أهداف_الفريق1 scorers_الفريق1 أهداف_الفريق2 scorers_الفريق2\n"
        "⚠️ إذا أكثر من هداف، افصل الأسماء بفاصلة بدون فراغ\n"
        "/standings - ترتيب الفرق\n"
        "/topscorers - أفضل الهدافين\n"
    )
    update.message.reply_text(msg)

def add_team(update: Update, context: CallbackContext):
    name = " ".join(context.args)
    if not name:
        update.message.reply_text("❌ اكتب اسم الفريق بعد الأمر")
        return
    teams = get_all_teams()
    if len(teams) >= 8:
        update.message.reply_text("❌ تم تسجيل 8 فرق بالفعل")
        return
    if name in teams:
        update.message.reply_text("⚠️ هذا الفريق مسجل مسبقًا")
        return
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO teams (name) VALUES (?)", (name,))
    update.message.reply_text(f"✅ تم تسجيل الفريق: {name}")

def add_player(update: Update, context: CallbackContext):
    if len(context.args) < 2:
        update.message.reply_text("❌ الصيغة: /addplayer اسم_الفريق اسم_اللاعب")
        return
    team = context.args[0]
    player = " ".join(context.args[1:])
    teams = get_all_teams()
    if team not in teams:
        update.message.reply_text("❌ هذا الفريق غير موجود")
        return
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO players (name, team) VALUES (?,?)", (player, team))
    update.message.reply_text(f"✅ تم إضافة اللاعب {player} إلى فريق {team}")

def remove_team(update: Update, context: CallbackContext):
    name = " ".join(context.args)
    if not name:
        update.message.reply_text("❌ اكتب اسم الفريق بعد الأمر")
        return
    teams = get_all_teams()
    if name not in teams:
        update.message.reply_text("⚠️ هذا الفريق غير موجود")
        return
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM teams WHERE name=?", (name,))
        c.execute("DELETE FROM matches WHERE team1=? OR team2=?", (name, name))
        c.execute("DELETE FROM players WHERE team=?", (name,))
    update.message.reply_text(f"🗑️ تم حذف الفريق {name}")
    reset_tournament()

def make_groups(update: Update, context: CallbackContext):
    teams = get_all_teams()
    if len(teams) != 8:
        update.message.reply_text("❌ يجب تسجيل 8 فرق بالضبط")
        return
    random.shuffle(teams)
    groupA = teams[:4]
    groupB = teams[4:]
    reset_tournament()
    start_date = datetime.now()
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        for i in range(4):
            for j in range(i + 1, 4):
                dateA = (start_date + timedelta(days=(i+j)*2)).strftime("%Y-%m-%d %H:%M")
                dateB = (start_date + timedelta(days=(i+j)*2+1)).strftime("%Y-%m-%d %H:%M")
                c.execute("INSERT INTO matches (team1, team2, score1, score2, stage, date) VALUES (?,?,?,?,?,?)",
                          (groupA[i], groupA[j], -1, -1, 'group', dateA))
                c.execute("INSERT INTO matches (team1, team2, score1, score2, stage, date) VALUES (?,?,?,?,?,?)",
                          (groupB[i], groupB[j], -1, -1, 'group', dateB))
    msg = "📋 المجموعات:\n\nGroup A:\n" + "\n".join(groupA) + "\n\nGroup B:\n" + "\n".join(groupB)
    update.message.reply_text(msg)
    update.message.reply_text("📅 جدول المباريات تم إنشاؤه تلقائيًا. استخدم /schedule لرؤيته.")

def show_schedule(update: Update, context: CallbackContext):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT id, team1, team2, date FROM matches ORDER BY date")
        matches = c.fetchall()
    if not matches:
        update.message.reply_text("⚠️ لم يتم توليد أي مباريات بعد")
        return
    msg = "📅 جدول المباريات:\n"
    for mid, t1, t2, date in matches:
        msg += f"ID {mid}: {date}: {t1} vs {t2}\n"
    update.message.reply_text(msg)

def show_players(update: Update, context: CallbackContext):
    if not context.args:
        update.message.reply_text("❌ الصيغة: /players اسم_الفريق")
        return
    team = " ".join(context.args)
    teams = get_all_teams()
    if team not in teams:
        update.message.reply_text("❌ هذا الفريق غير موجود")
        return
    players = get_players(team)
    if not players:
        update.message.reply_text(f"⚠️ لا يوجد لاعبين مسجلين في فريق {team}")
        return
    msg = f"⚽ لاعبي فريق {team}:\n" + "\n".join(players)
    update.message.reply_text(msg)

def record_result(update: Update, context: CallbackContext):
    if len(context.args) != 5:
        update.message.reply_text(
            "❌ الصيغة: /result match_id أهداف_الفريق1 scorers_الفريق1 أهداف_الفريق2 scorers_الفريق2\n"
            "⚠️ إذا أكثر من هداف، افصل الأسماء بفاصلة بدون فراغ"
        )
        return
    try:
        match_id = int(context.args[0])
        score1 = int(context.args[1])
        scorers1 = context.args[2].split(',')
        score2 = int(context.args[3])
        scorers2 = context.args[4].split(',')
    except ValueError:
        update.message.reply_text("❌ يجب أن تكون الأرقام صحيحة")
        return

    match = get_match(match_id)
    if not match:
        update.message.reply_text("❌ هذا الـ match_id غير موجود")
        return

    team1, team2 = match[1], match[2]

    if len(scorers1) != score1 or len(scorers2) != score2:
        update.message.reply_text("❌ عدد الهدافين لا يتطابق مع عدد الأهداف")
        return

    players1 = get_players(team1)
    players2 = get_players(team2)
    if not all(player in players1 for player in scorers1):
        update.message.reply_text(f"❌ أحد اللاعبين في scorers1 غير موجود في فريق {team1}")
        return
    if not all(player in players2 for player in scorers2):
        update.message.reply_text(f"❌ أحد اللاعبين في scorers2 غير موجود في فريق {team2}")
        return

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("UPDATE matches SET score1=?, score2=? WHERE id=?", (score1, score2, match_id))
        for player in scorers1:
            c.execute("UPDATE players SET goals = goals + 1 WHERE name=? AND team=?", (player, team1))
        for player in scorers2:
            c.execute("UPDATE players SET goals = goals + 1 WHERE name=? AND team=?", (player, team2))

    update.message.reply_text(
        f"✅ تم تسجيل النتيجة: {team1} {score1} - {score2} {team2}\n"
        f"الأهداف:\n{team1}: {', '.join(scorers1)}\n{team2}: {', '.join(scorers2)}"
    )

def show_standings(update: Update, context: CallbackContext):
    teams = get_all_teams()
    table = []
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        for team in teams:
            c.execute("SELECT score1, score2, team1, team2 FROM matches")
            wins = draws = losses = 0
            for s1, s2, t1, t2 in c.fetchall():
                if t1 == team:
                    if s1 == -1: continue
                    if s1 > s2: wins += 1
                    elif s1 == s2: draws += 1
                    else: losses += 1
                elif t2 == team:
                    if s2 == -1: continue
                    if s2 > s1: wins += 1
                    elif s1 == s2: draws += 1
                    else: losses += 1
            points = wins*3 + draws
            table.append((team, points, wins, draws, losses))
    table.sort(key=lambda x: x[1], reverse=True)
    msg = "🏆 ترتيب الفرق:\n"
    for t, pts, w, d, l in table:
        msg += f"{t}: {pts} نقاط (فوز:{w} تعادل:{d} خسارة:{l})\n"
    update.message.reply_text(msg)

def show_top_scorers(update: Update, context: CallbackContext):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT name, team, goals FROM players ORDER BY goals DESC LIMIT 10")
        top = c.fetchall()
    if not top:
        update.message.reply_text("⚠️ لا يوجد أهداف مسجلة بعد")
        return
    msg = "🥇 أفضل الهدافين:\n"
    for name, team, goals in top:
        msg += f"{name} ({team}): {goals} هدف\n"
    update.message.reply_text(msg)

# ================== تشغيل البوت ==================
def main():
    init_db()
    updater = Updater(TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("addteam", add_team))
    dp.add_handler(CommandHandler("removeteam", remove_team))
    dp.add_handler(CommandHandler("addplayer", add_player))
    dp.add_handler(CommandHandler("players", show_players))
    dp.add_handler(CommandHandler("groups", make_groups))
    dp.add_handler(CommandHandler("schedule", show_schedule))
    dp.add_handler(CommandHandler("result", record_result))
    dp.add_handler(CommandHandler("standings", show_standings))
    dp.add_handler(CommandHandler("topscorers", show_top_scorers))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()