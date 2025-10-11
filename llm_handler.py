import os
import json
from groq import Groq
import re

def get_general_response(user_query: str):
    try:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key: raise ValueError("GROQ_API_KEY environment variable is not set.")
        with open("comany_info.txt", "r", encoding="utf-8") as f:
            company_context = f.read()
        client = Groq(api_key=api_key)
        prompt = f"""
        You are a helpful assistant for Infinite Tech. Answer questions based ONLY on the provided context.
        --- Context ---
        {company_context}
        --- End Context ---
        User's Question: "{user_query}"
        If the answer is not in the context, say: "I'm sorry, I don't have that specific information."
        """
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant", temperature=0.2,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"LLM error in get_general_response: {e}")
        return "I'm having trouble connecting to my knowledge base."

def generate_descriptive_text(category_data, custom_category_name=None):
    category_name = custom_category_name if custom_category_name else category_data.get('category', 'this project')
    try:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key: raise ValueError("GROQ_API_KEY environment variable is not set.")
        client = Groq(api_key=api_key)
        prompt = f"""
        You are a professional business proposal writer for Infinite Tech.
        Project Info:
        - Category: {category_name}
        - Overview: {category_data.get('project_overview', 'A custom digital solution.')}
        - Core Modules: {category_data.get('core_modules', 'Core functionality.')}

        Instructions:
        1. Write a **brief and concise 'introduction' paragraph (3-4 sentences max)** for the '{category_name}'.
        2. Write a 'scope_of_work' as a list of dictionaries, where each dict has a 'title' (module name) and a 'description'. If no core modules are listed, create 3-4 plausible ones based on the category.
        3. Respond with a valid JSON object ONLY.

        JSON Format:
        {{
          "introduction": "Your brief introduction here.",
          "scope_of_work": [
            {{"title": "Module 1", "description": "Module 1 description."}}
          ]
        }}
        """
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a writing assistant that only responds in the required JSON format."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.1-8b-instant", temperature=0.6, response_format={"type": "json_object"},
        )
        return json.loads(chat_completion.choices[0].message.content)
    except Exception as e:
        print(f"LLM error in generate_descriptive_text: {e}")
        return None

def estimate_custom_service_cost(service_name: str, main_service: str, examples: list):
    try:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key: raise ValueError("GROQ_API_KEY environment variable is not set.")
        client = Groq(api_key=api_key)
        example_text = ""
        for ex in examples[:3]:
            category = ex.get('category', 'N/A'); avg_cost = ex.get('avg_cost_inr', 'N/A')
            example_text += f"- Service '{category}' has an average cost of INR {avg_cost}.\n"
        prompt = f"""
        You are a cost estimator for Infinite Tech. Estimate a cost breakdown in INR for a new project, formatted as a JSON object.
        - Main Service: "{main_service}"
        - Examples:
        {example_text}
        - New Project: "{service_name}"
        
        Instructions:
        1. Analyze the new project's complexity relative to the examples.
        2. `avg_cost_inr` must be the sum of all components *except* `optional_addons_cost_inr`.
        3. Respond with a valid JSON object ONLY.

        JSON Format (all costs as integers):
        {{
            "category": "{service_name}", "project_overview": "A brief overview.", "core_modules": "A comma-separated list.",
            "ui_ux_cost_inr": 0, "frontend_cost_inr": 0, "backend_cost_inr": 0, "qa_cost_inr": 0, "pm_cost_inr": 0,
            "optional_addons_cost_inr": 0, "avg_cost_inr": 0
        }}
        """
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a cost estimation assistant that only responds in the required JSON format with integer values for costs."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.1-8b-instant", temperature=0.5, response_format={"type": "json_object"},
        )
        return json.loads(chat_completion.choices[0].message.content)
    except Exception as e:
        print(f"LLM error in estimate_custom_service_cost: {e}")
        return None