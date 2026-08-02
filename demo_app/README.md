# Sentinel Shop

Observable FastAPI shop containing one intentional defect: `SAVE10` plus region `TN` causes a 500 because a legacy nullable tax rate participates in Decimal multiplication. SentinelOps must reproduce and patch it in isolation.
