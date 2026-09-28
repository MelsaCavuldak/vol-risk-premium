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
