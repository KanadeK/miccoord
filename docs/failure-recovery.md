# Failure recovery

MicCoord does not modify inputs or external systems. Recovery therefore means correcting the declared evidence or constraints and rerunning the same command.

## Exit 1: `CONFLICTS`

Read each conflict's `expression`, `target_mhz`, `product_mhz`, and `separation_khz`. Change the caller-owned carrier set, then rerun `audit`. Do not suppress a witness or reduce the guard merely to obtain `CLEAR`; change the model only when the actual coordination requirement changed.

## Exit 1: `INFEASIBLE`

The candidate pool was searched completely. The report's frequencies are the strongest compatible partial set encountered. Recovery requires a material input change: widen a permitted range, reduce the requested count, revisit a verified exclusion, or change a spacing/guard requirement based on real device and venue evidence.

## Exit 2: `EXHAUSTED`

The node budget ended before the search completed. This is not evidence of infeasibility. First rerun with a larger `max_search_nodes`; if runtime is unacceptable, reduce the candidate pool by using a coarser justified step or narrower caller-approved ranges. The maximum accepted budget is 5,000,000 nodes.

## Exit 2: invalid input or output

MicCoord reports the first boundary violation on standard error and leaves no partial output. Correct the named JSON/CSV field, missing file, encoding problem, or output parent directory. Unknown JSON fields are rejected so spelling mistakes cannot silently change a plan.

## A report is unexpectedly clear

A `CLEAR` audit proves only that the selected carriers do not violate the declared minimum spacing and third-order guard. Recheck that the input contains every active carrier, local rules permit transmission, the equipment supports the selected tuning range, and current on-site spectrum evidence is represented. MicCoord intentionally has no hidden regulatory, device, or environmental database.
