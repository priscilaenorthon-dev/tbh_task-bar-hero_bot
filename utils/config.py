import random
from pathlib import Path
from tkinter import DoubleVar, IntVar, StringVar

from yaml import dump, safe_load

from utils.global_variables import BASE_DIR, CONFIG_PATH

WINDOW_SCALES = ("1", "1.25", "1.5", "2")
_SCALE_SUFFIX = {
    "1": "",
    "1.25": "_1-25",
    "1.5": "_1-50",
    "2": "_2",
}
_SCALE_SUFFIXES = tuple(_SCALE_SUFFIX.values())


def _template_path(relative_path: str) -> str:
    return str((BASE_DIR / relative_path).resolve())


def _ms_range(raw_value, default_spread=0.15):
    if isinstance(raw_value, dict):
        return int(raw_value["min"]), int(raw_value["max"])
    value = int(raw_value)
    spread = max(50, int(value * default_spread))
    return max(0, value - spread), value + spread


def _seconds_range(raw_value, default_spread=0.2):
    if isinstance(raw_value, dict):
        return float(raw_value["min"]), float(raw_value["max"])
    value = float(raw_value)
    spread = max(0.05, value * default_spread)
    return max(0.0, round(value - spread, 2)), round(value + spread, 2)


def _offset_range(raw_config):
    if raw_config is None:
        return -6, 6
    if isinstance(raw_config, dict):
        return int(raw_config["min"]), int(raw_config["max"])
    value = int(raw_config)
    return -value, value


def _normalize_config(config):
    """Upgrade older config.yml shapes to min/max ranges."""
    loop_min, loop_max = _ms_range(config["timeouts"]["loop_ms"])
    config["timeouts"]["loop_ms"] = {"min": loop_min, "max": loop_max}

    after_click = config["timeouts"]["after_click"]
    if not isinstance(after_click, dict):
        min_s, max_s = _seconds_range(after_click)
        config["timeouts"]["after_click"] = {"min": min_s, "max": max_s}

    wait_min, wait_max = _ms_range(config["combine_flow"]["wait_ms"])
    config["combine_flow"]["wait_ms"] = {"min": wait_min, "max": wait_max}

    interval_raw = config["periodic_stash_sort"]["interval_ms"]
    interval_min, interval_max = _ms_range(interval_raw)
    config["periodic_stash_sort"]["interval_ms"] = {
        "min": interval_min,
        "max": interval_max,
    }

    periodic = config["periodic_stash_sort"]
    if "between_clicks_ms" not in periodic:
        periodic["between_clicks_ms"] = {"min": 200, "max": 600}
    elif not isinstance(periodic["between_clicks_ms"], dict):
        b_min, b_max = _ms_range(periodic["between_clicks_ms"], default_spread=0.25)
        periodic["between_clicks_ms"] = {"min": b_min, "max": b_max}

    if "randomization" not in config:
        config["randomization"] = {}
    offset_min, offset_max = _offset_range(config["randomization"].get("click_offset_px"))
    config["randomization"]["click_offset_px"] = {"min": offset_min, "max": offset_max}

    scale = str(config.get("window_scale", "1"))
    config["window_scale"] = scale if scale in _SCALE_SUFFIX else "1"

    return config


def base_template_name(filename: str) -> str:
    """Strip scale suffix so config stores e.g. auto_fill.png, not auto_fill_1-25.png."""
    path = Path(filename)
    stem = path.stem
    for scale_suffix in _SCALE_SUFFIXES:
        if scale_suffix and stem.endswith(scale_suffix):
            return f"{stem[: -len(scale_suffix)]}{path.suffix}"
    return path.name


def _load_template_basename(relative_path: str) -> str:
    return base_template_name(Path(relative_path).name)


def _load_config():
    with open(CONFIG_PATH, encoding="utf-8") as config_file:
        return _normalize_config(safe_load(config_file))


config = _load_config()

