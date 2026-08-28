import pytest

def test_sql_safety_rejection():
    dangerous_queries = ["DROP TABLE floats;", "DELETE FROM profiles;", "UPDATE measurements SET temp=0;"]
    forbidden_words = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE"]
    
    for query in dangerous_queries:
        is_safe = not any(word in query.upper() for word in forbidden_words)
        assert is_safe is False
