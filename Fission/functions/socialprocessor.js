module.exports = async function (context) {
  console.log(`Processed 40 social data at a time`);
  return {
    status: 200,
    body: JSON.stringify (context.request.body.toots.map ((obs) => {
        return {
            type:"mastodon_social",
            id: obs.id,
            created_at: obs.created_at,
            content: obs.content,
            sentiment: obs.sentiment
        };
      }
    ))
  };
}
