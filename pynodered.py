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


@node_red(category="TSMInput",
          properties=dict(port=NodeProperty("Port", value="8443", type="num", required=False),
                          host=NodeProperty("Host", value="ibg3wradar.ibg.kfa-juelich.de", required=False),
                          procedure=NodeProperty("Procedure", required=False),
                          path=NodeProperty("Path", value="/eifelrur_public/sos", required=False),
                          config=NodeProperty("Config", type="text", required=False, input_type="text")
                          )
          )
def tsm_clisos(node, msg):
    config_string = "".join(map(chr, list(map(int, msg["payload"]["data"]))))

    resultModel = "om:Observation"
    srs = None
    spatialFilterSrs = None
    host = node.host.value
    offering = None
    port = node.port.value
    procedure = None
    path = node.path.value
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
    #print(s)

    so = """############## PROCESSINGSTATUS ################
# approved upload = 4
# checked automatically = 6
# derived product = 5
# unevaluated = 1
# upload waiting for approval = 2
# visual inspected = 3
############## QUALIFIER #######################
# baddata_autosampler = 4010
# baddata_backwater = 4043
# baddata_badquality = 4024
# baddata_change sensor MPS = 4028
# baddata_changeflow/positionsensor = 4035
# baddata_controlaffected = 4041
# baddata_data not plausible = 4022
# baddata_data transfer disturbed = 4021
# baddata_deadsignal = 4050
# baddata_frozen = 4023
# baddata_irregular = 4013
# baddata_isolatedspike = 4019
# baddata_liquidapplication = 4040
# baddata_maintenancedisturbance = 4037
# baddata_manual deactivation = 4054
# baddata_max = 4012
# baddata_max preciptiation 12h = 4056
# baddata_max preciptiation 24h = 4057
# baddata_max preciptiation 2d = 4058
# baddata_max preciptiation 5d = 4059
# baddata_max preciptiation 6h = 4055
# baddata_min = 4011
# baddata_missing = 4017
# baddata_noisydata = 4033
# baddata_noprecipitation = 4051
# baddata_outoforder = 4018
# baddata_ppleaking = 4047
# baddata_pumpfailure = 4038
# baddata_removablematter = 4039
# baddata_sealinglip = 4069
# baddata_tankrelease = 4042
# baddata_technicaldisturbance = 4036
# baddata_temperature effects = 4034
# baddata_unplausiblevariation = 4020
# baddata_waterwithdrawal = 4052
# gapfilled_extrapolated = 5016
# gapfilled_interpolated = 5015
# goodquality_linreg time = 25066
# interpolated_linreg DWD station = 15063
# interpolated_linreg other station = 15061
# interpolated_linreg time = 15066
# interpolated_replacedby DWD station = 15064
# interpolated_replacedby other station = 15062
# interpolated_spline time = 15065
# interpolated_unknown = 15014
# modified_data not plausible = 7022
# modified_drift corrected = 7060
# ok_above detection limit = 2068
# ok_autosampler = 2010
# ok_below detection limit = 2067
# ok_goodquality = 2025
# ok_moderatequality = 2026
# ok_ok = 2002
# ok_qualityunknown = 2027
# suspicious_autosampler = 3010
# suspicious_backwater = 3043
# suspicious_change sensor MPS = 3028
# suspicious_changeflow/positionsensor = 3035
# suspicious_check for sensor drift = 3046
# suspicious_frozen = 3023
# suspicious_inconsistent time period = 3048
# suspicious_leaking tank = 3045
# suspicious_maintenancedisturbance = 3037
# suspicious_max = 3012
# suspicious_min = 3011
# suspicious_missing = 3017
# suspicious_nodatachange = 3044
# suspicious_noisydata = 3033
# suspicious_sensor reports malfunction = 3053
# suspicious_technicaldisturbance = 3036
# suspicious_tillage = 3049
# suspicious_unknown = 3014
# suspicious_unplausiblevariation = 3020
# unevaluated_autosampler = 1010
# unevaluated_change sensor MPS = 1028
# unevaluated_unevaluated = 1001
############## QualityFlag SYNTAX ##############
# PROCESSINGSTATUS_QUALIFIER
################################################
#Time,feature,SurfaceWaterLevel_Thomson in [cm],SurfaceWaterLevel_ThomsonQualityFlag in [],SurfaceWaterLevel_Venturi in [cm],SurfaceWaterLevel_VenturiQualityFlag in [],SurfaceWaterRunoff in [L*s-1],SurfaceWaterRunoffQualityFlag in []
2020-01-01T13:50:00.000+01:00,WU_AW_010,12.6363,4_2002,6.2699199999999999,4_2002,7.951003786015943,5_2002
2020-01-01T14:00:00.000+01:00,WU_AW_010,12.6401,4_2002,6.2489800000000004,4_2002,7.9117850579791158,5_2002
2020-01-01T14:10:00.000+01:00,WU_AW_010,12.6442,4_2002,5.9843200000000003,4_2002,7.4208549678287286,5_2002
2020-01-01T14:20:00.000+01:00,WU_AW_010,12.652900000000001,4_2002,6.1725000000000003,4_2002,7.769013152126111,5_2002
2020-01-01T14:30:00.000+01:00,WU_AW_010,12.6454,4_2002,6.0962399999999999,4_2002,7.6273845107664142,5_2002
2020-01-01T14:40:00.000+01:00,WU_AW_010,12.641999999999999,4_2002,6.0743200000000002,4_2002,7.5868105570558724,5_2002
2020-01-01T14:50:00.000+01:00,WU_AW_010,12.6325,4_2002,5.6566099999999997,4_2002,6.8252143932513798,5_2002
2020-01-01T15:00:00.000+01:00,WU_AW_010,12.632,4_2002,5.9125500000000004,4_2002,7.2892466158786879,5_2002
2020-01-01T15:10:00.000+01:00,WU_AW_010,12.6234,4_2002,6.0330300000000001,4_2002,7.5105470838913737,5_2002
2020-01-01T15:20:00.000+01:00,WU_AW_010,12.6205,4_2002,5.9665600000000003,4_2002,7.3882270325208532,5_2002
2020-01-01T15:30:00.000+01:00,WU_AW_010,12.6181,4_2002,5.9885599999999997,4_2002,7.4286504019850517,5_2002
2020-01-01T15:40:00.000+01:00,WU_AW_010,12.6081,4_2002,6.1207599999999998,4_2002,7.6728427585622816,5_2002
2020-01-01T15:50:00.000+01:00,WU_AW_010,12.605700000000001,4_2002,5.8170400000000004,4_2002,7.1151134991465055,5_2002
2020-01-01T16:00:00.000+01:00,WU_AW_010,12.5992,4_2002,6.0278900000000002,4_2002,7.5010684343488476,5_2002
2020-01-01T16:10:00.000+01:00,WU_AW_010,12.584899999999999,4_2002,5.8300799999999997,4_2002,7.1388199999488036,5_2002
2020-01-01T16:20:00.000+01:00,WU_AW_010,12.5777,4_2002,6.1401399999999997,4_2002,7.7088253774236675,5_2002
2020-01-01T16:30:00.000+01:00,WU_AW_010,12.572100000000001,4_2002,6.1165099999999999,4_2002,7.6649581535539335,5_2002
2020-01-01T16:40:00.000+01:00,WU_AW_010,12.568300000000001,4_2002,5.9667000000000003,4_2002,7.3884840791471733,5_2002
2020-01-01T16:50:00.000+01:00,WU_AW_010,12.5474,4_2002,5.77529,4_2002,7.0393572822906068,5_2002
2020-01-01T17:00:00.000+01:00,WU_AW_010,12.5433,4_2002,6.2115299999999998,4_2002,7.8417819866684235,5_2002
2020-01-01T17:10:00.000+01:00,WU_AW_010,12.5304,4_2002,6.0471899999999996,4_2002,7.5366766922980633,5_2002
2020-01-01T17:20:00.000+01:00,WU_AW_010,12.5198,4_2002,5.7812200000000002,4_2002,7.0501039582689122,5_2002
2020-01-01T17:30:00.000+01:00,WU_AW_010,12.5205,4_2002,5.7801400000000003,4_2002,7.0481463909733195,5_2002
2020-01-01T17:40:00.000+01:00,WU_AW_010,12.511799999999999,4_2002,6.0456899999999996,4_2002,7.5339075288489168,5_2002
2020-01-01T17:50:00.000+01:00,WU_AW_010,12.5016,4_2002,5.7125599999999999,4_2002,6.925946902693112,5_2002
2020-01-01T18:00:00.000+01:00,WU_AW_010,12.4854,4_2002,5.9096299999999999,4_2002,7.2839058220827466,5_2002
2020-01-01T18:10:00.000+01:00,WU_AW_010,12.466699999999999,4_2002,5.8033900000000003,4_2002,7.0903210525867832,5_2002
2020-01-01T18:20:00.000+01:00,WU_AW_010,12.463800000000001,4_2002,5.89567,4_2002,7.2583873122005356,5_2002
2020-01-01T18:30:00.000+01:00,WU_AW_010,12.4543,4_2002,5.9633799999999999,4_2002,7.3823890678769652,5_2002
2020-01-01T18:40:00.000+01:00,WU_AW_010,12.4336,4_2002,5.9462000000000002,4_2002,7.3508714350846054,5_2002
2020-01-01T18:50:00.000+01:00,WU_AW_010,12.4352,4_2002,5.6227799999999997,4_2002,6.7644991274769675,5_2002
2020-01-01T19:00:00.000+01:00,WU_AW_010,12.4122,4_2002,5.8850800000000003,4_2002,7.2390454855137731,5_2002
2020-01-01T19:10:00.000+01:00,WU_AW_010,12.406700000000001,4_2002,5.7602099999999998,4_2002,7.0120485021468104,5_2002
2020-01-01T19:20:00.000+01:00,WU_AW_010,12.387,4_2002,5.9411800000000001,4_2002,7.3416690056817187,5_2002
2020-01-01T19:30:00.000+01:00,WU_AW_010,12.374000000000001,4_2002,5.6427899999999998,4_2002,6.8003938903174861,5_2002
2020-01-01T19:40:00.000+01:00,WU_AW_010,12.367599999999999,4_2002,5.8768599999999998,4_2002,7.2240420452579697,5_2002
2020-01-01T19:50:00.000+01:00,WU_AW_010,12.3453,4_2002,5.7747900000000003,4_2002,7.0384513577569452,5_2002
2020-01-01T20:00:00.000+01:00,WU_AW_010,12.3468,4_2002,5.4556699999999996,4_2002,6.4667129914764985,5_2002
2020-01-01T20:10:00.000+01:00,WU_AW_010,12.3246,4_2002,5.8989799999999999,4_2002,7.2644356791937996,5_2002
2020-01-01T20:20:00.000+01:00,WU_AW_010,12.3087,4_2002,5.5517300000000001,4_2002,6.6374567538881042,5_2002
2020-01-01T20:30:00.000+01:00,WU_AW_010,12.3154,4_2002,5.7289500000000002,4_2002,6.9555305460899381,5_2002
2020-01-01T20:40:00.000+01:00,WU_AW_010,12.299300000000001,4_2002,5.5628200000000003,4_2002,6.6572442912698833,5_2002
2020-01-01T20:50:00.000+01:00,WU_AW_010,12.2889,4_2002,5.6452600000000004,4_2002,6.8048281957649346,5_2002
2020-01-01T21:00:00.000+01:00,WU_AW_010,12.279400000000001,4_2002,5.7419900000000004,4_2002,6.9790917845079816,5_2002
2020-01-01T21:10:00.000+01:00,WU_AW_010,12.275399999999999,4_2002,5.7400500000000001,4_2002,6.9755851458743843,5_2002
2020-01-01T21:20:00.000+01:00,WU_AW_010,12.27,4_2002,5.98611,4_2002,7.4241456882800838,5_2002
2020-01-01T21:30:00.000+01:00,WU_AW_010,12.2575,4_2002,5.31928,4_2002,6.2262976413008522,5_2002
2020-01-01T21:40:00.000+01:00,WU_AW_010,12.2483,4_2002,5.6750499999999997,4_2002,6.8583700190055916,5_2002
2020-01-01T21:50:00.000+01:00,WU_AW_010,12.248799999999999,4_2002,5.76959,4_2002,7.0290316168856295,5_2002
2020-01-01T22:00:00.000+01:00,WU_AW_010,12.2315,4_2002,5.4074799999999996,4_2002,6.3814980815879272,5_2002
2020-01-01T22:10:00.000+01:00,WU_AW_010,12.230700000000001,4_2002,5.5666900000000004,4_2002,6.6641530818095438,5_2002
2020-01-01T22:20:00.000+01:00,WU_AW_010,12.2209,4_2002,5.6705500000000004,4_2002,6.850274923180538,5_2002
2020-01-01T22:30:00.000+01:00,WU_AW_010,12.224600000000001,4_2002,5.70594,4_2002,6.914007566335056,5_2002
2020-01-01T22:40:00.000+01:00,WU_AW_010,12.2155,4_2002,5.7510300000000001,4_2002,6.9954382766098719,5_2002
2020-01-01T22:50:00.000+01:00,WU_AW_010,12.1897,4_2002,5.6182699999999999,4_2002,6.7564159101598831,5_2002
2020-01-01T23:00:00.000+01:00,WU_AW_010,12.23,4_2002,5.9002400000000002,4_2002,7.2667384422154866,5_2002
2020-01-01T23:10:00.000+01:00,WU_AW_010,12.2347,4_2002,5.5748100000000003,4_2002,6.6786552189899648,5_2002
2020-01-01T23:20:00.000+01:00,WU_AW_010,12.1851,4_2002,5.7472599999999998,4_2002,6.9886199539739264,5_2002
2020-01-01T23:30:00.000+01:00,WU_AW_010,12.193099999999999,4_2002,5.5350700000000002,4_2002,6.60776016393653,5_2002
2020-01-01T23:40:00.000+01:00,WU_AW_010,12.1723,4_2002,5.4559899999999999,4_2002,6.4672798370557274,5_2002
2020-01-01T23:50:00.000+01:00,WU_AW_010,12.1683,4_2002,5.8065199999999999,4_2002,7.0960039793184153,5_2002
2020-01-02T00:00:00.000+01:00,WU_AW_010,12.1616,4_2002,5.8234000000000004,4_2002,7.1266731875502431,5_2002
2020-01-02T00:10:00.000+01:00,WU_AW_010,12.141299999999999,4_2002,5.5601599999999998,4_2002,6.6524967150344887,5_2002
2020-01-02T00:20:00.000+01:00,WU_AW_010,12.135300000000001,4_2002,5.5864700000000003,4_2002,6.6994943395724595,5_2002
2020-01-02T00:30:00.000+01:00,WU_AW_010,12.1374,4_2002,5.5260699999999998,4_2002,6.5917322383769781,5_2002
2020-01-02T00:40:00.000+01:00,WU_AW_010,12.1472,4_2002,5.76335,4_2002,7.0177324421358529,5_2002
2020-01-02T00:50:00.000+01:00,WU_AW_010,12.1372,4_2002,5.62209,4_2002,6.7632622819782844,5_2002
2020-01-02T01:00:00.000+01:00,WU_AW_010,12.141299999999999,4_2002,5.7202200000000003,4_2002,6.9397688277607061,5_2002
2020-01-02T01:10:00.000+01:00,WU_AW_010,12.137700000000001,4_2002,5.6596099999999998,4_2002,6.830605542154383,5_2002
2020-01-02T01:20:00.000+01:00,WU_AW_010,12.1411,4_2002,5.5180400000000001,4_2002,6.5774404433419216,5_2002
2020-01-02T01:30:00.000+01:00,WU_AW_010,12.129300000000001,4_2002,5.8474000000000004,4_2002,7.1703406936254686,5_2002
2020-01-02T01:40:00.000+01:00,WU_AW_010,12.1379,4_2002,5.7723800000000001,4_2002,7.0340852449709184,5_2002
2020-01-02T01:50:00.000+01:00,WU_AW_010,12.1219,4_2002,5.6975100000000003,4_2002,6.8988118795608129,5_2002
2020-01-02T02:00:00.000+01:00,WU_AW_010,12.1067,4_2002,5.6831199999999997,4_2002,6.8728936471414501,5_2002
2020-01-02T02:10:00.000+01:00,WU_AW_010,12.111599999999999,4_2002,5.84063,4_2002,7.1580154481867835,5_2002
2020-01-02T02:20:00.000+01:00,WU_AW_010,12.1128,4_2002,5.6430899999999999,4_2002,6.8009324286884292,5_2002
2020-01-02T02:30:00.000+01:00,WU_AW_010,12.107900000000001,4_2002,5.6584899999999996,4_2002,6.8285927132093951,5_2002
2020-01-02T02:40:00.000+01:00,WU_AW_010,12.1206,4_2002,5.4856999999999996,4_2002,6.5199645587690389,5_2002
2020-01-02T02:50:00.000+01:00,WU_AW_010,12.080399999999999,4_2002,5.9060600000000001,4_2002,7.2773776153581844,5_2002
2020-01-02T03:00:00.000+01:00,WU_AW_010,12.132999999999999,4_2002,5.7760699999999998,4_2002,7.0407705876948716,5_2002
2020-01-02T03:10:00.000+01:00,WU_AW_010,12.078200000000001,4_2002,5.5542699999999998,4_2002,6.6419874185078855,5_2002
2020-01-02T03:20:00.000+01:00,WU_AW_010,12.0686,4_2002,5.5270900000000003,4_2002,6.5935482202013853,5_2002
2020-01-02T03:30:00.000+01:00,WU_AW_010,12.0959,4_2002,5.4498600000000001,4_2002,6.4564234632975426,5_2002
2020-01-02T03:40:00.000+01:00,WU_AW_010,12.0764,4_2002,5.35107,4_2002,6.282122633087031,5_2002
2020-01-02T03:50:00.000+01:00,WU_AW_010,12.097,4_2002,5.5646800000000001,4_2002,6.6605645581729798,5_2002
2020-01-02T04:00:00.000+01:00,WU_AW_010,12.0785,4_2002,5.5731200000000003,4_2002,6.675636228009231,5_2002
2020-01-02T04:10:00.000+01:00,WU_AW_010,12.0686,4_2002,5.6484399999999999,4_2002,6.8105382777252812,5_2002
2020-01-02T04:20:00.000+01:00,WU_AW_010,12.087899999999999,4_2002,5.5623399999999998,4_2002,6.6563875194254019,5_2002
2020-01-02T04:30:00.000+01:00,WU_AW_010,12.0845,4_2002,5.7150100000000004,4_2002,6.9303669456133852,5_2002
2020-01-02T04:40:00.000+01:00,WU_AW_010,12.0764,4_2002,5.6996700000000002,4_2002,6.9027045790757606,5_2002
2020-01-02T04:50:00.000+01:00,WU_AW_010,12.0944,4_2002,5.6613600000000002,4_2002,6.8337509054654637,5_2002
2020-01-02T05:00:00.000+01:00,WU_AW_010,12.1296,4_2002,5.6789199999999997,4_2002,6.8653338524394139,5_2002
2020-01-02T05:10:00.000+01:00,WU_AW_010,12.090400000000001,4_2002,5.5283800000000003,4_2002,6.595845092158287,5_2002
2020-01-02T05:20:00.000+01:00,WU_AW_010,12.0861,4_2002,5.7070100000000004,4_2002,6.9159369623748157,5_2002
2020-01-02T05:30:00.000+01:00,WU_AW_010,12.097799999999999,4_2002,5.7906899999999997,4_2002,7.0672752401195202,5_2002
2020-01-02T05:40:00.000+01:00,WU_AW_010,12.1435,4_2002,5.7900200000000002,4_2002,7.0660600037005663,5_2002
2020-01-02T05:50:00.000+01:00,WU_AW_010,12.1205,4_2002,5.5786699999999998,4_2002,6.685552024151634,5_2002
2020-01-02T06:00:00.000+01:00,WU_AW_010,12.075699999999999,4_2002,5.6020399999999997,4_2002,6.7273484128189152,5_2002
2020-01-02T06:10:00.000+01:00,WU_AW_010,12.0184,4_2002,5.4175000000000004,4_2002,6.3991922599394835,5_2002
2020-01-02T06:20:00.000+01:00,WU_AW_010,12.117100000000001,4_2002,5.9337900000000001,4_2002,7.3281277891579526,5_2002
2020-01-02T06:30:00.000+01:00,WU_AW_010,12.083500000000001,4_2002,5.73489,4_2002,6.9662605278712517,5_2002
2020-01-02T06:40:00.000+01:00,WU_AW_010,12.067399999999999,4_2002,5.5374299999999996,4_2002,6.6119647430132522,5_2002
2020-01-02T06:50:00.000+01:00,WU_AW_010,12.0886,4_2002,5.7292100000000001,4_2002,6.9560001151536417,5_2002
2020-01-02T07:00:00.000+01:00,WU_AW_010,12.101900000000001,4_2002,5.5207800000000002,4_2002,6.5823161760086384,5_2002
2020-01-02T07:10:00.000+01:00,WU_AW_010,12.1137,4_2002,5.6494499999999999,4_2002,6.8123521252740309,5_2002
2020-01-02T07:20:00.000+01:00,WU_AW_010,12.053900000000001,4_2002,5.6702899999999996,4_2002,6.8498072848995681,5_2002
2020-01-02T07:30:00.000+01:00,WU_AW_010,12.0558,4_2002,5.2185199999999998,4_2002,6.0502075321849471,5_2002
2020-01-02T07:40:00.000+01:00,WU_AW_010,12.068300000000001,4_2002,5.5461499999999999,4_2002,6.6275064353124629,5_2002
2020-01-02T07:50:00.000+01:00,WU_AW_010,12.071999999999999,4_2002,5.6270199999999999,4_2002,6.7721007779215556,5_2002
2020-01-02T08:00:00.000+01:00,WU_AW_010,12.0459,4_2002,5.54643,4_2002,6.6280056403258909,5_2002
2020-01-02T08:10:00.000+01:00,WU_AW_010,12.062799999999999,4_2002,5.6624600000000003,4_2002,6.8357281895172823,5_2002
2020-01-02T08:20:00.000+01:00,WU_AW_010,12.0541,4_2002,5.6272900000000003,4_2002,6.7725849224396368,5_2002
2020-01-02T08:30:00.000+01:00,WU_AW_010,12.061199999999999,4_2002,5.8346,4_2002,7.1470422993168858,5_2002
2020-01-02T08:40:00.000+01:00,WU_AW_010,12.0632,4_2002,5.4992799999999997,4_2002,6.5440832848774084,5_2002
2020-01-02T08:50:00.000+01:00,WU_AW_010,12.098800000000001,4_2002,5.4324300000000001,4_2002,6.4255806070158323,5_2002
2020-01-02T09:00:00.000+01:00,WU_AW_010,12.076499999999999,4_2002,5.7735300000000001,4_2002,7.036168568159062,5_2002
2020-01-02T09:10:00.000+01:00,WU_AW_010,12.0748,4_2002,5.6070599999999997,4_2002,6.7363355325993615,5_2002
2020-01-02T09:20:00.000+01:00,WU_AW_010,12.075100000000001,4_2002,5.3509399999999996,4_2002,6.2818940841359003,5_2002
2020-01-02T09:30:00.000+01:00,WU_AW_010,12.0817,4_2002,5.6155999999999997,4_2002,6.7516317169081583,5_2002
2020-01-02T09:40:00.000+01:00,WU_AW_010,12.0809,4_2002,5.4699299999999997,4_2002,6.491985670930859,5_2002
2020-01-02T09:50:00.000+01:00,WU_AW_010,12.0862,4_2002,5.4689800000000002,4_2002,6.4903012042403763,5_2002
2020-01-02T10:00:00.000+01:00,WU_AW_010,12.0801,4_2002,5.4043599999999996,4_2002,6.3759911222576013,5_2002
2020-01-02T10:10:00.000+01:00,WU_AW_010,12.123699999999999,4_2002,5.80159,4_2002,7.0870534767209419,5_2002
2020-01-02T10:20:00.000+01:00,WU_AW_010,12.1233,4_2002,5.8024699999999996,4_2002,7.0886509070807682,5_2002
2020-01-02T10:30:00.000+01:00,WU_AW_010,12.123100000000001,4_2002,5.6573099999999998,4_2002,6.8264722260283071,5_2002
2020-01-02T10:40:00.000+01:00,WU_AW_010,12.118,4_2002,5.7355999999999998,4_2002,6.9675433665062156,5_2002
2020-01-02T10:50:00.000+01:00,WU_AW_010,12.1265,4_2002,5.6451000000000002,4_2002,6.8045409298944373,5_2002
2020-01-02T11:00:00.000+01:00,WU_AW_010,12.144500000000001,4_2002,5.8210699999999997,4_2002,7.1224376768697288,5_2002
2020-01-02T11:10:00.000+01:00,WU_AW_010,12.142200000000001,4_2002,5.6163400000000001,4_2002,6.7529575825869399,5_2002
2020-01-02T11:20:00.000+01:00,WU_AW_010,12.143700000000001,4_2002,5.6206100000000001,4_2002,6.7606095415113883,5_2002
2020-01-02T11:30:00.000+01:00,WU_AW_010,12.171200000000001,4_2002,5.59192,4_2002,6.709240663544997,5_2002
2020-01-02T11:40:00.000+01:00,WU_AW_010,12.1496,4_2002,5.7328799999999998,4_2002,6.9626291756625287,5_2002
2020-01-02T11:50:00.000+01:00,WU_AW_010,12.1495,4_2002,5.3919899999999998,4_2002,6.3541696180981893,5_2002
2020-01-02T12:00:00.000+01:00,WU_AW_010,12.1539,4_2002,5.5080200000000001,4_2002,6.5596183223908469,5_2002
2020-01-02T12:10:00.000+01:00,WU_AW_010,12.155900000000001,4_2002,5.6465899999999998,4_2002,6.8072162188423428,5_2002
2020-01-02T12:20:00.000+01:00,WU_AW_010,12.173999999999999,4_2002,5.4660399999999996,4_2002,6.4850889492918098,5_2002
2020-01-02T12:30:00.000+01:00,WU_AW_010,12.183199999999999,4_2002,5.6565799999999999,4_2002,6.8251604875193932,5_2002
2020-01-02T12:40:00.000+01:00,WU_AW_010,12.1965,4_2002,5.8820399999999999,4_2002,7.2334957736370695,5_2002
2020-01-02T12:50:00.000+01:00,WU_AW_010,12.1899,4_2002,5.7135199999999999,4_2002,6.9276787473542401,5_2002
2020-01-02T13:00:00.000+01:00,WU_AW_010,12.1958,4_2002,5.7268600000000003,4_2002,6.9517562439981271,5_2002
2020-01-02T13:10:00.000+01:00,WU_AW_010,12.220499999999999,4_2002,5.6126899999999997,4_2002,6.7464185128006884,5_2002
2020-01-02T13:20:00.000+01:00,WU_AW_010,12.2211,4_2002,5.7421199999999999,4_2002,6.9793267824711629,5_2002
2020-01-02T13:30:00.000+01:00,WU_AW_010,12.2294,4_2002,5.5211600000000001,4_2002,6.5829924477381789,5_2002
2020-01-02T13:40:00.000+01:00,WU_AW_010,12.2464,4_2002,5.7404200000000003,4_2002,6.9762539010295255,5_2002
""".strip()
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
                                                ,parameter=NodeProperty("Graph Parameter", required=True)))
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
    #plt.gcf().autofmt_xdate()
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


