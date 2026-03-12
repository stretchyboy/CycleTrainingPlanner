from __future__ import annotations

import argparse
import csv
import dataclasses
import json
import math
import sqlite3
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Dict, Iterable, List, Optional, Tuple

MILES_TO_KM = 1.6
DEFAULT_DELTA = timedelta(days=2)


@dataclass(frozen=True)
class PlanConfig:
    name: str
    current_weekly_mileage: float
    target_distance: float
    current_standard_commute: float
    target_total_time: float
    target_total_climb: float
    target_max_incline_percentage: float
    start_week: int
    target_week: int
    target_year: int
    rest_cycle_weeks: int
    rest_percentage: float
    taper_weeks: int
    plateau_weeks: int
    taper_percentage: float
    target_ride_percentage: float
    target_week_percentage: float
    long_commute: float
    max_long_commutes: int
    commutes_per_week: int
    second_ride_percentage: float
    step_after_rest: bool
    distance_unit: str = "miles"
    algorithm: str = "simple"
    week1_step: bool = False
    second_ride_percentage_of_long: Optional[float] = None
    min_second_ride: float = 0.0
    step_denominator_offset: int = 0
    rest_weeks: Optional[List[int]] = None
    non_commute_weeks: Optional[List[int]] = None
    commutes_per_rest_week: Optional[int] = None
    current_lr_distance: float = 0.0
    target_total_ascent: Optional[float] = None
    ascent_percentage: float = 100.0
    week_start_offset_days: int = -2
    distance_floor_commute_and_long: bool = False


@dataclass(frozen=True)
class PlanWeek:
    index: int
    week_number: int
    week_start: date
    week_end: date
    distance_km: float
    commute_km: float
    main_ride_km: float
    second_ride_km: float
    leftovers_km: float
    duration_hours: float
    climb_m: float


@dataclass(frozen=True)
class WeekActuals:
    distance_km: float
    climb_m: float
    duration_hours: float


PLAN_CONFIGS: Dict[str, PlanConfig] = {
    "nbnw_plan_2023_ascent": PlanConfig(
        name="North By North West",
        current_weekly_mileage=64,
        target_distance=200,
        current_standard_commute=8,
        target_total_time=0,
        target_total_climb=3510,
        target_max_incline_percentage=10,
        start_week=2,
        target_week=22,
        target_year=2023,
        rest_cycle_weeks=4,
        rest_percentage=50,
        taper_weeks=2,
        plateau_weeks=0,
        taper_percentage=75,
        target_ride_percentage=60,
        target_week_percentage=150,
        long_commute=15,
        max_long_commutes=2,
        commutes_per_week=10,
        second_ride_percentage=0,
        step_after_rest=False,
        distance_unit="km",
        algorithm="step_week",
        week1_step=False,
        second_ride_percentage_of_long=75,
        min_second_ride=15,
        step_denominator_offset=-1,
        commutes_per_rest_week=8,
        current_lr_distance=0,
        target_total_ascent=3510,
        ascent_percentage=110,
        week_start_offset_days=-2,
        distance_floor_commute_and_long=True,
    ),
    "nbnw_plan_2024": PlanConfig(
        name="North By North West 24",
        current_weekly_mileage=70,
        target_distance=212,
        current_standard_commute=7,
        target_total_time=12,
        target_total_climb=3510,
        target_max_incline_percentage=10,
        start_week=1,
        target_week=21,
        target_year=2024,
        rest_cycle_weeks=4,
        rest_percentage=50,
        taper_weeks=2,
        plateau_weeks=0,
        taper_percentage=75,
        target_ride_percentage=75,
        target_week_percentage=150,
        long_commute=15,
        max_long_commutes=2,
        commutes_per_week=10,
        second_ride_percentage=0,
        step_after_rest=True,
        distance_unit="km",
        algorithm="step_week",
        week1_step=False,
        second_ride_percentage_of_long=50,
        min_second_ride=10,
        rest_weeks=[4, 8, 11, 14, 18],
        non_commute_weeks=[1, 7, 14, 15],
        commutes_per_rest_week=8,
        current_lr_distance=0,
        target_total_ascent=3510,
        ascent_percentage=110,
        week_start_offset_days=0,
        distance_floor_commute_and_long=True,
    ),
}

# Default weighting by BikeComputer Pro session category (sessions.cat)
# Update with real category values once known.
DEFAULT_CAT_MULTIPLIERS: Dict[int, float] = {
    0: 1.0,
}


def generate_plan(config: PlanConfig) -> List[PlanWeek]:
    distance_factor = MILES_TO_KM if config.distance_unit == "miles" else 1.0
    if config.algorithm == "step_week":
        return generate_step_week_plan(config, distance_factor)
    return generate_simple_plan(config, distance_factor)


