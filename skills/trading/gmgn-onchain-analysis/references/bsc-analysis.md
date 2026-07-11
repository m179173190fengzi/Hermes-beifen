# BSC Chain Analysis Notes

## Key Differences from Solana

| Dimension | Solana | BSC |
|-----------|--------|-----|
| Daily active tokens | 100+ | 20-40 |
| Dominant culture | Western meme | Chinese communities |
| Token names | English (ANSEM, FOMO, BITCH) | Chinese (哈基米, 龙虾, 哭哭马, 白毛股神) |
| Launchpads | Pump.fun, Moonshot, letsbonk | FourMeme, Flap |
| KOL influence | Strong (Ansem, Murad, Belmar) | Weaker, mostly Chinese telegram groups |

## BSC Commands

```bash
# BSC 24h trending
gmgn-cli market trending --chain bsc --interval 24h --order-by volume --limit 20

# BSC new tokens (trenches)
gmgn-cli market trenches --chain bsc --type new_creation --filter-preset safe

# BSC token info
gmgn-cli token info --chain bsc --address <token_address>
```

## BSC Multi-Chain Context

When presenting BSC data alongside Solana:
- Always label chains clearly (`## 🔥 Solana` vs `## 🔥 BSC`)
- BSC has MUCH less volume — a top BSC token might have similar volume to a #5 Solana token
- BSC token names are predominantly Chinese — explain the cultural reference for non-Chinese readers
- Smart money counts on BSC can be very high (200+) on established projects due to stable/chinese trader base
- **MC thresholds differ:** BSC monitoring threshold is `100K` vs Solana's `200K` due to lower overall activity. BSC 24h active tokens ~20-40 vs Solana's 100+.
- **Recent BSC examples:** 哈基米 ($14.1M MC, SM 207), 龙虾 ($11.5M MC, SM 157), Freedom of Money ($6.2M MC, SM 207), 哭哭马 ($3.5M, SM 220)
- **Caution:** BSC tokens with very high SM counts (200+) but low volume/activity may indicate stale SM labels rather than genuine active interest. Cross-check with 24h volume.
