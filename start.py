import json

import matplotlib.pyplot as plt
from org.fzj.ibg3.algo.loaddataandresample import execute
from pynodered.server import app

from clisos_mod.clisos import CliSos
from org.fzj.ibg3.algo.runoff import weighted_average
from org.fzj.ibg3.pnr.ParseData import *
from pynodered import node_red, NodeProperty

app.config['MAX_CONTENT_LENGTH'] = 5000 * 1024 * 1024
app.config['DEBUG'] = True


@node_red(title="Clisos", category="TSM Input", description="This Node takes a Clisos-Configuration and outputs three "
                                                            "values 1. orig_data: Data coming from SOS 2. payload: "
                                                            "parsed data 3. header: header of data",
          properties=dict(
              config=NodeProperty("Configuration", type="text", required=True, input_type="textarea")
          )
          )
def tsm_clisos(node, msg):
    # config_string = "".join(map(chr, list(map(int, msg["payload"]["data"]))))
    config_string = node.config.value
    print(config_string)
    resultModel = "om:Observation"
    srs = None
    spatialFilterSrs = None
    host = None
    offering = None
    port = None
    procedure = None
    path = None
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

    # configFilename = "/home/t.korf/PycharmProjects/clisos/data/local/data.cfg"
    configFilename = node.config.value
    # configString = None
    verbose = "2"
    method = "POST"

    sos = CliSos(resultModel, srs, spatialFilterSrs, configFilename, host, offering, port, procedure, path,
                 xcoordinate, ycoordinate, verbose, proxyHostname, proxyPort, responseFormat, csvSeparator,
                 matlibplot, matlibplot_fmt, preDefObservedProperties, preDefProcs, timeInterval, bbox,
                 noMessageAboutNoData, printNoQualityInfo, printOm, last, onlyCount, bearerToken, method,
                 configString=config_string)

    s = sos.getObservation()

    header, out = parse_data(s)
    msg['orig_data'] = s
    msg['payload'] = out
    msg['header'] = header

    return msg


@node_red(category="TSMFilter",
          properties=dict(
              suspicious_min=NodeProperty("Min (suspicious)", type="num", required=False),
              suspicious_max=NodeProperty("Max (suspicious)", type="num", required=False),
              bad_min=NodeProperty("Min (bad)", type="num", required=False),
              bad_max=NodeProperty("Max (bad)", type="num", required=False),
              #                          no_import_min=NodeProperty("Min (No import)", type="num", required=False),
              #                          no_import_max=NodeProperty("Max (No import)", type="num", required=False),
              skip_bad=NodeProperty("Skip bad", required=False, input_type="checkbox"),
              skip_suspicious=NodeProperty("Skip suspicious", type="num", required=False, input_type="checkbox")
          ))
def min_max(node, msg):
    return msg
    suspicious_min_value = float(node.suspicious_min.value)
    suspicious_max_value = float(node.suspicious_max.value)
    bad_min_value = float(node.bad_min.value)
    bad_max_value = float(node.bad_max.value)
    no_import_min_value = float(node.no_import_min.value)
    no_import_max_value = float(node.no_import_max.value)

    data = parse_data_from_json(msg['payload'])
    to_append = []
    for dv in data:
        if dv.variable.endswith('_flag'):
            continue

        for dv_flag in data:
            pass
        if not (suspicious_min_value < dv.value < suspicious_max_value):
            pass
        elif not (bad_min_value < dv.value < bad_max_value):
            pass
        elif not (no_import_min_value < dv.value < no_import_max_value):
            print('found!')
            to_append.append(DataValue(dt=dv.dt, value=dv.value, feature=dv.feature,
                                       variable=dv.variable + '_flag', processing_queue=dv.processing_queue))
    data.extend(to_append)

    msg['payload'] = dump_data_to_json(data)

    return msg


@node_red(category="TSMFilter",
          properties=dict(min=NodeProperty("Min", type="num", required=True),
                          max=NodeProperty("Max", type="num", required=True)
                          )
          )
def peak(node, msg):
    min = node.min.value
    max = node.max.value
    print(msg["payload"])

    return msg


@node_red(category="TSMOutput", properties=dict(variable=NodeProperty("Variables", required=True),
                                                save=NodeProperty("Savepath", required=False)
    , parameter=NodeProperty("Graph Parameter", required=True)))
def picture(node, msg):
    variable_to_print = node.variable.value
    save_path = node.save.value

    arr = json_to_datemap(msg["payload"])

    x = []
    y = []
    for dv in arr:
        for data in arr[dv]:

            if data.variable == variable_to_print:
                x.append(data.dt)
                y.append(data.value)

    plt.plot(x, y)
    # plt.gcf().autofmt_xdate()
    plt.show()
    fig = plt.figure()
    if save_path is not None:
        fig.savefig(save_path)

    return msg


@node_red(category="TSMOutput")
def clisos_format(node, msg):
    message = msg['payload']

    arr = json_to_datemap(message)

    msg['payload'] = date_map_to_clisos_output_format(arr)

    return msg


@node_red(category="TSMOutput",
          properties=dict(bad_min=NodeProperty("Min (bad)", type="num", required=False),
                          bad_max=NodeProperty("Max (bad)", type="num", required=False),
                          suspicious_min=NodeProperty("Min (suspicious)", type="num", required=False),
                          suspicious_max=NodeProperty("Max (suspicious)", type="num", required=False),
                          no_import_min=NodeProperty("Min (No import)", type="num", required=False),
                          no_import_max=NodeProperty("Max (No import)", type="num", required=False),
                          skip_bad=NodeProperty("Skip bad", required=False, input_type="checkbox"),
                          skip_suspicious=NodeProperty("Skip suspicious", type="num", required=False,
                                                       input_type="checkbox")

                          )
          )
def sos(node, msg):
    print(msg["payload"])

    return msg


@node_red(category="TSMFilter")
def variables(node, msg):
    variables = []

    for data in parse_data_from_json(msg["payload"]):
        if data.variable not in variables:
            variables.append(data.variable)

    msg['payload'] = json.dumps(variables)

    return msg


@node_red(category="TSMFilter",
          properties=dict(json=NodeProperty("text", type="text", required=True)

                          )
          )
def mean(node, msg):
    print(msg["payload"])

    return msg


@node_red(category="TSMFilter")
def runoff(node, msg):
    # print(msg["payload"])

    data_grouped_by_date = json_to_datemap(msg["payload"])

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

    header, out = parse_data(date_map_to_clisos_output_format(data_grouped_by_date))

    msg['payload'] = out
    return msg


@node_red(title="Inject Text", category="TSM Input",
          properties=dict(
              topic=NodeProperty("Topic", type="text", required=True),
              text=NodeProperty("Text", type="text", required=True, input_type="textarea")

          )
          )
def inject_text(node, msg):
    msg[node.topic.value] = node.text.value

    return msg


@node_red(category="TSMFilter")
def lsar(node, msg):
    data_grouped_by_date = json_to_datemap(msg["payload"])

    msg['payload'] = execute(msg, data_grouped_by_date)

    return msg


@node_red(category="TSMFilter")
def show_msg(node, msg):
    print("######### SHOW MSG ##########")
    print(msg.keys())

    return msg

@node_red(category="TSMOutput")
def send_mail(node, msg):
    print("######### SHOW MSG ##########")
    print(msg.keys())

    return msg

@node_red(category="TSMOutput", title="SOS T (WIP)")
def sos_t(node, msg):
    print("######### SHOW MSG ##########")
    print(msg.keys())

    return msg