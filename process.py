from perc import db
from perc.models import Location, Reading
import pandas as pd


class Report:
    def __init__(self, location, temperature: float, humidity: float,
                 temperature_tolerance: float,
                 humidity_tolerance: float, start_date, end_date):
        self.location = location
        self.temperature = temperature
        self.humidity = humidity
        self.temperature_tolerance = temperature_tolerance
        self.humidity_tolerance = humidity_tolerance
        self.start_date = start_date
        self.end_date = end_date
        self.df = self.get_details()
        self.temp_data = self.temp_details()
        self.humidity_data = self.humidity_details()
        self.combined_data = self.combined_details()

    @staticmethod
    def celsius_to_fahr(temp_celsius):
        """Convert Fahrenheit to Celsius

        Return Celsius conversion of input"""
        temp_fahr = (temp_celsius * 1.8) + 32
        return temp_fahr

    def get_location_name(self):
        names = [loc.location_name for loc in Location.query.all()]
        location_name = names[int(self.location)]
        return location_name

    def get_details(self):
        guids = [loc.location_guid for loc in Location.query.all()]
        location_guid = guids[int(self.location)]
        report_query = Reading.query.filter_by(location_guid=location_guid). \
            filter(Reading.time_stamp.between(self.start_date,
                                              self.end_date)).statement

        df = pd.read_sql(report_query, db.engine)

        df.loc[df['reading_type'] == 0, 'reading'] = df.reading.apply(
            self.celsius_to_fahr)

        return df

    def get_specification(self):
        specification = "Temp {} ± {}° F RH {}% ± {}%".format(self.temperature,
                                                              self.temperature_tolerance,
                                                              self.humidity,
                                                              self.humidity_tolerance)
        return specification

    def get_total_hours_evaluated(self):
        total_hours = pd.to_datetime(self.end_date) - pd.to_datetime(
            self.start_date)
        return total_hours

    def temp_details(self):
        temp_df = self.df[self.df['reading_type'] == 0]

        temp_df = temp_df.set_index('time_stamp')
        temp_df['duration'] = temp_df.index.to_series().diff().dt.seconds.div(
            60, fill_value=0)

        return temp_df

    def humidity_details(self):
        humidity_df = self.df[self.df['reading_type'] == 1]

        humidity_df = humidity_df.set_index('time_stamp')
        humidity_df['duration'] = humidity_df.index.to_series().diff().dt.seconds.div(
            60, fill_value=0)

        return humidity_df

    def combined_details(self):
        td = self.temp_data.drop(
            ['reading_guid', 'reading_type', 'log_session_guid',
             'sensor_guid', 'location_guid', 'channel', 'max_alarm',
             'min_alarm', 'compromised',
             'duration'], axis=1)
        td.columns = ['TempReading', 'TempAlarmMax', 'TempAlarmMin']

        td.TempAlarmMax = float(self.temperature) + float(self.temperature_tolerance)
        td.TempAlarmMin = float(self.temperature) - float(self.temperature_tolerance)

        hd = self.humidity_data.drop(
            ['reading_guid', 'reading_type', 'log_session_guid',
             'sensor_guid', 'location_guid', 'channel', 'max_alarm',
             'min_alarm', 'compromised',
             'duration'], axis=1)
        hd.columns = ['HumidReading', 'HumidAlarmMax', 'HumidAlarmMin']

        hd.HumidAlarmMax = float(self.humidity) + float(self.humidity_tolerance)
        hd.HumidAlarmMin = float(self.humidity) - float(self.humidity_tolerance)

        combined_readings = pd.concat([hd, td], axis=1)
        combined_readings['TempInRange'] = combined_readings.TempReading.between(
            combined_readings.TempAlarmMin, combined_readings.TempAlarmMax)
        combined_readings['HumidityInRange'] = combined_readings.HumidReading.between(
            combined_readings.HumidAlarmMin, combined_readings.HumidAlarmMax)
        combined_readings[
            'duration'] = combined_readings.index.to_series().diff().dt.seconds.div(60,
                                                                           fill_value=0)

        return combined_readings.to_html()

    def temp_hours_high(self):
        temp_hi = self.temp_data[
            self.temp_data.reading > (
                float(self.temperature) + float(self.temperature_tolerance))]
        return temp_hi.duration.sum(axis=0) / 60

    def temp_hours_low(self):
        temp_lo = self.temp_data[
            self.temp_data.reading < (
                float(self.temperature) - float(self.temperature_tolerance))]
        return temp_lo.duration.sum(axis=0) / 60


    def humidity_hours_high(self):
        humidity_hi = self.humidity_data[
            self.humidity_data.reading > (
                float(self.humidity) + float(self.humidity_tolerance))]

        return humidity_hi.duration.sum(axis=0) / 60

    def humidity_hours_low(self):
        humidity_lo = self.humidity_data[
            self.humidity_data.reading < (
                float(self.humidity) - float(self.humidity_tolerance))]

        return humidity_lo.duration.sum(axis=0) / 60

    def generate_summary(self):
        summary = pd.DataFrame(index=None,
                               columns=['LOCATION', 'SPECIFICATION',
                                        'START_DATE', 'END_DATE',
                                        'FIRST_POINT_RECORDED',
                                        'LAST_POINT_RECORDED',
                                        'TOTAL_HOURS_EVALUATED',
                                        'TOTAL_HOURS_RECORDED',
                                        'TOTAL_HOURS_OUT',
                                        'PERCENT_OUT', 'HOURS_TEMP_HIGH',
                                        'HOURS_TEMP_LOW', 'HOURS_RH_HIGH',
                                        'HOURS_RH_LOW', 'HOURS_OVERLAP',
                                        'HOURS_NO_DATA', 'INT_GREATER_THAN_15',
                                        'HRS_DOWN_FOR_MAINT', 'DUPE_RECORDS'])

        summary.LOCATION = [self.get_location_name()]
        summary.loc[summary.LOCATION == self.get_location_name(), 'SPECIFICATION'] = self.get_specification()
        summary.loc[summary.LOCATION == self.get_location_name(), 'START_DATE'] = pd.to_datetime(self.start_date)
        summary.loc[summary.LOCATION == self.get_location_name(), 'END_DATE'] = pd.to_datetime(self.end_date)
        summary.loc[summary.LOCATION == self.get_location_name(), 'FIRST_POINT_RECORDED'] = self.df.time_stamp.min()
        summary.loc[summary.LOCATION == self.get_location_name(), 'LAST_POINT_RECORDED'] = self.df.time_stamp.max()
        summary.loc[summary.LOCATION == self.get_location_name(), 'TOTAL_HOURS_EVALUATED'] = (summary.END_DATE - summary.START_DATE).astype('timedelta64[s]') / 3600.0
        summary.loc[summary.LOCATION == self.get_location_name(), 'TOTAL_HOURS_RECORDED'] = (summary.LAST_POINT_RECORDED - summary.FIRST_POINT_RECORDED).astype('timedelta64[s]') / 3600.0
        summary.loc[summary.LOCATION == self.get_location_name(), 'TOTAL_HOURS_OUT'] = 'TBA'
        summary.loc[summary.LOCATION == self.get_location_name(), 'PERCENT_OUT'] = 'TBA'
        summary.loc[summary.LOCATION == self.get_location_name(), 'HOURS_TEMP_HIGH'] = self.temp_hours_high()
        summary.loc[summary.LOCATION == self.get_location_name(), 'HOURS_TEMP_LOW'] = self.temp_hours_low()
        summary.loc[summary.LOCATION == self.get_location_name(), 'HOURS_RH_HIGH'] = self.humidity_hours_high()
        summary.loc[summary.LOCATION == self.get_location_name(), 'HOURS_RH_LOW'] = self.humidity_hours_low()
        summary.loc[summary.LOCATION == self.get_location_name(), 'HOURS_OVERLAP'] = 'TBA'
        summary.loc[summary.LOCATION == self.get_location_name(), 'HOURS_NO_DATA'] = 'TBA'
        summary.loc[summary.LOCATION == self.get_location_name(), 'INT_GREATER_THAN_15'] = 'TBA'
        summary.loc[summary.LOCATION == self.get_location_name(), 'HRS_DOWN_FOR_MAINT'] = 'TBA'
        summary.loc[summary.LOCATION == self.get_location_name(), 'DUPE_RECORDS'] = 'TBA'

        return summary.to_html()
