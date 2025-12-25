"""
Text-based summarization utilities for search results.
No AI models used - pure algorithmic approach.
"""
import re
from collections import Counter
from typing import List, Dict, Any


def extract_keywords(text: str, min_length: int = 3, max_keywords: int = 10) -> List[str]:
    """
    Extract important keywords from text using frequency analysis.
    """
    if not text:
        return []
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Convert to lowercase and split into words
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    
    # Common stop words to exclude
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that',
        'these', 'those', 'it', 'its', 'they', 'them', 'their', 'there',
        'then', 'than', 'when', 'where', 'what', 'which', 'who', 'how',
        'why', 'about', 'into', 'onto', 'upon', 'over', 'under', 'through',
        'during', 'before', 'after', 'above', 'below', 'between', 'among'
    }
    
    # Filter out stop words and count frequencies
    filtered_words = [w for w in words if w not in stop_words and len(w) >= min_length]
    word_freq = Counter(filtered_words)
    
    # Get top keywords
    keywords = [word for word, count in word_freq.most_common(max_keywords)]
    return keywords


def extract_sentences(text: str) -> List[str]:
    """
    Extract sentences from text.
    """
    if not text:
        return []
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Split by sentence endings
    sentences = re.split(r'[.!?]+\s+', text)
    
    # Clean and filter sentences
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    return sentences


def score_sentence(sentence: str, keywords: List[str], query_terms: List[str]) -> float:
    """
    Score a sentence based on keyword density and query term matches.
    """
    sentence_lower = sentence.lower()
    score = 0.0
    
    # Count keyword matches
    keyword_matches = sum(1 for keyword in keywords if keyword in sentence_lower)
    score += keyword_matches * 2.0
    
    # Count query term matches (higher weight)
    query_matches = sum(1 for term in query_terms if term.lower() in sentence_lower)
    score += query_matches * 5.0
    
    # Prefer sentences of medium length (not too short, not too long)
    length = len(sentence.split())
    if 10 <= length <= 30:
        score += 1.0
    elif length > 50:
        score -= 0.5
    
    return score


