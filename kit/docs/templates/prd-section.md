## NN. Step N · <Name>

<What this step is and why it exists, in 3 to 6 lines of product language. Who triggers it, what they expect.>

<How it works, with one concrete example: "A customer <does X> → the system <does Y>, and <Z> is stored.">

> [!IMPORTANT]
> <Something a reader must not miss: an approved amendment, a dependency on another step. Delete when there is none.>

> [!CAUTION]
> **<A verified defect, in one line> *(checked in code)***
>
> <What happens and to whom, with the evidence by file and symbol. Delete when there is none.>

| How it ends | Variant | What the user experiences | Final state | Reaches <consumer>? |
|---|---|---|---|---|
| <outcome> | <all or variant> | <experience> | <STATE> | <yes or no> |

The Example column is optional (four columns stay valid) but required for a rule with a number, a branch or a failure path. A rule that comes only from documents is `*(proposed)*` with Source `planned`.

| ID | Rule | Source | Change via | Example |
|---|---|---|---|---|
| PFX-01 | <One behavior, in product language: trigger, limit, order, failure, who sees what.> | path/to/file.ext::symbol | code | <given> → <expected outcome> |
| PFX-02 | <A configurable limit names where it is configured: "after the provider timeout (`PaymentConfig.timeout`)".> | path/to/config.ext | config | <A payment that takes longer than the timeout> → <the cart is kept and the user sees "try again"> |
| PFX-03 | *(proposed)* <A rule taken from a document and not proven by code.> | planned | code | <given> → <outcome> |
