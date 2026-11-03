# N-M1-11: terminal target probability

Source: Model 5 / N-M1-11 in the model-limits and known-errors registers at
research ref `2da6469d8b3d45eab61d682555ff630ce1f564f7`. Product baseline `ec98cbef`.

The existing engine computes `mean(terminal >= target)`. Its narrative called
this “Probability of reaching” the target, and both interfaces labeled it
`P(target)`. A path can cross a target and then finish below it; those events
have different probabilities. The same terminal comparison also applies when
the target is below spot.

The narrative now says “finishing at or above [price] after [N] sessions”.
Flet and PyQt6 use `P(terminal ≥ target)`; native notes identify the final
session, and Flet AI input adds an explicit terminal-event definition.
The engine's module description is corrected. No function, path generation,
comparison operator, probability or numerical result is changed. Absent target
still produces `None`. ResearchRun's existing seven-metric schema, parameters,
`NOT_RUN` verdict and partial reproducibility remain unchanged; this patch
does not expand the persisted ResearchRun contract.

Validation (synthetic/injected, requests blocked):

`python -m unittest tests.terminal_target_acceptance tests.desktop_acceptance.NativeDesktopTests.test_terminal_target_label_and_notes_preserve_research_contract -v`

Five tests cover paths crossing above then finishing below the target, targets
below spot, exact equality, missing target, actual Flet tile/AI payload and
offscreen native worker/result notes. The synthetic crossing case has 50%
pathwise hits and 0% terminal success; the lower/equal target cases have 100%
pathwise hits and 50% terminal success. Every Monte Carlo function/class has
the same AST as the baseline. CI includes the new focused module and native
test on Windows and Ubuntu. Live-provider and actual Windows manual checks
are separate and were not performed.

The queue now records 7/67 corrected groups, 60 remaining groups, 14 observation
model rows and 15 ambiguous mappings. Historical probe/PR counts remain
historical evidence, not claims of current totals.
