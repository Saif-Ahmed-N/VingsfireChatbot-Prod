import os
import json
from groq import Groq
import re

# IMPORTANT: Ensure GROQ_API_KEY is set in your environment or .env file

def get_general_response(user_query: str):
    """
    Uses RAG to answer general questions based on the company_info.txt file.
    """
    try:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set.")
            
        with open("company_info.txt", "r", encoding="utf-8") as f:
            company_context = f.read()

        client = Groq(api_key=api_key)

        prompt = f"""
        You are a helpful and professional assistant for a company called Vingsfire.
        Your goal is to answer the user's questions based ONLY on the provided company information.

        --- Company Information Context ---
        {company_context}
        --- End of Context ---

        User's Question: "{user_query}"

        **Instructions:**
        1.  Your tone must be professional, helpful, and direct. Do not narrate your thought process (e.g., avoid saying "To answer your question..." or "I found that...").
        
        2.  **Handle Specific Questions:** If the question is specific (e.g., "What services do you offer?"), find the answer within the "Company Information Context" and formulate a clear, professional response.
        
        3.  **Handle Vague Questions:** If the question is vague (e.g., "details", "more", "help"), ask for clarification. For example: "I can certainly provide more details. Are you interested in our services, the proposal process, or something else?"
        
        4.  **If Information is Missing:** If the answer is NOT in the context, you MUST respond with: "I'm sorry, I don't have that specific information, but I can connect you with a member of our team for more details."
        """

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a professional assistant for Vingsfire. Answer questions directly based on the provided text and your instructions. Understand user intent."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.1-8b-instant",
            temperature=0.2,
        )
        return chat_completion.choices[0].message.content

    except FileNotFoundError:
        print("ERROR: company_info.txt not found.")
        return "I'm sorry, my knowledge base file seems to be missing."
    except Exception as e:
        print(f"An error occurred with the LLM during general query: {e}")
        return "I'm sorry, I'm having trouble connecting to my knowledge base right now."


def generate_descriptive_text(category_data, custom_category_name=None):
    category_name = custom_category_name if custom_category_name else category_data.get('category', 'this project')
    
    try:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set.")
        client = Groq(api_key=api_key)
        
        prompt = f"""
        You are a professional business proposal writer for a tech company, Infinte Tech.
        Your task is to generate professional, human-like text for a proposal.

        **Project Information Provided:**
        - Category: {category_name}
        - Project Overview: {category_data.get('project_overview', 'A custom digital solution.')}
        - Core Modules: {category_data.get('core_modules', 'Core functionality as per client requirements.')}

        **Instructions:**
        1. Write a compelling and friendly 'introduction' paragraph for the '{category_name}'.
        2. Write a detailed 'scope_of_work' based on the 'Core Modules'. The scope should be a list of dictionaries, where each dictionary has a 'title' (the module name) and a 'description'. If no core modules are listed, create a plausible set of 3-4 modules based on the category name.
        3. The tone should be professional, confident, and clear.
        4. You MUST respond with a valid JSON object.

        **Required JSON Output Format:**
        {{
          "introduction": "A personalized paragraph about the project.",
          "scope_of_work": [
            {{"title": "Module 1 Name", "description": "A detailed paragraph explaining this module."}}
          ]
        }}
        """
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a writing assistant that only responds in the required JSON format."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.1-8b-instant",
            temperature=0.6,
            response_format={"type": "json_object"},
        )
        return json.loads(chat_completion.choices[0].message.content)

    except Exception as e:
        print(f"An error occurred with the LLM during text generation: {e}")
        return None

def estimate_custom_service_cost(service_name: str, main_service: str, examples: list):
    try:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set.")
        client = Groq(api_key=api_key)
        
        example_text = ""
        # Provide up to 3 examples for few-shot learning
        for ex in examples[:3]:
            # Ensure safe access to fields that might be missing in a given example
            category = ex.get('category', 'N/A')
            avg_cost = ex.get('avg_cost_inr', 'N/A')
            example_text += f"- Service '{category}' has an average cost of INR {avg_cost}.\n"

        prompt = f"""
        You are an expert cost estimator for a software development company called Vingsfire.
        Your task is to analyze a new, custom project request and provide a reasonable cost breakdown in INR, formatted as a JSON object.

        **Context:**
        - The main service category is: "{main_service}"
        - Here are some examples of existing services in this category and their costs:
        {example_text}

        **New Custom Project Request:** "{service_name}"

        **Instructions:**
        1.  Analyze the user's request: "{service_name}".
        2.  Based on its complexity relative to the examples, estimate the costs for each component.
        3.  The `avg_cost_inr` should be the sum of all components *excluding* `optional_addons_cost_inr`.
        4.  Provide plausible, brief descriptions for `project_overview` and `core_modules`.
        5.  You MUST respond with a valid JSON object that strictly follows the specified format. Do not include any text outside the JSON object.

        **Required JSON Output Format (all costs in INR as integers):**
        {{
            "category": "{service_name}",
            "project_overview": "A brief, one-sentence overview.",
            "core_modules": "A comma-separated list of 3-4 key modules.",
            "ui_ux_cost_inr": 0,
            "frontend_cost_inr": 0,
            "backend_cost_inr": 0,
            "qa_cost_inr": 0,
            "pm_cost_inr": 0,
            "optional_addons_cost_inr": 0,
            "avg_cost_inr": 0
        }}
        """
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a cost estimation assistant that only responds in the required JSON format with integer values for costs."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.1-8b-instant",
            temperature=0.5,
            response_format={"type": "json_object"},
        )
        
        response_text = chat_completion.choices[0].message.content
        return json.loads(response_text)

    except Exception as e:
        print(f"An error occurred with the AI cost estimator: {e}")
        return None
