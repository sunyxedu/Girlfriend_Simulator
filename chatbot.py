from openai import OpenAI
import time
import os
import json
import readline
from dotenv import load_dotenv
import sqlite3
from new_related import fetch_news, check_news_relevance
from database_related import init_database, load_chat_history, save_chat_message, clear_chat_history, view_chat_history, update_daily_experience
from colorama import init, Fore, Style
from utils import (
    clear_screen, print_header, print_menu, init_daily_experiences, 
    get_todays_experience, update_todays_experience,
    check_for_new_experience, SYSTEM_PROMPT_TEMPLATE
)
from rag_utils import init_vector_db, update_vector_db, get_relevant_context, load_chat_history_for_rag, append_message_to_vector_db
import sys
import termios
import tty

init()

DB_FILE = "chat_history.db"
readline.set_completer_delims(' \t\n;')

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

FINE_TUNED_MODEL = "ft:gpt-4o-2024-08-06:personal::Az6qDyVY:ckpt-step-1440"

def view_daily_experiences():
    try:
        clear_screen()
        print(f"{Fore.CYAN}=== Daily Experiences === (Type 'exit' to return){Style.RESET_ALL}")
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        init_daily_experiences()
        c.execute("SELECT date, experience FROM daily_experiences ORDER BY date DESC")
        experiences = c.fetchall()
        conn.close()

        if not experiences:
            print(f"\n{Fore.YELLOW}No daily experiences recorded yet.{Style.RESET_ALL}")
        else:
            for date, experience in experiences:
                print(f"\n{Fore.YELLOW}[{date}]{Style.RESET_ALL}")
                print(f"{experience}")

        while True:
            user_input = input().lower()
            if user_input == 'exit':
                clear_screen()
                print_header()
                print_menu()
                break
    except Exception as e:
        print(f"{Fore.RED}Error viewing daily experiences: {e}{Style.RESET_ALL}")

init_daily_experiences()

def print_typing_animation():
    old_settings = termios.tcgetattr(sys.stdin)
    try:
        tty.setraw(sys.stdin.fileno())

        base_text = f"{Fore.LIGHTMAGENTA_EX}Your sweetheart is typing{Style.RESET_ALL}"
        for _ in range(3):
            sys.stdout.write("\033[2K\r")
            sys.stdout.write(f"{base_text}{Fore.LIGHTMAGENTA_EX}.{Style.RESET_ALL}")
            sys.stdout.flush()
            time.sleep(0.3)

            sys.stdout.write("\033[2K\r")
            sys.stdout.write(f"{base_text}{Fore.LIGHTMAGENTA_EX}..{Style.RESET_ALL}")
            sys.stdout.flush()
            time.sleep(0.3)

            sys.stdout.write("\033[2K\r")
            sys.stdout.write(f"{base_text}{Fore.LIGHTMAGENTA_EX}...{Style.RESET_ALL}")
            sys.stdout.flush()
            time.sleep(0.3)

        sys.stdout.write("\033[2K\r")
        sys.stdout.flush()
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

def should_respond(messages):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a judgment assistant. \
                                You need to determine if the AI girlfriend should respond to the user's message. \
                                If the user's message is a command, greeting, question, news-related, needs emotional support, expresses emotions, greets, or requires a response, then respond; if it's self-talk, meaningless content, or doesn't require a response, then don't respond."
                },
                {
                    "role": "user",
                    "content": "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
                }
            ],
            functions=[{
                "name": "check_response_needed",
                "description": "Based on the conversation before. Determine if the response for the latest message is needed",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "should_respond": {
                            "type": "boolean",
                            "description": "Whether a response is needed"
                        },
                        "reason": {
                            "type": "string",
                            "description": "Reason for the judgment"
                        }
                    },
                    "required": ["should_respond", "reason"]
                }
            }],
            function_call={"name": "check_response_needed"}
        )

        result = json.loads(response.choices[0].message.function_call.arguments)
        # print(f"{Fore.BLUE}Response needed: {result['should_respond']} - {result['reason']}{Style.RESET_ALL}")
        return result["should_respond"]
    except Exception as e:
        print(f"{Fore.RED}Error checking if should respond: {e}{Style.RESET_ALL}")
        return True

