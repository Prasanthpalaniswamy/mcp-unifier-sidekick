import json
import os
from typing import Any


def _normalize_chart_records(content: Any) -> list[dict[str, Any]]:
    if isinstance(content, str):
        try:
            content = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError("content must be valid JSON when provided as a string") from exc

    if isinstance(content, dict) and isinstance(content.get("data"), list):
        records = content["data"]
    elif isinstance(content, list):
        records = content
    elif isinstance(content, dict):
        records = [content]
    else:
        raise ValueError("Unsupported content format. Provide dict, list of dicts, or JSON string.")

    normalized = []
    for item in records:
        if isinstance(item, dict):
            normalized.append(item)
        else:
            normalized.append({"value": item})
    return normalized


def generate_chart_image(
    content: Any,
    chart_type: str,
    output_file: str,
    x_field: str,
    y_field: str = "",
    title: str = "Chart",
    group_by: str = "",
) -> str:
    """
    Generate a chart image from fetched JSON content.

    Supported chart types: bar, line, pie, horizontal_bar
    Output format: .png
    """
    import pandas as pd
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    records = _normalize_chart_records(content)
    if not records:
        raise ValueError("No records available for visualization.")

    df = pd.json_normalize(records)
    output_file = os.path.normpath(output_file)

    if os.path.splitext(output_file)[1].lower() != ".png":
        raise ValueError("output_file must end with .png")

    output_dir = os.path.dirname(output_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    if x_field not in df.columns:
        raise ValueError(f"x_field '{x_field}' not found in content")

    chart_type = chart_type.strip().lower()

    plt.figure(figsize=(10, 6))

    if chart_type == "pie":
        counts = df[x_field].astype(str).value_counts()
        plt.pie(counts.values, labels=counts.index, autopct="%1.1f%%", startangle=90)
        plt.title(title)
    else:
        if y_field:
            if y_field not in df.columns:
                raise ValueError(f"y_field '{y_field}' not found in content")
            plot_df = df[[x_field, y_field]].copy()
            plot_df[y_field] = pd.to_numeric(plot_df[y_field], errors="coerce")
            plot_df = plot_df.dropna(subset=[y_field])
            if plot_df.empty:
                raise ValueError(f"No numeric values found in y_field '{y_field}'")

            if group_by and group_by in df.columns:
                grouped = df.groupby([x_field, group_by])[y_field].sum().unstack(fill_value=0)
                if chart_type == "bar":
                    grouped.plot(kind="bar")
                elif chart_type == "line":
                    grouped.plot(kind="line", marker="o")
                elif chart_type == "horizontal_bar":
                    grouped.plot(kind="barh")
                else:
                    raise ValueError("Unsupported chart_type. Use bar, line, pie, or horizontal_bar.")
            else:
                aggregated = plot_df.groupby(x_field, as_index=False)[y_field].sum()
                if chart_type == "bar":
                    plt.bar(aggregated[x_field].astype(str), aggregated[y_field])
                elif chart_type == "line":
                    plt.plot(aggregated[x_field].astype(str), aggregated[y_field], marker="o")
                elif chart_type == "horizontal_bar":
                    plt.barh(aggregated[x_field].astype(str), aggregated[y_field])
                else:
                    raise ValueError("Unsupported chart_type. Use bar, line, pie, or horizontal_bar.")
        else:
            counts = df[x_field].astype(str).value_counts()
            if chart_type == "bar":
                plt.bar(counts.index, counts.values)
            elif chart_type == "line":
                plt.plot(counts.index, counts.values, marker="o")
            elif chart_type == "horizontal_bar":
                plt.barh(counts.index, counts.values)
            else:
                raise ValueError("For charts without y_field, use bar, line, pie, or horizontal_bar.")

        plt.title(title)
        plt.xlabel(x_field)
        plt.ylabel(y_field if y_field else "Count")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()

    plt.savefig(output_file, dpi=150, bbox_inches="tight")
    plt.close()
    return f"Chart saved to: {output_file}"


def generate_summary_dashboard(
    content: Any,
    output_file: str,
    title: str = "Summary Dashboard",
    metric_fields: str = "",
    category_field: str = "",
    top_n: int = 10,
) -> str:
    """
    Generate a simple dashboard image with summary metrics and an optional top-categories chart.

    Output format: .png
    """
    import pandas as pd
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    records = _normalize_chart_records(content)
    if not records:
        raise ValueError("No records available for dashboard generation.")

    df = pd.json_normalize(records)
    output_file = os.path.normpath(output_file)

    if os.path.splitext(output_file)[1].lower() != ".png":
        raise ValueError("output_file must end with .png")

    output_dir = os.path.dirname(output_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    metric_list = [field.strip() for field in metric_fields.split(",") if field.strip()]
    numeric_metrics = []
    for field in metric_list:
        if field in df.columns:
            series = pd.to_numeric(df[field], errors="coerce")
            if series.notna().any():
                numeric_metrics.append((field, series))

    fig = plt.figure(figsize=(14, 8))
    fig.suptitle(title, fontsize=16, fontweight="bold")

    ax_text = plt.subplot2grid((2, 2), (0, 0), colspan=2)
    ax_text.axis("off")

    summary_lines = [f"Total rows: {len(df)}", f"Total columns: {len(df.columns)}"]
    for field, series in numeric_metrics[:4]:
        summary_lines.append(
            f"{field}: sum={series.sum():,.2f}, avg={series.mean():,.2f}, min={series.min():,.2f}, max={series.max():,.2f}"
        )
    ax_text.text(0.01, 0.95, "\n".join(summary_lines), va="top", fontsize=11, family="monospace")

    if category_field and category_field in df.columns:
        counts = df[category_field].astype(str).value_counts().head(top_n)
        ax_bar = plt.subplot2grid((2, 2), (1, 0), colspan=2)
        ax_bar.bar(counts.index, counts.values)
        ax_bar.set_title(f"Top {min(top_n, len(counts))} values in {category_field}")
        ax_bar.set_xlabel(category_field)
        ax_bar.set_ylabel("Count")
        ax_bar.tick_params(axis="x", rotation=45)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(output_file, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return f"Summary dashboard saved to: {output_file}"


def generate_table_image(
    content: Any,
    output_file: str,
    title: str = "Data Table",
    columns: str = "",
    max_rows: int = 20,
) -> str:
    """
    Render fetched content as a table image.

    Output format: .png
    """
    import pandas as pd
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    records = _normalize_chart_records(content)
    if not records:
        raise ValueError("No records available for table rendering.")

    df = pd.json_normalize(records).fillna("")
    output_file = os.path.normpath(output_file)

    if os.path.splitext(output_file)[1].lower() != ".png":
        raise ValueError("output_file must end with .png")

    selected_columns = [column.strip() for column in columns.split(",") if column.strip()]
    if selected_columns:
        missing = [column for column in selected_columns if column not in df.columns]
        if missing:
            raise ValueError(f"Columns not found in content: {', '.join(missing)}")
        df = df[selected_columns]

    df = df.head(max_rows)

    output_dir = os.path.dirname(output_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    fig_height = max(2, min(12, 1 + 0.4 * (len(df) + 1)))
    fig_width = max(8, min(20, 2 + 1.5 * len(df.columns)))

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    ax.axis("off")
    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)

    table = ax.table(
        cellText=df.astype(str).values,
        colLabels=[str(col) for col in df.columns],
        loc="center",
        cellLoc="left",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.2)

    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return f"Table image saved to: {output_file}"