def generate_summary(results: Dict[str, List[Any]], query: str) -> str:
    """
    Generate a grammatically correct, AI-style text-based summary of search results.
    Uses keyword extraction, frequency analysis, and sentence scoring.
    """
    if not results or not any(results.values()):
        return f"I couldn't find any results matching '{query}'. Please try different keywords or check your spelling."
    
    # Extract query terms
    query_terms = [term.lower() for term in re.findall(r'\b\w+\b', query.lower()) if len(term) >= 3]
    
    # Collect all text content from results
    all_text = []
    result_counts = {}
    
    for category, items in results.items():
        if not items:
            continue
        
        result_counts[category] = len(items)
        
        for item in items[:5]:  # Limit to first 5 items per category
            text_parts = []
            
            if category == 'faculty':
                text_parts.extend([
                    getattr(item, 'name', ''),
                    getattr(item, 'designation', ''),
                    getattr(item, 'bio', '') or '',
                    getattr(item, 'about', '') or '',
                    getattr(item, 'researches', '') or '',
                ])
            elif category == 'publications':
                text_parts.extend([
                    getattr(item, 'title', ''),
                    getattr(item, 'published_at', '') or '',
                    getattr(item, 'contribution', '') or '',
                ])
            elif category == 'posts':
                text_parts.extend([
                    getattr(item, 'short_title', ''),
                    getattr(item, 'long_title', ''),
                    getattr(item, 'tags', '') or '',
                    str(getattr(item, 'description', '') or ''),
                ])
            elif category == 'club_posts':
                text_parts.extend([
                    getattr(item, 'short_title', ''),
                    getattr(item, 'long_title', ''),
                    getattr(item, 'tags', '') or '',
                    str(getattr(item, 'description', '') or ''),
                ])
            elif category == 'courses':
                text_parts.extend([
                    getattr(item, 'title', ''),
                    getattr(item, 'course_code', ''),
                ])
            elif category == 'clubs':
                text_parts.extend([
                    getattr(item, 'name', ''),
                    getattr(item, 'moto', '') or '',
                    str(getattr(item, 'description', '') or ''),
                ])
            elif category == 'staff':
                text_parts.extend([
                    getattr(item, 'name', ''),
                    getattr(item, 'designation', ''),
                ])
            elif category == 'officers':
                text_parts.extend([
                    getattr(item, 'name', ''),
                    getattr(item, 'position', ''),
                ])
            
            all_text.append(' '.join([str(t) for t in text_parts if t]))
    
    # Combine all text
    combined_text = ' '.join(all_text)
    
    # Extract keywords
    keywords = extract_keywords(combined_text, max_keywords=15)
    
    # Extract sentences
    sentences = extract_sentences(combined_text)
    
    # Score and rank sentences
    scored_sentences = [(score_sentence(s, keywords, query_terms), s) for s in sentences]
    scored_sentences.sort(reverse=True, key=lambda x: x[0])
    
    # Select top sentences for summary
    top_sentences = [s for score, s in scored_sentences[:3] if score > 0]
    
    # Build grammatically correct summary
    total_results = sum(result_counts.values())
    num_categories = len(result_counts)
    
    # Category names with proper pluralization
    category_names = {
        'faculty': ('Faculty Member', 'Faculty Members'),
        'publications': ('Publication', 'Publications'),
        'posts': ('Post/Notice', 'Posts/Notices'),
        'club_posts': ('Club Post', 'Club Posts'),
        'courses': ('Course', 'Courses'),
        'clubs': ('Club', 'Clubs'),
        'staff': ('Staff Member', 'Staff Members'),
        'officers': ('Officer', 'Officers'),
    }
    
    # Start building the summary
    summary_parts = []
    
    # Opening statement
    if total_results == 1:
        summary_parts.append(f"I found {total_results} result for '{query}'.")
    else:
        summary_parts.append(f"I found {total_results} results for '{query}'.")
    
    # Category breakdown with proper grammar
    if num_categories == 1:
        cat_name, count = list(result_counts.items())[0]
        singular, plural = category_names.get(cat_name, (cat_name, cat_name))
        if count == 1:
            summary_parts.append(f"The result is {count} {singular.lower()}.")
        else:
            summary_parts.append(f"All results are {count} {plural.lower()}.")
    elif num_categories == 2:
        items = list(result_counts.items())
        items.sort(key=lambda x: x[1], reverse=True)
        cat1_name, count1 = items[0]
        cat2_name, count2 = items[1]
        _, plural1 = category_names.get(cat1_name, (cat1_name, cat1_name))
        _, plural2 = category_names.get(cat2_name, (cat2_name, cat2_name))
        summary_parts.append(f"The results include {count1} {plural1.lower()} and {count2} {plural2.lower()}.")
    else:
        category_list = []
        for cat, count in sorted(result_counts.items(), key=lambda x: x[1], reverse=True):
            _, plural = category_names.get(cat, (cat, cat))
            if count == 1:
                category_list.append(f"{count} {plural.lower()}")
            else:
                category_list.append(f"{count} {plural.lower()}")
        
        if len(category_list) > 2:
            last_item = category_list.pop()
            summary_parts.append(f"The results span {len(category_list) + 1} categories: {', '.join(category_list)}, and {last_item}.")
        else:
            summary_parts.append(f"The results include {', '.join(category_list)}.")
    
    # Add key information if available
    if top_sentences:
        # Clean and format sentences
        clean_sentences = []
        for s in top_sentences[:2]:
            # Remove extra whitespace and ensure proper capitalization
            s = re.sub(r'\s+', ' ', s.strip())
            if s and not s[0].isupper():
                s = s[0].upper() + s[1:] if len(s) > 1 else s.upper()
            if s and not s.endswith(('.', '!', '?')):
                s = s + '.'
            clean_sentences.append(s)
        
        if clean_sentences:
            summary_parts.append("Key highlights: " + " ".join(clean_sentences))
    
    # Add related topics if available
    if keywords and query_terms:
        matching_keywords = [kw for kw in keywords[:5] if any(term in kw for term in query_terms)]
        if matching_keywords:
            # Capitalize keywords
            formatted_keywords = [kw.capitalize() for kw in matching_keywords[:3]]
            if len(formatted_keywords) == 1:
                summary_parts.append(f"Related topic: {formatted_keywords[0]}.")
            elif len(formatted_keywords) == 2:
                summary_parts.append(f"Related topics: {formatted_keywords[0]} and {formatted_keywords[1]}.")
            else:
                summary_parts.append(f"Related topics: {', '.join(formatted_keywords[:-1])}, and {formatted_keywords[-1]}.")
    
    return " ".join(summary_parts)

