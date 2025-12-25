import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

model_to_test = "llama3-8b-8192"

try:
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "Hello",
            }
        ],
        model=model_to_test,
    )
    print(f"Model {model_to_test} is working!")
    print(chat_completion.choices[0].message.content)
except Exception as e:
    print(f"Model {model_to_test} failed: {e}")
    # Fallback check
    print("Listing available models again to pick a valid one:")
    from groq import GroqError
    try:
        models = client.models.list()
        for m in models.data:
            print(f"- {m.id}")
    except Exception as list_e:
        print(f"Failed to list models: {list_e}")
