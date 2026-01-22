# Lead Scoring Service Documentation

## Overview

The Lead Scoring Service analyzes Reddit posts to determine if they are potential leads for Better2Know's STI/STD testing services. It calculates a comprehensive lead score out of 100 based on various factors without requiring expensive LLM API calls.

## Scoring System

### 📊 Scoring Contribution Breakdown

| Component                | Weight | Max Points | Purpose                          |
| ------------------------ | ------ | ---------- | -------------------------------- |
| **Keyword Analysis**     | 35%    | 100        | Primary/Symptom/Context keywords |
| **Question Patterns**    | 25%    | 100        | Question format detection        |
| **Urgency Indicators**   | 20%    | 100        | Immediate concern detection      |
| **Geographic Relevance** | 10%    | 100        | Supported countries              |
| **Engagement Quality**   | 10%    | 100        | Number of comments               |

### 🎯 Score Interpretation

- **70-100**: 🔥 **HIGH PRIORITY LEAD** - Immediate follow-up recommended
- **50-69**: ⚡ **MEDIUM PRIORITY LEAD** - Good candidate for outreach
- **30-49**: 💡 **LOW PRIORITY LEAD** - Monitor for additional signals
- **0-29**: ❌ **NOT A LEAD** - Filter out

## Service Components

### 1. Keyword Analysis (35% weight)

Analyzes three categories of keywords based on Better2Know's supported tests:

#### Primary Keywords (50% of keyword score)

**Scoring**: Full 50 points awarded if **any** primary keyword is found (not cumulative)

- **Main categories**: STI, STD, sexually transmitted infection/disease
- **Specific conditions**: chlamydia, gardnerella, gonorrhoea, HIV, HPV, hepatitis A/B/C, herpes, mycoplasma, syphilis, trichomonas, ureaplasma, zika
- **General terms**: infection, sexual health, reproductive health

#### Symptom Keywords (30% of keyword score)

**Scoring**: Full 30 points awarded if **any** symptom keyword is found (not cumulative)

- **Urinary symptoms**: burning urination, painful urination, frequent urination, blood in urine
- **Genital symptoms**: discharge, unusual discharge, genital pain/itching/burning, genital sores/bumps
- **Visible symptoms**: bumps, sores, blisters, ulcers, lesions, rash, swollen glands
- **General symptoms**: fever, fatigue, flu-like symptoms, bleeding between periods

#### Context Keywords (20% of keyword score)

**Scoring**: Full 20 points awarded if **any** context keyword is found (not cumulative)

- **Risk behaviors**: unprotected sex, no condom, multiple partners, one night stand
- **Exposure concerns**: exposed to, partner has, partner tested positive
- **Testing/medical**: should I get tested, test results, clinic, doctor, screening
- **Emotional context**: worried about, concerned about, scared of, panic, anxiety

### 2. Question Patterns (25% weight)

**Scoring**: Full 100 points awarded if **any** question pattern is detected (not cumulative)

Detects common question formats using regex patterns:

- **Testing questions**: "Should I get tested?", "When should I test?", "How long after... test?"
- **Symptom questions**: "What are symptoms of...?", "Is this a symptom of...?", "Does this look like...?"
- **Risk assessment**: "Am I at risk?", "What are my chances?", "How likely is it?"
- **Exposure questions**: "I think I might have...", "I was exposed to...", "My partner has..."

### 3. Urgency Indicators (20% weight)

Identifies words/phrases showing immediate concern:

- **Direct urgency**: urgent, emergency, ASAP, immediately, right away
- **Emotional urgency**: panic, panicking, scared, terrified, freaking out, help, desperate
- **Time-sensitive**: today, now, this morning, tonight, yesterday, just happened
- **Severity indicators**: getting worse, spreading, severe, intense, extreme, unbearable

### 4. Geographic Relevance (10% weight)

Checks for supported countries and regions:

- **Australia**: australia, australian, aussie, sydney, melbourne, brisbane, perth
- **Canada**: canada, canadian, toronto, vancouver, montreal, calgary, ottawa
- **Colombia**: colombia, colombian, bogota, medellin, cali, barranquilla
- **India**: india, indian, mumbai, delhi, bangalore, hyderabad, chennai
- **Panama**: panama, panamanian, panama city
- **Peru**: peru, peruvian, lima, arequipa, trujillo
- **Poland**: poland, polish, warsaw, krakow, gdansk, wroclaw, poznan

### 5. Engagement Quality (10% weight)

Based on number of comments (indicates genuine concern and community engagement):

- **20+ comments**: 100 points (very high engagement)
- **10-19 comments**: 80 points (high engagement)
- **5-9 comments**: 60 points (medium engagement)
- **2-4 comments**: 40 points (low engagement)
- **1 comment**: 20 points (minimal engagement)
- **0 comments**: 0 points (no engagement)

