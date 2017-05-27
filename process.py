from perc import db
from perc.models import Location, Reading
import pandas as pd


class Report:
    def __init__(self, location, temperature, humidity, temperature_tolerance,
                 humidity_tolerance, start_date, end_date):
        self.location = location
        self.temperature = temperature
        self.humidity = humidity
        self.temperature_tolerance = temperature_tolerance
        self.humidity_tolerance = humidity_tolerance
        self.start_date = start_date
        self.end_date = end_date
        self.df = self.get_details()

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

        summary.loc[summary.LOCATION == self.get_location_name(),'SPECIFICATION'] = self.get_specification()

        summary.loc[summary.LOCATION == self.get_location_name(),'START_DATE'] = pd.to_datetime(self.start_date)

        summary.loc[summary.LOCATION == self.get_location_name(),'END_DATE'] = pd.to_datetime(self.end_date)

        summary.loc[summary.LOCATION == self.get_location_name(),'FIRST_POINT_RECORDED'] = self.df.time_stamp.min()

        summary.loc[summary.LOCATION == self.get_location_name(),'LAST_POINT_RECORDED'] = self.df.time_stamp.max()

        summary.loc[summary.LOCATION == self.get_location_name(),'TOTAL_HOURS_EVALUATED'] = (summary.END_DATE - summary.START_DATE).astype('timedelta64[s]') / 3600.0

        summary.loc[summary.LOCATION == self.get_location_name(),'TOTAL_HOURS_RECORDED'] = (summary.LAST_POINT_RECORDED - summary.FIRST_POINT_RECORDED).astype('timedelta64[s]') / 3600.0

        return summary.to_html()
