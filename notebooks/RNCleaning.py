import pandas as pd
import numpy as np


d1 = pd.read_csv("NYC_school_speeding.csv")
print(d1)
d2 = pd.read_csv("Nys_traffic_violations_historical.csv")

#d1['violation_date'] = pd.to_datetime(d1['violation_year'].astype(str) + "-" + d1['violation_month'].astype(str).str.zfill(2),format ='%Y-%m')
#d1.drop(columns=['violation_year','violation_month'])
#d2['violation_date'] = pd.to_datetime(d2['violation_date'])





