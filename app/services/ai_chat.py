import os
import tempfile
from typing import Dict, Optional, Any, Tuple
import openai
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.config import settings
from app.models.communication import ChatMessage, MessageTypeEnum
from app.schemas.communication import AIChatRequest, AIChatResponse
from app.utils.audio import AudioProcessor

# Configure OpenAI API
openai.api_key = settings.OPENAI_API_KEY

class AIChatService:
    """Service for AI chat functionality."""

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

        # Generate AI response
        ai_response = await AIChatService._generate_ai_response(text_input)

        # Analyze sentiment
        sentiment_analysis = await AIChatService._analyze_sentiment(text_input)

        # Generate audio response if original request was audio
        audio_response = None
        if request.audio_file:
            audio_response = await AIChatService._text_to_speech(ai_response)

        # Save the conversation to the database
        AIChatService._save_conversation(
            db, request.user_id, text_input, ai_response
        )

        return AIChatResponse(
            response=ai_response,
            audio_response=audio_response,
            sentiment_analysis=sentiment_analysis
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
    async def _generate_ai_response(text_input: str) -> str:
        """
        Generate an AI response using OpenAI.

        Args:
            text_input: User input text

        Returns:
            AI generated response
        """
        # Check if OpenAI API key is set
        if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY.startswith("sk-") and len(settings.OPENAI_API_KEY) < 50:
            print("OpenAI API key is not set or invalid, using mock response")
            # Use a mock response for testing
            if "anxiety" in text_input.lower() or "anxious" in text_input.lower():
                return "I understand you're feeling anxious. Deep breathing exercises can help. Try breathing in for 4 counts, holding for 4, and exhaling for 6. Would you like more coping strategies?"
            elif "depression" in text_input.lower() or "sad" in text_input.lower():
                return "I'm sorry to hear you're feeling down. Remember that it's okay to not be okay sometimes. Have you tried talking to someone you trust about how you're feeling?"
            elif "stress" in text_input.lower() or "overwhelmed" in text_input.lower():
                return "It sounds like you're dealing with a lot of stress. Taking small breaks throughout the day and practicing mindfulness can help manage overwhelming feelings."
            elif "sleep" in text_input.lower() or "insomnia" in text_input.lower():
                return "Sleep issues can be challenging. Try establishing a consistent sleep schedule and creating a relaxing bedtime routine. Avoiding screens an hour before bed can also help."
            else:
                return f"Thank you for sharing that with me. I'm here to support you with your mental health concerns. Could you tell me more about how you've been feeling lately?"

        try:
            # Call OpenAI API
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful healthcare assistant specializing in mental health support. Provide empathetic, supportive responses that are concise and helpful. Focus on evidence-based approaches and gentle encouragement."},
                    {"role": "user", "content": text_input}
                ],
                max_tokens=500,
                temperature=0.7
            )

            # Extract the response text
            return response.choices[0].message.content.strip()
        except Exception as e:
            # Handle any errors
            print(f"Error generating AI response: {str(e)}")

            # Provide a more helpful fallback response
            if "anxiety" in text_input.lower():
                return "I understand anxiety can be challenging. Deep breathing and grounding exercises may help. Would you like to know more about these techniques?"
            elif "depression" in text_input.lower():
                return "I hear that you're struggling with feelings of depression. Remember that seeking support is a sign of strength, not weakness. Have you considered talking to a mental health professional?"
            elif "stress" in text_input.lower():
                return "Managing stress is important for your wellbeing. Regular exercise, adequate sleep, and mindfulness practices can all help reduce stress levels."
            else:
                return "I'm here to support you with your mental health concerns. While I'm having some technical difficulties right now, please know that your wellbeing matters. Consider reaching out to a healthcare provider if you need immediate assistance."

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
        db: Session, user_id: str, user_message: str, ai_response: str
    ) -> None:
        """
        Save the conversation to the database.

        Args:
            db: Database session
            user_id: User ID
            user_message: User message
            ai_response: AI response
        """
        # Save user message
        user_chat = ChatMessage(
            sender_id=user_id,
            message_text=user_message,
            timestamp=func.now()
        )
        db.add(user_chat)

        # Save AI response
        ai_chat = ChatMessage(
            receiver_id=user_id,
            message_text=ai_response,
            timestamp=func.now()
        )
        db.add(ai_chat)

        # Commit the changes
        db.commit()
