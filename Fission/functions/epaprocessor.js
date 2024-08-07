module.exports = async function (context) {
  console.log(`Processed EPA observations data at a time`);
  return {
    status: 200,
    body: JSON.stringify (context.request.body.records.map ((epa) => {
        return {
            type:"epa",
            siteName: epa.siteName,
            siteType:epa.siteType,
            lat: epa.lat,
            lon: epa.lon,
            since: epa.since,
            until: epa.until,
            healthAdvice: epa.healthAdvice,
            averageValue: epa.averageValue,
            healthParameter: epa.healthParameter
        };
      }
    ))
  };
}
