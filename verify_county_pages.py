#!/usr/bin/env python3
"""
Verify word count (300+ words) and detect duplicate content blocks on all county pages.
"""

import os
import re
from pathlib import Path
from bs4 import BeautifulSoup
from collections import defaultdict
import sys

COUNTIES_DIR = Path("dist/counties")
MIN_WORD_COUNT = 300
BLOCK_MIN_LENGTH = 50  # minimum characters to consider as a content block

def extract_text_content(html_content):
    """Extract readable text from HTML."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove script and style elements
    for script in soup(['script', 'style']):
        script.decompose()
    
    # Get text
    text = soup.get_text()
    
    # Break into lines and remove leading/trailing whitespace
    lines = (line.strip() for line in text.splitlines())
    # Remove empty lines
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = ' '.join(chunk for chunk in chunks if chunk)
    
    return text

def count_words(text):
    """Count words in text."""
    # Remove extra whitespace and split
    words = text.split()
    return len(words)

def extract_content_blocks(html_content):
    """Extract main content blocks (paragraphs, divs with text)."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove script, style, meta, etc.
    for tag in soup(['script', 'style', 'meta', 'link', 'nav', 'footer']):
        tag.decompose()
    
    blocks = []
    
    # Get main content blocks
    for element in soup.find_all(['p', 'div', 'section', 'article']):
        text = element.get_text(strip=True)
        if len(text) > BLOCK_MIN_LENGTH:
            # Normalize whitespace
            normalized = ' '.join(text.split())
            blocks.append(normalized)
    
    return blocks

def find_duplicate_blocks(blocks, min_similarity=0.95):
    """Find potentially duplicate blocks."""
    duplicates = []
    checked = set()
    
    for i, block1 in enumerate(blocks):
        if i in checked:
            continue
        for j, block2 in enumerate(blocks[i+1:], i+1):
            if j in checked:
                continue
            
            # Exact match
            if block1 == block2:
                duplicates.append((i, j, block1[:100]))
                checked.add(j)
    
    return duplicates

def main():
    """Main verification function."""
    if not COUNTIES_DIR.exists():
        print(f"Error: {COUNTIES_DIR} not found")
        sys.exit(1)
    
    html_files = sorted(COUNTIES_DIR.glob("*.html"))
    print(f"Found {len(html_files)} county HTML files\n")
    print("=" * 100)
    
    issues = defaultdict(list)
    stats = {
        'total_files': len(html_files),
        'word_count_pass': 0,
        'word_count_fail': 0,
        'duplicate_blocks': 0,
        'files_with_issues': 0
    }
    
    for html_file in html_files:
        county_name = html_file.stem
        
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Extract and count words
            text = extract_text_content(html_content)
            word_count = count_words(text)
            
            # Extract blocks and check for duplicates
            blocks = extract_content_blocks(html_content)
            duplicates = find_duplicate_blocks(blocks)
            
            # Check word count
            if word_count < MIN_WORD_COUNT:
                issues['word_count'].append({
                    'file': county_name,
                    'count': word_count,
                    'required': MIN_WORD_COUNT
                })
                stats['word_count_fail'] += 1
            else:
                stats['word_count_pass'] += 1
            
            # Check for duplicates
            if duplicates:
                issues['duplicates'].append({
                    'file': county_name,
                    'count': len(duplicates),
                    'details': duplicates
                })
                stats['duplicate_blocks'] += len(duplicates)
            
            # Track if file has any issues
            if word_count < MIN_WORD_COUNT or duplicates:
                stats['files_with_issues'] += 1
        
        except Exception as e:
            print(f"ERROR processing {county_name}: {e}")
            issues['errors'].append({'file': county_name, 'error': str(e)})
    
    # Print summary
    print("\n" + "=" * 100)
    print("SUMMARY")
    print("=" * 100)
    print(f"Total files: {stats['total_files']}")
    print(f"Word count PASS (≥300): {stats['word_count_pass']}")
    print(f"Word count FAIL (<300): {stats['word_count_fail']}")
    print(f"Files with duplicate blocks: {len(issues.get('duplicates', []))}")
    print(f"Total duplicate blocks found: {stats['duplicate_blocks']}")
    print(f"Total files with issues: {stats['files_with_issues']}")
    
    # Print detailed issues
    if issues.get('word_count'):
        print("\n" + "=" * 100)
        print("FILES WITH INSUFFICIENT WORD COUNT (<300 words)")
        print("=" * 100)
        for item in sorted(issues['word_count'], key=lambda x: x['count']):
            print(f"  {item['file']}: {item['count']} words (need {item['required']})")
    
    if issues.get('duplicates'):
        print("\n" + "=" * 100)
        print("FILES WITH DUPLICATE CONTENT BLOCKS")
        print("=" * 100)
        for item in issues['duplicates']:
            print(f"\n  {item['file']}: {item['count']} duplicate block(s)")
            for dup in item['details']:
                idx1, idx2, preview = dup
                print(f"    Block {idx1} ≈ Block {idx2}: \"{preview}...\"")
    
    if issues.get('errors'):
        print("\n" + "=" * 100)
        print("PROCESSING ERRORS")
        print("=" * 100)
        for item in issues['errors']:
            print(f"  {item['file']}: {item['error']}")
    
    # Exit with proper status
    if stats['word_count_fail'] > 0 or stats['duplicate_blocks'] > 0:
        print("\n" + "=" * 100)
        print("ACTION REQUIRED: Issues found that need to be addressed.")
        print("=" * 100)
        return 1
    else:
        print("\n" + "=" * 100)
        print("✓ ALL COUNTY PAGES PASS VERIFICATION")
        print("=" * 100)
        return 0

if __name__ == "__main__":
    sys.exit(main())