class ChatBot:
    def __init__(self, model_name):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model_name
        self.chat_history = self.load_chat_history()
        self.vector_db = init_vector_db()
        messages = load_chat_history_for_rag()
        update_vector_db(self.vector_db, messages)

    def load_chat_history(self):
        try:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute('SELECT role, content FROM chat_history ORDER BY id')
            return [{"role": role, "content": content} for role, content in c.fetchall()]
        except Exception as e:
            print(f"{Fore.RED}Error loading chat history: {e}{Style.RESET_ALL}")
            return []

    def get_response(self, message):
        try:
            print_typing_animation()

            recent_messages = self.chat_history[-4:] if len(self.chat_history) > 4 else self.chat_history
            messages_with_history = [{"role": "system", "content": SYSTEM_PROMPT_TEMPLATE.format(daily_experience=get_todays_experience())}]
            messages_with_history.extend(recent_messages)
            messages_with_history.append({"role": "user", "content": "latest message (judge if it's news): " + message})

            news_check = check_news_relevance(messages_with_history)
            news_context = ""
            if news_check["is_news_related"]:
                if "keywords" in news_check and len(news_check["keywords"]) > 0:
                    for keyword in news_check["keywords"]:
                        news_list = fetch_news(keyword)
                        if news_list:
                            news_context = "Recent related news:\n"
                            for news in news_list:
                                news_context += f"- {news['title']}\n"
                else:
                    news_list = fetch_news("hot topics")
                    if news_list:
                        news_context = "Today's hot news:\n"
                        for news in news_list:
                            news_context += f"- {news['title']}\n"

            recent_messages = self.chat_history[-4:] if len(self.chat_history) > 4 else self.chat_history
            messages_with_history = [{"role": "system", "content": SYSTEM_PROMPT_TEMPLATE.format(daily_experience=get_todays_experience())}]
            messages_with_history.extend(recent_messages)
            messages_with_history.append({"role": "user", "content": news_context})
            messages_with_history.append({"role": "user", "content": "latest message (judge if need respond): " + message})

            if not should_respond(messages_with_history):
                # print(f"{Fore.YELLOW}No response needed for this message.{Style.RESET_ALL}")
                return None

            relevant_context = get_relevant_context(message, self.vector_db)
            rag_context = ""
            if relevant_context:
                rag_context = "Relevant conversation history:\n" + "\n".join([f"- {ctx}" for ctx in relevant_context])
                
            messages = [{"role": "system", "content": SYSTEM_PROMPT_TEMPLATE.format(daily_experience=get_todays_experience())}]
            recent_history = self.chat_history[-6:] if len(self.chat_history) > 6 else self.chat_history
            messages.extend(recent_history)
            messages.append({"role": "user", "content": news_context})
            if rag_context:
                messages.append({"role": "user", "content": rag_context})
                
            messages.append({"role": "system", "content": "Remember that in daily experiences, 'we' refers to me and my boyfriend (the person I'm responding to). If my boyfriend doesn't remember our experience, I should feel shocked."})
            messages.append({"role": "user", "content": message})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )

            response_text = response.choices[0].message.content
            print(f"{Fore.YELLOW}Girlfriend: {response_text}{Style.RESET_ALL}")
            
            self.chat_history.append({"role": "user", "content": message})
            self.chat_history.append({"role": "assistant", "content": response_text})
            
            append_message_to_vector_db(self.vector_db, {"role": "user", "content": message})
            append_message_to_vector_db(self.vector_db, {"role": "assistant", "content": response_text})

            update_daily_experience(check_for_new_experience(response_text, get_todays_experience()))
            return response_text
        except Exception as e:
            print(f"{Fore.RED}Error generating response: {e}{Style.RESET_ALL}")
            return f"Error: {str(e)}"

def chat_with_bot():
    clear_screen()
    print_header()
    print_menu()

    init_database()

    chat_history = load_chat_history(SYSTEM_PROMPT_TEMPLATE.format(daily_experience=get_todays_experience()))

    chatbot = ChatBot(FINE_TUNED_MODEL)
    chatbot.chat_history = chat_history[1:]

    while True:
        user_input = input(f"{Fore.GREEN}You: {Style.RESET_ALL}")

        if user_input.lower() == "exit":
            print(f"\n{Fore.YELLOW}👋 Goodbye! I'll miss you! (｡•́︿•̀｡){Style.RESET_ALL}")
            break
        elif user_input.lower() == "clear":
            clear_chat_history()
            chat_history = load_chat_history(SYSTEM_PROMPT_TEMPLATE.format(daily_experience=get_todays_experience()))
            chatbot.chat_history = chat_history[1:]
            continue
        elif user_input.lower() == "history":
            view_chat_history()
            continue
        elif user_input.lower() == "diary":
            view_daily_experiences()
            continue

        save_chat_message("user", user_input)

        try:
            response = chatbot.get_response(user_input)
            if response:
                save_chat_message("assistant", response)
        except Exception as e:
            print(f"\n{Fore.RED}⚠️ Error: {e}{Style.RESET_ALL}")
            break

if __name__ == "__main__":
    chat_with_bot()