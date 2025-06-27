import json


def validate_dataframe(method):
    def wrapper(self, *args, **kwargs):
        df = kwargs.get('df')
        if df is not None:
            required_columns = ['measurement_id',
                                'sample_id',
                                'instrument_id',
                                'measurement_date',
                                'sample_name',
                                'internal_code',
                                'collected_by',
                                'comments',
                                'data',
                                'metadata_id',
                                'date_added']

            # Check column existence
            missing_columns = [col for col in required_columns
                               if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns:{missing_columns}")  # noqa E51
            # Validate data parsing
            try:
                # Attempt to parse first row's data
                json.loads(df.iloc[0].data)
            except (json.JSONDecodeError, TypeError):
                raise ValueError("Invalid JSON in data column")

        return method(self, *args, **kwargs)
    return wrapper
