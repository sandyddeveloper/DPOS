"""
SQL, URL, token, code, text detection.
"""
import re

def detect_category(content: str) -> str:
    """Categorize text content into SQL, URL, token, code, or generic text."""
    if not content:
        return "text"
        
    content_strip = content.strip()
    
    # 1. Detect URL
    url_pattern = re.compile(r'^https?://[^\s/$.?#].[^\s]*$', re.IGNORECASE)
    if url_pattern.match(content_strip):
        return "url"
        
    # 2. Detect SQL
    sql_keywords = {"select", "insert", "update", "delete", "create table", "drop table", "alter table", "where", "from", "join"}
    words = set(re.findall(r'\b\w+\b', content_strip.lower()))
    if len(words.intersection(sql_keywords)) >= 2:
        return "sql"
        
    # 3. Detect Token / JWT / API Key
    token_pattern = re.compile(r'^(ghp_[a-zA-Z0-9]{36}|xoxb-[a-zA-Z0-9-]+|eyJ[a-zA-Z0-9-_]+\.eyJ[a-zA-Z0-9-_]+\.[a-zA-Z0-9-_]+)$')
    if token_pattern.match(content_strip) or ((len(content_strip) == 32 or len(content_strip) == 40 or len(content_strip) == 64) and content_strip.isalnum()):
        return "token"
        
    # 4. Detect Code
    code_indicators = {"def ", "class ", "import ", "const ", "let ", "function ", "void ", "public static", "package ", "<?php", "<html>"}
    if any(ind in content_strip for ind in code_indicators) or ("{" in content_strip and "}" in content_strip and ";" in content_strip):
        return "code"
        
    return "text"
