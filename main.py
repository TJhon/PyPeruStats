from perustats import print_tree

print_tree(
    ".",
    exclude_extensions=[".egg-info"],
    exclude_dirs=[".venv", "datos_inei", "__pycache__", ".git"],
)

# steps

# root: python -m pip install -e .
# probar local:  python -c "import pyperustats; print(pyperustats.__version__)"
# pip build: python -m pip install build
# build: python -m build
# twine: python -m pip install twine
# upload twine: twine upload dist/*

from perustats import BCRPDataSeries, BCRPSeries

series = BCRPSeries(
    [
        " RD16085DA",
        "PD04657MD",
        "PD04646PD",
        "RD13761DM",
        "RD13805DM",
        "      RD13845DM",
        "RD15478DQ",
        "RD14266DQ",
        "CD10401DA",
        "CD10422DA",
        "fakecodeA",
    ],
    start_date="2000-01-02",
    end_date="2020-01-01",
)
data = BCRPDataSeries(series).fetch_data()

for freq in data.result.keys():
    print(data.result.get(freq))
