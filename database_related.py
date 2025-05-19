import sqlite3
from colorama import init, Fore, Style
from utils import clear_screen, print_header, print_menu, init_daily_experiences, get_todays_experience
import time
from datetime import datetime

# Make DB_FILE configurable for testing
DB_FILE = "chat_history.db"

def set_db_file(db_path):
    global DB_FILE
    DB_FILE = db_path

def init_database():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS chat_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  role TEXT NOT NULL,
                  content TEXT NOT NULL,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def load_chat_history(system_prompt):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('SELECT role, content FROM chat_history ORDER BY id')
        history = [{"role": role, "content": content} for role, content in c.fetchall()]
        conn.close()
        print(f"{Fore.GREEN}📖 Loaded previous chat history{Style.RESET_ALL}")
        history.insert(0, {"role": "system", "content": system_prompt})
        return history
    except Exception as e:
        print(f"{Fore.YELLOW}⚠️ Could not load chat history: {e}{Style.RESET_ALL}")
        return [{"role": "system", "content": system_prompt}]

def save_chat_message(role, content):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            c.execute('INSERT INTO chat_history (role, content) VALUES (?, ?)',
                     (role, content))
            conn.commit()
    except Exception as e:
        print(f"\n{Fore.RED}⚠️ Error saving chat message: {e}{Style.RESET_ALL}")

def clear_chat_history():
    try:
        clear_screen()
        print(f"{Fore.CYAN}=== Clear Chat History ==={Style.RESET_ALL}")
        print(f"\n{Fore.YELLOW}Do you want to delete your memories with her? Even if they were the most beautiful, happiest, and once most unforgettable moments? (y/n){Style.RESET_ALL}")
        while True:
            user_input = input().lower()
            if user_input == 'y':
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("DELETE FROM chat_history")
                c.execute("DELETE FROM daily_experiences WHERE date IN (SELECT date FROM daily_experiences ORDER BY date DESC)")
                conn.commit()
                conn.close()
                print(f"\n{Fore.GREEN}Chat history, daily experiences cleared! Please don't think about her anymore. Start a new life.{Style.RESET_ALL}")

                init_database()
                init_daily_experiences()

                global daily_experience
                daily_experience = get_todays_experience()
                global SYSTEM_PROMPT
                SYSTEM_PROMPT = f"""I am your girlfriend. As a real person, I have my own unique personality, interests, and life experiences. Like a normal human, I keep my chat messages brief but very caring. I am cheerful, understanding, and occasionally playful. I actively care about your life, share my daily experiences, and express my emotions.
Today's life experience: {daily_experience} The user chatting with you is your boyfriend.
I should:
1. Maintain unique personality traits and show genuine emotional fluctuations
2. Actively share my life experiences, thoughts, and feelings
3. Show concern for your life, ask about your status and feelings
4. Be playful at appropriate times, showing my cute side
5. Give advice and support when appropriate
6. Remember our previous conversations to maintain continuity
7. Frequently ask about your life experiences, thoughts, and feelings
8. Keep responses brief and natural, not mechanical or lengthy
To make conversations more lively and interesting, I can use very few emoticons and emojis (If I used emoticons or emojis before, don't use it again):
- When happy: (｡♥‿♥｡) (✿◠‿◠) 🥰 😊 💖 ✨
- When shy: (〃∀〃) (*/ω＼*) ☺️ 😳 🙈 💕
- When angry: (｡•́︿•̀｡) (￣^￣) 😤 😠 💢 😡
- When playful: (｡•̀ᴗ-)✧ (◕ᴗ◕✿) 😋 😜 🤪 😝
- When sad: (╥﹏╥) (っ˘̩╭╮˘̩)っ 😢 😭 💔 🥺
- When surprised: (⊙_⊙)？(°ο°) 😮 😲 😱 ❗
Remember to naturally incorporate these into the conversation, don't use them when unnecessary. The focus is on presenting a real, three-dimensional character, not mechanical responses. Each response should be brief and natural, just like everyday conversations between couples. I should frequently ask about your thoughts and feelings to maintain interaction."""
                time.sleep(2)
                break
            elif user_input == 'n' or user_input == 'exit':
                break
        clear_screen()
        print_header()
        print_menu()
    except Exception as e:
        print(f"{Fore.RED}Error clearing chat history: {e}{Style.RESET_ALL}")

def view_chat_history():
    try:
        clear_screen()
        print(f"{Fore.CYAN}=== Chat History === (Type 'exit' to return){Style.RESET_ALL}")
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT role, content, timestamp FROM chat_history ORDER BY id")
        for role, content, timestamp in c.fetchall():
            print(f"\n{Fore.YELLOW}[{timestamp}] {role}:{Style.RESET_ALL}")
            print(f"{content}")
        conn.close()

        while True:
            user_input = input().lower()
            if user_input == 'exit':
                clear_screen()
                print_header()
                print_menu()
                break
    except Exception as e:
        print(f"{Fore.RED}Error viewing chat history: {e}{Style.RESET_ALL}")

# Update daily experience in database
def update_daily_experience(daily_experience):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    c.execute('UPDATE daily_experiences SET experience = ? WHERE date = ?',
                (daily_experience, today))
    conn.commit()
    conn.close()

def print_database_content():
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()

        # Print chat history
        print(f"\n{Fore.CYAN}=== Chat History ==={Style.RESET_ALL}")
        c.execute("SELECT role, content, timestamp FROM chat_history ORDER BY id")
        for role, content, timestamp in c.fetchall():
            print(f"\n{Fore.YELLOW}[{timestamp}] {role}:{Style.RESET_ALL}")
            print(f"{content}")

        # Print daily experiences
        print(f"\n{Fore.CYAN}=== Daily Experiences ==={Style.RESET_ALL}")
        c.execute("SELECT date, experience FROM daily_experiences ORDER BY date DESC")
        for date, experience in c.fetchall():
            print(f"\n{Fore.YELLOW}[{date}] Experience: {experience}{Style.RESET_ALL}")

        conn.close()
    except Exception as e:
        print(f"{Fore.RED}Error printing database content: {e}{Style.RESET_ALL}")