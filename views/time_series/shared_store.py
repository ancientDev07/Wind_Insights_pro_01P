# shared_store.py
stores: dict = {}
# Key: turbine_key (str)
# Value: { "data": pd.DataFrame, "params": list, "timestamp_col": str }