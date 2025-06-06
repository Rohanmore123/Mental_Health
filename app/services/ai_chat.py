import os
import json
import uuid
import tempfile
from typing import Dict, Any, List, Tuple
import openai
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.config import settings
from app.models.communication import ChatMessage
from app.schemas.communication import AIChatRequest, AIChatResponse
from app.utils.audio import AudioProcessor

# Configure OpenAI API
openai.api_key = settings.OPENAI_API_KEY

class AIChatService:
    """Service for AI chat functionality."""

    @staticmethod
    def _get_chat_history(db: Session, user_id: str, limit: int = 10) -> list:
        """
        Get recent chat history for a user.

        Args:
            db: Database session
            user_id: User ID
            limit: Maximum number of messages to retrieve

        Returns:
            List of chat messages in chronological order
        """
        ai_user_id = "00000000-0000-0000-0000-000000000000"  # Using a fixed UUID for the AI

        # Fetch recent messages that are part of the conversation between the user and the AI
        messages = db.query(ChatMessage).filter(
            # User messages to AI
            ((ChatMessage.sender_id == user_id) & (ChatMessage.receiver_id == ai_user_id)) |
            # AI messages to user
            ((ChatMessage.sender_id == ai_user_id) & (ChatMessage.receiver_id == user_id))
        ).order_by(ChatMessage.timestamp.asc()).limit(limit).all()

        print(f"Retrieved {len(messages)} messages from database for user {user_id}")

        # Format messages for the LLM
        formatted_messages = []

        for msg in messages:
            sender_id_str = str(msg.sender_id) if msg.sender_id else ""
            receiver_id_str = str(msg.receiver_id) if msg.receiver_id else ""

            print(f"Processing message: sender={sender_id_str}, receiver={receiver_id_str}, text={msg.message_text[:30]}...")

            if sender_id_str == user_id and receiver_id_str == ai_user_id:
                # This is a user message
                formatted_messages.append({"role": "user", "content": msg.message_text})
                print(f"Added user message to history: {msg.message_text[:30]}...")
            elif sender_id_str == ai_user_id and receiver_id_str == user_id:
                # This is an AI message
                formatted_messages.append({"role": "assistant", "content": msg.message_text})
                print(f"Added AI message to history: {msg.message_text[:30]}...")

        print(f"Retrieved {len(formatted_messages)} messages from chat history for user {user_id}")
        if formatted_messages:
            print(f"Sample message: {formatted_messages[0]}")

        return formatted_messages

    @staticmethod
    async def process_chat(
        db: Session, request: AIChatRequest
    ) -> AIChatResponse:
        """
        Process a chat request and generate a response.

        Args:
            db: Database session
            request: AI chat request

        Returns:
            AI chat response
        """
        # Process audio if provided
        text_input = request.message
        if request.audio_file:
            # If audio is provided, transcribe it
            text_input = await AIChatService._transcribe_audio(request.audio_file)

        # Get recent chat history
        print(f"Fetching chat history for user {request.user_id}")
        chat_history = AIChatService._get_chat_history(db, str(request.user_id))
        print(f"Found {len(chat_history)} messages in chat history")

        # Generate AI response and extract keywords
        ai_response, extracted_keywords = await AIChatService._generate_ai_response(text_input, chat_history)

        # Analyze sentiment
        sentiment_analysis = await AIChatService._analyze_sentiment(text_input)

        # Generate audio response if original request was audio
        audio_response = None
        if request.audio_file:
            audio_response = await AIChatService._text_to_speech(ai_response)

        # Save the conversation to the database
        AIChatService._save_conversation(
            db, request.user_id, text_input, ai_response, extracted_keywords
        )

        return AIChatResponse(
            response=ai_response,
            audio_response=audio_response,
            sentiment_analysis=sentiment_analysis,
            extracted_keywords=extracted_keywords
        )

    @staticmethod
    async def _transcribe_audio(audio_data: str) -> str:
        """
        Transcribe audio to text.

        Args:
            audio_data: Base64 encoded audio or file path

        Returns:
            Transcribed text
        """
        try:
            # Check if audio_data is a file path or base64 string
            if os.path.exists(audio_data):
                audio_file_path = audio_data
            else:
                # Decode base64 audio to a temporary file
                audio_file_path = AudioProcessor.decode_base64_audio(audio_data)

            # Open the audio file
            with open(audio_file_path, "rb") as audio_file:
                # Transcribe using OpenAI's Whisper API
                transcript = openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )

            # Clean up temporary file if created
            if audio_file_path != audio_data:
                AudioProcessor.cleanup_temp_file(audio_file_path)

            return transcript.text
        except Exception as e:
            # Handle any errors
            print(f"Error transcribing audio: {str(e)}")
            return "Sorry, I couldn't transcribe your audio."

    @staticmethod
    async def _generate_ai_response(text_input: str, chat_history: list = None) -> tuple:
        """
        Generate an AI response using OpenAI.

        Args:
            text_input: User input text
            chat_history: List of previous chat messages in the format [{"role": "user/assistant", "content": "message"}]

        Returns:
            Tuple of (AI generated response, extracted keywords)
        """
        # Define the system prompt
        system_prompt = '''
        You are a mental health AI assistant. Respond like a compassionate psychiatrist — short, simple, supportive sentences.
        IMPORTANT: Maintain context from the conversation history. Remember what the user has told you previously.
        If the user asks about their problems or issues, refer back to what they've shared earlier in the conversation.

        Extract keywords from the user message (not from system generated text).

        ❗Reply ONLY in this JSON structure:
        {
          "response": "<short, empathetic reply that maintains conversation context>",
          "extracted_keywords": ["<keyword1>", "<keyword2>"]
        }
        Only output the JSON (no explanation, no markdown).
        '''

        # Check if OpenAI API key is set
        if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY.startswith("sk-") and len(settings.OPENAI_API_KEY) < 50:
            print("OpenAI API key is not set or invalid, using mock response")
            # Use a mock response for testing that maintains context
            response_text = ""
            extracted_keywords = []

            # Check if there's chat history to maintain context
            previous_issues = set()
            if chat_history:
                for msg in chat_history:
                    if msg["role"] == "user":
                        # Extract issues from previous messages
                        if "anxiety" in msg["content"].lower() or "anxious" in msg["content"].lower():
                            previous_issues.add("anxiety")
                        if "depression" in msg["content"].lower() or "sad" in msg["content"].lower():
                            previous_issues.add("depression")
                        if "stress" in msg["content"].lower() or "overwhelmed" in msg["content"].lower():
                            previous_issues.add("stress")
                        if "sleep" in msg["content"].lower() or "insomnia" in msg["content"].lower():
                            previous_issues.add("sleep")

            print(f"Previous issues identified: {previous_issues}")

            # Check if the user is asking about their problem
            asking_about_problem = any(phrase in text_input.lower() for phrase in ["my problem", "my issue", "what issue", "what problem", "tell me about my"])

            if asking_about_problem and previous_issues:
                # Respond based on previously mentioned issues
                if "anxiety" in previous_issues:
                    response_text = "Based on what you've shared, you mentioned feeling anxious. Anxiety can manifest as worry, restlessness, and physical symptoms like a racing heart. Would you like some coping strategies for anxiety?"
                    extracted_keywords = ["anxiety", "coping", "strategies"]
                elif "depression" in previous_issues:
                    response_text = "From our conversation, you've mentioned feeling down or sad. These can be signs of depression. It's important to be gentle with yourself and consider speaking with a mental health professional."
                    extracted_keywords = ["depression", "sad", "professional help"]
                elif "stress" in previous_issues:
                    response_text = "You've mentioned feeling stressed or overwhelmed. Chronic stress can affect both your mental and physical health. Let's work on some stress management techniques."
                    extracted_keywords = ["stress", "overwhelmed", "management"]
                elif "sleep" in previous_issues:
                    response_text = "You've mentioned having trouble sleeping. Sleep issues can significantly impact your mental health. Let's discuss some strategies to improve your sleep quality."
                    extracted_keywords = ["sleep", "insomnia", "quality"]
                else:
                    response_text = "Based on our conversation, you've been experiencing some mental health challenges. Could you tell me more specifically what's been troubling you the most recently?"
                    extracted_keywords = ["mental health", "challenges", "support"]
            elif "anxiety" in text_input.lower() or "anxious" in text_input.lower():
                response_text = "I understand you're feeling anxious. Deep breathing exercises can help. Try breathing in for 4 counts, holding for 4, and exhaling for 6. Would you like more coping strategies?"
                extracted_keywords = ["anxiety", "anxious", "breathing", "coping"]
            elif "depression" in text_input.lower() or "sad" in text_input.lower():
                response_text = "I'm sorry to hear you're feeling down. Remember that it's okay to not be okay sometimes. Have you tried talking to someone you trust about how you're feeling?"
                extracted_keywords = ["depression", "sad", "down", "feelings"]
            elif "stress" in text_input.lower() or "overwhelmed" in text_input.lower():
                response_text = "It sounds like you're dealing with a lot of stress. Taking small breaks throughout the day and practicing mindfulness can help manage overwhelming feelings."
                extracted_keywords = ["stress", "overwhelmed", "mindfulness", "breaks"]
            elif "sleep" in text_input.lower() or "insomnia" in text_input.lower():
                response_text = "Sleep issues can be challenging. Try establishing a consistent sleep schedule and creating a relaxing bedtime routine. Avoiding screens an hour before bed can also help."
                extracted_keywords = ["sleep", "insomnia", "routine", "screens"]
            elif "what should i do" in text_input.lower() and previous_issues:
                if "anxiety" in previous_issues:
                    response_text = "For anxiety, I recommend deep breathing exercises, mindfulness meditation, and physical activity. It can also help to limit caffeine and practice progressive muscle relaxation."
                    extracted_keywords = ["anxiety", "breathing", "meditation", "exercise"]
                elif "sleep" in previous_issues:
                    response_text = "To improve sleep, maintain a consistent sleep schedule, create a relaxing bedtime routine, avoid screens before bed, ensure your bedroom is dark and cool, and limit caffeine and alcohol."
                    extracted_keywords = ["sleep", "routine", "environment", "habits"]
                elif "stress" in previous_issues:
                    response_text = "To manage stress, try regular exercise, mindfulness meditation, time management techniques, setting boundaries, and making time for activities you enjoy."
                    extracted_keywords = ["stress", "exercise", "mindfulness", "boundaries"]
                else:
                    response_text = "Based on what you've shared, I recommend practicing self-care, maintaining a healthy routine, connecting with supportive people, and considering speaking with a mental health professional."
                    extracted_keywords = ["self-care", "routine", "support", "professional help"]
            else:
                response_text = f"Thank you for sharing that with me. I'm here to support you with your mental health concerns. Could you tell me more about how you've been feeling lately?"
                # Extract simple keywords from user input
                extracted_keywords = [word for word in text_input.lower().split() if len(word) > 4][:3]

            return response_text, extracted_keywords

        try:
            # Prepare messages for the API call
            messages = [{"role": "system", "content": system_prompt}]

            # Add chat history if available
            if chat_history and len(chat_history) > 0:
                print(f"Adding {len(chat_history)} messages from chat history to the prompt")
                messages.extend(chat_history)
            else:
                print("No chat history available to add to the prompt")

            # Add the current user message
            messages.append({"role": "user", "content": text_input})

            # Log the messages being sent to OpenAI
            print(f"Sending {len(messages)} messages to OpenAI API")
            for i, msg in enumerate(messages):
                print(f"Message {i}: role={msg['role']}, content={msg['content'][:50]}...")

            # Call OpenAI API with the specified system prompt and chat history
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )

            # Extract the response text
            ai_response = response.choices[0].message.content.strip()

            # Clean formatting if GPT returns with ```json
            ai_response = ai_response.strip('```json').strip('```').strip()

            try:
                # Parse the JSON response
                parsed_response = json.loads(ai_response)
                response_text = parsed_response.get("response", "")
                extracted_keywords = parsed_response.get("extracted_keywords", [])

                return response_text, extracted_keywords
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON response: {str(e)}")
                print(f"Raw response: {ai_response}")
                # If JSON parsing fails, return the raw response and extract keywords manually
                extracted_keywords = [word for word in text_input.lower().split() if len(word) > 4][:3]
                return ai_response, extracted_keywords

        except Exception as e:
            # Handle any errors
            print(f"Error generating AI response: {str(e)}")

            # Provide a more helpful fallback response
            response_text = ""
            extracted_keywords = []

            if "anxiety" in text_input.lower():
                response_text = "I understand anxiety can be challenging. Deep breathing and grounding exercises may help. Would you like to know more about these techniques?"
                extracted_keywords = ["anxiety", "breathing", "grounding"]
            elif "depression" in text_input.lower():
                response_text = "I hear that you're struggling with feelings of depression. Remember that seeking support is a sign of strength, not weakness. Have you considered talking to a mental health professional?"
                extracted_keywords = ["depression", "support", "strength"]
            elif "stress" in text_input.lower():
                response_text = "Managing stress is important for your wellbeing. Regular exercise, adequate sleep, and mindfulness practices can all help reduce stress levels."
                extracted_keywords = ["stress", "exercise", "sleep", "mindfulness"]
            else:
                response_text = "I'm here to support you with your mental health concerns. While I'm having some technical difficulties right now, please know that your wellbeing matters. Consider reaching out to a healthcare provider if you need immediate assistance."
                extracted_keywords = ["support", "wellbeing", "assistance"]

            return response_text, extracted_keywords

    @staticmethod
    async def _analyze_sentiment(text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of text.

        Args:
            text: Text to analyze

        Returns:
            Sentiment analysis results
        """
        # Check if OpenAI API key is set
        if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY.startswith("sk-") and len(settings.OPENAI_API_KEY) < 50:
            print("OpenAI API key is not set or invalid, using rule-based sentiment analysis")
            # Use a simple rule-based approach for sentiment analysis
            return AIChatService._rule_based_sentiment_analysis(text)

        try:
            # Call OpenAI API for sentiment analysis
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Analyze the sentiment of the following text. Provide a JSON response with 'sentiment' (positive, negative, or neutral), 'confidence' (0-1), and 'emotions' (a dictionary of emotions and their intensities from 0-1)."},
                    {"role": "user", "content": text}
                ],
                max_tokens=200,
                temperature=0.3
            )

            # Extract the response and parse it
            analysis_text = response.choices[0].message.content.strip()

            # Simple parsing (in a real app, you'd want more robust parsing)
            # This is a simplified approach
            if "positive" in analysis_text.lower():
                sentiment = "positive"
                confidence = 0.8
            elif "negative" in analysis_text.lower():
                sentiment = "negative"
                confidence = 0.8
            else:
                sentiment = "neutral"
                confidence = 0.6

            # Create a basic emotions dictionary
            emotions = {
                "joy": 0.0,
                "sadness": 0.0,
                "anger": 0.0,
                "fear": 0.0,
                "surprise": 0.0
            }

            # Simple emotion detection
            if "happy" in analysis_text.lower() or "joy" in analysis_text.lower():
                emotions["joy"] = 0.8
            if "sad" in analysis_text.lower() or "sadness" in analysis_text.lower():
                emotions["sadness"] = 0.8
            if "angry" in analysis_text.lower() or "anger" in analysis_text.lower():
                emotions["anger"] = 0.8
            if "fear" in analysis_text.lower() or "afraid" in analysis_text.lower():
                emotions["fear"] = 0.8
            if "surprise" in analysis_text.lower() or "shocked" in analysis_text.lower():
                emotions["surprise"] = 0.8

            return {
                "sentiment": sentiment,
                "confidence": confidence,
                "emotions": emotions
            }
        except Exception as e:
            # Handle any errors
            print(f"Error analyzing sentiment: {str(e)}")
            return AIChatService._rule_based_sentiment_analysis(text)

    @staticmethod
    def _rule_based_sentiment_analysis(text: str) -> Dict[str, Any]:
        """
        Perform a simple rule-based sentiment analysis.

        Args:
            text: Text to analyze

        Returns:
            Sentiment analysis results
        """
        text = text.lower()

        # Define positive and negative word lists
        positive_words = ["happy", "good", "great", "excellent", "wonderful", "amazing", "love", "enjoy", "pleased",
                         "joy", "delighted", "grateful", "thankful", "excited", "hopeful", "optimistic"]

        negative_words = ["sad", "bad", "terrible", "awful", "horrible", "hate", "dislike", "angry", "upset",
                         "depressed", "anxious", "worried", "stressed", "afraid", "scared", "unhappy", "miserable"]

        # Count occurrences
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)

        # Determine sentiment
        if positive_count > negative_count:
            sentiment = "positive"
            confidence = min(0.5 + (positive_count - negative_count) * 0.1, 0.9)
        elif negative_count > positive_count:
            sentiment = "negative"
            confidence = min(0.5 + (negative_count - positive_count) * 0.1, 0.9)
        else:
            sentiment = "neutral"
            confidence = 0.5

        # Create emotions dictionary
        emotions = {
            "joy": 0.0,
            "sadness": 0.0,
            "anger": 0.0,
            "fear": 0.0,
            "surprise": 0.0
        }

        # Simple emotion detection
        joy_words = ["happy", "joy", "delighted", "excited", "pleased", "enjoy"]
        sadness_words = ["sad", "unhappy", "depressed", "miserable", "disappointed"]
        anger_words = ["angry", "mad", "furious", "annoyed", "irritated", "hate"]
        fear_words = ["afraid", "scared", "fearful", "terrified", "anxious", "worried"]
        surprise_words = ["surprised", "shocked", "amazed", "astonished", "unexpected"]

        for word in joy_words:
            if word in text:
                emotions["joy"] = min(emotions["joy"] + 0.2, 0.9)

        for word in sadness_words:
            if word in text:
                emotions["sadness"] = min(emotions["sadness"] + 0.2, 0.9)

        for word in anger_words:
            if word in text:
                emotions["anger"] = min(emotions["anger"] + 0.2, 0.9)

        for word in fear_words:
            if word in text:
                emotions["fear"] = min(emotions["fear"] + 0.2, 0.9)

        for word in surprise_words:
            if word in text:
                emotions["surprise"] = min(emotions["surprise"] + 0.2, 0.9)

        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "emotions": emotions
        }

    @staticmethod
    async def _text_to_speech(text: str) -> str:
        """
        Convert text to speech.

        Args:
            text: Text to convert to speech

        Returns:
            Base64 encoded audio
        """
        # Check if OpenAI API key is set
        if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY.startswith("sk-") and len(settings.OPENAI_API_KEY) < 50:
            print("OpenAI API key is not set or invalid, skipping text-to-speech conversion")
            return ""

        try:
            # Create a temporary file for the audio
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                temp_file_path = temp_file.name

            # Call OpenAI API for text-to-speech
            response = openai.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=text
            )

            # Save the audio to the temporary file
            with open(temp_file_path, "wb") as f:
                f.write(response.content)

            # Encode the audio to base64
            base64_audio = AudioProcessor.encode_audio_to_base64(temp_file_path)

            # Clean up the temporary file
            AudioProcessor.cleanup_temp_file(temp_file_path)

            return base64_audio
        except Exception as e:
            # Handle any errors
            print(f"Error converting text to speech: {str(e)}")
            return ""

    @staticmethod
    def _save_conversation(
        db: Session, user_id: str, user_message: str, ai_response: str, extracted_keywords: list = None
    ) -> None:
        """
        Save the conversation to the database.

        Args:
            db: Database session
            user_id: User ID
            user_message: User message
            ai_response: AI response
            extracted_keywords: Keywords extracted from the user message
        """
        # Generate a UUID for the AI (system) user
        ai_user_id = "00000000-0000-0000-0000-000000000000"  # Using a fixed UUID for the AI

        # Save user message
        user_chat = ChatMessage(
            chat_message_id=str(uuid.uuid4()),
            sender_id=user_id,
            receiver_id=ai_user_id,  # User is sending to AI
            message_text=user_message,
            timestamp=func.now()
        )
        db.add(user_chat)

        # Save AI response with extracted keywords
        ai_chat = ChatMessage(
            chat_message_id=str(uuid.uuid4()),
            sender_id=ai_user_id,  # AI is sending to user
            receiver_id=user_id,
            message_text=ai_response,
            extracted_keywords=extracted_keywords if extracted_keywords else [],
            timestamp=func.now()
        )
        db.add(ai_chat)

        print(f"Saved conversation: User {user_id} -> AI {ai_user_id}")
        print(f"User message: {user_message[:50]}...")
        print(f"AI response: {ai_response[:50]}...")

        # Commit the changes
        db.commit()
