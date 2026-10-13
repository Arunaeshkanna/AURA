from pathlib import Path


class DataTool:
    def summarize_csvs(self, root: Path) -> str:
        try:
            import pandas as pd
        except Exception:
            return "Pandas is not installed, so structured data analysis is unavailable."

        summaries = []
        for path in root.glob("**/*.csv"):
            df = pd.read_csv(path)
            summaries.append(
                f"{path.name}: {len(df)} rows, {len(df.columns)} columns. "
                f"Columns: {', '.join(map(str, df.columns[:10]))}."
            )
        return "\n".join(summaries) or "No CSV files found."
