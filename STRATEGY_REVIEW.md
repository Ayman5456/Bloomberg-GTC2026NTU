# Competition research plan: review and next steps

Prepared 9 October 2026. This is a research-process recommendation, not a validated trading strategy or a set of live trade instructions. No return model, backtest or portfolio has been estimated yet.

## The main correction

Keep three separate questions:

1. **Return forecast:** which eligible stocks may outperform over the next 5–20 trading days, and why?
2. **Valuation:** what cash flows, growth, margins and risk assumptions support the current price or a different price?
3. **Risk:** how uncertain are the outcomes, how correlated are the positions, and what happens if the thesis fails?

A volatility model does not produce a stock's fair value. A return-prediction model does not establish mispricing. Monte Carlo propagates assumptions; it does not independently validate the expected returns fed into it.

## Competition constraints that determine the research

The provided 2026 handbook specifies a five-week period (12 October–13 November), long-only positions, no leverage, WLS membership, $1 million initial capital, a stated 20%/$200,000 company limit and ranking by relative P&L. It describes 20-minute execution and captain-only trade submission through TMSG. Verify exact operational rules in the competition network: the handbook alone does not specify the full scoring formula, benchmark-return convention, execution-price construction, currency conversion, corporate actions or treatment of pending orders.

Selling a high-momentum stock means reducing an existing holding, or choosing not to own it; opening a short is not permitted. A cheap company without a catalyst inside the competition window may remain cheap throughout it. A stop level is not a guaranteed loss cap around gaps or delayed execution.

## What to change in the proposed workflow

| Proposed step | Weakness | Better version |
|---|---|---|
| Split the team into emerging markets, developed markets, tech and high beta | Country groups, sectors and factors overlap. Several analysts can recommend the same underlying risk. | Use nonoverlapping coverage ownership, plus one shared data/backtest owner and one portfolio/risk owner. Keep sector, geography, currency and factor exposure in a common portfolio view. |
| Buy medium momentum and sell high momentum | This asserts a particular nonlinear pattern without evidence. Momentum depends on horizon and regime. | Define windows and ranks in advance; compare continuation, medium-rank and simple reversal rules on the same out-of-sample periods. Do not choose thresholds on the final test set. |
| Use ML to identify mispricing | The target is undefined; model residuals can reflect omitted risk or bad data. | First predict a specified forward return or cross-sectional rank. Treat outputs as hypotheses requiring evidence and a catalyst. |
| Build a volatility model to determine fair value | Volatility measures uncertainty, not business value. | Use scenario earnings/cash flows and comparable valuation for shortlisted companies; use volatility/correlation separately for sizing. |
| Run Monte Carlo to validate the model | Precise-looking results can be driven entirely by arbitrary drift, normality and correlation assumptions. | Validate signals out of sample first. Then simulate correlated scenarios, parameter uncertainty and gaps; include deterministic stress cases. |
| Optimize expected return and variance | Noisy mean estimates can dominate an optimizer. Individual variances ignore co-movement. | Start with capped equal weights or capped inverse-volatility weights. Compare with a shrinkage/factor covariance model and conservative return forecasts. |
| Rebalance whenever forecasts move | Small noisy changes can create excessive turnover. | Schedule reviews and use material-change thresholds, with exceptional reviews for thesis-breaking events. Model costs and TMSG execution. |

