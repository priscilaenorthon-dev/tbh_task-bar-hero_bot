import utils.global_variables as gv
from functionality.image_search import find_template
from utils.config import (
    chest_check_entries,
    dict,
    random_click_offset,
    random_ms,
    random_timeout,
    step_entries,
    template_path_for,
)
from wrappers.logging_wrapper import debug, info
from wrappers.win32api_wrapper import (
    click_mouse_with_coordinates,
    right_click_mouse_with_coordinates,
    space_bar,
)


def _steps():
    return step_entries()


def stash_loop():
    if not gv.continue_stash:
        gv.status_message = "Stopped"
        _update_status_label()
        return

    steps = _steps()
    step = steps[gv.current_step_index]
    region = _search_region()
    threshold = dict["matching"]["threshold"].get()

    if step["name"] == "open_chest":
        _handle_open_chest_step(region, threshold)
        return

    match = find_template(region, step["template"], threshold)

    if match is None:
        gv.status_message = f"Waiting for {step['name']}..."
        debug(gv.status_message)
        _update_status_label()
        gv.root.after(random_ms(dict["timeouts"]["loop_ms"]), stash_loop)
        return

    center_x, center_y, score = match
    info(f"Found {step['name']} at ({center_x}, {center_y}) score={score:.3f}")
    _click_at(center_x, center_y)

    if step["name"] == "auto_fill":
        gv.combine_check_pending = True
        wait_ms = random_ms(dict["combine_flow"]["wait_ms"])
        gv.status_message = (
            f"Auto fill clicked, checking for combine in {wait_ms / 1000:.1f}s..."
        )
        _update_status_label()
        gv.root.after(wait_ms, _check_combine_after_auto_fill)
        return

    _advance_to_next_step(step["name"])
    delay_ms = int(random_timeout(dict["timeouts"]["after_click"]) * 1000)
    gv.root.after(delay_ms, stash_loop)


def _handle_open_chest_step(region, threshold):
    for chest in chest_check_entries():
        match = find_template(region, chest["template"], threshold)
        if match is None:
            continue

        center_x, center_y, score = match
        info(
            f"Found {chest['name']} at ({center_x}, {center_y}) score={score:.3f}, right-clicking"
        )
        _right_click_at(center_x, center_y)
        _advance_to_next_step("open_chest")
        delay_ms = int(random_timeout(dict["timeouts"]["after_click"]) * 1000)
        gv.root.after(delay_ms, stash_loop)
        return

    gv.status_message = "Waiting for boss_chest or chest icon..."
    debug(gv.status_message)
    _update_status_label()
    gv.root.after(random_ms(dict["timeouts"]["loop_ms"]), stash_loop)


def _check_combine_after_auto_fill():
    gv.combine_check_pending = False

    if not gv.continue_stash:
        gv.status_message = "Stopped"
        _update_status_label()
        return

    region = _search_region()
    threshold = dict["matching"]["threshold"].get()
    combine_template = template_path_for(dict["combine_flow"]["template"])
    combine_match = find_template(region, combine_template, threshold)

    if combine_match is None:
        info("Combine not present, continuing normal stash flow")
        gv.current_step_index = _step_index("stash_all")
        gv.status_message = "No combine prompt, continuing to stash_all"
        _update_status_label()
        delay_ms = int(random_timeout(dict["timeouts"]["after_click"]) * 1000)
        gv.root.after(delay_ms, stash_loop)
        return

    center_x, center_y, score = combine_match
    info(f"Found combine at ({center_x}, {center_y}) score={score:.3f}")
    _click_at(center_x, center_y)

    back_template = template_path_for(dict["combine_flow"]["back_template"])
    back_match = find_template(region, back_template, threshold)

    if back_match is None:
        gv.status_message = "Combine clicked, waiting for back_arrow..."
        debug(gv.status_message)
        _update_status_label()
        gv.root.after(random_ms(dict["timeouts"]["loop_ms"]), _click_back_after_combine)
        return

    back_x, back_y, back_score = back_match
    info(f"Found back_arrow at ({back_x}, {back_y}) score={back_score:.3f}")
    _click_at(back_x, back_y)
    _restart_loop("Combine flow complete")


