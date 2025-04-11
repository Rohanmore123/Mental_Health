from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID

import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.communication import Mydiary, ChatMessage
from app.schemas.communication import MoodAnalysisRequest, SentimentAnalysisRequest

class AnalyticsService:
    """Service for analytics functionality."""
    
    @staticmethod
    def analyze_mood(
        db: Session, request: MoodAnalysisRequest
    ) -> Dict[str, Any]:
        """
        Analyze patient mood based on diary entries and chat messages.
        
        Args:
            db: Database session
            request: Mood analysis request
            
        Returns:
            Mood analysis results
        """
        # Set default date range if not provided
        end_date = request.end_date or datetime.utcnow()
        start_date = request.start_date or (end_date - timedelta(days=30))
        
        # Get diary entries
        diary_entries = db.query(Mydiary).filter(
            Mydiary.patient_id == request.patient_id,
            Mydiary.created_at.between(start_date, end_date)
        ).order_by(Mydiary.created_at).all()
        
        # Get chat messages
        chat_messages = db.query(ChatMessage).filter(
            ChatMessage.sender_id == request.patient_id,
            ChatMessage.timestamp.between(start_date, end_date)
        ).order_by(ChatMessage.timestamp).all()
        
        # Combine diary entries and chat messages
        entries = []
        
        for entry in diary_entries:
            entries.append({
                "date": entry.created_at,
                "text": entry.notes,
                "source": "diary"
            })
        
        for message in chat_messages:
            entries.append({
                "date": message.timestamp,
                "text": message.message_text,
                "source": "chat"
            })
        
        # Sort entries by date
        entries.sort(key=lambda x: x["date"])
        
        # If no entries, return default response
        if not entries:
            return {
                "patient_id": request.patient_id,
                "mood_scores": {},
                "trend": "No data available",
                "recommendations": []
            }
        
        # Analyze sentiment for each entry
        mood_scores = {}
        for entry in entries:
            date_str = entry["date"].strftime("%Y-%m-%d")
            sentiment = AnalyticsService._analyze_text_sentiment(entry["text"])
            
            if date_str not in mood_scores:
                mood_scores[date_str] = []
            
            mood_scores[date_str].append(sentiment)
        
        # Calculate average mood score for each day
        avg_mood_scores = {}
        for date_str, scores in mood_scores.items():
            avg_mood_scores[date_str] = sum(scores) / len(scores)
        
        # Determine trend
        trend = AnalyticsService._determine_mood_trend(avg_mood_scores)
        
        # Generate recommendations
        recommendations = AnalyticsService._generate_mood_recommendations(trend)
        
        return {
            "patient_id": request.patient_id,
            "mood_scores": avg_mood_scores,
            "trend": trend,
            "recommendations": recommendations
        }
    
    @staticmethod
    def analyze_sentiment(
        request: SentimentAnalysisRequest
    ) -> Dict[str, Any]:
        """
        Analyze sentiment of text.
        
        Args:
            request: Sentiment analysis request
            
        Returns:
            Sentiment analysis results
        """
        # Calculate sentiment score (-1 to 1)
        sentiment_score = AnalyticsService._analyze_text_sentiment(request.text)
        
        # Determine sentiment label
        if sentiment_score > 0.3:
            sentiment = "positive"
        elif sentiment_score < -0.3:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        # Calculate confidence
        confidence = abs(sentiment_score) * 0.8 + 0.2
        
        # Detect emotions
        emotions = AnalyticsService._detect_emotions(request.text)
        
        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "emotions": emotions
        }
    
    @staticmethod
    def _analyze_text_sentiment(text: str) -> float:
        """
        Analyze sentiment of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Sentiment score (-1 to 1)
        """
        # This is a simplified sentiment analysis
        # In a real application, you would use a more sophisticated model
        
        # List of positive and negative words
        positive_words = [
            "happy", "good", "great", "excellent", "wonderful", "fantastic",
            "amazing", "awesome", "joy", "love", "like", "better", "improved",
            "positive", "well", "nice", "perfect", "best", "glad", "pleased"
        ]
        
        negative_words = [
            "sad", "bad", "terrible", "awful", "horrible", "poor", "worst",
            "hate", "dislike", "angry", "upset", "disappointed", "negative",
            "worse", "sick", "pain", "hurt", "unhappy", "sorry", "worried"
        ]
        
        # Convert text to lowercase
        text = text.lower()
        
        # Count positive and negative words
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        # Calculate sentiment score
        total_count = positive_count + negative_count
        if total_count == 0:
            return 0.0
        
        return (positive_count - negative_count) / total_count
    
    @staticmethod
    def _detect_emotions(text: str) -> Dict[str, float]:
        """
        Detect emotions in text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary of emotions and their intensities
        """
        # This is a simplified emotion detection
        # In a real application, you would use a more sophisticated model
        
        # Define emotion keywords
        emotion_keywords = {
            "joy": ["happy", "joy", "delighted", "pleased", "glad", "excited", "cheerful"],
            "sadness": ["sad", "unhappy", "depressed", "down", "blue", "gloomy", "miserable"],
            "anger": ["angry", "mad", "furious", "irritated", "annoyed", "frustrated", "enraged"],
            "fear": ["afraid", "scared", "frightened", "terrified", "anxious", "worried", "nervous"],
            "surprise": ["surprised", "shocked", "amazed", "astonished", "stunned", "unexpected"]
        }
        
        # Convert text to lowercase
        text = text.lower()
        
        # Calculate emotion intensities
        emotions = {}
        for emotion, keywords in emotion_keywords.items():
            count = sum(1 for keyword in keywords if keyword in text)
            intensity = min(1.0, count * 0.2)  # Scale intensity (max 1.0)
            emotions[emotion] = intensity
        
        return emotions
    
    @staticmethod
    def _determine_mood_trend(mood_scores: Dict[str, float]) -> str:
        """
        Determine mood trend from mood scores.
        
        Args:
            mood_scores: Dictionary of dates and mood scores
            
        Returns:
            Trend description
        """
        if not mood_scores:
            return "No data available"
        
        # Convert to pandas Series for trend analysis
        dates = list(mood_scores.keys())
        scores = list(mood_scores.values())
        
        # If only one data point, can't determine trend
        if len(dates) == 1:
            score = scores[0]
            if score > 0.3:
                return "Positive mood"
            elif score < -0.3:
                return "Negative mood"
            else:
                return "Neutral mood"
        
        # Calculate trend
        try:
            # Create a pandas Series
            series = pd.Series(scores, index=pd.to_datetime(dates))
            
            # Calculate rolling average (if enough data points)
            if len(series) >= 3:
                rolling_avg = series.rolling(window=3).mean()
                recent_avg = rolling_avg.iloc[-1] if not pd.isna(rolling_avg.iloc[-1]) else series.iloc[-1]
                past_avg = rolling_avg.iloc[0] if not pd.isna(rolling_avg.iloc[0]) else series.iloc[0]
            else:
                recent_avg = series.iloc[-1]
                past_avg = series.iloc[0]
            
            # Determine trend direction
            diff = recent_avg - past_avg
            
            if diff > 0.2:
                return "Improving mood trend"
            elif diff < -0.2:
                return "Declining mood trend"
            else:
                # Check absolute mood level
                if recent_avg > 0.3:
                    return "Consistently positive mood"
                elif recent_avg < -0.3:
                    return "Consistently negative mood"
                else:
                    return "Stable neutral mood"
        
        except Exception as e:
            print(f"Error determining mood trend: {str(e)}")
            return "Unable to determine mood trend"
    
    @staticmethod
    def _generate_mood_recommendations(trend: str) -> List[str]:
        """
        Generate recommendations based on mood trend.
        
        Args:
            trend: Mood trend description
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        if "declining" in trend.lower():
            recommendations = [
                "Consider scheduling a consultation with your doctor",
                "Try incorporating mindfulness or meditation practices",
                "Maintain a regular sleep schedule",
                "Engage in physical activity for at least 30 minutes daily",
                "Connect with friends or family for social support"
            ]
        elif "negative" in trend.lower():
            recommendations = [
                "Schedule a consultation with your doctor to discuss your mood",
                "Consider speaking with a mental health professional",
                "Practice self-care activities that you enjoy",
                "Establish a daily routine with regular sleep patterns",
                "Spend time outdoors in natural settings"
            ]
        elif "improving" in trend.lower():
            recommendations = [
                "Continue your current positive practices",
                "Share your progress with your healthcare provider",
                "Identify what factors are contributing to your improved mood",
                "Gradually increase your activity levels",
                "Celebrate your progress and achievements"
            ]
        elif "positive" in trend.lower():
            recommendations = [
                "Maintain your current wellness practices",
                "Share positive experiences in your diary",
                "Consider mentoring or supporting others",
                "Set new health and wellness goals",
                "Continue regular check-ins with your healthcare provider"
            ]
        else:  # neutral or stable
            recommendations = [
                "Maintain regular check-ins with your healthcare provider",
                "Consider adding new wellness activities to your routine",
                "Practice gratitude journaling",
                "Ensure you're getting adequate sleep and nutrition",
                "Engage in regular physical activity"
            ]
        
        return recommendations