Momentum can suffer severe regime-dependent losses; see [Daniel and Moskowitz](https://www.nber.org/papers/w20439). Testing many variants increases selection bias; see [Bailey et al., The Probability of Backtest Overfitting](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf). Covariance estimation error matters for portfolio construction; see [Ledoit and Wolf](https://ledoit.net/honey.pdf).

## A feasible weekend build

**Friday: rules and clean inputs.** Confirm TMSG scoring/execution. Map the WLS listings to Capital IQ trading-item identifiers, preserving share classes and currencies. Assign coverage owners. Agree on a limited hypothesis set and one common investment memo template.

**Saturday: simple baselines before ML.** Use available adjusted daily returns, volume, sectors, fundamentals and estimates. Screen for data quality and practical execution; an initial research universe of a few hundred liquid names is an illustrative scope choice, not a competition rule. Compare one or two transparent signals against simple baselines. Review sector and country contributions so a supposed stock-selection result is not merely a market bet.

**Sunday: shortlist and portfolio review.** Research a manageable number of candidates. For each, record the variant view, dated catalyst, evidence, bull/base/bear returns over the actual holding horizon, invalidation trigger, execution plan and portfolio exposure. Only add a regularized model if it improves genuinely held-out results. Agree on initial sizing and review rules before Monday.

Keep the core model small enough to audit. A rank-based score or regularized regression is a reasonable first baseline; model complexity is earned by out-of-sample improvement, not by sophistication alone.

## Backtesting requirements

- Split chronologically **by date across all stocks**, not randomly by individual stock-day rows.
- Purge training observations whose forward-return labels overlap validation/test periods. Fit imputation, scaling, feature selection and model tuning on training data only. [scikit-learn leakage guidance](https://scikit-learn.org/stable/common_pitfalls.html).
- Use information available at the decision time: filing/release timestamps, historical estimate vintages, market hours and realistic execution delays. A latest revised financial series is not automatically point-in-time data.
- Today's WLS membership produces survivorship/selection bias if applied retrospectively. Without historical membership and delisted securities, label any result as exploratory rather than a clean historical strategy test.
- Model total-return adjustments, currency conversions and transaction costs consistently. Align international market closes before using cross-market signals.
- Evaluate rank correlation, realized benchmark-relative returns, drawdown, turnover, sector/country concentration, tail losses and performance across regimes. Forecast RMSE or classification accuracy alone is insufficient.
- Keep an untouched final test period. Record every hypothesis tried; do not repeatedly retune against that holdout.

For a stock with local-currency return r and return f on its currency measured in USD per local currency unit, USD return is (1+r)(1+f)-1. FX can therefore dominate an apparently sound local-market idea.

## Portfolio construction

For weights w and a covariance matrix Sigma, portfolio variance is w' Sigma w, not the weighted average of individual stock variances. Keep intended stock/catalyst exposures separate from unintended sector, country, beta and FX concentrations.

Start with simple, capped allocations. Treat the handbook's maximum as a hard ceiling, not a target. Aggregate exposure to the same company across listings. Use a scenario loss budget as an additional sizing constraint: for example, a **hypothetical** 1% portfolio loss budget under a 15% stock decline implies a weight no greater than 1%/15% = 6.67% before other constraints. This is an illustration, not a calibrated recommendation; a larger gap can exceed that loss budget.

Review both absolute portfolio risk and benchmark-relative risk. A high-beta portfolio can outperform in a rally without demonstrating stock-selection skill. Under the long-only/no-leverage constraint, manage unwanted risk through position selection, sizing and cash rather than assuming derivatives or shorts are available.

Monitor thesis changes, catalyst changes, limit breaches and material exposure drift daily. Rebalance on a planned schedule or meaningful change, not every minor model fluctuation. Model no-catalyst, adverse FX, earnings-gap and correlation-spike cases alongside the base case.

## What to obtain before leaving Bloomberg

These are priorities, **not additional API requests already made**. Sizes below are illustrative observations, not Bloomberg quota or billing estimates. Actual field access and allowance are account-specific.

| Priority | Item | Narrow scope and reason |
|---|---|---|
| First | TMSG scoring and execution help/settings | Save the relevant rule/help details: exact benchmark, price versus total return, currency, cash treatment, fees, execution delay/pricing, partial fills, market closures and limit enforcement. Small or no API use; uniquely relevant to the simulation. |
| First | WLS benchmark identity and daily history | Exact index identity, currency and return convention; 2–3 years of daily levels for the confirmed benchmark. One series is roughly 500–750 daily observations, not a stock-universe history. Useful for benchmark-relative research. |
| First | Current WLS constituent weights | One dated snapshot; earlier weights were deliberately discarded. About 10,419 weights, enabling active-weight/sector/country analysis once classifications are joined. Membership can change before the start. |
| Next | Cross-provider identifiers | Add listing ISIN and currency only if needed for Capital IQ mapping, preferably unresolved rows first. A company identifier alone cannot distinguish trading items. ISIN can still be shared across venues. |
| Shortlist only | Earnings/catalyst timing and consensus context | Confirmed/estimated dates, release times, relevant fiscal periods, consensus dispersion/revisions and source timestamps. Check Capital IQ access before duplicating this on Bloomberg. |
| Shortlist only | Quotes and microstructure sample | If an intraday hypothesis remains viable after checking TMSG, obtain spreads and a small 5-minute-bar sample for perhaps 10–20 names over 10–20 sessions. OHLCV bars alone do not establish order-book liquidity sweeps or actual stop-order activity. |
| Optional | Implied volatility/event expectations | Only for names with relevant, liquid options and a clear question. These are risk-neutral market-implied inputs, not objective probabilities or stock fair values. No full option-chain universe download. |

Capital IQ has financials, estimates, revisions and point-in-time estimate datasets; exact access depends on your license and interface. Do not assume these are Bloomberg-only. [S&P Capital IQ Estimates](https://www.spglobal.com/market-intelligence/en/solutions/capital-iq-estimates), [Capital IQ Pro](https://www.spglobal.com/market-intelligence/en/solutions/products/sp-capital-iq-pro).

Ask Bloomberg Help for the applicable remaining data allowance and how the intended fields are counted. Batching and caching avoid redundant requests but do not make a large data retrieval free. Do not download all stocks' tick histories, full option chains or broad financial histories merely because Terminal is about to close.
