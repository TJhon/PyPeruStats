from ..pyPeruStats import BCRPDataProcessor


# Ejemplo de uso

diarios = ["PD38032DD", "PD04699XD"]
mensuales = ["RD38085BM", "RD38307BM"]
trimestrales = ["PD37940PQ", "PN38975BQ"]
anuales = [
    "PM06069MA",
    "PM06078MA",
    "PM06101MA",
    "	PM06088MA",
    "PM06087MA",
    "	PM06086MA",
    "	PM06085MA",
    "	PM06084MA",
    "	PM06083MA",
    "	PM06082MA",
    "	PM06081MA",
    "	PM06070MA",
]
# print(len(anuales))
all_freq = diarios + mensuales + trimestrales + anuales
# print(all_freq)
processor = BCRPDataProcessor(all_freq, "2002-01-02", "2023-01-01", parallel=True)
data = processor.process_data(save_sqlite=True)
# dataframes
print(data.get("A"))  # anuales
print(data.get("Q"))  # trimestrales
print(data.get("M"))  # mensuales
print(data.get("D"))  #
