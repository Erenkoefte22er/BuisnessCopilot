import pandas as pd

from services.analytics import find_business_column


def _get_numeric_series(
    dataframe: pd.DataFrame,
    column: str | None,
) -> pd.Series:
    if column is None or column not in dataframe.columns:
        return pd.Series(dtype="float64")

    return pd.to_numeric(dataframe[column], errors="coerce")


def _percentage_change(
    current: float,
    previous: float,
) -> float | None:
    if previous == 0:
        return None

    return ((current - previous) / abs(previous)) * 100


def calculate_period_comparison(
    dataframe: pd.DataFrame,
    columns: dict,
) -> dict:
    """
    Compare the latest 30 days with the previous 30 days.
    """

    date_column = find_business_column(
        dataframe,
        [
            "Date",
            "Datum",
            "Order Date",
            "Transaction Date",
        ],
    )

    revenue_column = columns.get("revenue")
    profit_column = columns.get("profit")

    if date_column is None:
        return {}

    working_data = dataframe.copy()

    working_data[date_column] = pd.to_datetime(
        working_data[date_column],
        errors="coerce",
        dayfirst=True,
    )

    working_data = working_data.dropna(subset=[date_column])

    if working_data.empty:
        return {}

    latest_date = working_data[date_column].max()

    current_start = latest_date - pd.Timedelta(days=29)
    previous_start = current_start - pd.Timedelta(days=30)

    current_period = working_data[
        working_data[date_column].between(
            current_start,
            latest_date,
        )
    ]

    previous_period = working_data[
        working_data[date_column].between(
            previous_start,
            current_start - pd.Timedelta(days=1),
        )
    ]

    result = {}

    if revenue_column:
        current_revenue = _get_numeric_series(
            current_period,
            revenue_column,
        ).sum()

        previous_revenue = _get_numeric_series(
            previous_period,
            revenue_column,
        ).sum()

        result["current_revenue"] = current_revenue
        result["previous_revenue"] = previous_revenue
        result["revenue_growth"] = _percentage_change(
            current_revenue,
            previous_revenue,
        )

    if profit_column:
        current_profit = _get_numeric_series(
            current_period,
            profit_column,
        ).sum()

        previous_profit = _get_numeric_series(
            previous_period,
            profit_column,
        ).sum()

        result["current_profit"] = current_profit
        result["previous_profit"] = previous_profit
        result["profit_growth"] = _percentage_change(
            current_profit,
            previous_profit,
        )

    return result


def generate_business_insights(
    dataframe: pd.DataFrame,
    columns: dict,
) -> list[str]:
    """
    Generate deterministic business insights from a dataframe.
    """

    insights = []

    revenue_column = columns.get("revenue")
    cost_column = columns.get("cost")
    profit_column = columns.get("profit")

    product_column = find_business_column(
        dataframe,
        [
            "Product",
            "Produkt",
            "Item",
            "Artikel",
        ],
    )

    region_column = find_business_column(
        dataframe,
        [
            "Region",
            "Market",
            "Markt",
            "Country",
            "Land",
        ],
    )

    if revenue_column:
        revenue = _get_numeric_series(
            dataframe,
            revenue_column,
        )

        total_revenue = revenue.sum()

        insights.append(
            f"Total revenue is {total_revenue:,.2f}."
        )

    if revenue_column and profit_column:
        revenue = _get_numeric_series(
            dataframe,
            revenue_column,
        )

        profit = _get_numeric_series(
            dataframe,
            profit_column,
        )

        total_revenue = revenue.sum()
        total_profit = profit.sum()

        if total_revenue != 0:
            margin = (total_profit / total_revenue) * 100

            insights.append(
                f"Overall profit margin is {margin:.1f}%."
            )

    if revenue_column and cost_column:
        revenue = _get_numeric_series(
            dataframe,
            revenue_column,
        ).sum()

        cost = _get_numeric_series(
            dataframe,
            cost_column,
        ).sum()

        if revenue != 0:
            cost_ratio = (cost / revenue) * 100

            insights.append(
                f"Costs represent {cost_ratio:.1f}% of revenue."
            )

    if revenue_column and product_column:
        product_revenue = (
            dataframe
            .assign(
                _revenue=_get_numeric_series(
                    dataframe,
                    revenue_column,
                )
            )
            .groupby(product_column)["_revenue"]
            .sum()
            .sort_values(ascending=False)
        )

        if not product_revenue.empty:
            top_product = product_revenue.index[0]
            top_revenue = product_revenue.iloc[0]

            insights.append(
                f"{top_product} is the top-performing product "
                f"with {top_revenue:,.2f} in revenue."
            )

    if revenue_column and region_column:
        region_revenue = (
            dataframe
            .assign(
                _revenue=_get_numeric_series(
                    dataframe,
                    revenue_column,
                )
            )
            .groupby(region_column)["_revenue"]
            .sum()
            .sort_values(ascending=False)
        )

        if not region_revenue.empty:
            top_region = region_revenue.index[0]
            top_revenue = region_revenue.iloc[0]

            insights.append(
                f"{top_region} is the strongest region "
                f"with {top_revenue:,.2f} in revenue."
            )

    comparison = calculate_period_comparison(
        dataframe,
        columns,
    )

    revenue_growth = comparison.get("revenue_growth")

    if revenue_growth is not None:
        if revenue_growth >= 0:
            insights.append(
                f"Revenue increased by {revenue_growth:.1f}% "
                "compared with the previous 30-day period."
            )
        else:
            insights.append(
                f"Revenue decreased by {abs(revenue_growth):.1f}% "
                "compared with the previous 30-day period."
            )

    profit_growth = comparison.get("profit_growth")

    if profit_growth is not None:
        if profit_growth >= 0:
            insights.append(
                f"Profit increased by {profit_growth:.1f}% "
                "compared with the previous 30-day period."
            )
        else:
            insights.append(
                f"Profit decreased by {abs(profit_growth):.1f}% "
                "compared with the previous 30-day period."
            )

    return insights
