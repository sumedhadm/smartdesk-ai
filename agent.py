import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

import tools
import db
from prompts import SYSTEM_PROMPT

load_dotenv()

MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
MAX_TOOL_ROUNDS = 3  # stops infinite tool-call loops
MAX_MESSAGE_CHARS = 2000

class MissingAPIKeyError(Exception):
    pass


# Tool definitions sent to the model. This is the ONLY set of actions it can request.
TOOL_DECLARATIONS = [
    {
        "name": "analyze_sales",
        "description": "Calculate sales statistics (total, average, median, best product, "
                       "per-product and per-month sales) from the sales dataset.",
    },
    {
        "name": "create_task",
        "description": "Add a task to the user's task list.",
        "parameters": {
            "type": "object",
            "properties": {
                "task_description": {
                    "type": "string",
                    "description": "Short description of the task to add.",
                }
            },
            "required": ["task_description"],
        },
    },
]

class SmartDeskAgent:
    def __init__(self, task_store: list, user_id: int | None = None):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise MissingAPIKeyError(
                "GEMINI_API_KEY not found. Add it to your .env file and restart the app."
            )
        self.client = genai.Client(api_key=api_key)
        self.task_store = task_store
        self.user_id = user_id
        self.history: list[types.Content] = []
        self.config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=[types.Tool(function_declarations=TOOL_DECLARATIONS)],
        )
        # Whitelist: tool name -> callable. Nothing outside this dict can run.
        self.registry = {
            "analyze_sales": lambda args: tools.analyze_sales(),
            "create_task": self._create_task,
        }

    def _create_task(self, args: dict) -> dict:
        result = tools.create_task(self.task_store, args.get("task_description"))
        if result["status"] == "ok" and self.user_id is not None:
            db.save_task(self.user_id, result["task"]["description"])
        return result

    def _execute_tool(self, name: str, args: dict) -> dict:
        if name not in self.registry:
            return {"status": "error", "message": f"Unknown tool: {name}"}
        try:
            return self.registry[name](args or {})
        except Exception as e:
            return {"status": "error", "message": f"Tool failed: {e}"}

    def chat(self, user_message: str) -> dict:
        user_message = (user_message or "").strip()
        if not user_message:
            return {"reply": "Please type a message first.", "tools_used": []}

        start_len = len(self.history)  # for rollback if the API call fails
        self.history.append(
            types.Content(role="user", parts=[types.Part.from_text(text=user_message)])
        )
        tools_used = []

        try:
            for _ in range(MAX_TOOL_ROUNDS + 1):
                response = self.client.models.generate_content(
                    model=MODEL, contents=self.history, config=self.config
                )
                # Keep the model's full turn (preserves any internal metadata the API needs)
                self.history.append(response.candidates[0].content)

                calls = response.function_calls or []
                if not calls:
                    return {"reply": response.text or "(empty response)", "tools_used": tools_used}

                result_parts = []
                for call in calls:
                    args = dict(call.args or {})
                    result = self._execute_tool(call.name, args)
                    tools_used.append({"name": call.name, "args": args, "result": result})
                    result_parts.append(
                        types.Part.from_function_response(
                            name=call.name, response={"result": result}
                        )
                    )
                self.history.append(types.Content(role="user", parts=result_parts))

            return {"reply": "I couldn't finish that request (too many tool steps).",
                    "tools_used": tools_used}


        except Exception as e:
            print(f"[agent error] {type(e).__name__}: {e}") 
            del self.history[start_len:]  # don't leave a half-finished turn in history
            msg = str(e)
            if "429" in msg or "quota" in msg.lower():
                friendly = "Rate limit reached. Please wait a minute and try again."
            elif "API key" in msg or "401" in msg or "403" in msg:
                friendly = "The API key was rejected. Check GEMINI_API_KEY in your .env."
            else:
                friendly = f"Something went wrong calling the model: {msg[:200]}"
            return {"reply": friendly, "tools_used": tools_used}