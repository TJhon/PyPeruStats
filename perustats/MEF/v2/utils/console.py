from rich.console import Console


def get_console():
    return Console(
        force_terminal=not _is_jupyter(), width=100, emoji=False, soft_wrap=True
    )


def _is_jupyter():
    try:
        from IPython import get_ipython

        return get_ipython() is not None
    except Exception:
        return False


console = get_console()
