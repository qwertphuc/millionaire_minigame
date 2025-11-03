import os
import google.generativeai as genai
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class GeminiAISupport:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        
        if not self.api_key:
            raise ValueError(
                "Gemini API key not found."
            )
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    def get_ai_hint(self, question: str, answers: Dict[int, str], explanation: str) -> str:
        # Create a prompt
        prompt = f"""You are an AI assistant helping a player in a millionaire quiz game. 
You have access to verified factual information about the topic and use it as a hint for player.

VERIFIED FACTS:
{explanation}

QUESTION:
{question}

OPTIONS:
A) {answers[1]}
B) {answers[2]}
C) {answers[3]}
D) {answers[4]}

Your task: Provide a helpful hint based ONLY on the verified facts provided above. 
- DO NOT mention the VERIFIED FACTS in response
- DO NOT contradict the verified facts
- Keep your response concise (3-4 sentences)
- Make it sound like you're helping them reason through it, then giving away the answer at the end of the sentence with more human like "i think", "my guess is"

Hint:"""

        try:
            response = self.model.generate_content(prompt)
            ai_hint = response.text.strip()
            
            return ai_hint
            
        except Exception as e:
            # Fallback
            print(f"Gemini API Error: {e}")
            return f"Dựa vào: {explanation[:150]}... Hãy suy nghĩ cẩn thận về thông tin này."
    
    def get_simple_hint(self, explanation: str) -> str:
        sentences = explanation.split('. ')
        if len(sentences) > 0:
            first_sentence = sentences[0] + '.'
            return f"Dựa vào: {first_sentence} Hãy suy nghĩ cẩn thận về thông tin này."
        else:
            return f"Đây là những gì tôi có thể nói với bạn: {explanation[:200]}..."


def create_ai_support(api_key: Optional[str] = None) -> GeminiAISupport:
    return GeminiAISupport(api_key=api_key)
