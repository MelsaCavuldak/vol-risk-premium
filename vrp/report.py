import pandas as pd


def markdown_table(frame, formats=None):
    formats = formats or {}
    header = "| " + " | ".join([frame.index.name or ""] + [str(c) for c in frame.columns]) + " |"
    rule = "|" + "---|" * (len(frame.columns) + 1)
    lines = [header, rule]
    for idx, row in frame.iterrows():
        cells = [formats.get(c, "{:.3f}").format(v) if pd.notna(v) else "" for c, v in row.items()]
        label = str(idx.date()) if hasattr(idx, "date") else str(idx)
        lines.append("| " + " | ".join([label] + cells) + " |")
    return "\n".join(lines)


def as_percent(frame, columns, digits=1):
    """Return a copy where the given columns are expressed in percent and renamed 'name (%)'."""
    out = frame.copy()
    for column in columns:
        out[column] = (100 * out[column]).round(digits)
    return out.rename(columns={column: f"{column} (%)" for column in columns})
