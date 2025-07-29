import json
import os
import logging
from dotenv import load_dotenv

import google.generativeai as genai
from typing import Dict, Any

load_dotenv()

# Use existing logger instead of configuring again
logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        """Initialize the Gemini LLM service"""
        self.api_key = os.getenv('GEMINI_API_KEY')
        
        if not self.api_key:
            raise ValueError('Missing Gemini API key in environment variables')
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        logger.info("Gemini LLM service initialized successfully")
    
    # Removed unused functions: analyze_user_response, generate_bot_response, generate_greeting_followup

    def generate_optimized_bot_response(self, conversation_type: str, user_message: str, conversation_history: list, turn_count: int) -> Dict[str, Any]:
        """
        OPTIMIZED: Generate bot response with analysis in a single LLM call for faster response times
        
        Args:
            conversation_type: Type of conversation
            user_message: Latest user message
            conversation_history: Previous conversation messages
            turn_count: Current turn number
            
        Returns:
            Dictionary with response, intent, and other analysis
        """
        try:
            logger.info(f"LLM processing: type={conversation_type}, turn={turn_count}, user_input='{user_message[:50]}...'")
            
            # Create context based on conversation type
            context_prompts = {
                "customer_feedback": "You are conducting a customer feedback survey. Be polite, ask relevant questions about their experience, and keep responses brief.",
                "sales_inquiry": "You are a sales representative. Be helpful, answer questions about products/services, and identify potential sales opportunities.",
                "appointment_reminder": "You are reminding about an upcoming appointment. Be clear about date/time and ask for confirmation.",
                "survey": "You are conducting a survey. Ask clear questions and acknowledge responses appropriately.",
                "support": "You are providing customer support. Be helpful, empathetic, and try to resolve issues.",
                "general": "You are a friendly assistant having a general conversation. Be helpful and engaging."
            }
            
            system_context = context_prompts.get(conversation_type, context_prompts["general"])
            
            # Build conversation history for context (only last 3 exchanges to keep it concise)
            history_text = "\n".join([f"{msg['speaker']}: {msg['message']}" for msg in conversation_history[-6:]])
            
            # Determine if this should be the final response based on turn count or user intent
            is_final_turn = turn_count >= 1 or any(word in user_message.lower() for word in ["no", "nothing", "nope", "that's all", "i'm good"])
            
            prompt = f"""
            {system_context}
            
            Conversation History:
            {history_text}
            
            User just said: "{user_message}"
            Turn count: {turn_count + 1}
            
            IMPORTANT: If user says "no", "nothing", "nope", "that's all" or similar, this means they want to END the conversation. Don't ask more questions.
            
            {"This should be your FINAL response. Wrap up the conversation politely and say goodbye." if is_final_turn else "Continue the conversation naturally."}
            
            Respond with JSON containing:
            1. "response": Your reply (1-2 sentences max, conversational, under 50 words)
            2. "intent": User's intent (positive/negative/neutral/confused/interested/not_interested/wants_to_end)
            3. "confidence": Confidence level (high/medium/low)
            4. "should_continue": true/false (false if conversation should end)
            
            Example:
            {{
                "response": "Thank you for your time. Have a great day!",
                "intent": "wants_to_end",
                "confidence": "high",
                "should_continue": false
            }}
            
            Keep responses very brief and natural for phone conversation.
            """
            
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Try to parse JSON response, fallback to simple response if parsing fails
            try:
                # Clean up response text to extract JSON
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_text = response_text[json_start:json_end]
                    parsed_response = json.loads(json_text)
                    
                    result = {
                        "response": parsed_response.get("response", "Thank you for sharing that with me."),
                        "intent": parsed_response.get("intent", "neutral"),
                        "confidence": parsed_response.get("confidence", "medium"),
                        "should_continue": parsed_response.get("should_continue", not is_final_turn)
                    }
                    
                    logger.info(f"LLM result: response='{result['response']}', intent={result['intent']}, continue={result['should_continue']}")
                    return result
            except Exception as parse_error:
                logger.warning(f"JSON parsing failed: {str(parse_error)}")
            
            # Fallback response if JSON parsing fails
            fallback_result = {
                "response": response_text if len(response_text) < 100 else "Thank you for sharing that with me.",
                "intent": "neutral",
                "confidence": "medium",
                "should_continue": not is_final_turn
            }
            
            logger.info(f"Using fallback response: '{fallback_result['response']}'")
            return fallback_result
            
        except Exception as e:
            logger.error(f"LLM processing failed: {str(e)}")
            return {
                "response": "I understand. Thank you for sharing that with me.",
                "intent": "neutral",
                "confidence": "low", 
                "should_continue": False
            }
