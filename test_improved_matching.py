#!/usr/bin/env python3
"""
Test script to verify the improved matching algorithm produces no negative percentages
and provides better matching results.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.improved_ai_models import improved_talent_matcher
import json

def test_sample_candidates():
    """Test the improved matching with sample candidates"""
    
    # Load sample resume data
    with open('data/resumes/sample_resumes.json', 'r') as f:
        sample_resumes = json.load(f)
    
    print("🔍 Testing Improved Talent Matching Algorithm")
    print("=" * 60)
    
    all_scores_positive = True
    total_tests = 0
    
    for candidate in sample_resumes:
        print(f"\n👤 Testing candidate: {candidate['name']}")
        print(f"   Skills: {', '.join(candidate['skills'][:5])}...")
        print(f"   Experience: {candidate['experience_years']} years")
        
        # Create candidate data for matching
        candidate_data = {
            "name": candidate['name'],
            "email": candidate['email'],
            "phone": candidate['phone'],
            "applied_for": candidate['applied_for'],
            "resume_text": candidate['resume_text'],
            "skills": candidate['skills'],
            "experience_years": candidate['experience_years']
        }
        
        # Get matches using improved algorithm
        matches = improved_talent_matcher.match_candidate_to_jobs(candidate_data, top_k=5)
        
        print(f"\n   📊 Match Results:")
        for i, match in enumerate(matches, 1):
            score = match['similarity_score']
            total_tests += 1
            
            # Check if score is negative
            if score < 0:
                all_scores_positive = False
                print(f"   ❌ {i}. {match['title']}: {score:.1f}% (NEGATIVE!)")
            else:
                print(f"   ✅ {i}. {match['title']}: {score:.1f}% ({match['confidence_band']})")
            
            # Show score breakdown if available
            if 'score_breakdown' in match:
                breakdown = match['score_breakdown']
                print(f"      📈 Breakdown: Semantic={breakdown['semantic_score']:.3f}, "
                      f"Skill={breakdown['skill_score']:.3f}, "
                      f"Experience={breakdown['experience_score']:.3f}")
            
            print(f"      💬 {match['explanation']}")
        
        print("-" * 50)
    
    print(f"\n🎯 Test Summary:")
    print(f"   Total scores tested: {total_tests}")
    print(f"   All scores positive: {'✅ YES' if all_scores_positive else '❌ NO'}")
    
    if all_scores_positive:
        print(f"   🎉 SUCCESS: No negative percentages found!")
    else:
        print(f"   ⚠️  FAILURE: Some negative percentages detected!")
    
    return all_scores_positive

def test_edge_cases():
    """Test edge cases that might produce negative scores"""
    
    print(f"\n🧪 Testing Edge Cases")
    print("=" * 60)
    
    edge_cases = [
        {
            "name": "No Skills Candidate",
            "skills": [],
            "experience_years": 0,
            "resume_text": "John Doe\nRecent graduate with no work experience."
        },
        {
            "name": "Mismatched Skills Candidate", 
            "skills": ["Cooking", "Driving", "Singing"],
            "experience_years": 10,
            "resume_text": "Jane Smith\nProfessional chef with 10 years experience in cooking and restaurant management."
        },
        {
            "name": "Single Skill Candidate",
            "skills": ["Python"],
            "experience_years": 1,
            "resume_text": "Bob Wilson\nJunior developer with basic Python knowledge."
        }
    ]
    
    all_positive = True
    
    for case in edge_cases:
        print(f"\n🔬 Testing: {case['name']}")
        
        candidate_data = {
            "name": case['name'],
            "email": "test@example.com",
            "phone": "+1234567890",
            "applied_for": "job_001",
            "resume_text": case['resume_text'],
            "skills": case['skills'],
            "experience_years": case['experience_years']
        }
        
        matches = improved_talent_matcher.match_candidate_to_jobs(candidate_data, top_k=3)
        
        for match in matches:
            score = match['similarity_score']
            if score < 0:
                all_positive = False
                print(f"   ❌ {match['title']}: {score:.1f}% (NEGATIVE!)")
            else:
                print(f"   ✅ {match['title']}: {score:.1f}%")
    
    return all_positive

def test_skill_normalization():
    """Test skill normalization functionality"""
    
    print(f"\n🔧 Testing Skill Normalization")
    print("=" * 60)
    
    test_skills = [
        ("js", "javascript"),
        ("k8s", "kubernetes"), 
        ("tf", "tensorflow"),
        ("ml", "machine learning"),
        ("react.js", "react"),
        ("node.js", "nodejs")
    ]
    
    all_correct = True
    
    for input_skill, expected in test_skills:
        normalized = improved_talent_matcher.normalize_skill_name(input_skill)
        if normalized == expected:
            print(f"   ✅ '{input_skill}' → '{normalized}'")
        else:
            print(f"   ❌ '{input_skill}' → '{normalized}' (expected '{expected}')")
            all_correct = False
    
    return all_correct

def main():
    """Run all tests"""
    
    print("🚀 Starting Improved Matching Algorithm Tests")
    print("=" * 80)
    
    try:
        # Test 1: Sample candidates
        test1_passed = test_sample_candidates()
        
        # Test 2: Edge cases
        test2_passed = test_edge_cases()
        
        # Test 3: Skill normalization
        test3_passed = test_skill_normalization()
        
        # Final summary
        print(f"\n🏁 Final Test Results")
        print("=" * 80)
        print(f"   Sample Candidates Test: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
        print(f"   Edge Cases Test: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
        print(f"   Skill Normalization Test: {'✅ PASSED' if test3_passed else '❌ FAILED'}")
        
        all_passed = test1_passed and test2_passed and test3_passed
        
        if all_passed:
            print(f"\n🎉 ALL TESTS PASSED! The improved matching algorithm is working correctly.")
            print(f"   ✅ No negative percentages detected")
            print(f"   ✅ All edge cases handled properly")
            print(f"   ✅ Skill normalization working correctly")
        else:
            print(f"\n⚠️  SOME TESTS FAILED! Please review the issues above.")
        
        return all_passed
        
    except Exception as e:
        print(f"\n❌ ERROR: Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
