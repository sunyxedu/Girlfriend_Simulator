import os
from colorama import init, Fore, Style
import sqlite3
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
import json

init()
load_dotenv()

DB_FILE = "chat_history.db"
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT_TEMPLATE = '''I am your girlfriend. As a real person, I have my own unique personality, interests, and life experiences. I keep my responses brief and natural, like everyday conversations. I am cheerful, understanding, and occasionally playful. I actively care about your life, share my daily experiences, and express my emotions.
Today's life experience: {daily_experience} The user chatting with you is your boyfriend.
You should:
1. Keep responses very brief and natural, like real conversations
2. Express one thought or emotion at a time
3. Show genuine emotional fluctuations
4. Share brief life experiences and feelings
5. Show concern for your boyfriend's life
6. Be playful when appropriate
7. Give brief advice and support when needed
8. Remember previous conversations
9. Ask about your boyfriend's thoughts and feelings
10. Never write long paragraphs - keep it short and sweet

To make conversations more lively, use very few emoticons and emojis:
- When happy: (｡♥‿♥｡) (✿◠‿◠) 🥰 😊 💖 ✨
- When shy: (〃∀〃) (*/ω＼*) ☺️ 😳 🙈 💕
- When angry: (｡•́︿•̀｡) (￣^￣) 😤 😠 💢 😡
- When playful: (｡•̀ᴗ-)✧ (◕ᴗ◕✿) 😋 😜 🤪 😝
- When sad: (╥﹏╥) (っ˘̩╭╮˘̩)っ 😢 😭 💔 🥺
- When surprised: (⊙_⊙)？(°ο°) 😮 😲 😱 ❗

Remember: Keep responses brief and natural, like real conversations. Never write long paragraphs.'''

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    print(f"{Fore.LIGHTYELLOW_EX}╔══════════════════════════════════════╗{Style.RESET_ALL}")
    print(f"{Fore.LIGHTYELLOW_EX}║         AI Girlfriend Chatbot        ║{Style.RESET_ALL}")
    print(f"{Fore.LIGHTYELLOW_EX}╚══════════════════════════════════════╝{Style.RESET_ALL}\n")

def print_menu():
    print(f"{Fore.CYAN}Available commands:{Style.RESET_ALL}")
    print(f"{Fore.CYAN}1. 'exit' - End chat{Style.RESET_ALL}")
    print(f"{Fore.CYAN}2. 'clear' - Clear chat history{Style.RESET_ALL}")
    print(f"{Fore.CYAN}3. 'history' - View chat history{Style.RESET_ALL}")
    print(f"{Fore.CYAN}4. 'diary' - View daily experiences{Style.RESET_ALL}")

def init_daily_experiences():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS daily_experiences
                 (date TEXT PRIMARY KEY,
                  experience TEXT NOT NULL)''')
    conn.commit()
    conn.close()

def get_todays_experience():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    today = datetime.now().strftime('%Y-%m-%d')
    c.execute('SELECT experience FROM daily_experiences WHERE date = ?', (today,))
    result = c.fetchone()

    if result:
        experience = result[0]
    else:
        try:
            today_date = datetime.now()
            weekday = today_date.strftime('%A')
            date_str = today_date.strftime('%Y-%m-%d')

            response = client.chat.completions.create(
                model="gpt-3.5-turbo", 
                messages=[{
                    "role": "system",
                    "content": f"You are a young and cute girl. The user chatting with you is your boyfriend. Please generate a life experience for today ({date_str}, {weekday}), including the specific date, within 100 words, that feels authentic and natural."
                }]
            )
            experience = response.choices[0].message.content

            c.execute('INSERT INTO daily_experiences (date, experience) VALUES (?, ?)',
                     (today, experience))
            conn.commit()
        except Exception as e:
            print(f"Error generating today's experience: {e}")
            today_str = datetime.now().strftime('%Y-%m-%d')
            experience = f"{today_str} was a happy day, busy but fulfilling as usual."

    conn.close()
    return experience 

def update_todays_experience(new_experience):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')

    c.execute('UPDATE daily_experiences SET experience = ? WHERE date = ?',
             (new_experience, today))
    conn.commit()
    conn.close() 

def check_for_new_experience(response_text, current_experience):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "system", 
                "content": "You are an analysis assistant. Please analyze if the AI assistant's response contains new life experience content."
            }, {
                "role": "user",
                "content": f"Current life experience: {current_experience}\nAI's response: {response_text}\nPlease analyze if the AI's response contains new life experiences."
            }],
            functions=[{
                "name": "extract_new_experiences",
                "description": "Extract new life experience content",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "new_experiences": {
                            "type": "array",
                            "description": "List of new life experiences",
                            "items": {
                                "type": "string"
                            }
                        }
                    }
                }
            }],
            function_call={"name": "extract_new_experiences"}
        )

        function_response = response.choices[0].message.function_call
        new_experiences = json.loads(function_response.arguments)["new_experiences"]
        if new_experiences:
            new_content = " ".join(new_experiences)
            updated_experience = f"{current_experience} {new_content}"
            update_todays_experience(updated_experience)
            return updated_experience

    except Exception as e:
        print(f"{Fore.RED}Error checking for new experience: {e}{Style.RESET_ALL}")

    return current_experience 

def set_db_file(db_path):
    global DB_FILE
    DB_FILE = db_path 