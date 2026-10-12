# Module 11. Information security

**Goal:** protect VaxRecords' patient data with the guard model (authenticate, authorize, audit
every request) and know what hashing, MACs and encryption each do and do not protect.

**Read in the book:** Chapter 11, *Information Security* (part of the online Part II): the
security design principles, the guard model, authentication, authorization, and cryptographic
primitives.

## Security is a negative goal

Most of the course has asked "does the system do X?". Security asks "can *anyone* make the system do
something it should not, ever?". The book stresses how hard that is: you cannot test every
adversary, so you rely on a few design principles and a simple, checkable structure.

**The principles**, and where they show up in VaxRecords:

| Principle | In plain language | In this module |
|---|---|---|
| Open design | Security must not depend on attackers not knowing the design | scrypt and HMAC are public algorithms; only keys and passwords are secret |
| Fail-safe defaults | Deny unless explicitly allowed | an unknown role reads nothing |
| Least privilege | Give each user the least access their job needs | a district officer sees one district |
| Complete mediation | Check every access, every time | `before_request` authenticates all routes; every read is authorized |
| Economy of mechanism | Keep the guard small enough to review | one `can_read` function decides record access |
| Psychological acceptability | If security is painful, people work around it | nurses who find login slow will share one account |

## The guard model

Every request to a protected resource passes a **guard** that does three things:

1. **Authenticate:** who is asking? VaxRecords checks a password, then issues a random token for
   later requests. Passwords are never stored: the server keeps a random **salt** and a **slow hash**
   (`hashlib.scrypt`) of salt plus password. If the user table leaks, the salt stops one precomputed
   table from cracking everyone, and the slowness makes each guess expensive.
2. **Authorize:** may *this* principal do *this* to *this* object? Being logged in is not the
   same as being allowed. The starting version, `vax_api_insecure.py`, makes exactly this mistake:
   any logged-in officer can change the ID in `/patients/<id>` and read any child in the country.
   This is called an insecure direct object reference (IDOR), and it is one of the most common real
   web bugs. The fix is complete mediation: compare the record's district to the user's on every read.
3. **Audit:** record who asked for what, and the answer, in a log that the people being audited
   cannot rewrite. An audit log does not prevent misuse; it makes misuse discoverable and deters it.
   Exercise 2 makes the log **tamper-evident** by chaining hashes: each entry includes the hash of
   the one before, so editing, deleting or reordering any entry breaks every link after it. Keep the
   latest hash somewhere else (another server, a printed report) or an attacker can cut entries off
   the end unnoticed.

## What each cryptographic tool protects

- A **hash** (SHA-256) detects accidental or unkeyed change: anyone can recompute it, so it proves
  integrity only when the hash itself is kept safe, as with the head of the audit chain.
- A **message authentication code** (HMAC) is a hash keyed with a shared secret. When SurveilLite
  asks VaxRecords for coverage figures it signs the method, path, timestamp and body; VaxRecords
  recomputes the HMAC and compares with `hmac.compare_digest` (constant time, so the comparison
  does not leak how many characters matched). An altered body or a guessed key fails. The timestamp
  limits **replay** to a short window; a nonce would close it fully.
- **Encryption** protects confidentiality: who can *read* the data. A MAC does not hide anything,
  and encryption alone does not stop tampering. In production VaxRecords would run behind TLS,
  which provides both on the wire; this module runs on plain localhost HTTP to keep the code short.

All users and passwords in this module are synthetic test values. Real keys and passwords never
belong in source code: load them from the environment or a secrets manager.

## Run the example

```bash
python lessons/11_security/secure_vax_api.py
```

It starts both versions of VaxRecords on free localhost ports. Amina, a North-Central district
officer, walks the patient IDs: the insecure version hands her records from other districts, the
secure version refuses and audits each attempt. Then SurveilLite makes one genuine signed request,
followed by an altered, a replayed and a forged one. Answer `predict.md` first, then:

```bash
pytest lessons/11_security
```
