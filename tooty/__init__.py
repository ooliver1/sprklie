"""
Sphinx Theme 
~~~~~~~~~~~~
A sphinx theme with accessibility in mind.
:copyright: (c) 2021-present ooliver1
:license: MIT, see LICENSE for more details.
"""

# credit to tooty as I kinda took a decent chunk

from __future__ import annotations

__version__ = "0.0.0a"
__title__ = "tooty-theme"
__author__ = "Oliver Wilkes - ooliver1"
__license__ = "MIT"
__copyright__ = "Copyright (c) 2021-present Oliver Wilkes"


import os
import sys
import hashlib
import logging
from os import path
from pathlib import Path
from functools import lru_cache
from typing import Any, Iterator, Optional

from pygments.token import Text
from pygments.style import Style
from sphinx.application import Sphinx
from pygments.formatters import HtmlFormatter
from sphinx.highlighting import PygmentsBridge
from sphinx.builders.html import StandaloneHTMLBuilder

from .static._pygments.dark import CustomDarkStyle
from .static._pygments.light import CustomLightStyle


sys.path.insert(0, os.path.abspath("./_pygments"))

logger = logging.getLogger(__name__)

_KNOWN_STYLES_IN_USE: dict[str, Optional[Style]] = {
    "light": None,
    "dark": None,
}

PATH = (Path(__file__).parent).resolve()


def get_pygments_style_colors(
    style: Style, *, fallbacks: dict[str, str]
) -> dict[str, str]:
    background = style.background_color
    text_colors = style.style_for_token(Text)
    foreground = text_colors["color"]

    if not background:
        background = fallbacks["background"]

    if not foreground:
        foreground = fallbacks["foreground"]
    else:
        foreground = f"#{foreground}"

    return {"background": background, "foreground": foreground}


def pygments_monkeypatch_style(mod_name, cls):
    import sys
    import pygments.styles

    cls_name = cls.__name__
    mod = type(__import__("os"))(mod_name)
    setattr(mod, cls_name, cls)
    setattr(pygments.styles, mod_name, mod)
    sys.modules["pygments.styles." + mod_name] = mod
    from pygments.styles import STYLE_MAP

    STYLE_MAP[mod_name] = mod_name + "::" + cls_name


@lru_cache(maxsize=None)
def _asset_hash(path_: str) -> str:
    # so the user gets the latest css
    full_path = PATH / "static" / path_
    digest = hashlib.sha1(full_path.read_bytes()).hexdigest()

    return f"_static/{path_}?digest={digest}"


def _add_asset_hashes(static: list[str], add_digest_to: list[str]) -> None:
    for asset in add_digest_to:
        index = static.index("_static/" + asset)
        static[index].filename = _asset_hash(asset)


def _html_page_context(
    app: Sphinx,
    pagename: str,
    templatename: str,
    context: dict[str, Any],
    doctree: Any,
):
    if app.config.html_theme != "tooty":
        return

    if "css_files" in context:
        _add_asset_hashes(
            context["css_files"],
            ["css/tooty.css"],
        )

    context["tooty_version"] = __version__

    context["tooty_pygments"] = {
        "light": get_pygments_style_colors(
            _KNOWN_STYLES_IN_USE["light"],
            fallbacks=dict(
                foreground="black",
                background="white",
            ),
        ),
        "dark": get_pygments_style_colors(
            _KNOWN_STYLES_IN_USE["dark"],
            fallbacks=dict(
                foreground="white",
                background="black",
            ),
        ),
    }


def _builder_inited(app: Sphinx) -> None:
    if app.config.html_theme != "tooty":
        return
    if "tooty" in app.config.extensions:
        raise Exception(
            "Did you list it in the `extensions` in conf.py? "
            "If so, please remove it. Tooty does not work with non-HTML builders "
            "and specifying it as an `html_theme` is sufficient."
        )

    if not isinstance(app.builder, StandaloneHTMLBuilder):
        raise Exception(
            "Tooty is being used as an extension in a non-HTML build. "
            "This should not happen."
        )

    builder = app.builder
    assert builder, "what?"
    assert (
        builder.highlighter is not None
    ), "there should be a default style known to Sphinx"
    assert (
        builder.dark_highlighter is None
    ), "this shouldn't be a dark style known to Sphinx"
    update_known_styles_state(app)


def update_known_styles_state(app: Sphinx) -> None:
    global _KNOWN_STYLES_IN_USE

    _KNOWN_STYLES_IN_USE = {
        "light": _get_light_style(app),
        "dark": _get_dark_style(app),
    }


def _get_dark_style(app: Sphinx) -> Style:
    return app.builder.highlighter.formatter_args["style"]


def _get_light_style(app: Sphinx) -> Style:
    # HACK: begins here
    light_style = None
    try:
        if (
            hasattr(app.config, "_raw_config")
            and isinstance(app.config._raw_config, dict)
            and "pygments_light_style" in app.config._raw_config
        ):
            light_style = app.config._raw_config["pygments_light_style"]
    except (AttributeError, KeyError) as e:
        logger.warn(
            (
                "tooty could not determine the value of `pygments_light_style`. "
                "Falling back to using the value provided by Sphinx.\n"
                "Caused by %s"
            ),
            e,
        )

    if light_style is None:
        light_style = app.config.pygments_light_style

    return PygmentsBridge("html", light_style).formatter_args["style"]


def _get_styles(formatter: HtmlFormatter, *, prefix: str) -> Iterator[str]:
    for line in formatter.get_linenos_style_defs():
        yield f"{prefix} {line}"
    yield from formatter.get_background_style_defs(prefix)
    yield from formatter.get_token_style_defs(prefix)


def get_pygments_stylesheet() -> str:
    # sphinx cant handle dark theme with pygments as of now
    light_formatter = HtmlFormatter(style=_KNOWN_STYLES_IN_USE["light"])
    dark_formatter = HtmlFormatter(style=_KNOWN_STYLES_IN_USE["dark"])

    lines: list[str] = []

    lines.extend(_get_styles(light_formatter, prefix=".highlight"))

    dark_prefix = 'body[data-theme="dark"] .highlight'
    lines.extend(_get_styles(dark_formatter, prefix=dark_prefix))

    not_light_prefix = 'body:not([data-theme="light"]) .highlight'
    lines.append("@media (prefers-color-scheme: dark) {")
    lines.extend(_get_styles(dark_formatter, prefix=not_light_prefix))
    lines.append("}")

    return "\n".join(lines)


def _overwrite_pygments_css(
    app: Sphinx,
    exception: Optional[Exception],
) -> None:
    if exception is not None:
        return

    assert app.builder
    with open(os.path.join(app.builder.outdir, "_static", "pygments.css"), "w") as f:
        f.write(get_pygments_stylesheet())


def setup(app: Sphinx) -> dict[str, str | bool]:
    app.add_html_theme("tooty", str(PATH))
    app.add_config_value(
        "pygments_light_style",
        default="lighte",
        rebuild="env",
        types=[str],
    )
    pygments_monkeypatch_style("darke", CustomDarkStyle)
    pygments_monkeypatch_style("lighte", CustomLightStyle)

    app.connect("html-page-context", _html_page_context)
    app.connect("builder-inited", _builder_inited)
    app.connect("build-finished", _overwrite_pygments_css)

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
        "version": __version__,
    }
