# Predict, then run

Answer each question in a sentence before running `python lessons/07_networks/sms_reports.py`.

1. The channel loses 20% of texts and duplicates 10%. With fire and forget, will a district's
   total be too low, too high, or could it be either? Which way will it lean on average?
2. With sequence numbers, ACKs and retransmission but *no* duplicate suppression, will the totals
   be correct? If not, too high or too low?
3. 480 reports are sent reliably over that channel, and ACKs travel over a channel that is just as
   lossy. Roughly how many texts will the clinics send in total?
4. Messages arrive out of order. Does the district office need to put them back in order to get
   correct totals? What kind of report would make order matter?
