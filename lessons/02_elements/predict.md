# Predict, then run

Answer each question in a sentence before running `python lessons/02_elements/case_definition.py`.

1. The rule is `fever AND (rash OR cough) AND age < 15`. When the interpreter traces a record where
   fever, rash and cough are all true, will it ever evaluate `cough`? Why or why not?
2. The record interpreter and the DataFrame interpreter evaluate the same tree over 20,000
   records. Will they find the same number of cases? Which do you expect to be faster, and by
   roughly how much: 2 times, 10 times, 100 times?
3. `fever AND rash OR cough` finds far more cases than `fever AND rash`. Before running, write the
   tree the parser will build for it. Is it what an epidemiologist writing the rule meant?
4. `tokenize` already treats `NOT` as a keyword. What happens if you call
   `parse("NOT fever")` before doing Exercise 1: a wrong answer, or an error? Which would you rather
   have in a surveillance system?
