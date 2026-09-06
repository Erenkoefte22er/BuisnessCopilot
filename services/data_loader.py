import io

import pandas as pd


def read_uploaded_file(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """Load a CSV or Excel file into a pandas DataFrame."""

    filename = filename.lower()

    if filename.endswith(".xlsx"):
        return pd.read_excel(io.BytesIO(file_bytes))

    if filename.endswith(".csv"):
        encodings = (
            "utf-8",
            "utf-8-sig",
            "latin1",
        )

        for encoding in encodings:
            try:
                text = file_bytes.decode(encoding)

                return pd.read_csv(
                    io.StringIO(text),
                    sep=None,
                    engine="python",
                )

            except (UnicodeDecodeError, pd.errors.ParserError):
                continue

    raise ValueError(
        "The file could not be read. Please use CSV or XLSX."
    )


def make_demo_data() -> pd.DataFrame:
    """Create demo business data for the example workspace."""

    dates = pd.date_range(
        start="2026-01-01",
        periods=120,
        freq="D",
    )

    products = [
        "Analytics Pro",
        "Finance Hub",
        "Sales Desk",
        "Ops Suite",
    ]

    regions = [
        "DACH",
        "North",
        "West",
        "South",
    ]

    rows = []

    for index, date in enumerate(dates):
        product = products[index % len(products)]
        region = regions[(index // 3) % len(regions)]

        revenue = (
            620
            + (index % 17) * 48
            + (index // 30) * 95
        )

        cost = revenue * (
            0.52
            + (index % 5) * 0.025
        )

        rows.append(
            {
                "Date": date,
                "Product": product,
                "Region": region,
                "Revenue": round(revenue, 2),
                "Cost": round(cost, 2),
                "Profit": round(revenue - cost, 2),
                "Orders": 8 + (index % 13),
            }
        )

    return pd.DataFrame(rows)


def detect_date_columns(dataframe: pd.DataFrame) -> list[str]:
    """Detect columns that most likely contain dates."""

    candidates = []

    date_keywords = (
        "date",
        "datum",
        "time",
        "zeit",
        "month",
        "monat",
        "day",
        "tag",
    )

    for column in dataframe.columns:
        column_name = str(column).lower()

        if pd.api.types.is_datetime64_any_dtype(
            dataframe[column]
        ):
            candidates.append(column)
            continue

        if (
            dataframe[column].dtype == "object"
            and any(
                keyword in column_name
                for keyword in date_keywords
            )
        ):
            parsed = pd.to_datetime(
                dataframe[column],
                errors="coerce",
                dayfirst=True,
            )

            if parsed.notna().mean() >= 0.65:
                candidates.append(column)

    return candidates
