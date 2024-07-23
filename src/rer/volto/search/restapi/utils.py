from plone import api
from  import _
from .interfaces import IRERVoltoSearchCustomFilters
from .interfaces import IRERVoltoSearchSettings
from zope.component import ComponentLookupError
from zope.component import getMultiAdapter
from zope.globalrequest import getRequest
from zope.i18n import translate

import json
import logging


logger = logging.getLogger(__name__)


def get_value_from_registry(field):
    try:
        return api.portal.get_registry_record(field, interface=IRERVoltoSearchSettings)
    except KeyError:
        return None


def get_types_groups():
    request = getRequest()
    all_label = translate(
        _("all_types_label", default="All content types"), context=request
    )
    res = {
        "order": [all_label],
        "values": {all_label: {"count": 0, "types": []}},
    }
    values = get_value_from_registry(field="types_grouping")
    if not values:
        return res
    values = json.loads(values)
    portal = api.portal.get()
    for value in values:
        label = _extract_label(value.get("label", ""))
        res["order"].append(label)
        res["values"][label] = {"types": value.get("types", []), "count": 0}
        advanced_filters = value.get("advanced_filters", "")
        icon = value.get("icon", "")
        if icon:
            res["values"][label]["icon"] = icon
        if advanced_filters:
            try:
                adapter = getMultiAdapter(
                    (portal, request),
                    IRERVoltoSearchCustomFilters,
                    name=advanced_filters,
                )
                res["values"][label]["advanced_filters"] = adapter()
            except ComponentLookupError:
                continue
    return res


def get_indexes_mapping():
    res = {"order": [], "values": {}}
    values = get_value_from_registry(field="available_indexes")
    if not values:
        return res
    values = json.loads(values)
    pc = api.portal.get_tool(name="portal_catalog")
    for value in values:
        label = _extract_label(value.get("label", ""))
        index = value.get("index", "")
        res["order"].append(index)
        res["values"][index] = {
            "label": label,
            "values": {},
            "type": pc.Indexes[index].__class__.__name__,
        }
    return res


def _extract_label(value):
    string_value = ""
    if len(value) == 1:
        string_value = value[0]
    else:
        current_lang = api.portal.get_current_language()
        string_value = ""
        for option in value:
            lang, label = option.split("|")
            if lang and lang == current_lang:
                string_value = label
                break
    return string_value
