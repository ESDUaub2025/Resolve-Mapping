import pandas as pd

df = pd.read_csv('data/layers/English/Water_1.0.en.csv', encoding='utf-8-sig')
df.columns = [c.rstrip(': ') for c in df.columns]

print("DataFrame columns:")
for i, col in enumerate(df.columns):
    print(f"  {i}: {col}")

print("\nItertuples namedtuple fields:")
for row in df.itertuples(index=False):
    d = row._asdict()
    for key in list(d.keys()):
        print(f"  {key}")
    break
