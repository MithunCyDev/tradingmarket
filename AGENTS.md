# Agent playbook — Elite Forex

When the user says **analyze** an instrument in this repo, produce a **signal ticket and a marked graph**, not a research essay. Phone Cursor chats use this same flow. The PC browser at `http://localhost:5173` polls the ticket every 3 seconds. The desk has a **SWING | SCALP** toggle; each style is a separate file. Every analyze reply must include the ticket text **and** the graph in the same message.

## Instruments

| User says            | Desk id | TradingView     | Yahoo    |
| -------------------- | ------- | --------------- | -------- |
| GOLD                 | XAUUSD  | OANDA:XAUUSD    | PAXG-USD |
| BTC / Bitcoin        | BTCUSD  | BINANCE:BTCUSDT | BTC-USD  |
| Silver               | XAGUSD  | OANDA:XAGUSD    | SI=F     |
| US OIL / Oil / Crude | USOIL   | TVC:USOIL       | CL=F     |
| EUR/USD / EUR        | EURUSD  | FX:EURUSD       | EURUSD=X |

Scalp is first-class for **GOLD** and **BTC**. For Silver, US OIL, and EUR/USD, default to **NO TRADE** unless the M5 tape is unusually clean.

## Swing analyze flow

Plain `analyze GOLD` (or BTC, Silver, US OIL, EUR/USD) writes the swing ticket only. Do not touch the scalp file.

1. Map the user's words to a desk id using the table above.
2. Capture a technical snapshot. Do not invent OHLC, ATR, EMAs, or swing levels.

```powershell
npm run snapshot -- GOLD
```

3. Read `data/snapshots/{id}.json`. If `error` is set, or `lastPrice` / timeframes are missing, write **NO TRADE** and say the snapshot failed. Do not guess prices.
4. Write `data/signals/{id}.json` using the swing contract below. Overwrite the previous **swing** ticket for that symbol.
5. Validate:

```powershell
npm run check-signal -- GOLD
```

6. Render the marked chart from the same Yahoo OHLC (do not invent candles):

```powershell
npm run chart -- GOLD
```

Copy the PNG into `/opt/cursor/artifacts/` if `npm run chart` did not already print `ARTIFACT …`. Use a unique snake_case name.

7. Tell the user the action, entry zone, stop, TP1/TP2, invalidation, and that the open desk (SWING) should update within a few seconds. **In the same reply**, embed the graph with an HTML image tag (never markdown `![]()` to a workspace path — that shows “Waiting for upload…” and does not count):

```html
<img alt="GOLD H1 marked chart" src="/opt/cursor/artifacts/xauusd_swing_h1_no_trade.png" />
```

Use the `ARTIFACT` path printed by `npm run chart`. The marked chart and **Why HIGH / MEDIUM / LOW / NO TRADE** board are computed from this ticket plus the snapshot. Write `timeframeBias` and levels honestly so the visual reason matches the tape.

## Scalp analyze flow

`analyze scalp GOLD` / `analyze scalp BTC` writes a **separate** scalp ticket. Never overwrite `data/signals/{id}.json`.

1. Map the instrument the same way.
2. Capture the same snapshot (`npm run snapshot -- GOLD`). M1/M5 are included when Yahoo has them.
3. Read `data/snapshots/{id}.json`. If `error` is set, `lastPrice` is missing, or **M1 / M5 / M5 ATR** are missing, write **NO TRADE**. Do not guess prices.
4. Write `data/signals/scalp/{id}.json` using the scalp contract below. Overwrite the previous **scalp** ticket only.
5. Validate:

```powershell
npm run check-signal -- GOLD --style scalp
```

6. Render the scalp chart:

```powershell
npm run chart -- GOLD --style scalp
```

7. Tell the user the action, entry zone, stop, TP1/TP2, invalidation, and that the open desk **SCALP** toggle should update within a few seconds. Embed the graph with an HTML `<img>` tag to `/opt/cursor/artifacts/…` in the same reply. Confluence uses H1 + M15 as the stack, M5 as the signal frame, and M1 as the LTF guard.

## Swing ticket contract