dict = {
    "search_region": {
        "x": IntVar(value=config["search_region"]["x"]),
        "y": IntVar(value=config["search_region"]["y"]),
        "width": IntVar(value=config["search_region"]["width"]),
        "height": IntVar(value=config["search_region"]["height"]),
    },
    "matching": {
        "threshold": DoubleVar(value=config["matching"]["threshold"]),
    },
    "timeouts": {
        "loop_ms": {
            "min": IntVar(value=config["timeouts"]["loop_ms"]["min"]),
            "max": IntVar(value=config["timeouts"]["loop_ms"]["max"]),
        },
        "after_click": {
            "min": DoubleVar(value=config["timeouts"]["after_click"]["min"]),
            "max": DoubleVar(value=config["timeouts"]["after_click"]["max"]),
        },
    },
    "combine_flow": {
        "wait_ms": {
            "min": IntVar(value=config["combine_flow"]["wait_ms"]["min"]),
            "max": IntVar(value=config["combine_flow"]["wait_ms"]["max"]),
        },
        "template": StringVar(value=_load_template_basename(config["combine_flow"]["template"])),
        "back_template": StringVar(
            value=_load_template_basename(config["combine_flow"]["back_template"])
        ),
    },
    "periodic_stash_sort": {
        "interval_ms": {
            "min": IntVar(value=config["periodic_stash_sort"]["interval_ms"]["min"]),
            "max": IntVar(value=config["periodic_stash_sort"]["interval_ms"]["max"]),
        },
        "between_clicks_ms": {
            "min": IntVar(value=config["periodic_stash_sort"]["between_clicks_ms"]["min"]),
            "max": IntVar(value=config["periodic_stash_sort"]["between_clicks_ms"]["max"]),
        },
        "stash_template": StringVar(
            value=_load_template_basename(config["periodic_stash_sort"]["stash_template"])
        ),
        "sort_template": StringVar(
            value=_load_template_basename(config["periodic_stash_sort"]["sort_template"])
        ),
    },
    "randomization": {
        "click_offset_px": {
            "min": IntVar(value=config["randomization"]["click_offset_px"]["min"]),
            "max": IntVar(value=config["randomization"]["click_offset_px"]["max"]),
        },
    },
    "chest_check": [
        {
            "name": entry["name"],
            "template": StringVar(value=_load_template_basename(entry["template"])),
        }
        for entry in config["chest_check"]["templates"]
    ],
    "steps": [
        {
            "name": step["name"],
            **(
                {"template": StringVar(value=_load_template_basename(step["template"]))}
                if "template" in step
                else {}
            ),
        }
        for step in config["steps"]
    ],
    "log_lvl": StringVar(value=config.get("log_lvl", "INFO")),
    "window_scale": StringVar(value=config["window_scale"]),
}


def scaled_template_name(filename: str, scale: str | None = None) -> str:
    """Apply window scale suffix: 1 → no suffix, 1.25 → _1-25, 1.5 → _1-50, 2 → _2."""
    base = base_template_name(filename)
    path = Path(base)
    scale_key = scale if scale is not None else dict["window_scale"].get()
    suffix = _SCALE_SUFFIX.get(str(scale_key), "")
    return f"{path.stem}{suffix}{path.suffix}"


def _resolved_template(filename: str) -> str:
    name = Path(filename).name
    return _template_path(f"assets/{name}")


def template_path_for(variable) -> str:
    from wrappers.logging_wrapper import debug, warning

    base = base_template_name(variable.get())
    scaled = scaled_template_name(base)
    path = _resolved_template(scaled)
    if Path(path).is_file():
        debug(f"Template: {Path(path).name} (scale {dict['window_scale'].get()})")
        return path
    if scaled != base:
        warning(
            f"Scaled template missing: {scaled} (scale {dict['window_scale'].get()}), "
            f"trying base {base}"
        )
        path = _resolved_template(base)
    if not Path(path).is_file():
        raise FileNotFoundError(f"Template not found: {scaled} or {base}")
    return path


