# A month in the life of Melbourne

A D3 reverse-engineering of [Morphocode](https://morphocode.com/location-time-urban-data-visualization/)’s Melbourne pedestrian visualization. Each row is one sensor’s **hourly pedestrian counts** for March 2018.

As in the original, each row is a horizon chart: values are folded `bands` times, and darker color means a higher band.

## Controls

| Group   | Options                            | What it does                                                        |
| ------- | ---------------------------------- | ------------------------------------------------------------------- |
| Sort by | Name / Busiest / Weekend ÷ weekday | Reorders rows. The right-hand numbers show the current sort metric. |
| Scale   | Each sensor / Shared               | Color scale uses each sensor’s own max, or the global max.          |
| Show    | Busy hours / Quiet hours           | Quiet inverts values so empty hours are darker.                     |

## Chart built:

1. Group the CSV by sensor ID and fill a `days × 24` array for the month.
2. For each sensor, compute max, total, and weekend mean ÷ weekday mean.
3. The x-axis is hour index; top ticks are calendar dates.
4. Each row stacks `bands` area paths inside a `clipPath`. The same curve is shifted up by one row height at a time, so the clipped slices become the color bands.
5. Buttons only change `state`, then `update(true)` redraws order, paths, colors, and the legend.