@node_red(category="TSMFilter")
def lsar(node, msg):
    # print(msg["payload"])

    #calibration = """Country and Station Name,Station_ID,Calibration Time,MOD [cts/hr],P [mb],Temp [°C],RH [%],SM [m3/m3],BD [g/cm3],SOC [%],LW [g/g],Lat,Lon
    #Denmark_Harrild,,29.10.2015 10:30,669.42,1015.33,9.4,73.9,0.378,1.264,54.3,0.0009,56.01332,9.09293
    #"""

    #calibration = """Calibration Time,SM [m3/m3],BD [g/cm3],SOC [%],LW [g/g]
    #02.06.2013 14:00,0.194,1.482,4.5,0.0044
    #29.08.2013 11:00,0.146,1.482,4.5,0.0044
    #19.06.2015 15:00,0.203,1.482,4.5,0.0044
    #16.07.2015 11:00,0.152,1.482,4.5,0.0044
    #23.09.2015 11:00,0.222,1.482,4.5,0.0044
    #"""
    calibration = """Calibration Time,SM [m3/m3],BD [g/cm3],SOC [%],LW [g/g]
    05.09.2015 12:00, 0.2296, 1.26, 0, 0.04"""

    data_grouped_by_date = json_to_datemap(msg["payload"])

    msg['payload'] = execute(msg, data_grouped_by_date, calibration)

    return msg
