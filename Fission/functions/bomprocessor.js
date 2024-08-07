module.exports = async function (context) {
  console.log(`Processed all stations observations data at a time`);
  return {
    status: 200,
    body: JSON.stringify (context.request.body.allstation.map ((obs) => {
        const f = (i, n) => {
          return obs.local_date_time_full.substring (i, i + n);
        };
        const ts= `${f (0, 4)}-${f (4, 2)}-${f (6, 2)}T${f (8, 2)}:${f (10, 2)}:00`;
        return {
            type:"bom",
            STATE: "VIC",
            wmo:obs.wom,
            STATION: obs.name,
            Location: [obs.lon, obs.lat],
            DATE: ts,
            air_temp: obs.air_temp,
            rel_hum: obs.rel_hum,
            rain_trace: obs.rain_trace,
            press: obs.press,
            apparent_t: obs.apparent_t,
            dewpt:obs.dewpt,
            delta_t:obs.delta_t,
            wind_dir:obs.wind_dir,
            wind_spd_kmh:obs.wind_spd_kmh,
            wind_spd_kt:obs.wind_spd_kt,
            gust_kmh:obs.gust_kmh,
            gust_kt:obs.gust_kt
        };
      }
    ))
  };
}
