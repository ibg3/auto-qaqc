import math

# Measurements i,1
from org.fzj.ibg3.pnr.ParseData import DataValue, ProcessingEntry

_nodename = "runoff"


def thomson(dv):
    if dv.value > 0:
        # Measurements i,3
        return 0.0146 * math.pow(dv.value, 2.5)
    return None


# Measurements i,2
def venturi(dv):
    # Measurements i,4
    if dv.value >= 3:
        return -0.000285522198896342 * math.pow(dv.value, 3) + 0.0681799264498377 * math.pow(dv.value, 2) \
               + 1.05293288954037 * dv.value - 1.2607072190857
    elif dv.value > 0:
        return 0.234700999661566 * math.pow(dv.value, 2) + 0.130562339667476 * dv.value

    return None


def determine_weight_thomson(dv):
    if dv is None:
        return

    if 5 < dv.value < 10:
        return -0.2 * dv.value + 2
    else:
        return 0


# 5
def weighted_average(thomson_dv, venturi_dv, dateTime=None, variable=None, feature=None):
    variable_to_use = None
    feature_to_use = None
    dateTime_to_use = None

    if thomson_dv is None and venturi_dv is not None:
        raise ValueError(
            "no data available for timestamp %s and station %s (thomson)" % (venturi_dv.dateTime, venturi_dv.feature))
    if thomson_dv is not None and venturi_dv is None:
        raise ValueError(
            "no data available for timestamp %s and station %s (venturi)" % (thomson_dv.dateTime, thomson_dv.feature))
    if thomson_dv is None and venturi_dv is None and dateTime is not None:
        raise ValueError(
            "no data available for timestamp %s and unknown station (venturi AND thomson missing)" % dateTime)
    if thomson_dv is None and venturi_dv is None and dateTime is None:
        raise ValueError("no data available for unknown timestamp and unknown station (venturi AND thomson missing)")

    if feature is None and \
            (thomson_dv.feature is None or venturi_dv.feature is None or thomson_dv.feature != venturi_dv.feature):
        raise ValueError("cannot determine feature")
    if variable is None and \
            (thomson_dv.variable is None or venturi_dv.variable is None or thomson_dv.variable != venturi_dv.variable):
        raise ValueError("cannot determine variable")
    if dateTime is None and \
            (thomson_dv.dateTime is None or venturi_dv.dateTime is None or thomson_dv.dateTime != venturi_dv.dateTime):
        raise ValueError("cannot determine dateTime")

    if variable is None:
        variable_to_use = thomson_dv.variable
    else:
        variable_to_use = variable

    if feature is None:
        feature_to_use = thomson_dv.feature
    else:
        feature_to_use = feature

    if dateTime is None:
        dateTime_to_use = thomson_dv.dt
    else:
        dateTime_to_use = dateTime

    # 3
    thomson_erg = thomson(thomson_dv)
    # 4
    venturi_erg = venturi(venturi_dv)

    weight_thomson = determine_weight_thomson(thomson_dv)

    result = None

    if thomson_erg is not None and venturi_erg is not None and thomson_dv.value < 10:
        # Measurements i,5
        result = thomson_erg * weight_thomson + venturi_erg * (1 - weight_thomson)

    elif thomson_erg is None or thomson_dv.value >= 10:
        result = venturi_erg

    elif venturi_erg is None and thomson_erg < 10:
        result = thomson_erg

    processingqueue_to_use = [ProcessingEntry(_nodename)]

    return DataValue(dt=dateTime_to_use, value=result, feature=feature_to_use,
                     variable=variable_to_use, processing_queue=processingqueue_to_use)
