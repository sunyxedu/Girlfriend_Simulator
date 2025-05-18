import openai
import json
import time
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

try:
    with open("girlfriend question answer.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    formatted_data = []
    for item in data:
        formatted_data.append({
            "messages": [
                {"role": "user", "content": item["question"]},
                {"role": "assistant", "content": item["answer"]}
            ]
        })

    jsonl_file = "girlfriend_simulator.jsonl"
    with open(jsonl_file, "w", encoding="utf-8") as f:
        for entry in formatted_data:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"Data saved to {jsonl_file}")

    with open(jsonl_file, "rb") as f:
        upload_response = client.files.create(
            file=f,
            purpose="fine-tune"
        )
    training_file_id = upload_response.id
    print("Upload file ID:", training_file_id)

    fine_tune_response = client.fine_tuning.jobs.create(
        training_file=training_file_id,
        model="gpt-4o-2024-08-06",
        hyperparameters={
            "n_epochs": 4
        }
    )
    fine_tune_id = fine_tune_response.id
    print("Fine-tuning job ID:", fine_tune_id)

    def poll_fine_tune_job(ft_id):
        while True:
            try:
                status_response = client.fine_tuning.jobs.retrieve(ft_id)
                status = status_response.status
                print("Current status:", status)
                if status in ["succeeded", "failed", "cancelled"]:
                    return status
                time.sleep(30)
            except Exception as e:
                print(f"Error checking status: {e}")
                time.sleep(60)

    final_status = poll_fine_tune_job(fine_tune_id)

    if final_status == "succeeded":
        print("Fine-tuning completed successfully!")
        fine_tuned_model = f"ft:gpt-4o-2024-08-06:{fine_tune_id}"
        response = client.chat.completions.create(
            model=fine_tuned_model,
            messages=[
                {"role": "user", "content": "Hello, dear!"}
            ]
        )
        print("Model response:", response.choices[0].message.content)
    else:
        print(f"Fine-tuning failed with status: {final_status}")

except FileNotFoundError as e:
    print(f"Error: Could not find the input file - {e}")
except json.JSONDecodeError as e:
    print(f"Error: Invalid JSON format in input file - {e}")
except Exception as e:
    print(f"Unexpected error: {e}")