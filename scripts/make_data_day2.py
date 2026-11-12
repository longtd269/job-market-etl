import pandas as pd
from job_etl.config import RAW_DATA_PATH

df = pd.read_csv(RAW_DATA_PATH)

day2 = df.iloc[300:].copy()
day2["created_date"] = "2023-08-02"
day2["link_description"] = day2["link_description"].str.replace(
    "ta_source=JobSearchList_LinkDetail", "ta_source=Homepage")
day2.iloc[:5, day2.columns.get_loc("salary")] = "50 - 60 triệu"

new = df.iloc[:50].copy()
new["created_date"] = "2023-08-02"
new["link_description"] = [f"https://www.topcv.vn/viec-lam/tin-moi-{i}/9{i:06d}.html"
                           for i in range(50)]
pd.concat([day2, new]).to_csv("data/raw/jobs_2023-08-02.csv", index=False)
print("Đã ghi", len(day2) + len(new), "dòng")