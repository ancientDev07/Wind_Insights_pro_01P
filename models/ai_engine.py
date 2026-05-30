import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression

class WindAIEngine:

    def detect_anomalies(self, df: pd.DataFrame, contamination=0.05) -> pd.DataFrame:
        numeric = df.select_dtypes(include=[np.number]).dropna(axis=1)
        if numeric.empty or len(numeric) < 10:
            return pd.DataFrame()
        scaled = StandardScaler().fit_transform(numeric)
        labels = IsolationForest(contamination=contamination, random_state=42).fit_predict(scaled)
        result = df.copy()
        result["_anomaly"] = labels
        return result[result["_anomaly"] == -1].drop(columns=["_anomaly"])

    def performance_score(self, df: pd.DataFrame, power_col: str, ws_col: str) -> float:
        """0-100 score: actual vs theoretical power ratio"""
        try:
            pw = pd.to_numeric(df[power_col], errors="coerce").dropna()
            ws = pd.to_numeric(df[ws_col], errors="coerce").dropna()
            theoretical = 0.5 * 1.225 * (ws ** 3) * 0.4
            ratio = (pw.sum() / theoretical.sum()) * 100
            return min(round(ratio, 2), 100.0)
        except Exception:
            return 0.0

    def availability(self, df: pd.DataFrame, power_col: str) -> float:
        pw = pd.to_numeric(df[power_col], errors="coerce")
        return round((pw > 0).sum() / len(pw) * 100, 2) if len(pw) > 0 else 0.0

    def plf(self, df: pd.DataFrame, power_col: str) -> float:
        pw = pd.to_numeric(df[power_col], errors="coerce").dropna()
        if pw.empty or pw.max() == 0:
            return 0.0
        return round((pw.sum() / (pw.max() * len(df))) * 100, 2)

    def wind_power_trend(self, df: pd.DataFrame, ws_col: str, power_col: str) -> dict:
        """Linear regression of power vs wind speed"""
        try:
            ws = pd.to_numeric(df[ws_col], errors="coerce")
            pw = pd.to_numeric(df[power_col], errors="coerce")
            mask = ws.notna() & pw.notna()
            X = ws[mask].values.reshape(-1, 1)
            y = pw[mask].values
            model = LinearRegression().fit(X, y)
            return {"slope": round(model.coef_[0], 3), "r2": round(model.score(X, y), 3)}
        except Exception:
            return {"slope": 0, "r2": 0}

    def generate_insights(self, df: pd.DataFrame, column_cache: dict, turbine_name: str = "") -> list:
        insights = []
        ws_col = column_cache.get("wind_speed")
        pw_col = column_cache.get("power")
        rs_col = column_cache.get("rotor_speed")
        ts_col = column_cache.get("timestamp")

        insights.append(f"Turbine: {turbine_name} | Records: {len(df)}")

        if ws_col and ws_col in df.columns:
            ws = pd.to_numeric(df[ws_col], errors="coerce").dropna()
            insights.append(f"Wind Speed — Avg: {ws.mean():.2f} m/s | Max: {ws.max():.2f} m/s | Std: {ws.std():.2f}")
            low = (ws < 3).sum()
            if low > len(ws) * 0.1:
                insights.append(f"⚠ {low} records below cut-in speed (3 m/s)")

        if pw_col and pw_col in df.columns:
            pw = pd.to_numeric(df[pw_col], errors="coerce").dropna()
            neg = (pw < 0).sum()
            if neg > 0:
                insights.append(f"⚠ {neg} negative power readings — possible sensor fault")
            insights.append(f"PLF: {self.plf(df, pw_col)}% | Availability: {self.availability(df, pw_col)}%")
            insights.append(f"Max Power: {pw.max():.2f} kW | Mean Power: {pw.mean():.2f} kW")

        if ws_col and pw_col and ws_col in df.columns and pw_col in df.columns:
            score = self.performance_score(df, pw_col, ws_col)
            insights.append(f"Performance Score: {score:.1f}/100")
            trend = self.wind_power_trend(df, ws_col, pw_col)
            insights.append(f"Wind-Power Regression — Slope: {trend['slope']}, R²: {trend['r2']}")

        if rs_col and rs_col in df.columns:
            rs = pd.to_numeric(df[rs_col], errors="coerce").dropna()
            if rs.std() > rs.mean() * 0.5:
                insights.append("⚠ High rotor speed variability — inspect mechanical components")

        anomalies = self.detect_anomalies(df)
        pct = round(len(anomalies) / len(df) * 100, 1) if len(df) > 0 else 0
        insights.append(f"Anomalies Detected: {len(anomalies)} ({pct}% of records)")

        return insights