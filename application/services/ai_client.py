import requests
import json
from flask import current_app

class AIService:
    """
    Service layer to handle communication between Flicket and the 
    AI Proxy or external LLMs.
    """

    @staticmethod
    def get_summary(text):
        # 1. Configuration Retrieval
        url = current_app.config.get('AI_ENDPOINT')
        api_key = current_app.config.get('AI_API_KEY')
        provider = current_app.config.get('AI_PROVIDER', '').lower()
        
        if not url or not api_key:
            current_app.logger.error("AI Configuration missing: Check AI_ENDPOINT and AI_API_KEY")
            return "AI Summary unavailable (Config Error)."

        # Define the system prompt and instructions
        system_instruction = (
            "You are an expert Site Reliability Engineer (SRE). "
            "Analyze the following helpdesk ticket and provide three distinct sections:\n"
            "1. PROBLEM STATEMENT: A neutral, fact-based summary. DO NOT include theories.\n"
            "2. HYPOTHESIS: Most likely root causes based on symptoms.\n"
            "3. SUGGESTED REMEDIATION: Specific, actionable steps. Format as commands or config changes where possible."
        )
        user_message = f"Analyze this ticket content: {text}"

        # 2. Payload Construction (Dynamic based on Provider)
        payload = {}

        # Format A: Industry Standard (OpenAI / Anthropic / Ollama standard chat completions)
        if provider in ['openai', 'azure', 'ollama']:
            payload = {
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.5
            }
            
        # Format B: Proxy/Custom String Format
        elif provider in ['pluralsight', 'custom_proxy']:
            prompt_template = f"SYSTEM: {system_instruction}\n\nUSER: {user_message}"
            payload = {
                "prompt": prompt_template
            }
            
        # Fallback: Default to industry standard if unspecified
        else:
            current_app.logger.warning(f"Unknown provider '{provider}'. Defaulting to standard OpenAI formatting.")
            payload = {
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_message}
                ]
            }

        # 3. Headers
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        try:
            # 4. Request Execution
            response = requests.post(
                url, 
                json=payload, 
                headers=headers, 
                timeout=15, 
                allow_redirects=True
            )

            response.raise_for_status()
            data = response.json()
            
            # 5. Response Parsing (Also dynamic based on provider)
            
            # Parsing for Proxy/Custom Format
            if provider in ['pluralsight', 'custom_proxy'] and 'response' in data:
                return data['response'].strip()
            
            # Parsing for Industry Standard (OpenAI-style response)
            if 'choices' in data and len(data['choices']) > 0:
                return data['choices'][0]['message']['content'].strip()
            
            # Generic catch-all in case the standard format is returned by the proxy
            if 'response' in data:
                return data['response'].strip()
                
            current_app.logger.warning(f"AI returned unexpected JSON structure: {data}")
            return "AI was unable to format a summary."

        except requests.exceptions.HTTPError as http_err:
            current_app.logger.error(f"HTTP error occurred: {http_err} - Response: {response.text}")
            return "AI Service error (Check Sandbox Status)."
        except requests.exceptions.ConnectionError:
            current_app.logger.error("Could not connect to the AI endpoint. Is it offline?")
            return "AI Service is currently offline."
        except Exception as e:
            current_app.logger.error(f"Unexpected error in AIService: {str(e)}")
            return "An error occurred while generating the summary."