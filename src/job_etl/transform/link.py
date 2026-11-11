import pandas as pd
from urllib.parse import urlsplit, urlunsplit

def normalize_link(url: str) -> str:
    parts = urlsplit(url.strip())
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))

def transform_links(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["link_description"] = out["link_description"].map(normalize_link)
    return out
