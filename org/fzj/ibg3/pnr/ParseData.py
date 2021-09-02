from datetime import datetime, date
from json import dumps, loads
from enum import Enum
import matplotlib.pyplot as plt
import ciso8601

raw_data = []


def as_datavalue(dct):
    if 'feature' in dct and 'dt' in dct and 'variable' in dct and 'value' in dct and 'processing_queue' in dct:

        # processing_queue_dct = dct['processing_queue']

        parsed_processing_queue = []

        for item in dct['processing_queue']:
            if 'processingproperties' in item and 'processingname' in item:
                parsed_processing_queue.append(ProcessingEntry(processingname=item['processingname'],
                                                               processingproperties=item['processingproperties']))
            elif 'filterproperties' in item and 'filtername' in item:
                parsed_processing_queue.append(
                    FilterEntry(filtername=item['filtername'], filterproperties=item['filterproperties']))

        return DataValue(dt=dct['dt'], variable=dct['variable'], value=dct['value'], feature=dct['feature'],
                         processing_queue=parsed_processing_queue)

    elif 'dt' in dct:
        dct['dt'] = datetime.fromisoformat(dct('dt'))

    return dct


def default(obj):
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    else:
        return obj.__dict__


class FlagValues(Enum):
    OK = 0
    BAD = 1
    SUSPICIOUS = 2


class SubFlagValue(Enum):
    OK = 0


class ProcessingValue(Enum):
    CREATED = 0
    EDITED = 1


class FilterEntry(object):
    """Class which represents one filter in the filteringqueue.
    """

    def __init__(self, filtername, filterproperties):
        """
        Constructs a new filter for the filteringqueue
        :param filtername: represents the name of the filter
        :param filterproperties: contains an array of properties associated with this filter e.g. flag or subflag
        """
        self.filterproperties = filterproperties
        self.filtername = filtername


class ProcessingEntry(object):
    """Class which represents a Step in the processingqueue.
    """

    def __init__(self, processingname, processingproperties=None):
        """
        Constructs a new step in the processingqueue
        :param processingname: represents the name
        :param processingproperties: contains an array of properties, associated with the step e.g. processingvalue
        """
        if processingproperties is None:
            processingproperties = []
        self.processingproperties = processingproperties
        self.processingname = processingname


class DataValue(object):

    def __init__(self, dt, variable, value, feature, processing_queue=None):

        if processing_queue is None:
            processing_queue = []

        self.processing_queue = processing_queue

        if isinstance(dt, datetime):
            self.dt = dt
        elif dt is None:
            raise ValueError("Datetime is None")
        else:
            self.dt = datetime.fromisoformat(dt)

        if isinstance(value, str):
            try:
                self.value = float(value)
            except ValueError:
                self.value = value
        else:
            self.value = value

        self.variable = variable
        self.feature = feature


def parse_data(s):
    data_values = []

    firstline = True
    header = None
    for line in s.splitlines():
        if line.startswith("#"):
            if firstline:
                line = line[1:]
                header = line.split(",")
                firstline = False

            continue

        splitline = line.split(",")
        time = None
        feature = None
        for i in range(0, len(splitline)):

            if header[i].lower() == 'time':
                #time = datetime.strptime(splitline[i], '%Y-%m-%dT%H:%M:%S.%f%z')
                time = ciso8601.parse_datetime(splitline[i])
            elif header[i].lower() == 'feature':
                feature = splitline[i]
            else:
                x = splitline[i]

                if x.endswith("\n"):
                    x = x[:-1]

                if x.lower() == 'nodata':
                    continue

                data_values.append(DataValue(time, header[i], splitline[i], feature))

    return header, dumps(data_values, default=default)


def parse_data_stat(arr, save=None):
    x = []
    y = []
    for dv in arr:
        for data in arr[dv]:

            if data.variable == 'SurfaceWaterRunoff in [L*s-1]_new':
                x.append(data.dt)
                y.append(data.value)

    plt.plot(x, y)
    # plt.gcf().autofmt_xdate()
    plt.show()
    fig = plt.figure()
    if save is not None:
        fig.savefig(save)


def date_map_to_clisos_output_format(arr):

    time_feature_map = {}
    variables = []
    features = []

    for timestamp in arr:
        if timestamp not in time_feature_map:
            time_feature_map[timestamp] = {}
        for data in arr[timestamp]:

            if data.variable not in variables:
                variables.append(data.variable)
            if data.feature not in features:
                features.append(data.feature)

            if data.feature not in time_feature_map[timestamp]:
                time_feature_map[timestamp][data.feature] = []

            time_feature_map[timestamp][data.feature].append(data)

    ret = '#Time,feature,' + ','.join(variables)

    for time in time_feature_map:
        for feature in time_feature_map[time]:
            ret_append = time.strftime('%Y-%m-%dT%H:%M:%S.%f%z') + ',' + feature
            variable_map = {}
            for data in time_feature_map[time][feature]:
                variable_map[data.variable] = data.value

            for possible_variable in variables:
                if possible_variable in variable_map:
                    ret_append += ',' + str(variable_map[possible_variable])
                else:
                    ret_append += ',' + 'nodata'
        ret += '\n' + ret_append

    return ret

def json_to_datemap(str):
    in_data = parse_data_from_json(str)

    data_grouped_by_date = dict()

    for datavalue in in_data:
        time = datavalue.dt
        if time in data_grouped_by_date:
            tmp_data_array = data_grouped_by_date[time]
            tmp_data_array.append(datavalue)
        else:
            data_grouped_by_date[time] = [datavalue]

    return  data_grouped_by_date


def parse_data_from_json(str):
    return loads(str, object_hook=as_datavalue)


def dump_data_to_json(data):
    return dumps(data, default=default)

def get_flag_for_variable(data, datavalue):
    flag = None
    if datavalue.variable.endswith('_flag'):
        return None

    for dv in data:
        if dv.variable.endswith('_flag'):
            continue
        if datavalue.variable + '_flag' == dv.variable:
            flag = dv

    if flag is None:
        flag = DataValue(dt=None, value=None, feature=datavalue.feature,
                  variable=datavalue.variable + '_flag', processing_queue=None)

    return flag