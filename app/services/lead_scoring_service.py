"""
Lead Scoring Service - Analyzes Reddit posts to determine if they are potential leads for Better2Know.
Calculates a comprehensive lead score out of 100 based on various factors.
"""

import re
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class LeadScore:
    """Data class to hold lead scoring results."""
    total_score: float
    keyword_score: float
    pattern_score: float
    urgency_score: float
    geographic_score: float
    engagement_score: float
    breakdown: Dict[str, any]


class LeadScoringService:
    """Service class for analyzing Reddit posts and calculating lead scores."""
    
    def __init__(self):
        # Scoring contribution ratios (adjustable)
        # Original weights (commented out):
        # self.KEYWORD_WEIGHT = 0.35        # 35% - Most important
        # self.PATTERN_WEIGHT = 0.25        # 25% - Question patterns
        # self.URGENCY_WEIGHT = 0.20        # 20% - Urgency indicators
        # self.GEOGRAPHIC_WEIGHT = 0.10     # 10% - Geographic relevance
        # self.ENGAGEMENT_WEIGHT = 0.10     # 10% - Engagement quality
        
        # New adjusted weights:
        self.KEYWORD_WEIGHT = 0.40        # 40% - Most important (decreased from 50%)
        self.PATTERN_WEIGHT = 0.25        # 25% - Question patterns (same)
        self.URGENCY_WEIGHT = 0.00        # 0% - Urgency indicators (disabled)
        self.GEOGRAPHIC_WEIGHT = 0.00     # 0% - Geographic relevance (disabled)
        self.ENGAGEMENT_WEIGHT = 0.35     # 35% - Engagement quality (increased from 25%)
        
        # Initialize keyword sets
        self._initialize_keywords()
        self._initialize_patterns()
        self._initialize_supported_countries()
    
    def _initialize_keywords(self):
        """Initialize all keyword sets based on Better2Know supported tests."""
        
        # Primary Keywords - Direct test/condition names
        self.primary_keywords = {
            # Main categories
            'sti', 'std', 'sexually transmitted infection', 'sexually transmitted disease',
            
            # Specific conditions (based on Better2Know tests)
            'chlamydia', 'gardnerella', 'gonorrhoea', 'gonorrhea', 'hiv', 'aids',
            'hpv', 'human papillomavirus', 'genital warts', 'warts',
            'hepatitis a', 'hepatitis b', 'hepatitis c', 'hep a', 'hep b', 'hep c',
            'herpes', 'hsv', 'hsv1', 'hsv2', 'cold sores', 'genital herpes',
            'mycoplasma', 'syphilis', 'trichomonas', 'trich',
            'ureaplasma', 'zika', 'zika virus',
            
            # General terms
            'infection', 'bacterial infection', 'viral infection',
            'sexual health', 'reproductive health'
        }
        
        # Symptom Keywords - Physical symptoms people might describe
        self.symptom_keywords = {
            # Urinary symptoms
            'burning urination', 'painful urination', 'burning when peeing', 'burning pee',
            'frequent urination', 'blood in urine', 'cloudy urine',
            
            # Genital symptoms
            'discharge', 'unusual discharge', 'yellow discharge', 'green discharge',
            'white discharge', 'smelly discharge', 'fishy smell', 'bad odor',
            'genital pain', 'genital itching', 'genital burning', 'genital sores',
            'genital bumps', 'genital rash', 'genital swelling',
            
            # Specific body parts
            'penis pain', 'vaginal pain', 'vaginal itching', 'vaginal burning',
            'testicular pain', 'pelvic pain', 'anal pain', 'throat infection',
            
            # Visible symptoms
            'bumps', 'sores', 'blisters', 'ulcers', 'lesions', 'rash',
            'swollen glands', 'swollen lymph nodes',
            
            # General symptoms
            'fever', 'fatigue', 'flu-like symptoms', 'body aches',
            'bleeding between periods', 'irregular periods', 'painful sex'
        }
        
        # Context Keywords - Situations/behaviors that indicate risk
        self.context_keywords = {
            # Risk behaviors
            'unprotected sex', 'no condom', 'without protection', 'raw sex',
            'multiple partners', 'new partner', 'casual sex', 'one night stand',
            'hookup', 'risky behavior', 'unsafe sex',
            
            # Exposure concerns
            'exposed to', 'partner has', 'partner tested positive', 'partner infected',
            'cheating partner', 'unfaithful partner',
            
            # Testing/medical
            'should i get tested', 'need to get tested', 'when to test',
            'test results', 'positive test', 'negative test',
            'clinic', 'doctor', 'medical advice', 'health check',
            'screening', 'blood test', 'urine test', 'swab test',
            
            # Emotional context
            'worried about', 'concerned about', 'scared of', 'afraid of',
            'panic', 'anxiety', 'stress', 'embarrassed'
        }
    
    def _initialize_patterns(self):
        """Initialize question patterns and urgency indicators."""
        
        # Question Patterns - Common ways people ask for help
        self.question_patterns = [
            # Testing questions
            r'\b(?:should|do) i (?:get )?test(?:ed)?\b',
            r'\bhow (?:long|soon) (?:after|before) .* test\b',
            r'\bwhen (?:should|can|do) i (?:get )?test\b',
            r'\bwhat test(?:s)? (?:should|do) i\b',
            r'\bwhere (?:can|should) i (?:get )?test\b',
            
            # Symptom questions
            r'\bwhat (?:are|could be) (?:the )?symptoms? of\b',
            r'\bis this (?:a )?(?:symptom|sign) of\b',
            r'\bdoes this (?:look|sound) like\b',
            r'\bcould (?:this|i) (?:be|have)\b',
            
            # Risk assessment
            r'\bam i at risk\b',
            r'\bwhat (?:are )?(?:my|the) (?:chances|odds)\b',
            r'\bhow likely (?:am i|is it)\b',
            r'\bshould i (?:be )?(?:worry|worried|concern)\b',
            
            # Exposure questions
            r'\bi (?:think|might) (?:have|be)\b',
            r'\bi was exposed to\b',
            r'\bmy partner (?:has|tested)\b',
            r'\bhelp.*(?:sti|std|infection)\b'
        ]
        
        # Urgency Indicators - Words/phrases showing immediate concern
        self.urgency_indicators = {
            # Direct urgency
            'urgent', 'emergency', 'asap', 'immediately', 'right away',
            'as soon as possible', 'quickly', 'fast',
            
            # Emotional urgency
            'panic', 'panicking', 'scared', 'terrified', 'freaking out',
            'help', 'desperate', 'worried sick', 'can\'t sleep',
            
            # Time-sensitive
            'today', 'now', 'this morning', 'tonight', 'yesterday',
            'just happened', 'just noticed', 'suddenly appeared',
            
            # Severity indicators
            'getting worse', 'spreading', 'more painful', 'unbearable',
            'severe', 'intense', 'extreme'
        }
    
    def _initialize_supported_countries(self):
        """Initialize supported countries and related terms."""
        self.supported_countries = {
            'australia', 'australian', 'aussie', 'oz', 'sydney', 'melbourne', 
            'brisbane', 'perth', 'adelaide', 'canberra',
            
            'canada', 'canadian', 'toronto', 'vancouver', 'montreal', 
            'calgary', 'ottawa', 'edmonton',
            
            'colombia', 'colombian', 'bogota', 'medellin', 'cali', 'barranquilla',
            
            'india', 'indian', 'mumbai', 'delhi', 'bangalore', 'hyderabad', 
            'chennai', 'kolkata', 'pune',
            
            'panama', 'panamanian', 'panama city',
            
            'peru', 'peruvian', 'lima', 'arequipa', 'trujillo',
            
            'poland', 'polish', 'warsaw', 'krakow', 'gdansk', 'wroclaw', 'poznan'
        }
    
    def calculate_keyword_score(self, text: str) -> Tuple[float, Dict]:
        """
        Calculate score based on keyword matching.
        
        Args:
            text: The text to analyze
            
        Returns:
            Tuple of (score, breakdown_dict)
        """
        text_lower = text.lower()
        
        # Count matches for each category
        primary_matches = sum(1 for keyword in self.primary_keywords 
                            if keyword in text_lower)
        
        symptom_matches = sum(1 for keyword in self.symptom_keywords 
                            if keyword in text_lower)
        
        context_matches = sum(1 for keyword in self.context_keywords 
                            if keyword in text_lower)
        
        # Calculate weighted score
        # Primary keywords are most important (50%), symptoms (30%), context (20%)
        # Give full points if at least one keyword found in each category
        primary_score = 50 if primary_matches > 0 else 0    # Full 50 points if any match
        symptom_score = 30 if symptom_matches > 0 else 0    # Full 30 points if any match
        context_score = 20 if context_matches > 0 else 0    # Full 20 points if any match
        
        total_keyword_score = primary_score + symptom_score + context_score
        
        breakdown = {
            'primary_matches': primary_matches,
            'symptom_matches': symptom_matches,
            'context_matches': context_matches,
            'primary_score': primary_score,
            'symptom_score': symptom_score,
            'context_score': context_score,
            'total_matches': primary_matches + symptom_matches + context_matches
        }
        
        return min(total_keyword_score, 100), breakdown
    
    def calculate_pattern_score(self, text: str) -> Tuple[float, Dict]:
        """
        Calculate score based on question patterns.
        
        Args:
            text: The text to analyze
            
        Returns:
            Tuple of (score, breakdown_dict)
        """
        text_lower = text.lower()
        pattern_matches = 0
        matched_patterns = []
        
        for pattern in self.question_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                pattern_matches += 1
                matched_patterns.append(pattern)
        
        # Give full 100 points if any question pattern is found
        pattern_score = 100 if pattern_matches > 0 else 0
        
        breakdown = {
            'pattern_matches': pattern_matches,
            'matched_patterns': matched_patterns,
            'has_question_format': '?' in text
        }
        
        return pattern_score, breakdown
    
    def calculate_urgency_score(self, text: str) -> Tuple[float, Dict]:
        """
        Calculate score based on urgency indicators.
        
        Args:
            text: The text to analyze
            
        Returns:
            Tuple of (score, breakdown_dict)
        """
        text_lower = text.lower()
        urgency_matches = 0
        matched_indicators = []
        
        for indicator in self.urgency_indicators:
            if indicator in text_lower:
                urgency_matches += 1
                matched_indicators.append(indicator)
        
        # Each urgency indicator worth 15 points, max 100
        urgency_score = min(urgency_matches * 15, 100)
        
        breakdown = {
            'urgency_matches': urgency_matches,
            'matched_indicators': matched_indicators,
            'urgency_level': 'high' if urgency_score >= 60 else 'medium' if urgency_score >= 30 else 'low'
        }
        
        return urgency_score, breakdown
    
    def calculate_geographic_score(self, text: str, user_location: str = None) -> Tuple[float, Dict]:
        """
        Calculate score based on geographic relevance.
        
        Args:
            text: The text to analyze
            user_location: Optional user location info
            
        Returns:
            Tuple of (score, breakdown_dict)
        """
        combined_text = f"{text} {user_location or ''}".lower()
        
        geographic_matches = 0
        matched_locations = []
        
        for location in self.supported_countries:
            if location in combined_text:
                geographic_matches += 1
                matched_locations.append(location)
        
        # If any supported location found, give full score
        # Otherwise, assume English language gives partial score
        if geographic_matches > 0:
            geographic_score = 100
        else:
            # Partial score for English language content
            geographic_score = 30
        
        breakdown = {
            'geographic_matches': geographic_matches,
            'matched_locations': matched_locations,
            'is_supported_region': geographic_matches > 0
        }
        
        return geographic_score, breakdown
    
    def calculate_engagement_score(self, num_comments: int) -> Tuple[float, Dict]:
        """
        Calculate score based on engagement quality (number of comments).
        
        Args:
            num_comments: Number of comments on the post
            
        Returns:
            Tuple of (score, breakdown_dict)
        """
        # More comments = higher engagement = more likely genuine concern
        if num_comments >= 20:
            engagement_score = 100
        elif num_comments >= 10:
            engagement_score = 80
        elif num_comments >= 5:
            engagement_score = 60
        elif num_comments >= 2:
            engagement_score = 40
        elif num_comments >= 1:
            engagement_score = 20
        else:
            engagement_score = 0
        
        breakdown = {
            'num_comments': num_comments,
            'engagement_level': (
                'very_high' if num_comments >= 20 else
                'high' if num_comments >= 10 else
                'medium' if num_comments >= 5 else
                'low' if num_comments >= 1 else
                'none'
            )
        }
        
        return engagement_score, breakdown
    
    def calculate_lead_score(self, 
                           title: str, 
                           content: str, 
                           num_comments: int = 0,
                           user_location: str = None) -> LeadScore:
        """
        Calculate comprehensive lead score for a Reddit post.
        
        Args:
            title: Post title
            content: Post content/body
            num_comments: Number of comments
            user_location: Optional user location
            
        Returns:
            LeadScore object with detailed breakdown
        """
        # Combine title and content for analysis
        full_text = f"{title} {content}".strip()
        
        # Calculate individual scores
        keyword_score, keyword_breakdown = self.calculate_keyword_score(full_text)
        pattern_score, pattern_breakdown = self.calculate_pattern_score(full_text)
        urgency_score, urgency_breakdown = self.calculate_urgency_score(full_text)
        geographic_score, geographic_breakdown = self.calculate_geographic_score(full_text, user_location)
        engagement_score, engagement_breakdown = self.calculate_engagement_score(num_comments)
        
        # Calculate weighted total score
        total_score = (
            (keyword_score * self.KEYWORD_WEIGHT) +
            (pattern_score * self.PATTERN_WEIGHT) +
            (urgency_score * self.URGENCY_WEIGHT) +
            (geographic_score * self.GEOGRAPHIC_WEIGHT) +
            (engagement_score * self.ENGAGEMENT_WEIGHT)
        )
        
        # Create comprehensive breakdown
        breakdown = {
            'weights': {
                'keyword_weight': self.KEYWORD_WEIGHT,
                'pattern_weight': self.PATTERN_WEIGHT,
                'urgency_weight': self.URGENCY_WEIGHT,
                'geographic_weight': self.GEOGRAPHIC_WEIGHT,
                'engagement_weight': self.ENGAGEMENT_WEIGHT
            },
            'keyword_analysis': keyword_breakdown,
            'pattern_analysis': pattern_breakdown,
            'urgency_analysis': urgency_breakdown,
            'geographic_analysis': geographic_breakdown,
            'engagement_analysis': engagement_breakdown,
            'text_stats': {
                'title_length': len(title),
                'content_length': len(content),
                'total_words': len(full_text.split()),
                'has_content': bool(content.strip())
            }
        }
        
        return LeadScore(
            total_score=round(total_score, 2),
            keyword_score=round(keyword_score, 2),
            pattern_score=round(pattern_score, 2),
            urgency_score=round(urgency_score, 2),
            geographic_score=round(geographic_score, 2),
            engagement_score=round(engagement_score, 2),
            breakdown=breakdown
        )
    
    def update_weights(self, 
                      keyword_weight: float = None,
                      pattern_weight: float = None,
                      urgency_weight: float = None,
                      geographic_weight: float = None,
                      engagement_weight: float = None):
        """
        Update scoring weights dynamically.
        
        Args:
            keyword_weight: Weight for keyword scoring (0.0-1.0)
            pattern_weight: Weight for pattern scoring (0.0-1.0)
            urgency_weight: Weight for urgency scoring (0.0-1.0)
            geographic_weight: Weight for geographic scoring (0.0-1.0)
            engagement_weight: Weight for engagement scoring (0.0-1.0)
        """
        if keyword_weight is not None:
            self.KEYWORD_WEIGHT = keyword_weight
        if pattern_weight is not None:
            self.PATTERN_WEIGHT = pattern_weight
        if urgency_weight is not None:
            self.URGENCY_WEIGHT = urgency_weight
        if geographic_weight is not None:
            self.GEOGRAPHIC_WEIGHT = geographic_weight
        if engagement_weight is not None:
            self.ENGAGEMENT_WEIGHT = engagement_weight
        
        # Ensure weights sum to 1.0
        total_weight = (self.KEYWORD_WEIGHT + self.PATTERN_WEIGHT + 
                       self.URGENCY_WEIGHT + self.GEOGRAPHIC_WEIGHT + 
                       self.ENGAGEMENT_WEIGHT)
        
        if abs(total_weight - 1.0) > 0.01:
            print(f"Warning: Weights sum to {total_weight}, not 1.0")


# Singleton instance for dependency injection
lead_scoring_service = LeadScoringService()
