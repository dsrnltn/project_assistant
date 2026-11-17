def search_equipment(query: str, equipment_df, limit: int = 10):
    """
    Поиск по любому вхождению подстроки без учёта регистра.
    'виб' -> 'Электровибратор М3/65'
    """
    if not query or not query.strip():
        return []
    q = query.strip().lower()
    df = equipment_df
    mask = df["название"].str.lower().str.contains(q, regex=False)
    return df[mask].head(limit).to_dict("records")