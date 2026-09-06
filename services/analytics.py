import pandas as pd


def normalize_column_name(name: str) -> str:
    """
    Normalize column names so different spellings
    can be compared reliably.
    """

    return "".join(
        character.lower()
        for character in str(name)
        if character.isalnum()
    )


def find_business_column(
    dataframe: pd.DataFrame,
    aliases: list[str],
) -> str | None:
    """
    Find a business column using common German
    and English aliases.
    """

    normalized_columns = {
        normalize_column_name(column): column
        for column in dataframe.columns
    }

    for alias in aliases:
        normalized_alias = normalize_column_name(alias)

        if normalized_alias in normalized_columns:
            return normalized_columns[normalized_alias]

    return None


def enrich_business_metrics(
    dataframe: pd.DataFrame,
) -> tuple[pd.DataFrame, dict]:
    """
    Detect common business metrics and calculate
    missing metrics whenever possible.
    """

    result = dataframe.copy()

    detected = {
        "revenue": find_business_column(
            result,
            [
                "Revenue",
                "Umsatz",
                "Sales Revenue",
                "Turnover",
                "Erlös",
                "Erlöse",
            ],
        ),

        "cost": find_business_column(
            result,
            [
                "Cost",
                "Costs",
                "Kosten",
                "Expenses",
                "Aufwand",
            ],
        ),

        "profit": find_business_column(
            result,
            [
                "Profit",
                "Gewinn",
                "Operating Profit",
                "Ergebnis",
            ],
        ),

        "price": find_business_column(
            result,
            [
                "Price",
                "Preis",
                "Unit Price",
                "Stückpreis",
                "Stueckpreis",
                "Verkaufspreis",
            ],
        ),

        "quantity": find_business_column(
            result,
            [
                "Quantity",
                "Menge",
                "Qty",
                "Units",
                "Stückzahl",
                "Stueckzahl",
            ],
        ),

        "orders": find_business_column(
            result,
            [
                "Orders",
                "Bestellungen",
                "Order Count",
                "Anzahl Bestellungen",
            ],
        ),
    }

    # Revenue = Price × Quantity
    if (
        detected["revenue"] is None
        and detected["price"] is not None
        and detected["quantity"] is not None
    ):
        result["Revenue"] = (
            pd.to_numeric(
                result[detected["price"]],
                errors="coerce",
            )
            *
            pd.to_numeric(
                result[detected["quantity"]],
                errors="coerce",
            )
        )

        detected["revenue"] = "Revenue"

    # Profit = Revenue - Cost
    if (
        detected["profit"] is None
        and detected["revenue"] is not None
        and detected["cost"] is not None
    ):
        result["Profit"] = (
            pd.to_numeric(
                result[detected["revenue"]],
                errors="coerce",
            )
            -
            pd.to_numeric(
                result[detected["cost"]],
                errors="coerce",
            )
        )

        detected["profit"] = "Profit"

    # Profit Margin
    if (
        detected["revenue"] is not None
        and detected["profit"] is not None
    ):
        revenue = pd.to_numeric(
            result[detected["revenue"]],
            errors="coerce",
        )

        profit = pd.to_numeric(
            result[detected["profit"]],
            errors="coerce",
        )

        result["Profit Margin %"] = (
            profit.div(
                revenue.where(revenue != 0)
            )
            * 100
        )

        detected["margin"] = "Profit Margin %"

    else:
        detected["margin"] = None

    return result, detected


def calculate_business_kpis(
    dataframe: pd.DataFrame,
    columns: dict,
) -> dict:
    """
    Calculate the main management KPIs
    available in the current dataset.
    """

    kpis = {}

    revenue_column = columns.get("revenue")
    cost_column = columns.get("cost")
    profit_column = columns.get("profit")
    margin_column = columns.get("margin")
    orders_column = columns.get("orders")

    if revenue_column:
        kpis["revenue"] = pd.to_numeric(
            dataframe[revenue_column],
            errors="coerce",
        ).sum()

    if cost_column:
        kpis["cost"] = pd.to_numeric(
            dataframe[cost_column],
            errors="coerce",
        ).sum()

    if profit_column:
        kpis["profit"] = pd.to_numeric(
            dataframe[profit_column],
            errors="coerce",
        ).sum()

    if revenue_column and profit_column:
        revenue = kpis.get("revenue", 0)
        profit = kpis.get("profit", 0)

        kpis["margin"] = (
            profit / revenue * 100
            if revenue != 0
            else 0
        )

    elif margin_column:
        kpis["margin"] = pd.to_numeric(
            dataframe[margin_column],
            errors="coerce",
        ).mean()

    if orders_column:
        kpis["orders"] = pd.to_numeric(
            dataframe[orders_column],
            errors="coerce",
        ).sum()

    kpis["records"] = len(dataframe)

    return kpis


def calculate_percentage_change(
    current_value: float,
    previous_value: float,
) -> float | None:
    """
    Calculate percentage growth between two periods.
    """

    if (
        previous_value is None
        or pd.isna(previous_value)
        or previous_value == 0
    ):
        return None

    return (
        (current_value - previous_value)
        / abs(previous_value)
        * 100
    )
