import io

import pandas as pd
import pytest

from services.data_loader import (
    detect_date_columns,
    make_demo_data,
    read_uploaded_file,
)


def test_read_csv_file():
    csv_content = (
        "Product,Revenue,Cost\n"
        "Laptop,1200,800\n"
        "Monitor,500,300\n"
    ).encode("utf-8")

    result = read_uploaded_file(
        csv_content,
        "sales.csv",
    )

    assert len(result) == 2
    assert result["Revenue"].sum() == 1700


def test_read_excel_file():
    original = pd.DataFrame(
        {
            "Product": ["Laptop", "Monitor"],
            "Revenue": [1200, 500],
        }
    )

    buffer = io.BytesIO()

    original.to_excel(
        buffer,
        index=False,
    )

    result = read_uploaded_file(
        buffer.getvalue(),
        "sales.xlsx",
    )

    assert len(result) == 2
    assert result["Revenue"].sum() == 1700


def test_unsupported_file_type():
    with pytest.raises(ValueError):
        read_uploaded_file(
            b"example",
            "sales.txt",
        )


def test_demo_data_is_created():
    result = make_demo_data()

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 120

    expected_columns = {
        "Date",
        "Product",
        "Region",
        "Revenue",
        "Cost",
        "Profit",
        "Orders",
    }

    assert expected_columns.issubset(result.columns)


def test_demo_profit_is_correct():
    result = make_demo_data()

    expected_profit = (
        result["Revenue"] - result["Cost"]
    ).round(2)

    pd.testing.assert_series_equal(
        result["Profit"],
        expected_profit,
        check_names=False,
    )


def test_datetime_column_is_detected():
    data = pd.DataFrame(
        {
            "Date": pd.date_range(
                "2026-01-01",
                periods=3,
            ),
            "Revenue": [100, 200, 300],
        }
    )

    result = detect_date_columns(data)

    assert "Date" in result


def test_text_date_column_is_detected():
    data = pd.DataFrame(
        {
            "Order Date": [
                "01.01.2026",
                "02.01.2026",
                "03.01.2026",
            ],
            "Revenue": [100, 200, 300],
        }
    )

    result = detect_date_columns(data)

    assert "Order Date" in result


def test_normal_text_column_is_not_date():
    data = pd.DataFrame(
        {
            "Product": [
                "Laptop",
                "Monitor",
                "Keyboard",
            ],
        }
    )

    result = detect_date_columns(data)

    assert "Product" not in result
    