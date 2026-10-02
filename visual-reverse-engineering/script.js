const CONFIG = {
  file: "./data/melbourne_2018_03.csv",
  year: 2018,
  month: 2,
  bands: 4,
  rowHeight: 28,
  rowGap: 1,
  width: 1600,
  margin: { top: 28, right: 70, bottom: 10, left: 230 },
  colors: ["#f49cbb", "#f26a8d", "#dd2d4a", "#880d1e"],
  quietColors: ["#08306b", "#2171b5", "#6baed6", "#c6dbef"],
  duration: 750,
};

// interaction state
const state = {
  sort: "name",
  sharedScale: false,
  quiet: false,
};

// read data
d3.csv(CONFIG.file, (d) => ({
  id: +d.Sensor_ID,
  name: d.Sensor_Name.trim(),
  day: +d.Mdate, // 1–31
  hour: +d.Time, // 0–23
  count: +String(d.Hourly_Counts).replace(/,/g, ""),
})).then(init);

function init(rows) {
  const { bands, rowHeight, rowGap, width, margin } = CONFIG;

  // 2. transform data
  const daysInMonth = new Date(CONFIG.year, CONFIG.month + 1, 0).getDate();
  const hoursInMonth = daysInMonth * 24;

  // check if the array position i is weekend
  const isWeekend = (i) => {
    const weekday = new Date(
      CONFIG.year,
      CONFIG.month,
      Math.floor(i / 24) + 1,
    ).getDay();
    return weekday === 0 || weekday === 6;
  };

  const sensors = d3
    .groups(rows, (d) => d.id)
    .map(([id, list]) => {
      const values = new Array(hoursInMonth).fill(null);
      for (const d of list) values[(d.day - 1) * 24 + d.hour] = d.count;

      // weekend mean / weekday mean
      const weekendMean = d3.mean(
        values.filter((v, i) => v != null && isWeekend(i)),
      );
      const weekdayMean = d3.mean(
        values.filter((v, i) => v != null && !isWeekend(i)),
      );

      return {
        id,
        name: list[0].name,
        values,
        max: d3.max(values),
        total: d3.sum(values),
        ratio: weekdayMean ? (weekendMean || 0) / weekdayMean : 0,
      };
    });

  // 3. scale
  const innerW = width - margin.left - margin.right;
  const step = rowHeight + rowGap;
  const height = margin.top + sensors.length * step + margin.bottom;
  const globalMax = d3.max(sensors, (s) => s.max);

  // x: hour number (0 … 743) → horizontal position
  const x = d3.scaleLinear().domain([0, hoursInMonth]).range([0, innerW]);

  // 4. SVG skeleton
  const svg = d3
    .select("#chart")
    .append("svg")
    .attr("width", width)
    .attr("height", height);

  const g = svg
    .append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);

  // top axis: one tick per day
  const dayTicks = d3.range(0, daysInMonth).map((d) => d * 24);
  g.append("g")
    .attr("class", "axis")
    .call(
      d3
        .axisTop(x)
        .tickValues(dayTicks)
        .tickSize(4)
        .tickFormat((h) => {
          const date = new Date(CONFIG.year, CONFIG.month, h / 24 + 1);
          return date.getDate();
        }),
    )
    .selectAll("text")
    .attr("x", x(12)) // center the number in the date cell
    .style("text-anchor", "middle");

  // right column title (changes according to the sort criterion)
  const metricHeader = g
    .append("text")
    .attr("class", "metric")
    .attr("x", innerW + 8)
    .attr("y", -9);

  // 5. for each sensor, create a line (elements only, shapes and positions are determined in update())
  const row = g.selectAll(".row").data(sensors).join("g").attr("class", "row");

  // left column name
  row
    .append("text")
    .attr("class", "label")
    .attr("x", -8)
    .attr("y", rowHeight / 2)
    .attr("dy", "0.35em")
    .attr("text-anchor", "end")
    .text((s) => s.name);

  // right column number (sort criterion value)
  const metric = row
    .append("text")
    .attr("class", "metric")
    .attr("x", innerW + 8)
    .attr("y", rowHeight / 2)
    .attr("dy", "0.35em");

  // clip the line to the size of the line (clipPath)
  row
    .append("clipPath")
    .attr("id", (s) => `clip-${s.id}`)
    .append("rect")
    .attr("width", innerW)
    .attr("height", rowHeight);

  // draw the same area by stacking it bands times.
  // the b-th band is raised by (bands-1-b) × rowHeight,
  // so that only the pieces corresponding to the value range fit into the frame.
  const band = row
    .append("g")
    .attr("clip-path", (s) => `url(#clip-${s.id})`)
    .selectAll("path")
    .data((s) => d3.range(bands).map((b) => ({ s, b })))
    .join("path")
    .attr("transform", (d) => `translate(0,${-(bands - 1 - d.b) * rowHeight})`);

  //  (thin white line on the line)
  g.append("g")
    .selectAll("line")
    .data(dayTicks.slice(1))
    .join("line")
    .attr("class", "daygrid")
    .attr("x1", (h) => x(h))
    .attr("x2", (h) => x(h))
    .attr("y1", 0)
    .attr("y2", sensors.length * step - rowGap);

  // 6. update(): update the line order, area shape, color, and legend according to the state
  function update(animate) {
    const t = svg.transition().duration(animate ? CONFIG.duration : 0);

    // (a) line order
    const sorted = sensors.slice();
    if (state.sort === "total")
      sorted.sort((a, b) => d3.descending(a.total, b.total));
    else if (state.sort === "ratio")
      sorted.sort((a, b) => d3.descending(a.ratio, b.ratio));
    else sorted.sort((a, b) => d3.ascending(a.name, b.name));

    // sensor id → which line is it
    const position = new Map(sorted.map((s, i) => [s.id, i]));

    row
      .transition(t)
      .attr("transform", (s) => `translate(0,${position.get(s.id) * step})`);

    // right column number: show the value according to the current sort criterion
    metricHeader.text(
      state.sort === "total"
        ? "total"
        : state.sort === "ratio"
          ? "wkend ÷ wkday"
          : "",
    );
    metric.text((s) =>
      state.sort === "total"
        ? d3.format(".3s")(s.total)
        : state.sort === "ratio"
          ? "×" + d3.format(".2f")(s.ratio)
          : "",
    );

    // (b) area shape
    // for each sensor, calculate the path string once and use it for bands bands
    const shape = new Map(
      sensors.map((s) => {
        // the top value of this line: if shared scale, the global max, otherwise the sensor's own max
        const top = Math.max(1, state.sharedScale ? globalMax : s.max);

        // y: value → vertical position. range is rowHeight × bands,
        // so that the area is taller than the line by bands times, and then folded into the frame.
        const y = d3
          .scaleLinear()
          .domain([0, top])
          .range([rowHeight * bands, 0]);

        // show quiet time: reverse the value (top - value).
        // the less people, the higher the area, and the darker the color
        const shown = state.quiet
          ? s.values.map((v) => (v == null ? null : top - v))
          : s.values;

        const path = d3
          .area()
          .defined((v) => v != null) // empty time is broken
          .x((v, i) => x(i))
          .y0(rowHeight * bands)
          .y1((v) => y(v))(shown);

        return [s.id, path];
      }),
    );

    // (c) color
    const palette = state.quiet ? CONFIG.quietColors : CONFIG.colors;

    band
      .transition(t)
      .attr("d", (d) => shape.get(d.s.id))
      .attr("fill", (d) => palette[d.b]);

    // (d) legend
    const legend = d3.select("#legend");
    legend.selectAll("*").remove();
    legend.append("span").text(state.quiet ? "busier" : "fewer people");
    legend
      .selectAll(".swatch")
      .data(palette)
      .join("span")
      .attr("class", "swatch")
      .style("background", (c) => c);
    legend.append("span").text(state.quiet ? "quieter" : "more people");
    legend
      .append("span")
      .style("margin-left", "12px")
      .text(
        state.sharedScale
          ? "· darkest = busiest hour across all sensors"
          : "· darkest = each sensor's own busiest hour",
      );
    if (state.quiet)
      legend
        .select("span:last-child")
        .text(
          state.sharedScale
            ? "· darkest = empty, measured against the busiest sensor"
            : "· darkest = empty, measured against each sensor's own peak",
        );
  }

  // 7. connect the buttons: only the pressed button is on, change the state and update()
  function connect(groupId, onChange) {
    const buttons = d3.selectAll(`#${groupId} button`);
    buttons.on("click", function () {
      buttons.attr("aria-pressed", "false");
      d3.select(this).attr("aria-pressed", "true");
      onChange(this.dataset.value); // the value of the HTML data-value attribute
      update(true);
    });
  }

  connect("sort", (value) => {
    state.sort = value;
  });
  connect("scale", (value) => {
    state.sharedScale = value === "shared";
  });
  connect("mode", (value) => {
    state.quiet = value === "quiet";
  });

  update(false); // first screen
}
