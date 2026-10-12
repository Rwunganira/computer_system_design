# Module 4. Clients and services

**Goal:** split VaxRecords into a separate service, see a remote call fail in a way a local call
never does, and make retries safe.

**Read in the book:** Chapter 4, "Enforcing Modularity with Clients and Services".

## Soft modularity and enforced modularity

In Module 1 you split the dashboard into load, compute and present modules. That is *soft*
modularity: the modules are functions in one program, so the boundaries hold only as long as every
module behaves. A function can write into another module's data, loop forever, or crash, and the
whole program goes with it. A bug in the dashboard's chart code can stop health workers from
recording doses.

*Enforced* modularity puts each module in its own program and lets them talk only by sending
*messages*. The **client** sends a request; the **service** does the work and sends a reply. The
client cannot touch the service's memory, and the service checks every request it receives. If
the dashboard crashes, VaxRecords keeps running: the failure is contained. The book calls this
the client/service organization, and it is how almost every system you use is built.

## Remote procedure call

Writing every message by hand is tedious, so we wrap it in something that looks like a function:
`client.record_dose(dose)` builds an HTTP request, sends it, waits, and decodes the reply. This is a
**remote procedure call (RPC)**, and the code that hides the messages is the **stub**. Here the
stub is `VaxClient`, and `requests` plus Flask do the packing and unpacking.

The danger is that an RPC *looks* like a local call but is not one. A local call runs once and then
returns or raises. A remote call can also:

- be slow, because the network or the service is busy;
- get no reply at all, because the request was lost, or the service crashed, or the **reply** was lost;
- run twice, if the client sends it again.

The hard case is the lost reply. The client waits, gives up after a timeout, and cannot tell
whether the dose was recorded. It must choose.

## At-least-once, at-most-once, exactly-once

| Semantics | What the client does | What can go wrong |
|---|---|---|
| **At-most-once** | send once, never retry | a lost request means a dose never recorded |
| **At-least-once** | retry until a reply arrives | a lost reply means the dose recorded twice |
| **Exactly-once** | retry, and the service suppresses duplicates | needs the service to remember what it has done |

At-least-once is fine for an *idempotent* request, one that has the same effect however many
times it runs: "set Amina's MCV1 date to 2 March" is idempotent; "add an MCV1 dose for Amina" is
not. For VaxRecords a duplicate is not harmless: the register says a child had a second measles
dose, coverage figures are inflated, and stock looks lower than it is.

The fix is to make a non-idempotent request idempotent. The client gives each dose a unique
**idempotency key** (a UUID) and sends the *same* key with every retry of that dose. The service
remembers the reply it sent for each key; when a retry arrives with a key it has seen, it replays
that reply instead of recording again. Retrying gives at-least-once delivery, duplicate
suppression gives at-most-once execution, and together they give the effect of exactly-once.

## Health running case

`vax_server.py` is VaxRecords as a Flask service. With `drop_rate=0.3` it saves the dose and then
stalls until the client has given up, which to the client is a lost reply. The stalls come from a
seeded random generator, so every run loses the same replies. `vax_client.py` is the client: a
naive version that retries, and one that adds an idempotency key. `rpc_demo.py` starts the service
in a background thread on a free localhost port and records the same ten doses with each client.

Things to notice:

- The same lost replies happen in both runs. Only the key changes the outcome.
- The key is created once per dose, outside the retry loop. A new key on each attempt would look
  like a new dose to the service.
- The service checks and records under a lock, because two retries can arrive at once.
- The service now has to remember keys. How long should it keep them? (Real services keep them for
  a day or so.) What happens if the service itself crashes and forgets them? That is Chapter 9.

## Exercises

1. `post_with_backoff`: time out after 2 seconds and retry with exponential backoff (0.5 s, 1 s,
   2 s, ...), so a struggling service is not flooded with retries.
2. `record_dose_checked`: implement the idempotency-key check on the server, including the case of
   a buggy client that reuses a key for a different dose (reply 409 Conflict). The provided
   duplicate-dose test runs a retrying client against your handler.
3. `dose_total_for_dashboard`: make the dashboard show "unavailable" instead of crashing when
   VaxRecords is down, and explain in a comment why the dashboard crashing no longer takes
   VaxRecords down with it. The comment is for you; pytest checks only the code.

## Run the example

```bash
python lessons/04_client_service/rpc_demo.py       # naive client, then idempotency keys (about 7 s)
python lessons/04_client_service/vax_server.py     # or run the service alone on port 5004
pytest lessons/04_client_service
```
