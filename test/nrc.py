from clisos_mod.clisos import CliSos
from org.fzj.ibg3.algo.runoff import weighted_average
from org.fzj.ibg3.pnr.ParseData import parse_data, parse_data_from_json, date_map_to_clisos_output_format

resultModel = "om:Observation"
srs = None
spatialFilterSrs = None

offering = None

procedure = None

xcoordinate = None
ycoordinate = None
# debug level
proxyHostname = None
proxyPort = None
matlibplot = False
# change
# author: juergen sorg
# date: 2013-10-11
responseFormat = None
csvSeparator = ","
matlibplot_fmt = None
preDefObservedProperties = []
preDefProcs = []
timeInterval = []
bbox = []
noMessageAboutNoData = False
printNoQualityInfo = False
printOm = False
last = None
onlyCount = False
bearerToken = None

configFilename = "/home/t.korf/PycharmProjects/clisos/data/local/data.cfg"
verbose = "2"
method = "POST"

sos = CliSos(resultModel, srs, spatialFilterSrs, configFilename, "ibg3wrada.ibg.kfa-juelich.de", offering, 8080,
             procedure, "/eifelrur_public/sos",
             xcoordinate, ycoordinate, verbose, proxyHostname, proxyPort, responseFormat, csvSeparator,
             matlibplot, matlibplot_fmt, preDefObservedProperties, preDefProcs, timeInterval, bbox,
             noMessageAboutNoData, printNoQualityInfo, printOm, last, onlyCount, bearerToken, method)
s = sos.getObservation()
print(s.splitlines()[0])
print(s)
header, out = parse_data(s)

in_data = parse_data_from_json(out)

data_grouped_by_date = dict()

for datavalue in in_data:
    time = datavalue.dt
    if time in data_grouped_by_date:
        tmp_data_array = data_grouped_by_date[time]
        tmp_data_array.append(datavalue)
    else:
        data_grouped_by_date[time] = [datavalue]

for key in data_grouped_by_date:
    data = data_grouped_by_date[key]
    dateTime = key
    feature = None
    variable = None
    venturi = None
    thomson = None
    result_to_expect = None
    for item in data:
        if 'flag' in item.variable.lower():
            continue
        else:
            if 'venturi' in item.variable.lower():
                venturi = item
            elif 'thomson' in item.variable.lower():
                thomson = item
            elif 'runoff' in item.variable.lower():
                result_to_expect = item
                variable = item.variable + "_new"
                feature = item.feature

    result = weighted_average(thomson_dv=thomson, venturi_dv=venturi, dateTime=dateTime,
                              variable=variable, feature=feature)

    data.append(result)


    '''
    data_as_str = dump_data_to_json(result)
    json_data = parse_data_from_json(data_as_str)
'''


    same = result.value == result_to_expect.value
    if same:
         pass
    else:
        #stderr.write(('%s new: %s old: %s \n' % (dateTime, result.value, result_to_expect.value)))
        pass

#parse_data_stat(data_grouped_by_date)
date_map_to_clisos_output_format(data_grouped_by_date)