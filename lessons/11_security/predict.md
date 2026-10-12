# Predict, then run

Answer each question in a sentence before running `python lessons/11_security/secure_vax_api.py`.

1. Amina works in North-Central (N-CEN), about one district in five by population. Of the 30 patient
   IDs she tries against the insecure version, roughly how many records from other districts leak?
2. The secure version answers 403 both for a record that does not exist and for one Amina may not
   see. Why not return 404 for the missing one?
3. Hashing all three synthetic passwords with scrypt happens when the module is imported. Will you
   notice the delay? Why is a slow hash a feature here, and where would it become a problem?
4. An attacker captures SurveilLite's genuine signed request and replays it 10 minutes later,
   unchanged. The signature is still valid. What stops it? What if they replay it after 10 seconds?
