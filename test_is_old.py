from datetime import datetime, timedelta

def test_is_old():
    # Test when the timestamp is exactly 2 months ago
    two_months_ago = datetime.now() - timedelta(days=60)
    assert is_old(two_months_ago.timestamp() * 1000) == True

    # Test when the timestamp is less than 2 months ago
    one_month_ago = datetime.now() - timedelta(days=30)
    assert is_old(one_month_ago.timestamp() * 1000) == False

    # Test when the timestamp is more than 2 months ago
    three_months_ago = datetime.now() - timedelta(days=90)
    assert is_old(three_months_ago.timestamp() * 1000) == True
