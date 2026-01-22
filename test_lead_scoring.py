"""
Test script to demonstrate the Lead Scoring Service functionality.
"""

from app.services.lead_scoring_service import lead_scoring_service

def test_lead_scoring():
    """Test the lead scoring service with sample Reddit posts."""
    
    # Test cases with different types of posts
    test_cases = [
        {
            "name": "High-probability lead",
            "title": "Should I get tested for STDs? Worried about chlamydia",
            "content": "I had unprotected sex with a new partner last week and now I have burning when I pee and some discharge. I'm really scared and need to get tested ASAP. I'm in Toronto, Canada.",
            "num_comments": 15
        },
        {
            "name": "Medium-probability lead", 
            "title": "Unusual symptoms - could this be an STI?",
            "content": "I've been having some genital itching and noticed some bumps. My partner mentioned they had a cold sore recently. Should I be concerned?",
            "num_comments": 5
        },
        {
            "name": "Low-probability lead",
            "title": "General health question",
            "content": "What are some good ways to maintain sexual health? Looking for general advice.",
            "num_comments": 2
        },
        {
            "name": "Not a lead",
            "title": "Relationship advice needed",
            "content": "My boyfriend and I are having communication issues. How do we work through this?",
            "num_comments": 8
        },
        {
            "name": "High urgency lead",
            "title": "URGENT - Strange symptoms after risky encounter",
            "content": "I'm panicking. Had unprotected sex 3 days ago and now I have painful urination, discharge, and swollen glands. I'm in Sydney, Australia. Need help immediately!",
            "num_comments": 25
        }
    ]
    
    print("=" * 80)
    print("BETTER2KNOW LEAD SCORING SERVICE - TEST RESULTS")
    print("=" * 80)
    
    # Show current weights
    print(f"\nCurrent Scoring Weights:")
    print(f"• Keyword Analysis: {lead_scoring_service.KEYWORD_WEIGHT*100}%")
    print(f"• Question Patterns: {lead_scoring_service.PATTERN_WEIGHT*100}%")
    print(f"• Urgency Indicators: {lead_scoring_service.URGENCY_WEIGHT*100}%")
    print(f"• Geographic Relevance: {lead_scoring_service.GEOGRAPHIC_WEIGHT*100}%")
    print(f"• Engagement Quality: {lead_scoring_service.ENGAGEMENT_WEIGHT*100}%")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'-' * 60}")
        print(f"TEST CASE {i}: {test_case['name']}")
        print(f"{'-' * 60}")
        
        # Calculate lead score
        result = lead_scoring_service.calculate_lead_score(
            title=test_case['title'],
            content=test_case['content'],
            num_comments=test_case['num_comments']
        )
        
        # Display results
        print(f"Title: {test_case['title']}")
        print(f"Content: {test_case['content'][:100]}{'...' if len(test_case['content']) > 100 else ''}")
        print(f"Comments: {test_case['num_comments']}")
        
        print(f"\n🎯 TOTAL LEAD SCORE: {result.total_score}/100")
        
        # Categorize the lead
        if result.total_score >= 70:
            category = "🔥 HIGH PRIORITY LEAD"
        elif result.total_score >= 50:
            category = "⚡ MEDIUM PRIORITY LEAD"
        elif result.total_score >= 30:
            category = "💡 LOW PRIORITY LEAD"
        else:
            category = "❌ NOT A LEAD"
        
        print(f"Category: {category}")
        
        print(f"\n📊 Score Breakdown:")
        print(f"• Keyword Score: {result.keyword_score}/100 (Weight: {lead_scoring_service.KEYWORD_WEIGHT*100}%)")
        print(f"• Pattern Score: {result.pattern_score}/100 (Weight: {lead_scoring_service.PATTERN_WEIGHT*100}%)")
        print(f"• Urgency Score: {result.urgency_score}/100 (Weight: {lead_scoring_service.URGENCY_WEIGHT*100}%)")
        print(f"• Geographic Score: {result.geographic_score}/100 (Weight: {lead_scoring_service.GEOGRAPHIC_WEIGHT*100}%)")
        print(f"• Engagement Score: {result.engagement_score}/100 (Weight: {lead_scoring_service.ENGAGEMENT_WEIGHT*100}%)")
        
        # Show detailed analysis for high-scoring leads
        if result.total_score >= 50:
            print(f"\n🔍 Detailed Analysis:")
            
            # Keyword analysis
            kw = result.breakdown['keyword_analysis']
            print(f"Keywords: {kw['primary_matches']} primary, {kw['symptom_matches']} symptoms, {kw['context_matches']} context")
            
            # Pattern analysis
            pt = result.breakdown['pattern_analysis']
            if pt['pattern_matches'] > 0:
                print(f"Question Patterns: {pt['pattern_matches']} matches found")
            
            # Urgency analysis
            ur = result.breakdown['urgency_analysis']
            if ur['urgency_matches'] > 0:
                print(f"Urgency Level: {ur['urgency_level']} ({ur['urgency_matches']} indicators)")
            
            # Geographic analysis
            geo = result.breakdown['geographic_analysis']
            if geo['matched_locations']:
                print(f"Locations: {', '.join(geo['matched_locations'])}")
    
    print(f"\n{'=' * 80}")
    print("TEST COMPLETED")
    print(f"{'=' * 80}")


def test_weight_adjustment():
    """Test dynamic weight adjustment."""
    print(f"\n{'=' * 60}")
    print("TESTING DYNAMIC WEIGHT ADJUSTMENT")
    print(f"{'=' * 60}")
    
    sample_title = "Should I get tested for chlamydia? Having symptoms"
    sample_content = "I'm worried about STI exposure after unprotected sex. Having burning urination and discharge. In Canada."
    
    print(f"Sample Post: {sample_title}")
    print(f"Content: {sample_content}")
    
    # Test with default weights
    result1 = lead_scoring_service.calculate_lead_score(sample_title, sample_content, 10)
    print(f"\nDefault Weights - Total Score: {result1.total_score}")
    
    # Increase keyword importance
    lead_scoring_service.update_weights(
        keyword_weight=0.50,
        pattern_weight=0.20,
        urgency_weight=0.15,
        geographic_weight=0.10,
        engagement_weight=0.05
    )
    
    result2 = lead_scoring_service.calculate_lead_score(sample_title, sample_content, 10)
    print(f"Keyword-Heavy Weights - Total Score: {result2.total_score}")
    
    # Reset to default
    lead_scoring_service.update_weights(0.35, 0.25, 0.20, 0.10, 0.10)


if __name__ == "__main__":
    test_lead_scoring()
    test_weight_adjustment()