Write camelCase JSON that matches `app.schemas.signal.SignalTicket`. Omit `style` or set `"style": "swing"`.

```json
{
  "symbol": "XAUUSD",
  "style": "swing",
  "analyzedAt": "2026-09-08T18:00:00Z",
  "action": "long",
  "confidence": "medium",
  "timeframe": "H1",
  "timeframeBias": {
    "M15": "long",
    "H1": "long",
    "H4": "range",
    "D1": "long"
  },
  "entryZone": { "low": 2640.0, "high": 2648.0 },
  "stop": 2632.0,
  "targets": { "tp1": 2660.0, "tp2": 2675.0 },
  "invalidation": 2628.0,
  "narrative": "One or two sentences grounded in the snapshot (trend, swings, ATR).",
  "riskNotes": "What kills the idea, session risk, and when not to take it."
}
```

Swing rules:

- `action` is only `long`, `short`, or `no_trade`.
- `confidence` is only `low`, `medium`, or `high`.
- `timeframe` is the ticket timeframe, usually `H1` or `H4` (allowed: `M15`, `H1`, `H4`, `D1`).
- `timeframeBias` must include `M15`, `H1`, `H4`, and `D1`, each `long`, `short`, or `range`.
- For `long` or `short`, `entryZone`, `stop`, `targets.tp1`, `targets.tp2`, and `invalidation` are required and must come from snapshot prices (last close, ATR, swing highs/lows). Do not invent round numbers that are not near those levels.
- For `no_trade`, set `entryZone`, `stop`, `targets`, and `invalidation` to `null`.
- Prefer **NO TRADE** when HTF and LTF disagree, ATR is missing, or the tape is mid-range with no level.
- Yahoo can lag. GOLD snapshots use spot-linked `PAXG-USD` (about the same dollars as OANDA:XAUUSD), never COMEX `GC=F` futures. If the live chart and the snapshot disagree by more than a few dollars, say so in `riskNotes` and choose `no_trade`. Do not present futures prints as the desk spot tape.

## Scalp ticket contract

```json
{
  "symbol": "XAUUSD",
  "style": "scalp",
  "analyzedAt": "2026-09-08T18:00:00Z",
  "action": "long",
  "confidence": "medium",
  "timeframe": "M5",
  "timeframeBias": {
    "M1": "long",
    "M5": "long",
    "M15": "long",
    "H1": "range"
  },
  "entryZone": { "low": 2640.0, "high": 2642.0 },
  "stop": 2637.0,
  "targets": { "tp1": 2646.0, "tp2": 2650.0 },
  "invalidation": 2635.0,
  "narrative": "One or two sentences grounded in M5 trend, M5 swings, and M5 ATR.",
  "riskNotes": "Yahoo M5 can lag TradingView. What kills the idea, and when not to take it."
}
```

Scalp rules:

- `style` must be `scalp`.
- `timeframe` must be `M5`.
- `timeframeBias` must include **`M1`, `M5`, `M15`, and `H1`** only (not H4/D1).
- Levels come from the **M5** snapshot (last close, ATR, swing highs/lows). Do not invent round numbers that are not near those levels.
- For `no_trade`, null the level fields the same as swing.
- Prefer **NO TRADE** when H1 and M15 disagree, M1/M5/ATR are missing, or price is mid-range with no M5 level.
- Always mention Yahoo vs TradingView lag in `riskNotes`. Drop confidence or stand aside if they disagree. GOLD uses spot-linked `PAXG-USD` vs the live OANDA chart; BTC snapshot is `BTC-USD` vs the live Binance chart. Never analyze GOLD off `GC=F`.
- Do not chase M1 entries on this feed.

## What not to do

- Do not promise a win rate or call this financial advice.
- Do not auto-trade or talk as if orders were placed.
- Do not write tickets for symbols outside the five on the desk.
- Do not write a scalp ticket into `data/signals/{id}.json`, or a swing ticket into `data/signals/scalp/{id}.json`.
- Do not send an analyze reply without the marked graph in the same message.
- Do not embed charts as markdown images of local files (`![](/workspace/…)`). Always use an HTML `<img>` pointing at `/opt/cursor/artifacts/…`.