## Usage

### Basic Usage

```python
from app.services.lead_scoring_service import lead_scoring_service

# Analyze a Reddit post
result = lead_scoring_service.calculate_lead_score(
    title="Should I get tested for STDs?",
    content="I had unprotected sex and now have burning urination. I'm in Toronto, Canada.",
    num_comments=15,
    user_location="Toronto, ON"  # Optional
)

print(f"Lead Score: {result.total_score}/100")
print(f"Category: {'HIGH PRIORITY' if result.total_score >= 70 else 'MEDIUM' if result.total_score >= 50 else 'LOW' if result.total_score >= 30 else 'NOT A LEAD'}")
```

### Individual Component Analysis

```python
# Analyze individual components
keyword_score, keyword_breakdown = lead_scoring_service.calculate_keyword_score(full_text)
pattern_score, pattern_breakdown = lead_scoring_service.calculate_pattern_score(full_text)
urgency_score, urgency_breakdown = lead_scoring_service.calculate_urgency_score(full_text)
geographic_score, geographic_breakdown = lead_scoring_service.calculate_geographic_score(full_text)
engagement_score, engagement_breakdown = lead_scoring_service.calculate_engagement_score(num_comments)
```

### Dynamic Weight Adjustment

```python
# Adjust scoring weights dynamically
lead_scoring_service.update_weights(
    keyword_weight=0.40,      # Increase keyword importance to 40%
    pattern_weight=0.30,      # Increase pattern importance to 30%
    urgency_weight=0.15,      # Decrease urgency importance to 15%
    geographic_weight=0.10,   # Keep geographic same at 10%
    engagement_weight=0.05    # Decrease engagement importance to 5%
)
```

### Detailed Results Analysis

```python
result = lead_scoring_service.calculate_lead_score(title, content, num_comments)

# Access detailed breakdown
print("Keyword Analysis:")
print(f"- Primary matches: {result.breakdown['keyword_analysis']['primary_matches']}")
print(f"- Symptom matches: {result.breakdown['keyword_analysis']['symptom_matches']}")
print(f"- Context matches: {result.breakdown['keyword_analysis']['context_matches']}")

print("Pattern Analysis:")
print(f"- Pattern matches: {result.breakdown['pattern_analysis']['pattern_matches']}")
print(f"- Has question format: {result.breakdown['pattern_analysis']['has_question_format']}")

print("Urgency Analysis:")
print(f"- Urgency level: {result.breakdown['urgency_analysis']['urgency_level']}")
print(f"- Matched indicators: {result.breakdown['urgency_analysis']['matched_indicators']}")
```

## Testing

Run the test script to see the service in action:

```bash
python test_lead_scoring.py
```

This will demonstrate:

- Various types of Reddit posts and their scores
- Detailed breakdown of scoring components
- Dynamic weight adjustment examples
- Score categorization and interpretation

## Test Cases Included

1. **High-probability lead**: STD testing question with symptoms and urgency
2. **Medium-probability lead**: General STI concern with some symptoms
3. **Low-probability lead**: General health question
4. **Not a lead**: Unrelated relationship advice
5. **High urgency lead**: Urgent symptoms with panic indicators

## Performance Characteristics

- ✅ **Fast**: No external API calls, pure text analysis
- ✅ **Configurable**: Adjust weights dynamically based on performance
- ✅ **Detailed**: Full breakdown of scoring rationale
- ✅ **Comprehensive**: Covers all Better2Know test areas and conditions
- ✅ **Scalable**: Can process thousands of posts quickly
- ✅ **Cost-effective**: Minimal computational overhead

## Integration Notes

- The service is designed to work standalone without database dependencies
- Returns structured `LeadScore` objects with comprehensive breakdowns
- Can be easily integrated into batch processing workflows
- Suitable for pre-filtering before expensive LLM analysis
- Thread-safe for concurrent processing

## Supported Better2Know Tests

The keyword analysis is based on Better2Know's supported test areas:

- STI/STD (general)
- Chlamydia
- Gardnerella
- Gonorrhoea
- HIV
- HPV and Genital Warts
- Hepatitis A, B, C
- Herpes
- Mycoplasma
- Syphilis
- Trichomonas
- Ureaplasma
- Zika

## Supported Geographic Regions

- Australia
- Canada
- Colombia
- India
- Panama
- Peru
- Poland

(English language content assumed for all regions)

## Future Enhancements

Potential areas for improvement:

- Machine learning model training on historical lead data
- Sentiment analysis integration
- Named entity recognition for medical terms
- Time-based scoring (recency of posts)
- User history analysis
- Subreddit-specific scoring adjustments
