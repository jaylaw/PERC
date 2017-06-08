from perc import db
from perc.models import Location, Reading
import pandas as pd
import pytz
import datetime


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

        local = pytz.timezone("America/Anchorage")

        naive_start = datetime.datetime.strptime(self.start_date + " 00:00:00",
                                                 "%Y-%m-%d %H:%M:%S")
        naive_end = datetime.datetime.strptime(self.end_date + " 23:59:59",
                                               "%Y-%m-%d %H:%M:%S")

        local_start_dt = local.localize(naive_start, is_dst=None)
        local_end_dt = local.localize(naive_end, is_dst=None)

        utc_start_dt = local_start_dt.astimezone(pytz.utc)
        utc_end_dt = local_end_dt.astimezone(pytz.utc)

        start = utc_start_dt.strftime("%Y-%m-%d %H:%M:%S")
        end = utc_end_dt.strftime("%Y-%m-%d %H:%M:%S")

        report_query = Reading.query.filter_by(location_guid=location_guid). \
            filter(Reading.time_stamp.between(start,
                                              end)).statement

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
        total_hours = (pd.to_datetime(self.end_date) - pd.to_datetime(
            self.start_date)) + datetime.timedelta(hours=24)

        return total_hours / pd.Timedelta('1 hour')

    def get_first_point(self):
        first_point = self.df.time_stamp.min().tz_localize('utc')
        first_point = first_point.tz_convert('America/Anchorage')
        first_point = first_point.to_pydatetime()
        first_point = datetime.datetime.strftime(first_point,
                                                 "%Y-%m-%d %H:%M:%S")
        return first_point

    def get_last_point(self):
        last_point = self.df.time_stamp.max().tz_localize('utc')
        last_point = last_point.tz_convert('America/Anchorage')
        last_point = last_point.to_pydatetime()
        last_point = datetime.datetime.strftime(last_point,
                                                "%Y-%m-%d %H:%M:%S")
        return last_point

    def temp_details(self):
        temp_df = self.df[self.df['reading_type'] == 0]

        temp_df = temp_df.set_index('time_stamp')
        temp_df['duration'] = temp_df.index.to_series().diff().dt.seconds.div(
            60, fill_value=0)

        return temp_df

    def humidity_details(self):
        humidity_df = self.df[self.df['reading_type'] == 1]

        humidity_df = humidity_df.set_index('time_stamp')
        humidity_df[
            'duration'] = humidity_df.index.to_series().diff().dt.seconds.div(
            60, fill_value=0)

        return humidity_df

    def combined_details(self):
        td = self.temp_data.drop(
            ['reading_guid', 'reading_type', 'log_session_guid',
             'sensor_guid', 'location_guid', 'channel', 'max_alarm',
             'min_alarm', 'compromised',
             'duration'], axis=1)
        td.columns = ['TempReading', 'TempAlarmMax', 'TempAlarmMin']

        td.TempAlarmMax = float(self.temperature) + float(
            self.temperature_tolerance)
        td.TempAlarmMin = float(self.temperature) - float(
            self.temperature_tolerance)

        hd = self.humidity_data.drop(
            ['reading_guid', 'reading_type', 'log_session_guid',
             'sensor_guid', 'location_guid', 'channel', 'max_alarm',
             'min_alarm', 'compromised',
             'duration'], axis=1)
        hd.columns = ['HumidReading', 'HumidAlarmMax', 'HumidAlarmMin']

        hd.HumidAlarmMax = float(self.humidity) + float(
            self.humidity_tolerance)
        hd.HumidAlarmMin = float(self.humidity) - float(
            self.humidity_tolerance)

        combined_readings = pd.concat([hd, td], axis=1)
        combined_readings[
            'TempInRange'] = combined_readings.TempReading.between(
            combined_readings.TempAlarmMin, combined_readings.TempAlarmMax)
        combined_readings[
            'HumidityInRange'] = combined_readings.HumidReading.between(
            combined_readings.HumidAlarmMin, combined_readings.HumidAlarmMax)
        combined_readings[
            'duration'] = combined_readings.index.to_series().diff().dt.seconds.div(
            60,
            fill_value=0)

        return combined_readings

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

    def get_hours_overlap(self):
        readings = self.combined_data[(
        (self.combined_data['TempInRange'] == False) & (
        self.combined_data['HumidityInRange'] == False))]
        return readings.duration.sum(axis=0) / 60

    def total_hours_out(self):
        t_hi = self.temp_hours_high()
        t_lo = self.temp_hours_low()
        r_hi = self.humidity_hours_high()
        r_lo = self.humidity_hours_low()
        overlap = self.get_hours_overlap()
        total = (t_hi + t_lo) + (r_hi + r_lo) - overlap + self.hours_no_data()
        return total

    def hours_no_data(self):
        gap_time = pd.to_timedelta(self.get_large_gaps().duration.sum(axis=0), unit='m')
        first_point = pd.to_datetime(self.get_first_point())
        start = pd.to_datetime(self.start_date)
        start_gap = first_point - start
        end = pd.to_datetime(self.end_date) + pd.Timedelta(hours=24)
        last_point = pd.to_datetime(self.get_last_point())
        end_gap = end - last_point

        return (start_gap + end_gap + gap_time) / pd.Timedelta('1 hour')

    def get_large_gaps(self):
        return self.combined_data[self.combined_data.duration > 15]

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
        summary.loc[
            summary.LOCATION == self.get_location_name(), 'SPECIFICATION'] = self.get_specification()
        summary.loc[
            summary.LOCATION == self.get_location_name(), 'START_DATE'] = self.start_date
        summary.loc[
            summary.LOCATION == self.get_location_name(), 'END_DATE'] = self.end_date
        summary.loc[
            summary.LOCATION == self.get_location_name(), 'FIRST_POINT_RECORDED'] = self.get_first_point()
        summary.loc[
            summary.LOCATION == self.get_location_name(), 'LAST_POINT_RECORDED'] = self.get_last_point()
        summary.loc[
            summary.LOCATION == self.get_location_name(), 'TOTAL_HOURS_EVALUATED'] = self.get_total_hours_evaluated()
        summary.loc[
            summary.LOCATION == self.get_location_name(), 'TOTAL_HOURS_RECORDED'] = self.get_total_hours_evaluated() - self.hours_no_data()
        summary.loc[
            summary.LOCATION == self.get_location_name(), 'TOTAL_HOURS_OUT'] = self.total_hours_out()
        summary.loc[
            summary.LOCATION == self.get_location_name(), 'PERCENT_OUT'] = (self.total_hours_out() / self.get_total_hours_evaluated()) * 100
        summary.loc[
            summary.LOCATION == self.get_location_name(), 'HOURS_TEMP_HIGH'] = self.temp_hours_high()
        summary.loc[
            summary.LOCATION == self.get_location_name(), 'HOURS_TEMP_LOW'] = self.temp_hours_low()
        summary.loc[
            summary.LOCATION == self.get_location_name(), 'HOURS_RH_HIGH'] = self.humidity_hours_high()
        summary.loc[
            summary.LOCATION == self.get_location_name(), 'HOURS_RH_LOW'] = self.humidity_hours_low()
        summary.loc[
            summary.LOCATION == self.get_location_name(), 'HOURS_OVERLAP'] = self.get_hours_overlap()
        summary.loc[
            summary.LOCATION == self.get_location_name(), 'HOURS_NO_DATA'] = self.hours_no_data()
        summary.loc[
            summary.LOCATION == self.get_location_name(), 'INT_GREATER_THAN_15'] = len(
            self.get_large_gaps())
        summary.loc[
            summary.LOCATION == self.get_location_name(), 'HRS_DOWN_FOR_MAINT'] = 'TBA'
        summary.loc[
            summary.LOCATION == self.get_location_name(), 'DUPE_RECORDS'] = 'TBA'

        report = summary.to_dict(orient='list')

        return report
