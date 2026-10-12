# Predict, then run

Answer each question in a sentence before running `python lessons/04_client_service/rpc_demo.py`.

1. The service loses 30% of its replies after saving the dose, and the naive client retries until
   it gets a reply. For 10 doses, will the service record fewer than 10, exactly 10, or more than
   10? Could any dose be recorded three times?
2. Both runs use the same seed, so the same replies are lost. Will the client with idempotency keys
   see fewer timeouts than the naive client, the same number, or more?
3. Suppose `VaxClient` created a new idempotency key inside the retry loop, once per attempt. How
   many doses would the service record then?
4. Change the client so it never retries (`retries=0`). Which semantics do you get, and what does
   the client report for the doses whose replies were lost?
