#!/usr/bin/env python3
"""A command line tool for extracting text and images from PDF and
output it to plain text, html, xml or tags.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from pdf2zh_next.config import ConfigManager
from pdf2zh_next.high_level import do_translate_file_async
from pdf2zh_next.utils.profiler import PerformanceTracer
from pdf2zh_next.utils.profiler import set_global_tracer

__version__ = "2.6.4"

logger = logging.getLogger(__name__)


def find_all_files_in_directory(directory_path):
    """
    Recursively search all PDF files in the given directory and return their paths as a list.

    :param directory_path: str, the path to the directory to search
    :return: list of PDF file paths
    """
    directory_path = Path(directory_path)
    # Check if the provided path is a directory
    if not directory_path.is_dir():
        raise ValueError(f"The provided path '{directory_path}' is not a directory.")

    file_paths = []

    # Walk through the directory recursively
    for root, _, files in os.walk(directory_path):
        for file in files:
            # Check if the file is a PDF
            if file.lower().endswith(".pdf"):
                # Append the full file path to the list
                file_paths.append(Path(root) / file)

    return file_paths


async def main() -> int:
    from rich.logging import RichHandler

    logging.basicConfig(level=logging.INFO, handlers=[RichHandler()])

    # measure initialize_config
    t_init_tracer = PerformanceTracer(enabled=False)
    with t_init_tracer.section("initialize_config"):
        settings = ConfigManager().initialize_config()
    if settings.basic.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # disable httpx, openai, httpcore, http11 logs
    logging.getLogger("httpx").setLevel("CRITICAL")
    logging.getLogger("httpx").propagate = False
    logging.getLogger("openai").setLevel("CRITICAL")
    logging.getLogger("openai").propagate = False
    logging.getLogger("httpcore").setLevel("CRITICAL")
    logging.getLogger("httpcore").propagate = False
    logging.getLogger("http11").setLevel("CRITICAL")
    logging.getLogger("http11").propagate = False

    for v in logging.Logger.manager.loggerDict.values():
        if getattr(v, "name", None) is None:
            continue
        if (
            v.name.startswith("pdfminer")
            or v.name.startswith("peewee")
            or v.name.startswith("httpx")
            or "http11" in v.name
            or "openai" in v.name
            or "pdfminer" in v.name
        ):
            v.disabled = True
            v.propagate = False

    logger.debug(f"settings: {settings}")

    if settings.basic.version:
        print(f"pdf2zh-next version: {__version__}")
        return 0

    if settings.basic.gui:
        from pdf2zh_next.gui import setup_gui

        setup_gui(
            auth_file=settings.gui_settings.auth_file,
            welcome_page=settings.gui_settings.welcome_page,
            server_port=settings.gui_settings.server_port,
        )
        return 0

    # auto-enable profiling in debug mode
    if settings.basic.debug:
        if not getattr(settings.basic, "profile", False):
            settings.basic.profile = True
        if not getattr(settings.basic, "profile_file", None):
            default_profile_dir = Path(".perf")
            default_profile_dir.mkdir(parents=True, exist_ok=True)
            settings.basic.profile_file = (
                default_profile_dir
                / f"profile-{datetime.now().strftime('%Y%m%d-%H%M%S')}.jsonl"
            ).as_posix()
        if not getattr(settings.basic, "cprofile", False):
            settings.basic.cprofile = True
        if not getattr(settings.basic, "cprofile_dir", None):
            settings.basic.cprofile_dir = Path(".perf").as_posix()

    # setup tracer if enabled
    tracer_enabled = bool(getattr(settings.basic, "profile", False))
    profile_file = getattr(settings.basic, "profile_file", None)
    tracer = PerformanceTracer(
        enabled=tracer_enabled,
        output=Path(profile_file) if (tracer_enabled and profile_file) else None,
    )
    set_global_tracer(tracer)

    assert len(settings.basic.input_files) >= 1, "At least one input file is required"
    with tracer.section("cli_run_total"):
        await do_translate_file_async(settings, ignore_error=True)

    # print summary if enabled
    if tracer.enabled:
        for line in tracer.summary_lines():
            logger.info(f"[perf] {line}")
    return 0


def cli():
    # Ensure PyInstaller-frozen multiprocessing works reliably on macOS
    import multiprocessing as mp

    if sys.platform == "darwin":
        try:
            mp.set_start_method("spawn", force=True)
        except RuntimeError:
            pass
        mp.freeze_support()

    # Ensure tiktoken plugins are importable in frozen runtime
    try:
        # Prefer the internal plugin namespace shipped with tiktoken 0.11+
        import tiktoken_ext.openai_public  # noqa: F401
    except Exception:
        pass

    sys.exit(asyncio.run(main()))


if __name__ == "__main__":
    cli()