def generate_simple_plan(config: PlanConfig, distance_factor: float) -> List[PlanWeek]:
    total_weeks = (config.target_week - config.start_week) + 1
    rest_weeks = round((total_weeks - (config.plateau_weeks + config.taper_weeks)) / config.rest_cycle_weeks)
    if config.step_after_rest:
        steps = (total_weeks - (config.plateau_weeks + config.taper_weeks)) - rest_weeks
    else:
        steps = (total_weeks - (config.plateau_weeks + config.taper_weeks)) - (2 * rest_weeks)

    denominator = max(1, steps + config.step_denominator_offset)
    step_distance = ((config.target_distance * (config.target_week_percentage / 100)) - config.current_weekly_mileage) / denominator

    current_distance = config.current_weekly_mileage
    step = 0
    this_week_distance = current_distance

    weeks: List[PlanWeek] = []

    for i in range(1, total_weeks + 1):
        long_commutes = int((i + (total_weeks / config.max_long_commutes) - 1) // (total_weeks / config.max_long_commutes))
        rest_week = False
        week_number = config.start_week - 1 + i

        if i <= total_weeks - (config.plateau_weeks + config.taper_weeks):
            if i % config.rest_cycle_weeks:
                if config.step_after_rest or (i % config.rest_cycle_weeks > 1):
                    step += 1
                    current_distance += step_distance
                this_week_distance = round(current_distance)
            else:
                rest_week = True
                this_week_distance = round(current_distance * (config.rest_percentage / 100))
        elif i > (total_weeks - config.taper_weeks):
            rest_week = True
            this_week_distance = round(current_distance * (config.taper_percentage / 100))
        else:
            if i % config.rest_cycle_weeks:
                this_week_distance = round(current_distance)
            else:
                rest_week = True
                this_week_distance = round(current_distance * (config.rest_percentage / 100))

        week_metrics = build_week_metrics(
            config,
            week_number,
            i,
            this_week_distance,
            rest_week,
            long_commutes,
            distance_factor,
        )
        weeks.append(week_metrics)

    return weeks


def generate_step_week_plan(config: PlanConfig, distance_factor: float) -> List[PlanWeek]:
    total_weeks = (config.target_week - config.start_week) + 1
    steps = 0
    week_meta: List[Tuple[int, int, bool]] = []

    for i in range(1, total_weeks + 1):
        if is_step_week(config, i):
            steps += 1
        reduced = is_reduced_week(config, i)
        week_meta.append((i, steps, reduced))

    denominator = max(1, steps + config.step_denominator_offset)
    step_distance = ((config.target_distance * (config.target_week_percentage / 100)) - config.current_weekly_mileage) / denominator
    default_lr_step = ((config.target_distance * (config.target_ride_percentage / 100)) - config.current_lr_distance) / max(1, steps)

    weeks: List[PlanWeek] = []
    for i, step, reduced in week_meta:
        long_commutes = int((i + (total_weeks / config.max_long_commutes) - 1) // (total_weeks / config.max_long_commutes))
        distance = config.current_weekly_mileage + (step * step_distance)
        if reduced:
            distance = distance * (config.rest_percentage / 100)
        this_week_distance = round(distance)

        week_metrics = build_week_metrics(
            config,
            config.start_week - 1 + i,
            i,
            this_week_distance,
            reduced,
            long_commutes,
            distance_factor,
            step=step,
            total_steps=steps,
            default_lr_step=default_lr_step,
        )
        weeks.append(week_metrics)

    return weeks


def build_week_metrics(
    config: PlanConfig,
    week_number: int,
    index: int,
    this_week_distance: float,
    reduced: bool,
    long_commutes: int,
    distance_factor: float,
    step: int = 0,
    total_steps: int = 0,
    default_lr_step: float = 0.0,
) -> PlanWeek:
    commute_distance = compute_commute_distance(
        config,
        index,
        reduced,
        long_commutes,
        this_week_distance,
    )

    non_commute_distance = max(0.0, this_week_distance - commute_distance)

    second_ride = 0.0
    if config.second_ride_percentage_of_long is not None:
        max_long_ride = (config.target_ride_percentage / 100) * config.target_distance
        max_second_ride = (config.second_ride_percentage_of_long / 100) * max_long_ride
        if reduced:
            default_long = round(config.current_lr_distance + (step * default_lr_step))
            long_ride_floor = round(default_long * (config.rest_percentage / 100))
            main_ride = min(max_long_ride, max(non_commute_distance, long_ride_floor))
        else:
            balanced_long_ride = math.ceil(
                non_commute_distance / (1 + (config.second_ride_percentage_of_long / 100))
            )
            potential_second_ride = round(
                min(non_commute_distance / 2, non_commute_distance - balanced_long_ride, max_second_ride)
            )
            if potential_second_ride >= config.min_second_ride:
                second_ride = potential_second_ride

            main_ride = round(min(max_long_ride, non_commute_distance - second_ride))
    else:
        main_ride = round(
            min(
                ((config.target_ride_percentage / 100) * config.target_distance),
                non_commute_distance * (100 / (100 + config.second_ride_percentage)),
            )
        )
        second_ride = round(main_ride * (config.second_ride_percentage / 100))

    if config.distance_floor_commute_and_long:
        this_week_distance = max(this_week_distance, commute_distance + main_ride)
        non_commute_distance = max(0.0, this_week_distance - commute_distance)

    leftovers = max(0.0, non_commute_distance - (main_ride + second_ride))

    proportion_of_max_week = this_week_distance / ((config.target_week_percentage / 100) * config.target_distance)
    proportion_of_max_ride = main_ride / config.target_distance

    week_start = week_start_date(config.target_year, week_number, config.week_start_offset_days)
    week_end = week_start + timedelta(days=6)

    climb_target = round(config.target_total_climb * proportion_of_max_ride, 2)
    if config.target_total_ascent is not None and total_steps:
        ascent_fraction = (step / total_steps) if total_steps > 0 else 0.0
        climb_target = ascent_fraction * 1000 * main_ride * ((config.ascent_percentage / 100) * config.target_total_ascent) / (
            1000 * config.target_distance
        )
        if reduced:
            climb_target = climb_target * (config.rest_percentage / 100)
        climb_target = round(climb_target, 2)

    return PlanWeek(
        index=index,
        week_number=week_number,
        week_start=week_start,
        week_end=week_end,
        distance_km=round(this_week_distance * distance_factor, 2),
        commute_km=round(commute_distance * distance_factor, 2),
        main_ride_km=round(main_ride * distance_factor, 2),
        second_ride_km=round(second_ride * distance_factor, 2),
        leftovers_km=round(leftovers * distance_factor, 2),
        duration_hours=round(config.target_total_time * proportion_of_max_week, 2),
        climb_m=climb_target,
    )


def is_rest_week(config: PlanConfig, week: int) -> bool:
    if week <= 0:
        raise ValueError("week must be > 0")
    if config.rest_weeks:
        return week in config.rest_weeks
    return (week % config.rest_cycle_weeks) == 0


def is_taper_week(config: PlanConfig, week: int) -> bool:
    if week <= 0:
        raise ValueError("week must be > 0")
    return week > total_weeks(config) - config.taper_weeks


def is_plateau_week(config: PlanConfig, week: int) -> bool:
    if week <= 0:
        raise ValueError("week must be > 0")
    if is_taper_week(config, week):
        return False
    return week > (total_weeks(config) - (config.taper_weeks + config.plateau_weeks))


def is_reduced_week(config: PlanConfig, week: int) -> bool:
    return is_rest_week(config, week) or is_taper_week(config, week)


def is_step_week(config: PlanConfig, week: int) -> bool:
    if week <= 0:
        raise ValueError("week must be > 0")
    if week == 1:
        return config.week1_step
    if is_reduced_week(config, week) or is_plateau_week(config, week):
        return False
    if config.step_after_rest:
        return True
    return not is_rest_week(config, week - 1)


def total_weeks(config: PlanConfig) -> int:
    return (config.target_week - config.start_week) + 1


def week_start_date(year: int, week_number: int, offset_days: int) -> date:
    week_label = f"{year}-W{week_number - 1}"
    week_start = datetime.strptime(week_label + "-1", "%Y-W%W-%w") + timedelta(days=offset_days)
    return week_start.date()


def is_commute_week(config: PlanConfig, week: int) -> bool:
    if week <= 0:
        raise ValueError("week must be > 0")
    if config.non_commute_weeks:
        return week not in config.non_commute_weeks
    return True


def compute_commute_distance(
    config: PlanConfig,
    week: int,
    reduced: bool,
    long_commutes: int,
    this_week_distance: float,
) -> float:
    if reduced:
        rest_commutes = config.commutes_per_rest_week or config.commutes_per_week
        commute_distance = rest_commutes * config.current_standard_commute
    else:
        commute_distance = (
            (config.current_standard_commute * (config.commutes_per_week - long_commutes))
            + (config.long_commute * long_commutes)
        )

    if not is_commute_week(config, week):
        commute_distance = 0.0

    if not config.week1_step and week == 1:
        commute_distance = min(commute_distance, this_week_distance)

    return commute_distance


def load_sessions(db_path: str) -> List[dict]:
    query = """
        SELECT _id, starttime, distance, meters, sessiontime, pauseTime, title, cat
        FROM sessions
        ORDER BY starttime ASC
    """
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()

    sessions: List[dict] = []
    for row in rows:
        sessions.append(
            {
                "id": row[0],
                "starttime": row[1],
                "distance": row[2],
                "meters": row[3],
                "sessiontime": row[4],
                "pausetime": row[5],
                "title": row[6],
                "cat": row[7],
            }
        )
    return sessions


def normalize_distance_km(distance_value: Optional[float]) -> float:
    if distance_value is None:
        return 0.0
    if distance_value > 1000:
        return distance_value / 1000.0
    return distance_value


def parse_session_date(starttime: Optional[int]) -> Optional[date]:
    if starttime is None:
        return None
    # BikeComputer Pro stores milliseconds since epoch for starttime.
    timestamp_seconds = starttime / 1000.0
    return datetime.utcfromtimestamp(timestamp_seconds).date()


def calculate_duration_hours(sessiontime: Optional[int], pausetime: Optional[int]) -> float:
    if sessiontime is None:
        return 0.0
    paused = pausetime or 0
    moving_ms = max(0, sessiontime - paused)
    return moving_ms / 1000.0 / 3600.0


def aggregate_weekly_actuals(
    sessions: Iterable[dict],
    plan_weeks: List[PlanWeek],
    cat_multipliers: Dict[int, float],
) -> Dict[int, WeekActuals]:
    week_map: Dict[int, WeekActuals] = {}

    for week in plan_weeks:
        week_map[week.index] = WeekActuals(distance_km=0.0, climb_m=0.0, duration_hours=0.0)

    for session in sessions:
        ride_date = parse_session_date(session.get("starttime"))
        if ride_date is None:
            continue

        for week in plan_weeks:
            if week.week_start <= ride_date <= week.week_end:
                multiplier = cat_multipliers.get(session.get("cat", 0), 1.0)
                distance_km = normalize_distance_km(session.get("distance")) * multiplier
                climb_m = (session.get("meters") or 0.0) * multiplier
                duration_hours = calculate_duration_hours(session.get("sessiontime"), session.get("pausetime")) * multiplier

                existing = week_map[week.index]
                week_map[week.index] = WeekActuals(
                    distance_km=existing.distance_km + distance_km,
                    climb_m=existing.climb_m + climb_m,
                    duration_hours=existing.duration_hours + duration_hours,
                )
                break

    return week_map


def score_week(week: PlanWeek, actuals: WeekActuals) -> Dict[str, Optional[float]]:
    return {
        "distance_pct": percent_of_target(actuals.distance_km, week.distance_km),
        "climb_pct": percent_of_target(actuals.climb_m, week.climb_m),
        "duration_pct": percent_of_target(actuals.duration_hours, week.duration_hours),
    }


def percent_of_target(actual: float, target: float) -> Optional[float]:
    if target <= 0:
        return None
    return round((actual / target) * 100.0, 2)


def find_event_sessions(sessions: Iterable[dict], event_dates: Iterable[date]) -> List[dict]:
    event_set = set(event_dates)
    return [session for session in sessions if parse_session_date(session.get("starttime")) in event_set]


def parse_event_dates(values: List[str]) -> List[date]:
    parsed: List[date] = []
    for value in values:
        parsed.append(datetime.strptime(value, "%Y-%m-%d").date())
    return parsed


def parse_duration_hhmmss(value: str) -> float:
    if not value:
        return 0.0
    parts = value.split(":")
    if len(parts) != 3:
        return 0.0
    hours, minutes, seconds = (int(part) for part in parts)
    return hours + (minutes / 60.0) + (seconds / 3600.0)


def load_event_match_config(path: Optional[str]) -> dict:
    if not path:
        return {}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {}


def load_routes_config(path: Optional[str]) -> dict:
    if not path:
        return {}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {}

def select_event_summaries(summaries: List[dict], mode: str) -> List[dict]:
    if not summaries:
        return summaries
    if mode == "first_day":
        earliest = min(summary["date"] for summary in summaries)
        return [summary for summary in summaries if summary["date"] == earliest]
    if mode == "max_distance":
        chosen = max(summaries, key=lambda summary: summary["distance_km"])
        return [chosen]
    if mode == "two_day_consecutive_max":
        return select_two_day_consecutive_max(summaries)
    return summaries


def select_two_day_consecutive_max(summaries: List[dict]) -> List[dict]:
    aggregated = aggregate_summaries_by_date(summaries)
    if len(aggregated) < 2:
        return aggregated

    sorted_days = sorted(aggregated, key=lambda item: item["date"])
    best_pair: Optional[Tuple[dict, dict]] = None
    best_distance = -1.0

    for index in range(len(sorted_days) - 1):
        first_day = sorted_days[index]
        second_day = sorted_days[index + 1]
        if second_day["date"] != first_day["date"] + timedelta(days=1):
            continue
        combined_distance = first_day["distance_km"] + second_day["distance_km"]
        if combined_distance > best_distance:
            best_distance = combined_distance
            best_pair = (first_day, second_day)

    if best_pair:
        return [best_pair[0], best_pair[1]]

    return [max(aggregated, key=lambda summary: summary["distance_km"])]


def aggregate_summaries_by_date(summaries: List[dict]) -> List[dict]:
    totals: Dict[date, dict] = {}
    for summary in summaries:
        ride_date = summary["date"]
        entry = totals.setdefault(
            ride_date,
            {
                "date": ride_date,
                "distance_km": 0.0,
                "ascent_m": 0.0,
                "duration_hours": 0.0,
                "paths": [],
                "files": [],
            },
        )
        entry["distance_km"] += summary["distance_km"]
        entry["ascent_m"] += summary["ascent_m"]
        entry["duration_hours"] += summary["duration_hours"]
        if summary.get("path"):
            entry["paths"].append(summary["path"])
        if summary.get("files"):
            entry["files"].extend(summary["files"])

    aggregated: List[dict] = []
    for ride_date, entry in totals.items():
        entry["distance_km"] = round(entry["distance_km"], 2)
        entry["ascent_m"] = round(entry["ascent_m"], 1)
        entry["duration_hours"] = round(entry["duration_hours"], 2)
        aggregated.append(entry)

    return aggregated


def build_event_date_window(target_week: PlanWeek, days: int) -> Tuple[date, date]:
    if days <= 0:
        return target_week.week_start, target_week.week_end
    return target_week.week_start - timedelta(days=days), target_week.week_end + timedelta(days=days)


def parse_config_event_dates(values: Iterable[str]) -> List[date]:
    parsed: List[date] = []
    for value in values:
        try:
            parsed.append(datetime.strptime(value, "%Y-%m-%d").date())
        except ValueError:
            continue
    return parsed


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371.0
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    )
    return 2 * radius_km * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def find_xml_start(file_obj) -> int:
    head = file_obj.read(8192)
    if not head:
        return -1
    for marker in (b"<?xml", b"<gpx"):
        idx = head.find(marker)
        if idx != -1:
            return idx
    return head.find(b"<")


def parse_route_gpx_summary(path: Path) -> Optional[dict]:
    try:
        with path.open("rb") as file_obj:
            start = find_xml_start(file_obj)
            if start < 0:
                return None
            file_obj.seek(start)
            context = ET.iterparse(file_obj, events=("start", "end"))

            route_name = ""
            total_distance_km = 0.0
            total_ascent_m = 0.0
            last_lat: Optional[float] = None
            last_lon: Optional[float] = None
            last_ele: Optional[float] = None

            for event, elem in context:
                if event != "end":
                    continue
                if elem.tag.endswith("name") and not route_name and elem.text:
                    route_name = elem.text.strip()
                    elem.clear()
                    continue
                if not elem.tag.endswith("trkpt"):
                    continue

                lat = elem.get("lat")
                lon = elem.get("lon")
                if lat is None or lon is None:
                    elem.clear()
                    continue

                lat_val = float(lat)
                lon_val = float(lon)

                ele_elem = elem.find("{*}ele")
                ele_val = float(ele_elem.text) if ele_elem is not None and ele_elem.text else None

                if last_lat is not None and last_lon is not None:
                    total_distance_km += haversine_km(last_lat, last_lon, lat_val, lon_val)

                if ele_val is not None and last_ele is not None:
                    delta_ele = ele_val - last_ele
                    if delta_ele > 0:
                        total_ascent_m += delta_ele

                last_lat = lat_val
                last_lon = lon_val
                last_ele = ele_val
                elem.clear()

            return {
                "path": str(path),
                "name": route_name or path.stem,
                "distance_km": round(total_distance_km, 2),
                "ascent_m": round(total_ascent_m, 1),
            }
    except (OSError, ET.ParseError):
        return None


def load_route_summaries(route_paths: List[str]) -> List[dict]:
    summaries: List[dict] = []
    for route_path in route_paths:
        summary = parse_route_gpx_summary(Path(route_path))
        if summary:
            summaries.append(summary)
    return summaries


def resolve_route_paths(
    plan_routes: object,
    event_dates: List[dict],
    base_dir: Optional[Path],
) -> List[str]:
    if isinstance(plan_routes, dict):
        routes = []
        events_map = plan_routes.get("events", {})
        for event in event_dates:
            event_key = event["date"].isoformat()
            routes.extend(events_map.get(event_key, []))
        if not routes:
            routes = plan_routes.get("default", [])
    elif isinstance(plan_routes, list):
        routes = plan_routes
    else:
        routes = []

    if base_dir:
        routes = [str((base_dir / path).resolve()) for path in routes]
    return routes


def parse_gpx_summary(path: Path) -> Optional[dict]:
    try:
        with path.open("rb") as file_obj:
            start = find_xml_start(file_obj)
            if start < 0:
                return None
            file_obj.seek(start)
            try:
                context = ET.iterparse(file_obj, events=("start", "end"))
            except ET.ParseError:
                return None

            return extract_gpx_summary(context)
    except (OSError, ET.ParseError):
        return None


def extract_gpx_summary(context: Iterable[Tuple[str, ET.Element]]) -> Optional[dict]:

    first_time: Optional[datetime] = None
    last_time: Optional[datetime] = None
    last_lat: Optional[float] = None
    last_lon: Optional[float] = None
    last_ele: Optional[float] = None
    total_distance_km = 0.0
    total_ascent_m = 0.0

    try:
        for event, elem in context:
            if event != "end" or not elem.tag.endswith("trkpt"):
                continue

            lat = elem.get("lat")
            lon = elem.get("lon")
            if lat is None or lon is None:
                elem.clear()
                continue

            lat_val = float(lat)
            lon_val = float(lon)

            time_elem = elem.find("{*}time")
            if time_elem is not None and time_elem.text:
                try:
                    time_val = datetime.fromisoformat(time_elem.text.replace("Z", "+00:00"))
                except ValueError:
                    time_val = None
                if time_val:
                    if first_time is None:
                        first_time = time_val
                    last_time = time_val

            ele_elem = elem.find("{*}ele")
            ele_val = float(ele_elem.text) if ele_elem is not None and ele_elem.text else None

            if last_lat is not None and last_lon is not None:
                total_distance_km += haversine_km(last_lat, last_lon, lat_val, lon_val)

            if ele_val is not None and last_ele is not None:
                delta_ele = ele_val - last_ele
                if delta_ele > 0:
                    total_ascent_m += delta_ele

            last_lat = lat_val
            last_lon = lon_val
            last_ele = ele_val
            elem.clear()
    except ET.ParseError:
        return None

    if first_time is None or last_time is None:
        return None

    duration_hours = max(0.0, (last_time - first_time).total_seconds() / 3600.0)
    return {
        "path": "",
        "date": first_time.date(),
        "distance_km": round(total_distance_km, 2),
        "ascent_m": round(total_ascent_m, 1),
        "duration_hours": round(duration_hours, 2),
    }


def load_gpx_summaries(directory: Path) -> List[dict]:
    summaries: List[dict] = []
    for path in sorted(directory.glob("*.gpx")):
        summary = parse_gpx_summary(path)
        if summary:
            summary["path"] = str(path)
            summaries.append(summary)
    return summaries


def find_json_start(file_obj) -> int:
    head = file_obj.read(8192)
    if not head:
        return -1
    return head.find(b"{")


def parse_json_summary(path: Path) -> Optional[dict]:
    try:
        with path.open("rb") as file_obj:
            start = find_json_start(file_obj)
            if start < 0:
                return None
            file_obj.seek(start)
            data = file_obj.read()
        payload = json.loads(data)
    except (OSError, json.JSONDecodeError):
        return None

    date_value = payload.get("date_ymd")
    if not date_value:
        return None

    try:
        ride_date = datetime.strptime(date_value, "%Y-%m-%d").date()
    except ValueError:
        return None

    distance_km = float(payload.get("dist_km") or 0.0)
    ascent_m = float(payload.get("asc_m") or 0.0)
    duration_hours = parse_duration_hhmmss(payload.get("dur_time", ""))

    return {
        "path": str(path),
        "date": ride_date,
        "distance_km": round(distance_km, 2),
        "ascent_m": round(ascent_m, 1),
        "duration_hours": round(duration_hours, 2),
        "type_name": payload.get("type_name"),
    }


def load_json_summaries(directory: Path) -> List[dict]:
    summaries: List[dict] = []
    for path in sorted(directory.glob("*.json")):
        summary = parse_json_summary(path)
        if summary:
            summaries.append(summary)
    return summaries


def aggregate_by_date(summaries: Iterable[dict]) -> Dict[date, dict]:
    totals: Dict[date, dict] = defaultdict(
        lambda: {
            "distance_km": 0.0,
            "ascent_m": 0.0,
            "duration_hours": 0.0,
            "files": [],
        }
    )
    for summary in summaries:
        ride_date = summary["date"]
        entry = totals[ride_date]
        entry["distance_km"] += summary["distance_km"]
        entry["ascent_m"] += summary["ascent_m"]
        entry["duration_hours"] += summary["duration_hours"]
        entry["files"].append(summary["path"])

    for ride_date, entry in totals.items():
        entry["date"] = ride_date
        entry["distance_km"] = round(entry["distance_km"], 2)
        entry["ascent_m"] = round(entry["ascent_m"], 1)
        entry["duration_hours"] = round(entry["duration_hours"], 2)

    return totals


def render_weekly_report(plan_weeks: List[PlanWeek], actuals: Dict[int, WeekActuals]) -> None:
    for week in plan_weeks:
        week_actuals = actuals.get(week.index, WeekActuals(0.0, 0.0, 0.0))
        scores = score_week(week, week_actuals)
        print(
            "Week",
            week.index,
            f"{week.week_start} to {week.week_end}",
            "Target km",
            week.distance_km,
            "Actual km",
            round(week_actuals.distance_km, 2),
            "Distance %",
            scores["distance_pct"],
            "Climb %",
            scores["climb_pct"],
            "Duration %",
            scores["duration_pct"],
        )


def render_event_comparison(label: str, summaries: List[dict], target_week: PlanWeek) -> None:
    if not summaries:
        return

    target_distance = target_week.main_ride_km
    target_climb = target_week.climb_m
    target_duration = target_week.duration_hours

    print("Event comparison:", label)
    for summary in summaries:
        print(
            "Event",
            summary["date"],
            "Distance km",
            summary["distance_km"],
            "Distance %",
            percent_of_target(summary["distance_km"], target_distance),
            "Ascent m",
            summary["ascent_m"],
            "Ascent %",
            percent_of_target(summary["ascent_m"], target_climb),
            "Duration h",
            summary["duration_hours"],
            "Duration %",
            percent_of_target(summary["duration_hours"], target_duration),
        )

    if len(summaries) == 2:
        first, second = sorted(summaries, key=lambda item: item["date"])
        print(
            "Recovery day 2 vs day 1",
            "Distance %",
            percent_of_target(second["distance_km"], first["distance_km"]),
            "Ascent %",
            percent_of_target(second["ascent_m"], first["ascent_m"]),
            "Duration %",
            percent_of_target(second["duration_hours"], first["duration_hours"]),
        )


def render_route_comparison(routes: List[dict], events: List[dict]) -> None:
    if not routes or not events:
        return

    if len(routes) == len(events):
        events_sorted = sorted(events, key=lambda item: item.get("date", date.min))
        print("Route comparison (per day)")
        for route, event in zip(routes, events_sorted):
            print(
                "Route",
                route["name"],
                "Planned km",
                route["distance_km"],
                "Actual km",
                event["distance_km"],
                "Distance %",
                percent_of_target(event["distance_km"], route["distance_km"]),
                "Planned ascent m",
                route["ascent_m"],
                "Actual ascent m",
                event["ascent_m"],
                "Ascent %",
                percent_of_target(event["ascent_m"], route["ascent_m"]),
            )
        return

    route_total_distance = sum(route["distance_km"] for route in routes)
    route_total_ascent = sum(route["ascent_m"] for route in routes)
    event_total_distance = sum(event["distance_km"] for event in events)
    event_total_ascent = sum(event["ascent_m"] for event in events)

    print("Route comparison (total)")
    print(
        "Planned km",
        round(route_total_distance, 2),
        "Actual km",
        round(event_total_distance, 2),
        "Distance %",
        percent_of_target(event_total_distance, route_total_distance),
        "Planned ascent m",
        round(route_total_ascent, 1),
        "Actual ascent m",
        round(event_total_ascent, 1),
        "Ascent %",
        percent_of_target(event_total_ascent, route_total_ascent),
    )


def average(values: List[float]) -> Optional[float]:
    if not values:
        return None
    return round(sum(values) / len(values), 2)


def collect_compliance(plan_weeks: List[PlanWeek], actuals: Dict[int, WeekActuals]) -> List[dict]:
    rows: List[dict] = []
    for week in plan_weeks:
        week_actuals = actuals.get(week.index, WeekActuals(0.0, 0.0, 0.0))
        scores = score_week(week, week_actuals)
        rows.append(
            {
                "index": week.index,
                "distance_pct": scores["distance_pct"],
                "climb_pct": scores["climb_pct"],
                "duration_pct": scores["duration_pct"],
            }
        )
    return rows


def summarize_compliance(rows: List[dict]) -> dict:
    distance_vals = [row["distance_pct"] for row in rows if row["distance_pct"] is not None]
    climb_vals = [row["climb_pct"] for row in rows if row["climb_pct"] is not None]
    duration_vals = [row["duration_pct"] for row in rows if row["duration_pct"] is not None]
    return {
        "distance_pct": average(distance_vals),
        "climb_pct": average(climb_vals),
        "duration_pct": average(duration_vals),
    }


def render_progress_impact(
    plan_weeks: List[PlanWeek],
    actuals: Dict[int, WeekActuals],
    events: List[dict],
) -> None:
    if not plan_weeks or not events:
        return

    target_week_index = plan_weeks[-1].index
    prior_weeks = [row for row in collect_compliance(plan_weeks, actuals) if row["index"] < target_week_index]
    last_four = prior_weeks[-4:] if len(prior_weeks) >= 4 else prior_weeks

    overall = summarize_compliance(prior_weeks)
    recent = summarize_compliance(last_four)

    print("Progress impact")
    print(
        "Overall compliance",
        "Distance %",
        overall["distance_pct"],
        "Climb %",
        overall["climb_pct"],
        "Duration %",
        overall["duration_pct"],
    )
    print(
        "Recent compliance (last 4 weeks)",
        "Distance %",
        recent["distance_pct"],
        "Climb %",
        recent["climb_pct"],
        "Duration %",
        recent["duration_pct"],
    )

    if len(events) >= 1:
        top_event = max(events, key=lambda item: item["distance_km"])
        print(
            "Top event day",
            top_event["date"],
            "Distance km",
            top_event["distance_km"],
            "Ascent m",
            top_event["ascent_m"],
            "Duration h",
            top_event["duration_hours"],
        )


def select_event_dates_from_window(
    summaries: List[dict],
    target_week: PlanWeek,
    window_days: int,
    selection_mode: str,
    explicit_dates: List[date],
    prefer_explicit: bool,
) -> List[dict]:
    if prefer_explicit and explicit_dates:
        candidates = [summary for summary in summaries if summary["date"] in explicit_dates]
    else:
        window_start, window_end = build_event_date_window(target_week, window_days)
        candidates = [summary for summary in summaries if window_start <= summary["date"] <= window_end]
    return select_event_summaries(candidates, selection_mode)


def render_plan_event_summary(
    plan_key: str,
    config: PlanConfig,
    target_week: PlanWeek,
    summaries: List[dict],
) -> None:
    target_distance = target_week.main_ride_km
    target_climb = target_week.climb_m
    target_duration = target_week.duration_hours
    date_range = f"{target_week.week_start} to {target_week.week_end}"
    print("Plan", plan_key, "Event", config.name, "Target week", date_range)
    print(
        "Targets",
        "Distance km",
        target_distance,
        "Ascent m",
        target_climb,
        "Duration h",
        target_duration,
    )
    if not summaries:
        print("Event matches", 0)
        return

    print("Event matches", len(summaries))
    for summary in summaries:
        print(
            "Actual",
            summary["date"],
            "Distance km",
            summary["distance_km"],
            "Distance %",
            percent_of_target(summary["distance_km"], target_distance),
            "Ascent m",
            summary["ascent_m"],
            "Ascent %",
            percent_of_target(summary["ascent_m"], target_climb),
            "Duration h",
            summary["duration_hours"],
            "Duration %",
            percent_of_target(summary["duration_hours"], target_duration),
        )
    if len(summaries) == 2:
        first, second = sorted(summaries, key=lambda item: item["date"])
        print(
            "Recovery day 2 vs day 1",
            "Distance %",
            percent_of_target(second["distance_km"], first["distance_km"]),
            "Ascent %",
            percent_of_target(second["ascent_m"], first["ascent_m"]),
            "Duration %",
            percent_of_target(second["duration_hours"], first["duration_hours"]),
        )


def build_event_export_rows(
    plan_key: str,
    config: PlanConfig,
    target_week: PlanWeek,
    summaries: List[dict],
    source: str,
) -> List[dict]:
    rows: List[dict] = []
    target_distance = target_week.main_ride_km
    target_climb = target_week.climb_m
    target_duration = target_week.duration_hours

    for summary in summaries:
        rows.append(
            {
                "plan_key": plan_key,
                "event_name": config.name,
                "event_source": source,
                "target_week_start": target_week.week_start.isoformat(),
                "target_week_end": target_week.week_end.isoformat(),
                "target_distance_km": target_distance,
                "target_ascent_m": target_climb,
                "target_duration_h": target_duration,
                "event_date": summary["date"].isoformat(),
                "event_distance_km": summary["distance_km"],
                "event_ascent_m": summary["ascent_m"],
                "event_duration_h": summary["duration_hours"],
                "distance_pct": percent_of_target(summary["distance_km"], target_distance),
                "ascent_pct": percent_of_target(summary["ascent_m"], target_climb),
                "duration_pct": percent_of_target(summary["duration_hours"], target_duration),
            }
        )

    if len(summaries) == 2:
        first, second = sorted(summaries, key=lambda item: item["date"])
        rows.append(
            {
                "plan_key": plan_key,
                "event_name": config.name,
                "event_source": source,
                "target_week_start": target_week.week_start.isoformat(),
                "target_week_end": target_week.week_end.isoformat(),
                "target_distance_km": target_distance,
                "target_ascent_m": target_climb,
                "target_duration_h": target_duration,
                "event_date": f"{first['date'].isoformat()}->{second['date'].isoformat()}",
                "event_distance_km": second["distance_km"],
                "event_ascent_m": second["ascent_m"],
                "event_duration_h": second["duration_hours"],
                "distance_pct": percent_of_target(second["distance_km"], first["distance_km"]),
                "ascent_pct": percent_of_target(second["ascent_m"], first["ascent_m"]),
                "duration_pct": percent_of_target(second["duration_hours"], first["duration_hours"]),
                "note": "recovery_day2_vs_day1",
            }
        )

    return rows


def write_event_exports(base_path: str, rows: List[dict]) -> None:
    if not rows:
        return
    base = Path(base_path)
    json_path = base.with_suffix(".json")
    csv_path = base.with_suffix(".csv")

    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(rows, handle, indent=2)

    fieldnames = sorted({key for row in rows for key in row.keys()})
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare plan targets with BikeComputer Pro history.")
    parser.add_argument("--db-path", required=True, help="Path to backuped_sessions.db")
    parser.add_argument("--plan", choices=sorted(PLAN_CONFIGS.keys()))
    parser.add_argument("--all-plans", action="store_true", help="Compare all plan configs")
    parser.add_argument("--event-date", action="append", default=[], help="Event date YYYY-MM-DD (repeatable)")
    parser.add_argument("--gpx-dir", help="Directory containing GPX files to scan for events")
    parser.add_argument("--json-dir", help="Directory containing VeloHero JSON files to scan for events")
    parser.add_argument("--event-config", help="JSON config for event matching")
    parser.add_argument("--routes-config", help="JSON map of plans to route GPX files")
    parser.add_argument("--routes-dir", help="Base directory for routes in routes-config")
    parser.add_argument(
        "--event-source",
        choices=["auto", "json", "gpx", "none"],
        default="auto",
        help="Choose event matching source",
    )
    parser.add_argument(
        "--export-events",
        help="Base path to export event summaries (writes .json and .csv)",
    )

    args = parser.parse_args()

    event_config = load_event_match_config(args.event_config)
    routes_config = load_routes_config(args.routes_config)
    routes_base_dir = Path(args.routes_dir) if args.routes_dir else None
    window_days = int(event_config.get("event_window_days", 0) or 0)
    prefer_explicit = bool(event_config.get("prefer_explicit_event_dates", False))
    config_event_dates = parse_config_event_dates(event_config.get("event_dates", []))
    selection_mode = event_config.get("event_selection", "all")

    if not args.plan and not args.all_plans:
        raise SystemExit("Provide --plan or --all-plans")

    plan_keys = sorted(PLAN_CONFIGS.keys()) if args.all_plans else [args.plan]

    sessions = load_sessions(args.db_path)
    gpx_summaries: List[dict] = []
    json_summaries: List[dict] = []

    if args.gpx_dir and args.event_source in ("auto", "gpx"):
        gpx_dir = Path(args.gpx_dir)
        if gpx_dir.exists():
            gpx_summaries = load_gpx_summaries(gpx_dir)

    if args.json_dir and args.event_source in ("auto", "json"):
        json_dir = Path(args.json_dir)
        if json_dir.exists():
            json_summaries = load_json_summaries(json_dir)
            json_summaries = aggregate_summaries_by_date(json_summaries)

    export_rows: List[dict] = []
    for plan_key in plan_keys:
        config = PLAN_CONFIGS[plan_key]
        plan_weeks = generate_plan(config)
        target_week = plan_weeks[-1]

        plan_routes = routes_config.get(plan_key) or routes_config.get("routes_default") or []
        route_summaries: List[dict] = []

        actuals = aggregate_weekly_actuals(sessions, plan_weeks, DEFAULT_CAT_MULTIPLIERS)
        render_weekly_report(plan_weeks, actuals)

        if args.event_date:
            event_dates = parse_event_dates(args.event_date)
            events = find_event_sessions(sessions, event_dates)
            print("Event sessions matched:", len(events))
            for session in events:
                print(
                    "Event session",
                    session.get("id"),
                    "Date",
                    parse_session_date(session.get("starttime")),
                    "Distance km",
                    round(normalize_distance_km(session.get("distance")), 2),
                    "Climb m",
                    session.get("meters"),
                    "Duration h",
                    round(calculate_duration_hours(session.get("sessiontime"), session.get("pausetime")), 2),
                )

        if args.event_source != "none":
            if json_summaries and args.event_source in ("auto", "json"):
                event_dates = select_event_dates_from_window(
                    json_summaries,
                    target_week,
                    window_days,
                    selection_mode,
                    config_event_dates,
                    prefer_explicit,
                )
                route_paths = resolve_route_paths(plan_routes, event_dates, routes_base_dir)
                route_summaries = load_route_summaries(route_paths)
                print("JSON files scanned:", len(json_summaries))
                print("JSON dates in target week:", len(event_dates))
                for summary in event_dates:
                    print(
                        "JSON",
                        summary["date"],
                        "Distance km",
                        summary["distance_km"],
                        "Ascent m",
                        summary["ascent_m"],
                        "Duration h",
                        summary["duration_hours"],
                        "Files",
                        len(summary.get("files", [])),
                    )
                render_event_comparison("JSON", event_dates, target_week)
                render_plan_event_summary(plan_key, config, target_week, event_dates)
                render_route_comparison(route_summaries, event_dates)
                render_progress_impact(plan_weeks, actuals, event_dates)
                export_rows.extend(build_event_export_rows(plan_key, config, target_week, event_dates, "json"))
            elif gpx_summaries and args.event_source in ("auto", "gpx"):
                event_gpx = select_event_dates_from_window(
                    gpx_summaries,
                    target_week,
                    window_days,
                    selection_mode,
                    config_event_dates,
                    prefer_explicit,
                )
                route_paths = resolve_route_paths(plan_routes, event_gpx, routes_base_dir)
                route_summaries = load_route_summaries(route_paths)
                print("GPX files scanned:", len(gpx_summaries))
                print("GPX events in target week:", len(event_gpx))
                for summary in event_gpx:
                    print(
                        "GPX",
                        summary.get("path", ""),
                        "Date",
                        summary["date"],
                        "Distance km",
                        summary["distance_km"],
                        "Ascent m",
                        summary["ascent_m"],
                        "Duration h",
                        summary["duration_hours"],
                    )
                render_event_comparison("GPX", event_gpx, target_week)
                render_plan_event_summary(plan_key, config, target_week, event_gpx)
                render_route_comparison(route_summaries, event_gpx)
                render_progress_impact(plan_weeks, actuals, event_gpx)
                export_rows.extend(build_event_export_rows(plan_key, config, target_week, event_gpx, "gpx"))

    if args.export_events:
        write_event_exports(args.export_events, export_rows)


if __name__ == "__main__":
    main()
