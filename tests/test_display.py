"""Window sizing across the range of Mac displays (sizes in points, as macOS
reports them) and other common screens."""

import pytest

from src import display

# (name, desktop size in points)
MACS = [
    ("MacBook Air 13 (default scaling)", (1470, 956)),
    ("MacBook Air 13 (more space)", (1680, 1050)),
    ("MacBook Air 13 (larger text)", (1280, 800)),
    ("MacBook Pro 14", (1512, 982)),
    ("MacBook Pro 16", (1728, 1117)),
    ("MacBook Pro 16 (more space)", (2056, 1329)),
    ("iMac 24", (2240, 1260)),
    ("Studio Display / 5K external", (2560, 1440)),
    ("Pro Display XDR", (3008, 1692)),
    ("4K external (looks like 1080p)", (1920, 1080)),
    ("4K external (more space)", (2560, 1440)),
    ("Ultrawide 34", (3440, 1440)),
    ("Old 13 inch", (1440, 900)),
    ("Old 11 inch Air", (1366, 768)),
]


@pytest.mark.parametrize("name,desktop", MACS)
def test_the_default_window_fits_the_screen_and_is_comfortable(name, desktop):
    usable = display.usable_area(desktop, mac=True)
    width, height = display.default_window_size(usable)
    assert width <= usable[0] and height <= usable[1], name
    assert width >= display.MIN_SIZE[0] and height >= display.MIN_SIZE[1] or usable[1] < display.MIN_SIZE[1]
    assert width * 100 // height in range(150, 175) or desktop[0] / desktop[1] > 1.7 or usable[1] < 700   # near 16:10
    assert width <= desktop[0] * 0.95 and height <= desktop[1] * 0.92, name              # not covering everything


@pytest.mark.parametrize("name,desktop", MACS)
def test_every_offered_resolution_fits_and_the_list_is_sensible(name, desktop):
    usable = display.usable_area(desktop, mac=True)
    options = display.resolution_options(usable)
    assert options == sorted(options, key=lambda s: (s[0] * s[1], s[0]))
    assert len(options) == len(set(options)) and len(options) >= 2
    for width, height in options:
        assert width <= usable[0] and height <= usable[1], (name, (width, height))
    assert display.default_window_size(usable) in options
    assert display.clamp_size(usable, usable) in options                   # "fit the screen"


def test_physical_pixel_sizes_are_never_offered_on_a_retina_screen():
    """list_modes() on a 14-inch MacBook Pro returns 3024x1964, twice the
    screen's width in points; offering it would make a window that cannot fit."""
    usable = display.usable_area((1512, 982), mac=True)
    assert (3024, 1964) not in display.resolution_options(usable)
    assert all(w <= 1512 for w, _ in display.resolution_options(usable))


def test_a_saved_size_from_a_bigger_monitor_is_pulled_back_onto_this_screen():
    laptop = display.usable_area((1512, 982), mac=True)
    assert display.clamp_size((3440, 1440), laptop) == (1512, laptop[1])
    assert display.clamp_size((300, 200), laptop) == display.MIN_SIZE          # and not absurdly small
    assert display.clamp_size((1280, 800), laptop) == (1280, 800)             # a fine size is untouched


def test_a_screen_smaller_than_the_minimum_wins_over_the_minimum():
    tiny = (900, 500)
    assert display.clamp_size((1280, 800), tiny) == (900, 500)


def test_the_usable_area_leaves_room_for_the_menu_bar_dock_and_title_bar():
    usable = display.usable_area((1512, 982), mac=True)
    assert usable[0] == 1512
    assert usable[1] == 982 - display.MENU_BAR - display.DOCK - display.TITLE_BAR
    assert display.usable_area((1920, 1080), mac=False)[1] < 1080


def test_the_current_size_is_kept_in_the_list_so_the_menu_can_show_it():
    usable = display.usable_area((2560, 1440), mac=True)
    odd = (1333, 777)
    assert odd in display.resolution_options(usable, current=odd)


def test_stars_scale_with_the_window_and_stay_bounded():
    assert display.star_count((1280, 720)) == 100
    assert display.star_count((2560, 1440)) == 400
    assert display.star_count((7680, 4320)) == 500                           # capped
    assert display.star_count((320, 240)) == 50                              # never empty


def test_desktop_size_always_returns_something_usable():
    width, height = display.desktop_size()
    assert width > 0 and height > 0
    assert display.backing_scale() >= 1.0


def test_next_resolution_steps_through_sizes_that_fit_and_wraps(monkeypatch):
    from src.settings import Settings
    monkeypatch.setattr(display, "desktop_size", lambda index=0: (2240, 1260))
    settings = Settings()
    options = display.resolution_options(display.usable_area((2240, 1260)))

    settings.window_width, settings.window_height = options[0]
    assert settings.next_resolution(+1) == options[1]
    assert settings.next_resolution(-1) == options[-1]                       # wraps to the largest
    settings.window_width, settings.window_height = options[-1]
    assert settings.next_resolution(+1) == options[0]                        # wraps to the smallest


def test_next_resolution_from_a_dragged_odd_size_goes_to_the_nearest_listed_size(monkeypatch):
    from src.settings import Settings
    monkeypatch.setattr(display, "desktop_size", lambda index=0: (2560, 1440))
    settings = Settings()
    settings.window_width, settings.window_height = 1333, 777
    bigger, smaller = settings.next_resolution(+1), settings.next_resolution(-1)
    assert bigger[0] * bigger[1] > 1333 * 777 > smaller[0] * smaller[1]
    options = display.resolution_options(display.usable_area((2560, 1440)))
    assert bigger in options and smaller in options
    assert bigger == min((o for o in options if o[0] * o[1] > 1333 * 777), key=lambda o: o[0] * o[1])
