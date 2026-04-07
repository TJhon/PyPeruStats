from datetime import datetime


def _format_date_for_frequency(
    date_str: str, frequency: str, fmt: str = "%Y-%m-%d"
) -> str:
    """
    Convert a YYYY-MM-DD date string to the format expected by the BCRP API
    for the given frequency.

    Parameters
    ----------
    date_str:
        Date in ``fmt`` format (default ``%Y-%m-%d``).
    frequency:
        One of ``'D'``, ``'M'``, ``'Q'``, ``'A'``.
    fmt:
        strptime format of *date_str*.

    Returns
    -------
    str
        Date string formatted for the BCRP API endpoint.

    Examples
    --------
    >>> _format_date_for_frequency("2023-06-15", "D")
    '2023-06-15'
    >>> _format_date_for_frequency("2023-06-15", "M")
    '2023-06'
    >>> _format_date_for_frequency("2023-06-15", "Q")
    '2023-2'
    >>> _format_date_for_frequency("2023-06-15", "A")
    '2023'
    """
    dt = datetime.strptime(date_str, fmt)
    if frequency == "D":
        return dt.strftime("%Y-%m-%d")
    if frequency == "M":
        return dt.strftime("%Y-%m")
    if frequency == "Q":
        quarter = (dt.month - 1) // 3 + 1
        return f"{dt.year}-{quarter}"
    if frequency == "A":
        return dt.strftime("%Y")
    raise ValueError(f"Unknown frequency: {frequency!r}")
