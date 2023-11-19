"""VVM access module."""
from datetime import datetime
import json

import aiohttp


class VVMAccessApi:
    """VVM access API."""

    @staticmethod
    async def fetch_data(url, params):
        """Make an async HTTP request with given url and parameters."""
        async with aiohttp.ClientSession() as session, session.get(
            url, params=params
        ) as response:
            if response.status == 200:
                resp_text = await response.text()
                dec = resp_text
                return json.loads(dec)
            return None

    @staticmethod
    async def get_stop_list(keyword):
        """Obtain list of stops based on the passed keyword."""
        base_url = "https://mobile.defas-fgi.de/vvmapp/XML_STOPFINDER_REQUEST"
        params = {
            "name_sf": keyword,
            "regionID_sf": "1",
            "type_sf": "any",
            "outputFormat": "json",
        }

        data = await VVMAccessApi.fetch_data(base_url, params)
        result = []
        if data:
            points = data["stopFinder"]["points"]
            for p in points:
                if p["type"] == "any" and p["anyType"] == "stop":
                    i = {}
                    i["name"] = p["name"]
                    i["id"] = p["stateless"]
                    result.append(i)
        return result


class VVMStopMonitor:
    """VVM stop monitoring class."""

    stop_id: str

    def __init__(self, stop_id):
        """Contstruct VVMStopMonitor instance."""
        self.stop_id = stop_id

    @staticmethod
    async def get_departure_monitor_request(stop_id):
        """Make a low-level request to retrieve realtime departures for a given stop."""
        base_url = "https://mobile.defas-fgi.de/vvmapp/XML_DM_REQUEST"
        params = {
            "useRealtime": 1,
            "mode": "direct",
            "name_dm": stop_id,
            "type_dm": "stop",
            "useAllStops": "1",
            "mergeDep": "1",
            "maxTimeLoop": "2",
            "outputFormat": "json",
        }

        return await VVMAccessApi.fetch_data(base_url, params)

    @staticmethod
    async def is_stop_id_valid(stop_id):
        """Check if given stop Id is valid."""
        data = await VVMStopMonitor.get_departure_monitor_request(stop_id)
        err_code = None
        err_msg = None
        if data:
            if data["departureList"]:
                stop_name = None
                if (
                    data["dm"]
                    and data["dm"]["points"]
                    and data["dm"]["points"]["point"]
                ):
                    stop_name = data["dm"]["points"]["point"]["name"]
                return (True, stop_name)
            if data["dm"]:
                dm = data["dm"]
                if dm["message"]:
                    for m in dm["message"]:
                        if m["name"] == "code":
                            err_code = int(m["value"])
                        elif m["name"] == "error":
                            err_msg = m["value"]
                    return (False, err_code, err_msg)
        return (False, err_code, err_msg)

    async def get_stop_departures(self, timespan=30):
        """Retrieve the current departures for a stop of the current instance."""
        data = await self.get_departure_monitor_request(self.stop_id)
        result = []
        if data:
            deps = data["departureList"]
            for d in deps:
                countdown = int(d["countdown"])
                if countdown < timespan:
                    i = {}
                    i["left"] = countdown
                    i["delay"] = int(d["servingLine"]["delay"])
                    i["type"] = d["servingLine"]["name"]
                    i["num"] = d["servingLine"]["number"]
                    i["to"] = d["servingLine"]["direction"]
                    i["from"] = d["servingLine"]["directionFrom"]
                    result.append(i)
        return result


class VVMStopMonitorHA:
    """Class to hold the summary information for a given stop ID."""

    api: VVMStopMonitor
    timespan: int
    direction: str
    departures: list[dict]
    last_updated: datetime
    nearest_summary: str
    nearest_left_minutes: int
    nearest_delay_minutes: int

    def __init__(self, stop_id, timespan=30, direction=""):
        """Construct VVMStopMonitorHA instance."""
        self.api = VVMStopMonitor(stop_id)
        self.timespan = timespan
        self.direction = direction

    async def async_update(self):
        """Update departures async."""
        self.departures = await self.api.get_stop_departures(self.timespan)
        self.last_updated = datetime.now()
        closest = self.departures[0]
        self.nearest_summary = "({:d} min) {} {} ({})".format(
            closest["left"], closest["type"], closest["num"], closest["to"]
        )
        self.nearest_left_minutes = closest["left"]
        self.nearest_delay_minutes = closest["delay"]

    @property
    def stop_id(self):
        """Access stop id as a property."""
        return self.api.stop_id
