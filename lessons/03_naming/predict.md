# Predict, then run

Answer each question in a sentence before running `python lessons/03_naming/patient_resolver.py`.

1. Three clinics each give 200 patients local IDs starting from P-0001. How many different
   children can the name "P-0042" refer to, and how many does `clinic_a/P-0042` refer to?
2. There are 2,000 synthetic children, 16 given names, 12 family names and about 5 years of birth
   dates. Will "given name + family name + birth date" be unique for every child? Estimate how
   many collisions you expect.
3. In part 3 a child moves from Clinic A to Clinic B and their birth date is then corrected in the
   registry. Does Clinic A's name for the child see the correction? Would it if each clinic had
   stored its own copy of the record instead of a registry ID?
4. `create_app` builds `{district_name: district_id}` from 8 districts. How many entries will it
   have, and what will `GET /districts/Central/cases` return: an error, North Central, or South
   Central?