def chest_check_entries():
    return [
        {"name": entry["name"], "template": template_path_for(entry["template"])}
        for entry in dict["chest_check"]
    ]


def step_entries():
    steps = []
    for step in dict["steps"]:
        item = {"name": step["name"]}
        if "template" in step:
            item["template"] = template_path_for(step["template"])
        steps.append(item)
    return steps


def save_data():
    data = {
        "search_region": {
            "x": dict["search_region"]["x"].get(),
            "y": dict["search_region"]["y"].get(),
            "width": dict["search_region"]["width"].get(),
            "height": dict["search_region"]["height"].get(),
        },
        "matching": {
            "threshold": dict["matching"]["threshold"].get(),
        },
        "timeouts": {
            "loop_ms": {
                "min": dict["timeouts"]["loop_ms"]["min"].get(),
                "max": dict["timeouts"]["loop_ms"]["max"].get(),
            },
            "after_click": {
                "min": dict["timeouts"]["after_click"]["min"].get(),
                "max": dict["timeouts"]["after_click"]["max"].get(),
            },
        },
        "combine_flow": {
            "wait_ms": {
                "min": dict["combine_flow"]["wait_ms"]["min"].get(),
                "max": dict["combine_flow"]["wait_ms"]["max"].get(),
            },
            "template": f"assets/{base_template_name(dict['combine_flow']['template'].get())}",
            "back_template": f"assets/{base_template_name(dict['combine_flow']['back_template'].get())}",
        },
        "periodic_stash_sort": {
            "interval_ms": {
                "min": dict["periodic_stash_sort"]["interval_ms"]["min"].get(),
                "max": dict["periodic_stash_sort"]["interval_ms"]["max"].get(),
            },
            "between_clicks_ms": {
                "min": dict["periodic_stash_sort"]["between_clicks_ms"]["min"].get(),
                "max": dict["periodic_stash_sort"]["between_clicks_ms"]["max"].get(),
            },
            "stash_template": f"assets/{base_template_name(dict['periodic_stash_sort']['stash_template'].get())}",
            "sort_template": f"assets/{base_template_name(dict['periodic_stash_sort']['sort_template'].get())}",
        },
        "randomization": {
            "click_offset_px": {
                "min": dict["randomization"]["click_offset_px"]["min"].get(),
                "max": dict["randomization"]["click_offset_px"]["max"].get(),
            },
        },
        "chest_check": {
            "templates": [
                {
                    "name": entry["name"],
                    "template": f"assets/{base_template_name(entry['template'].get())}",
                }
                for entry in dict["chest_check"]
            ],
        },
        "steps": [
            (
                {
                    "name": step["name"],
                    "template": f"assets/{base_template_name(step['template'].get())}",
                }
                if "template" in step
                else {"name": step["name"]}
            )
            for step in dict["steps"]
        ],
        "log_lvl": dict["log_lvl"].get(),
        "window_scale": dict["window_scale"].get(),
    }

    with open(CONFIG_PATH, "w", encoding="utf-8") as yaml_file:
        dump(data, yaml_file, sort_keys=False)


def random_timeout(range_dict):
    low = float(range_dict["min"].get() if hasattr(range_dict["min"], "get") else range_dict["min"])
    high = float(range_dict["max"].get() if hasattr(range_dict["max"], "get") else range_dict["max"])
    if low > high:
        low, high = high, low
    return round(random.uniform(low, high), 2)


def random_ms(range_dict):
    low = int(range_dict["min"].get() if hasattr(range_dict["min"], "get") else range_dict["min"])
    high = int(range_dict["max"].get() if hasattr(range_dict["max"], "get") else range_dict["max"])
    if low > high:
        low, high = high, low
    return random.randint(low, high)


def random_click_offset():
    offset = dict["randomization"]["click_offset_px"]
    low = int(offset["min"].get())
    high = int(offset["max"].get())
    if low > high:
        low, high = high, low
    return random.randint(low, high), random.randint(low, high)