def _click_back_after_combine():
    if not gv.continue_stash:
        gv.status_message = "Stopped"
        _update_status_label()
        return

    region = _search_region()
    threshold = dict["matching"]["threshold"].get()
    back_template = template_path_for(dict["combine_flow"]["back_template"])
    back_match = find_template(region, back_template, threshold)

    if back_match is None:
        gv.status_message = "Waiting for back_arrow after combine..."
        debug(gv.status_message)
        _update_status_label()
        gv.root.after(random_ms(dict["timeouts"]["loop_ms"]), _click_back_after_combine)
        return

    back_x, back_y, back_score = back_match
    info(f"Found back_arrow at ({back_x}, {back_y}) score={back_score:.3f}")
    _click_at(back_x, back_y)
    _restart_loop("Combine flow complete")


def _restart_loop(message):
    gv.current_step_index = 0
    gv.status_message = f"{message}, restarting from open_chest"
    _update_status_label()
    delay_ms = int(random_timeout(dict["timeouts"]["after_click"]) * 1000)
    gv.root.after(delay_ms, stash_loop)


def _advance_to_next_step(current_name):
    steps = _steps()
    gv.current_step_index = (gv.current_step_index + 1) % len(steps)
    next_step = steps[gv.current_step_index]
    gv.status_message = f"Clicked {current_name}, next: {next_step['name']}"
    _update_status_label()


def _step_index(step_name):
    for index, step in enumerate(_steps()):
        if step["name"] == step_name:
            return index
    raise ValueError(f"Unknown step: {step_name}")


def _search_region():
    return (
        dict["search_region"]["x"].get(),
        dict["search_region"]["y"].get(),
        dict["search_region"]["width"].get(),
        dict["search_region"]["height"].get(),
    )


def _click_at(x, y):
    offset_x, offset_y = random_click_offset()
    click_mouse_with_coordinates(x + offset_x, y + offset_y)


def _right_click_at(x, y):
    offset_x, offset_y = random_click_offset()
    right_click_mouse_with_coordinates(x + offset_x, y + offset_y)


def reset_stash_state():
    gv.current_step_index = 0
    gv.combine_check_pending = False
    gv.status_message = "Running"


def start_periodic_stash_sort():
    periodic_stash_sort_loop()


def periodic_stash_sort_loop():
    if not gv.continue_stash:
        return

    region = _search_region()
    threshold = dict["matching"]["threshold"].get()
    stash_template = template_path_for(dict["periodic_stash_sort"]["stash_template"])
    sort_template = template_path_for(dict["periodic_stash_sort"]["sort_template"])

    stash_match = find_template(region, stash_template, threshold)
    if stash_match is not None:
        stash_x, stash_y, stash_score = stash_match
        info(f"Periodic: found stash_all at ({stash_x}, {stash_y}) score={stash_score:.3f}")
        _click_at(stash_x, stash_y)

        gap_ms = random_ms(dict["periodic_stash_sort"]["between_clicks_ms"])
        gv.root.after(gap_ms, _periodic_sort_click, region, threshold, sort_template)
        return

    debug("Periodic: stash_all not found, skipping")
    _periodic_finish_cycle()


def _periodic_sort_click(region, threshold, sort_template):
    if not gv.continue_stash:
        return

    sort_match = find_template(region, sort_template, threshold)
    if sort_match is not None:
        sort_x, sort_y, sort_score = sort_match
        info(f"Periodic: found sort at ({sort_x}, {sort_y}) score={sort_score:.3f}")
        _click_at(sort_x, sort_y)
    else:
        debug("Periodic: sort not found after stash_all")

    _periodic_finish_cycle()


def _periodic_finish_cycle():
    if not gv.continue_stash:
        return

    interval_ms = random_ms(dict["periodic_stash_sort"]["interval_ms"])
    info(f"Periodic: next cycle in {interval_ms / 1000:.1f}s")
    space_bar()
    info("Periodic: Pressed space bar")
    gv.root.after(interval_ms, periodic_stash_sort_loop)


def _update_status_label():
    if gv.status_label is not None:
        gv.status_label.configure(text=gv.status_message)
