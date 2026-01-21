from datetime import datetime
import pandas as pd

class AggregationService:
    @staticmethod
    def calculate_window(df: pd.DataFrame, window_minutes: int):
        """
        Receives a DataFrame of events and computes aggregation.
        Expects cols: [ts_event, site_id, zone_id, sensor_type, value]
        """
        if df.empty:
            return pd.DataFrame()

        # Floor timestamp to window
        freq = f'{window_minutes}min'
        df['window_start'] = df['ts_event'].dt.floor(freq)
        
        # GroupBy
        agg = df.groupby(['window_start', 'site_id', 'zone_id', 'sensor_type']).agg(
            avg_value=('value', 'mean'),
            min_value=('value', 'min'),
            max_value=('value', 'max'),
            count_events=('value', 'count')
        ).reset_index()
        
        agg['window_end'] = agg['window_start'] + pd.Timedelta(minutes=window_minutes)
        return agg
