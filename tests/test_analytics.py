import pandas as pd

from services.analytics import (
    calculate_business_kpis,
    calculate_percentage_change,
    enrich_business_metrics,
)


def test_revenue_is_calculated_from_price_and_quantity():
    data = pd.DataFrame(
        {
            "Price": [100, 200],
            "Quantity": [2, 3],
            "Cost": [120, 400],
        }
    )

    result, columns = enrich_business_metrics(data)

    assert "Revenue" in result.columns
    assert result["Revenue"].tolist() == [200, 600]
    assert columns["revenue"] == "Revenue"


def test_profit_is_calculated_correctly():
    data = pd.DataFrame(
        {
            "Revenue": [1000, 2000],
            "Cost": [700, 1200],
        }
    )

    result, columns = enrich_business_metrics(data)

    assert "Profit" in result.columns
    assert result["Profit"].tolist() == [300, 800]
    assert columns["profit"] == "Profit"


def test_profit_margin_is_calculated_correctly():
    data = pd.DataFrame(
        {
            "Revenue": [1000],
            "Cost": [750],
        }
    )

    result, columns = enrich_business_metrics(data)

    margin = result["Profit Margin %"].iloc[0]

    assert round(margin, 2) == 25.00
    assert columns["margin"] == "Profit Margin %"


def test_german_column_names_are_detected():
    data = pd.DataFrame(
        {
            "Umsatz": [1000],
            "Kosten": [600],
        }
    )

    result, columns = enrich_business_metrics(data)

    assert columns["revenue"] == "Umsatz"
    assert columns["cost"] == "Kosten"
    assert result["Profit"].iloc[0] == 400


def test_business_kpis():
    data = pd.DataFrame(
        {
            "Revenue": [1000, 2000],
            "Cost": [600, 1200],
            "Profit": [400, 800],
            "Orders": [5, 10],
        }
    )

    enriched, columns = enrich_business_metrics(data)

    kpis = calculate_business_kpis(
        enriched,
        columns,
    )

    assert kpis["revenue"] == 3000
    assert kpis["cost"] == 1800
    assert kpis["profit"] == 1200
    assert kpis["orders"] == 15
    assert round(kpis["margin"], 2) == 40.00
    assert kpis["records"] == 2


def test_percentage_growth():
    growth = calculate_percentage_change(
        current_value=120,
        previous_value=100,
    )

    assert growth == 20


def test_percentage_decline():
    growth = calculate_percentage_change(
        current_value=80,
        previous_value=100,
    )

    assert growth == -20


def test_percentage_change_handles_zero():
    growth = calculate_percentage_change(
        current_value=100,
        previous_value=0,
    )

    assert growth is None


def test_zero_revenue_does_not_break_margin():
    data = pd.DataFrame(
        {
            "Revenue": [0],
            "Cost": [100],
        }
    )

    result, columns = enrich_business_metrics(data)

    assert "Profit Margin %" in result.columns
    assert pd.isna(result["Profit Margin %"].iloc[0])
    