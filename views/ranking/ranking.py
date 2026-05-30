import pandas as pd
import numpy as np
from scipy.interpolate import UnivariateSpline
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from typing import List, Optional
from utils.plot_helpers import insert_nans_at_time_gaps

class TurbineRanker:
    def __init__(self, df: pd.DataFrame, id_col: str = 'turbine_id', date_col: str = 'timestamp'):
        self.df = df
        self.id_col = id_col
        self.date_col = date_col
        if self.id_col not in self.df.columns:
            raise ValueError(f"ID column '{self.id_col}' not found in DataFrame.")
        if self.date_col not in self.df.columns:
            raise ValueError(f"Date column '{self.date_col}' not found in DataFrame.")
        # self.df[self.date_col] = pd.to_datetime(self.df[self.date_col])
        self.df.loc[:, self.date_col] = pd.to_datetime(self.df[self.date_col])
    
    def rank_by_kpis(self, kpi_cols: List[str], ascending: Optional[List[bool]] = None, method: str = 'average', season: Optional[str] = None) -> pd.DataFrame:
        df = self._filter_by_season(season) if season else self.df
        
        if not all(col in df.columns for col in kpi_cols):
            missing = [col for col in kpi_cols if col not in df.columns]
            raise ValueError(f"Missing KPI columns: {missing}")
        
        if ascending is None:
            ascending = [False] * len(kpi_cols)
        
        result_df = df.groupby(self.id_col)[kpi_cols].mean().reset_index()
        
        if len(result_df) == 0:
            return pd.DataFrame(columns=[self.id_col] + kpi_cols + ['CompositeScore', 'Rank'])
        
        score = pd.Series(0.0, index=result_df.index)
        for i, col in enumerate(kpi_cols):
            vals = result_df[col].astype(float)
            val_range = vals.max() - vals.min()
            if val_range > 0:
                norm = (vals - vals.min()) / val_range
                score += norm if ascending[i] else (1 - norm)
        
        result_df['CompositeScore'] = score
        result_df['Rank'] = score.rank(ascending=False, method=method).astype(int)
        return result_df.sort_values('Rank').reset_index(drop=True)

    
    def _filter_by_season(self, season: str) -> pd.DataFrame:
        df = self.df
        df['month'] = df[self.date_col].dt.month
        season_months = {
            'winter': [12, 1, 2],
            'spring': [3, 4, 5],
            'summer': [6, 7, 8],
            'fall': [9, 10, 11]
        }
        if season.lower() not in season_months:
            raise ValueError(f"Invalid season. Must be one of {list(season_months.keys())}")
        return df[df['month'].isin(season_months[season.lower()])]

    def get_seasonal_performance(self, turbine_id: str, kpi_cols: List[str]) -> pd.DataFrame:
        seasons = ['winter', 'spring', 'summer', 'fall']
        seasonal_data = []
        for season in seasons:
            season_df = self._filter_by_season(season)
            turbine_data = season_df[season_df[self.id_col] == turbine_id]
            metrics = {kpi: turbine_data[kpi].mean() for kpi in kpi_cols}
            metrics['Season'] = season
            seasonal_data.append(metrics)
        return pd.DataFrame(seasonal_data)
    
    def get_reactive_power_data(self, power_col: str) -> pd.DataFrame:
        df = self.df.copy()
        df['reactive_power'] = df[power_col].where(df[power_col] < 0, 0)
        df['active_power'] = df[power_col].where(df[power_col] >= 0, 0)
        return df

    def plot_bar_graph(self, data: pd.DataFrame, turbines: List[str], kpis: List[str], ax):
        turbine_data = data[data[self.id_col].isin(turbines)]
        if turbine_data.empty:
            ax.text(0.5, 0.5, "No data to plot", ha='center', va='center')
            return
        means = turbine_data.groupby(self.id_col)[kpis].mean()
        if means.empty:
            ax.text(0.5, 0.5, "No data to plot", ha='center', va='center')
            return
        means.plot(kind='bar', ax=ax, color=plt.cm.Paired(np.arange(len(means))))
        ax.set_title("Average KPIs by Turbine")
        ax.set_xlabel("Turbine ID")
        # Add KPI label inside graph
        kpi_text = ", ".join([str(k) for k in means.columns])
        ax.text(0.02, 0.98, kpi_text, transform=ax.transAxes,
            fontsize=10, fontweight='bold', verticalalignment='top',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='white', alpha=0.85))
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45)

    def plot_trend_line(self, data: pd.DataFrame, turbines: List[str], kpis: List[str], ax):
        turbine_data = data[data[self.id_col].isin(turbines)]
        if turbine_data.empty:
            ax.text(0.5, 0.5, "No data to plot", ha='center', va='center')
            return
        for turbine in turbines:
            turbine_df = turbine_data[turbine_data[self.id_col] == turbine]
            # Insert NaNs at time gaps to break line connections
            turbine_df = insert_nans_at_time_gaps(turbine_df, self.date_col, max_gap_hours=24)
            for kpi in kpis:
                ax.plot(turbine_df[self.date_col], turbine_df[kpi], label=f"{turbine} - {kpi}")

        ax.set_title("KPI Trends Over Time")
        ax.set_xlabel("Timestamp")
        # Add KPI label inside graph
        kpi_text = ", ".join(kpis)
        ax.text(0.02, 0.98, kpi_text, transform=ax.transAxes,
                fontsize=10, fontweight='bold', verticalalignment='top',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='white', alpha=0.85))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m-%Y'))
        ax.tick_params(axis='x', rotation=45)
        ax.legend()
        ax.grid(True)

    # def plot_spline_trend_line(self, data: pd.DataFrame, turbines: List[str], kpis: List[str], ax, percentage: bool = False):
    #     turbine_data = data[data[self.id_col].isin(turbines)]
    #     if turbine_data.empty:
    #         ax.text(0.5, 0.5, "No data to plot", ha='center', va='center')
    #         return
    #     for turbine in turbines:
    #         turbine_df = turbine_data[turbine_data[self.id_col] == turbine].sort_values(self.date_col)
    #         # Insert NaNs at time gaps to break line connections
    #         turbine_df = insert_nans_at_time_gaps(turbine_df, self.date_col, max_gap_hours=24)
    #         for kpi in kpis:
    #             x = (turbine_df[self.date_col] - turbine_df[self.date_col].min()).dt.total_seconds()
    #             y = turbine_df[kpi].dropna()
    #             if len(x) > 3 and len(y) > 3:
    #                 spl = UnivariateSpline(x, y, s=len(y)*100)  # Increased smoothing factor
    #                 xs = np.linspace(x.min(), x.max(), 100)
    #                 ys = spl(xs)
    #                 ax.plot(turbine_df[self.date_col].min() + pd.to_timedelta(xs, unit='s'), ys, label=f"{turbine} - {kpi} (spline)")
    #                 if percentage:
    #                     percentage_change = (ys[-1] - ys[0]) / ys[0] * 100 if ys[0] != 0 else 0
    #                     ax.text(0.95, 0.95 - 0.05 * (turbines.index(turbine) + len(kpis)), 
    #                             f"{turbine} - {kpi}: {percentage_change:.2f}%", 
    #                             transform=ax.transAxes, ha='right', va='top')
       
    #     ax.set_title("Smoothed KPI Trends" + (" with Percentage Change" if percentage else ""))
    #     ax.set_xlabel("Timestamp")
    #     ax.set_ylabel("")  # Remove Y-axis label
    #     # Add KPI label inside graph
    #     kpi_text = ", ".join(kpis)
    #     ax.text(0.02, 0.98, kpi_text, transform=ax.transAxes,
    #             fontsize=10, fontweight='bold', verticalalignment='top',
    #             bbox=dict(boxstyle='round,pad=0.4', facecolor='white', alpha=0.85))

    #     ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m-%Y'))
    #     ax.tick_params(axis='x', rotation=45)
    #     ax.legend()
    #     ax.grid(True)

    def plot_spline_trend_line(self, data: pd.DataFrame, turbines: List[str], kpis: List[str], ax, percentage: bool = False):
        turbine_data = data[data[self.id_col].isin(turbines)]
        if turbine_data.empty:
            ax.text(0.5, 0.5, "No data to plot", ha='center', va='center')
            return
        for turbine in turbines:
            turbine_df = turbine_data[turbine_data[self.id_col] == turbine].sort_values(self.date_col)
            # Insert NaNs at time gaps BEFORE processing
            turbine_df = insert_nans_at_time_gaps(turbine_df, self.date_col, max_gap_hours=24)
            
            for kpi in kpis:
                # Split by NaN gaps to plot each segment separately
                turbine_df['segment'] = turbine_df[kpi].isna().cumsum()
                
                for segment_id, segment_df in turbine_df.groupby('segment'):
                    segment_df = segment_df[segment_df[kpi].notna()].copy()
                    
                    if len(segment_df) < 4:
                        continue
                    
                    x = (segment_df[self.date_col] - segment_df[self.date_col].min()).dt.total_seconds()
                    y = segment_df[kpi]
                    
                    spl = UnivariateSpline(x, y, s=len(y)*100)
                    xs = np.linspace(x.min(), x.max(), 100)
                    ys = spl(xs)
                    
                    # Only show label for first segment
                    label = f"{turbine} - {kpi} (spline)" if segment_id == 0 else ""
                    ax.plot(segment_df[self.date_col].min() + pd.to_timedelta(xs, unit='s'), ys, label=label)
                    
                    if percentage and segment_id == 0:
                        percentage_change = (ys[-1] - ys[0]) / ys[0] * 100 if ys[0] != 0 else 0
                        ax.text(0.95, 0.95 - 0.05 * (turbines.index(turbine) + len(kpis)), 
                                f"{turbine} - {kpi}: {percentage_change:.2f}%", 
                                transform=ax.transAxes, ha='right', va='top')
       
        ax.set_title("Smoothed KPI Trends" + (" with Percentage Change" if percentage else ""))
        ax.set_xlabel("Timestamp")
        ax.set_ylabel("")
        kpi_text = ", ".join(kpis)
        ax.text(0.02, 0.98, kpi_text, transform=ax.transAxes,
                fontsize=10, fontweight='bold', verticalalignment='top',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='white', alpha=0.85))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m-%Y'))
        ax.tick_params(axis='x', rotation=45)
        ax.legend()
        ax.grid(True)

    
    def compare_spline_percentages(self, data: pd.DataFrame, turbines: List[str], kpis: List[str]) -> dict:
        comparison = {}
        for turbine in turbines:
            turbine_df = data[data[self.id_col] == turbine].sort_values(self.date_col)
            for kpi in kpis:
                x = (turbine_df[self.date_col] - turbine_df[self.date_col].min()).dt.total_seconds()
                y = turbine_df[kpi].dropna()
                if len(x) > 3 and len(y) > 3:
                    spl = UnivariateSpline(x, y, s=len(y)*100)  # Increased smoothing factor
                    xs = np.linspace(x.min(), x.max(), 100)
                    ys = spl(xs)
                    percentage_change = (ys[-1] - ys[0]) / ys[0] * 100 if ys[0] != 0 else 0
                    comparison[(turbine, kpi)] = percentage_change
        return comparison
    
    def filter_by_time_interval(self, interval_type: str, interval_value: int = None) -> pd.DataFrame:
        df = self.df.copy()
        df[self.date_col] = pd.to_datetime(df[self.date_col])
        
        if interval_type.lower() == 'hourly':
            df['time_group'] = df[self.date_col].dt.floor('H')
            if interval_value is not None:
                df = df[df[self.date_col].dt.hour == interval_value]
            group_cols = [self.id_col, 'time_group']
        elif interval_type.lower() == 'daily':
            df['time_group'] = df[self.date_col].dt.date
            group_cols = [self.id_col, 'time_group']
        elif interval_type.lower() == 'weekly':
            df['time_group'] = df[self.date_col].dt.to_period('W').dt.start_time
            group_cols = [self.id_col, 'time_group']
        elif interval_type.lower() == 'monthly':
            df['time_group'] = df[self.date_col].dt.to_period('M').dt.start_time
            group_cols = [self.id_col, 'time_group']
        else:
            return df
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if self.date_col in numeric_cols:
            numeric_cols.remove(self.date_col)
        
        agg_dict = {col: 'mean' for col in numeric_cols}
        agg_dict[self.date_col] = 'first'
        
        grouped = df.groupby(group_cols).agg(agg_dict).reset_index()
        grouped = grouped.drop('time_group', axis=1)
        
        return grouped

    def filter_by_time_duration(self, duration_seconds: int) -> pd.DataFrame:
        df = self.df.copy()
        df[self.date_col] = pd.to_datetime(df[self.date_col])
        
        filtered_data = []
        for turbine_id in df[self.id_col].unique():
            turbine_data = df[df[self.id_col] == turbine_id].sort_values(self.date_col)
            
            start_time = turbine_data[self.date_col].min()
            end_time = turbine_data[self.date_col].max()
            
            current_time = start_time
            while current_time < end_time:
                window_end = current_time + pd.Timedelta(seconds=duration_seconds)
                window_data = turbine_data[
                    (turbine_data[self.date_col] >= current_time) & 
                    (turbine_data[self.date_col] < window_end)
                ]
                
                if not window_data.empty:
                    avg_data = window_data.select_dtypes(include=[np.number]).mean()
                    avg_data[self.id_col] = turbine_id
                    avg_data[self.date_col] = current_time
                    avg_data['window_end'] = window_end
                    filtered_data.append(avg_data)
                
                current_time = window_end
        
        return pd.DataFrame(filtered_data)
    
    def calculate_efficiency_metrics(self, power_col: str, wind_speed_col: str) -> pd.DataFrame:
        df = self.df.copy()
        
        df = df[(df[power_col].notna()) & (df[wind_speed_col].notna())]
        df = df[df[wind_speed_col] > 0]
        
        df['active_power'] = df[power_col].where(df[power_col] >= 0, 0)
        df['reactive_power'] = df[power_col].where(df[power_col] < 0, 0).abs()
        
        air_density = 1.225
        rotor_area = 5000
        df['theoretical_power'] = 0.5 * air_density * (df[wind_speed_col] ** 3) * rotor_area / 1000
        
        df['power_coefficient'] = df['active_power'] / df['theoretical_power']
        df['power_coefficient'] = df['power_coefficient'].clip(0, 0.59)
        
        rated_power = df['active_power'].quantile(0.95)
        if rated_power > 0:
            df['capacity_factor'] = (df['active_power'] / rated_power).clip(0, 1) * 100
        else:
            df['capacity_factor'] = 0
        
        total_power = df['active_power'] + df['reactive_power']
        df['power_quality'] = np.where(total_power > 0, (df['active_power'] / total_power) * 100, 100)
        
        return df
    
    def detect_anomalies(self, kpi_cols: List[str], method: str = 'iqr') -> pd.DataFrame:
        df = self.df.copy()
        
        for col in kpi_cols:
            if method == 'iqr':
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                df[f'{col}_anomaly'] = (df[col] < lower_bound) | (df[col] > upper_bound)
            
            elif method == 'zscore':
                z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
                df[f'{col}_anomaly'] = z_scores > 3
        
        return df

    def get_performance_statistics(self, kpi_cols: List[str]) -> pd.DataFrame:
        # Use groupby instead of loop
        agg_dict = {}
        for col in kpi_cols:
            agg_dict[col] = ['mean', 'std', 'min', 'max', 'median', 'skew', lambda x: x.kurtosis()]
        
        stats = self.df.groupby(self.id_col)[kpi_cols].agg(agg_dict)
        stats.columns = ['_'.join(col).strip() for col in stats.columns.values]
        return stats.reset_index()

    
    def rank_by_power_generation(self, power_col: str, method: str = 'sum', time_period: str = 'total', iec_standard: bool = True) -> pd.DataFrame:
        df = self.df[self.df[power_col] > 0].copy() if iec_standard else self.df.copy()
        df[power_col] = pd.to_numeric(df[power_col], errors='coerce')
        
        df['active_power'] = df[power_col].where(df[power_col] >= 0, 0)
        df['reactive_power'] = df[power_col].where(df[power_col] < 0, 0).abs()
            
        # Vectorized groupby aggregation
        generation_stats = df.groupby(self.id_col).agg({
            'active_power': ['sum', 'mean', 'max', 'std', 'count'],
            'reactive_power': 'sum',
            self.date_col: ['min', 'max']
        }).reset_index()
        
        generation_stats.columns = [self.id_col, 'total_generation', 'avg_power', 'max_power', 
                                    'power_std', 'operating_hours', 'total_reactive_power', 
                                    'start_date', 'end_date']
        
        # Vectorized calculations
        generation_stats['period_hours'] = ((pd.to_datetime(generation_stats['end_date']) - 
                                            pd.to_datetime(generation_stats['start_date'])).dt.total_seconds() / 3600).clip(lower=1)
        generation_stats['capacity_factor'] = (generation_stats['avg_power'] / generation_stats['max_power'] * 100).fillna(0)
        generation_stats['availability_factor'] = (generation_stats['operating_hours'] / generation_stats['period_hours'] * 100).clip(upper=100)
        generation_stats['power_quality_factor'] = ((generation_stats['total_generation'] / 
                                                    (generation_stats['total_generation'] + generation_stats['total_reactive_power']) * 100)
                                                   .fillna(100))
        
        max_gen = generation_stats['total_generation'].max()
        generation_stats['iec_performance_index'] = (
            0.3 * (generation_stats['total_generation'] / max_gen if max_gen > 0 else 0) +
            0.25 * (generation_stats['capacity_factor'] / 100) +
            0.2 * (generation_stats['availability_factor'] / 100) +
            0.15 * (generation_stats['power_quality_factor'] / 100) +
            0.1 * (1 - generation_stats['power_std'] / generation_stats['avg_power']).clip(0, 1)
        ) * 100
        
        generation_stats['rank'] = generation_stats['iec_performance_index'].rank(ascending=False, method='min').astype(int)
        return generation_stats.sort_values('rank').reset_index(drop=True)


    
    def get_iec_power_curve(self, power_col: str, wind_speed_col: str, bin_width: float = 0.5) -> pd.DataFrame:
        df = self.df.copy()
        df = df[(df[power_col] > 0) & (df[wind_speed_col] > 0)]
        
        if len(df) == 0:
            return pd.DataFrame()
        
        min_ws = df[wind_speed_col].min()
        max_ws = df[wind_speed_col].max()
        bins = np.arange(min_ws, max_ws + bin_width, bin_width)
        
        df['wind_speed_bin'] = pd.cut(df[wind_speed_col], bins=bins, include_lowest=True)
        
        power_curve_data = []
        for turbine_id in df[self.id_col].unique():
            turbine_data = df[df[self.id_col] == turbine_id]
            
            for bin_interval in turbine_data['wind_speed_bin'].dropna().unique():
                bin_data = turbine_data[turbine_data['wind_speed_bin'] == bin_interval]
                
                if len(bin_data) > 0:
                    power_curve_data.append({
                        'turbine_id': turbine_id,
                        'wind_speed_bin': bin_interval,
                        'wind_speed_center': bin_interval.mid,
                        'mean_power': bin_data[power_col].mean(),
                        'std_power': bin_data[power_col].std(),
                        'data_count': len(bin_data)
                    })
        
        return pd.DataFrame(power_curve_data)

       
    def calculate_annual_energy_production(self, power_col: str, wind_speed_col: str) -> pd.DataFrame:
        df = self.df[(self.df[power_col] > 0) & (self.df[wind_speed_col] > 0)]
        
        if len(df) == 0:
            return pd.DataFrame()
        
        # Vectorized groupby
        aep_df = df.groupby(self.id_col).agg({
            power_col: ['sum', 'max'],
            wind_speed_col: ['mean', 'std'],
            self.date_col: ['min', 'max']
        }).reset_index()
        
        aep_df.columns = ['turbine_id', 'measured_energy', 'max_power', 
                          'mean_wind_speed', 'wind_speed_std', 'start_date', 'end_date']
        
        # Vectorized calculations
        aep_df['measurement_period_hours'] = ((pd.to_datetime(aep_df['end_date']) - 
                                              pd.to_datetime(aep_df['start_date'])).dt.total_seconds() / 3600).clip(lower=1)
        aep_df['annual_energy_production'] = (aep_df['measured_energy'] / aep_df['measurement_period_hours']) * 8760
        aep_df['capacity_factor'] = ((aep_df['annual_energy_production'] / (aep_df['max_power'] * 8760)) * 100).fillna(0)
        aep_df['wind_speed_std'] = aep_df['wind_speed_std'].fillna(0)
        aep_df['aep_rank'] = aep_df['annual_energy_production'].rank(ascending=False, method='min').astype(int)
        
        return aep_df.sort_values('aep_rank')
    
    def plot_comparative_power_curve(self, data: pd.DataFrame, turbines: List[str],
                                      power_col: str, wind_speed_col: str, ax,
                                      enable_iec_binning: bool = True):
        """
        Plot comparative power curves using calculate_binned_curve
        (which now matches plot_binned_power_curve logic exactly)
        """
        from views.visualization_components.power_curve_logic import calculate_binned_curve

        colors = plt.cm.tab10(np.linspace(0, 1, len(turbines)))

        for i, turbine in enumerate(turbines):
            turbine_df = data[data[self.id_col] == turbine].copy()

            # Use enhanced calculate_binned_curve with explicit column names
            bin_stats = calculate_binned_curve(
                turbine_df, 
                enable_iec_binning=enable_iec_binning,
                wind_speed_col=wind_speed_col,
                power_col=power_col
            )

            if not bin_stats.empty:
                ax.plot(bin_stats['wind_speed'], bin_stats['power_mean'],
                        'o-', color=colors[i], linewidth=2, markersize=4,
                        label=str(turbine), alpha=0.85)

        ax.set_title("Comparative Power Curve Analysis", fontweight='bold', fontsize=12)
        ax.set_xlabel("Wind Speed (m/s)", fontweight='bold')
        ax.set_ylabel("Power (kW)", fontweight='bold')
        if ax.get_legend_handles_labels()[0]:  # Check if there are any labels
            ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)