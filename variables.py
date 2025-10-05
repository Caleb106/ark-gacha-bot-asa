import screen

data = {
    "transfer_all_from_x": 1935,
    "transfer_all_y": 270,
    "transfer_all_inventory_x": 550,
    "drop_all_x": 610,
    "search_inventory_x": 320,
    "search_object_x": 1680,
    "dedi_withdraw_x": 1290,
    "dedi_withdraw_y": 1118,
    "search_bar_bed_y": 1300,
    "search_bar_bed_dead_x": 300,
    "search_bar_bed_alive_x": 500,
    "spawn_button_x": 2200,
    "spawn_button_y": 1300,
    "implant_eat_x": 295,
    "implant_eat_y": 380,
    "radical_laydown_x": 1550,
    "radical_laydown_y": 620,
    "first_bed_slot_x": 450,
    "first_bed_slot_y": 300,
    "close_inv_x": 2400,
    "close_inv_y": 90,
    "inv_slot_start_x": 230,
    "inv_slot_start_y": 315,
    "inv_slot_end_x": 350,
    "inv_slot_end_y": 435,
    "buff_button_x": 1280,
    "buff_button_y": 1180,
    "drop_all_obj_x": 1978,
    "back_button_tp_x": 240,
    "back_button_tp_y": 1285
}

def get_pixel_loc(location):
    base = data.get(location)
    if screen.screen_resolution == 1080:
        base = round(base * 0.75)  # keep your 1080 scaling
    # center offset for 3440×1440
    if screen.screen_resolution == 1440 and screen.mon["width"] > 2560:
        if location.endswith("_x"):
            return base + screen.ultra_offset_x
    return base
