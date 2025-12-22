"""
Test time-travel debugging - simulate running dashboard at different times
"""
import asyncio
from datetime import datetime, timedelta
from main import main


async def test_time_travel():
    """Test the dashboard at different points in time."""

    print("\n" + "="*80)
    print("TEST 1: Run dashboard 'today'")
    print("="*80)
    await main(as_of=datetime.now())

    print("\n\n" + "="*80)
    print("TEST 2: Time-travel to 7 days ago")
    print("="*80)
    seven_days_ago = datetime.now() - timedelta(days=7)
    await main(as_of=seven_days_ago)

    print("\n\n" + "="*80)
    print("TEST 3: Time-travel to 15 days ago")
    print("="*80)
    fifteen_days_ago = datetime.now() - timedelta(days=15)
    await main(as_of=fifteen_days_ago)


if __name__ == "__main__":
    asyncio.run(test_time_travel())
