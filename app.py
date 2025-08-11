
import pandas as pd

# Beispiel DataFrame
result_df = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})

# Korrigierter Excel-Export mit korrektem Indentationsblock
with pd.ExcelWriter('output.xlsx', engine='openpyxl') as writer:
    result_df.to_excel(writer, index=False)
