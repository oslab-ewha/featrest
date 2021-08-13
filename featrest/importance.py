from flask import (request, abort, jsonify)

from featuretools.mkfeat.error import Error
from analyzer import Analyzer


_analyzers = []


def _reg_analyzer(analyzer):
    for tid, name in enumerate(_analyzers, start=1):
        if _analyzers[tid - 1] is None:
            _analyzers[tid - 1] = analyzer
            return tid
    _analyzers.append(analyzer)
    return len(_analyzers)


def _find_analyzer(tid) -> Analyzer:
    if tid > 0 and len(_analyzers) < tid:
        return None
    return _analyzers[tid - 1]


def _remove_analyzer(tid):
    if 0 < tid <= len(_analyzers):
        _analyzers[tid - 1] = None


def start_task():
    json_in = request.json
    if json_in is None:
        abort(400)
    if 'data' not in json_in:
        abort(400)
    json_data = json_in['data']
    if 'uri' not in json_data or 'columns' not in json_data:
        abort(400)

    path_data = json_data['uri']
    columns_data = json_data['columns']

    path_label = None
    columns_label = None
    if 'label' in json_in:
        json_label = json_in['label']
        if 'uri' not in json_label or 'columns' not in json_label:
            abort(400)
        path_label = json_label['uri']
        columns_label = json_label['columns']

    analyzer = Analyzer(path_data, columns_data, path_label, columns_label)
    err = analyzer.start()
    if err == Error.OK:
        tid = _reg_analyzer(analyzer)
        return {"tid": tid}

    if err == Error.ERR_DATA_NOT_FOUND or err == Error.ERR_LABEL_NOT_FOUND:
        abort(401)
    abort(500)


def status_task(tid):
    analyzer = _find_analyzer(tid)
    if analyzer is None:
        abort(501)
    return {"progress": analyzer.get_progress()}


def get_importance(tid):
    analyzer = _find_analyzer(tid)
    if analyzer is None:
        abort(501)

    importance = analyzer.get_importance()
    if isinstance(importance, list):
        return jsonify(importance)

    if importance == Error.ERR_ONGOING:
        abort(503)
    elif importance == Error.ERR_STOPPED:
        abort(502)
    abort(500)


def stop_task(tid):
    analyzer = _find_analyzer(tid)
    if analyzer is None:
        abort(501)
    err = analyzer.stop()
    if err == Error.OK:
        return ""
    if err == Error.ERR_STOPPED:
        abort(502)
    elif err == Error.ERR_ONGOING:
        abort(503)
    abort(500)


def remove_task(tid):
    analyzer = _find_analyzer(tid)
    if analyzer is None:
        abort(501)
    err = analyzer.cleanup()
    if err == Error.OK:
        _remove_analyzer(tid)
        return ""
    if err == Error.ERR_ONGOING:
        abort(503)
    abort(500)
