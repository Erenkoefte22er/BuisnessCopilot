import pandas as pd

from services.insight_engine import (
    calculate_period_comparison,
    generate_business_insights,
)


def test_period_comparison_revenue_growth():
    data = pd.DataFrame(
        {
            "Date": pd.date_range("2026-01-01", periods=60, freq="D"),
            "Revenue": [100] * 30 + [200] * 30,
            "Profit": [20] * 30 + [40] * 30,
        }
    )

    columns = {
        "revenue": "Revenue",
        "profit": "Profit",
    }

    result = calculate_period_comparison(data, columns)

    assert result["current_revenue"] == 6000
    assert result["previous_revenue"] == 3000
    assert result["revenue_growth"] == 100.0


def test_period_comparison_profit_growth():
    data = pd.DataFrame(
        {
            "Date": pd.date_range("2026-01-01", periods=60, freq="D"),
            "Revenue": [100] * 60,
            "Profit": [20] * 30 + [30] * 30,
        }
    )

    columns = {
        "revenue": "Revenue",
        "profit": "Profit",
    }

    result = calculate_period_comparison(data, columns)

    assert result["current_profit"] == 900
    assert result["previous_profit"] == 600
    assert result["profit_growth"] == 50.0


def test_period_comparison_without_date_returns_empty_dict():
    data = pd.DataFrame(
        {
            "Revenue": [100, 200, 300],
            "Profit": [20, 40, 60],
        }
    )

    columns = {
        "revenue": "Revenue",
        "profit": "Profit",
    }

    result = calculate_period_comparison(data, columns)

    assert result == {}


def test_zero_previous_revenue_returns_no_growth():
    data = pd.DataFrame(
        {
            "Date": pd.date_range("2026-01-01", periods=60, freq="D"),
            "Revenue": [0] * 30 + [200] * 30,
            "Profit": [0] * 30 + [40] * 30,
        }
    )

    columns = {
        "revenue": "Revenue",
        "profit": "Profit",
    }

    result = calculate_period_comparison(data, columns)

    assert result["revenue_growth"] is None


def test_business_insights_are_generated():
    data = pd.DataFrame(
        {
            "Date": pd.date_range("2026-01-01", periods=4, freq="D"),
            "Product": [
                "Analytics Pro",
                "Analytics Pro",
                "Finance Hub",
                "Finance Hub",
            ],
            "Region": [
                "DACH",
                "DACH",
                "West",
                "West",
            ],
            "Revenue": [1000, 1200, 500, 600],
            "Cost": [600, 700, 400, 450],
            "Profit": [400, 500, 100, 150],
        }
    )

    columns = {
        "revenue": "Revenue",
        "cost": "Cost",
        "profit": "Profit",
    }

    insights = generate_business_insights(data, columns)

    assert any("Total revenue" in insight for insight in insights)
    assert any("profit margin" in insight for insight in insights)
    assert any("Costs represent" in insight for insight in insights)
    assert any("Analytics Pro" in insight for insight in insights)
    assert any("DACH" in insight for insight in insights)


def test_top_product_is_detected():
    data = pd.DataFrame(
        {
            "Product": ["Product A", "Product A", "Product B"],
            "Revenue": [1000, 1000, 500],
        }
    )

    columns = {
        "revenue": "Revenue",
    }

    insights = generate_business_insights(data, columns)

    assert any(
        "Product A is the top-performing product" in insight
        for insight in insights
    )


def test_top_region_is_detected():
    data = pd.DataFrame(
        {
            "Region": ["DACH", "DACH", "West"],
            "Revenue": [1000, 800, 500],
        }
    )

    columns = {
        "revenue": "Revenue",
    }

    insights = generate_business_insights(data, columns)

    assert any(
        "DACH is the strongest region" in insight
        for insight in insights
    )
    